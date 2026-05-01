import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.event import SecurityEvent

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def _boost_severity(base: str, correlation_count: int) -> str:
    idx = _SEVERITY_ORDER.index(base) if base in _SEVERITY_ORDER else 0
    boost = correlation_count // 2
    new_idx = min(idx + boost, len(_SEVERITY_ORDER) - 1)
    return _SEVERITY_ORDER[new_idx]


async def enrich_alert(alert: Alert, db: AsyncSession) -> dict:
    now = datetime.now(UTC)
    window_24h = now - timedelta(hours=24)

    related_query = select(func.count()).select_from(SecurityEvent).where(
        SecurityEvent.source == alert.source,
        SecurityEvent.created_at >= window_24h,
    )
    related_events_count = (await db.execute(related_query)).scalar_one()

    history_conditions = [
        Alert.id != alert.id,
        Alert.created_at >= window_24h,
    ]
    or_clauses = [Alert.source == alert.source]
    if alert.mitre_technique:
        or_clauses.append(Alert.mitre_technique == alert.mitre_technique)
    history_conditions.append(or_(*or_clauses))
    history_query = (
        select(Alert)
        .where(*history_conditions)
        .order_by(Alert.created_at.desc())
    )
    history_result = await db.execute(history_query)
    history_alerts = history_result.scalars().all()

    correlated_alerts_count = len(history_alerts)
    calculated_severity = _boost_severity(alert.severity, correlated_alerts_count)

    return {
        "alert_id": alert.id,
        "related_events_count": related_events_count,
        "matched_rules": [],
        "entity_history": [
            {
                "alert_id": a.id,
                "title": a.title,
                "severity": a.severity,
                "source": a.source,
                "created_at": a.created_at,
            }
            for a in history_alerts
        ],
        "correlated_alerts_count": correlated_alerts_count,
        "calculated_severity": calculated_severity,
        "enrichment_timestamp": now,
    }


async def correlate_alerts(alert: Alert, db: AsyncSession) -> list[dict]:
    now = datetime.now(UTC)
    window = now - timedelta(hours=24)

    correlations: dict[str, dict] = {}

    if alert.source:
        result = await db.execute(
            select(Alert).where(
                Alert.source == alert.source,
                Alert.id != alert.id,
                Alert.created_at >= window,
            )
        )
        for a in result.scalars().all():
            if a.id not in correlations:
                correlations[a.id] = {
                    "alert_id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "source": a.source,
                    "correlation_reason": "same_source",
                    "created_at": a.created_at,
                }

    if alert.mitre_technique:
        result = await db.execute(
            select(Alert).where(
                Alert.mitre_technique == alert.mitre_technique,
                Alert.id != alert.id,
                Alert.created_at >= window,
            )
        )
        for a in result.scalars().all():
            if a.id not in correlations:
                correlations[a.id] = {
                    "alert_id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "source": a.source,
                    "correlation_reason": "same_mitre_technique",
                    "created_at": a.created_at,
                }
            elif correlations[a.id]["correlation_reason"] == "same_source":
                correlations[a.id]["correlation_reason"] = "same_source_and_technique"

    if alert.site:
        result = await db.execute(
            select(Alert).where(
                Alert.site == alert.site,
                Alert.id != alert.id,
                Alert.created_at >= window,
            )
        )
        for a in result.scalars().all():
            if a.id not in correlations:
                correlations[a.id] = {
                    "alert_id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "source": a.source,
                    "correlation_reason": "same_site",
                    "created_at": a.created_at,
                }

    return sorted(correlations.values(), key=lambda x: x["created_at"], reverse=True)


async def get_alert_timeline(alert_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return []

    timeline: list[dict] = []

    timeline.append({
        "timestamp": alert.created_at,
        "event_type": "alert_created",
        "description": f"Alert created: {alert.title}",
        "details": {"severity": alert.severity, "source": alert.source},
    })

    if alert.acknowledged_at:
        timeline.append({
            "timestamp": alert.acknowledged_at,
            "event_type": "alert_acknowledged",
            "description": f"Acknowledged by {alert.acknowledged_by or 'system'}",
            "details": {"acknowledged_by": alert.acknowledged_by},
        })

    if alert.updated_at and alert.updated_at != alert.created_at:
        timeline.append({
            "timestamp": alert.updated_at,
            "event_type": "alert_updated",
            "description": "Alert status updated",
            "details": {"status": alert.status},
        })

    window_start = alert.created_at - timedelta(hours=1)
    window_end = alert.created_at + timedelta(hours=1)
    events_result = await db.execute(
        select(SecurityEvent).where(
            SecurityEvent.source == alert.source,
            SecurityEvent.created_at.between(window_start, window_end),
        ).order_by(SecurityEvent.created_at)
    )
    for event in events_result.scalars().all():
        timeline.append({
            "timestamp": event.created_at,
            "event_type": "related_event",
            "description": event.description[:200],
            "details": {
                "event_id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
            },
        })

    timeline.sort(key=lambda x: x["timestamp"])
    return timeline
