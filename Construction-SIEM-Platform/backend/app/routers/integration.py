"""Integration API router: SIEM ↔ ZTIG / CAB cross-system communication."""
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.alert import Alert
from app.models.event import SecurityEvent

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

_api_key_header = APIKeyHeader(name="X-Integration-Key", auto_error=False)


async def verify_integration_key(
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> None:
    expected = getattr(settings, "integration_api_key", "dev-integration-key-change-in-prod")
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing integration API key",
        )


IntegrationAuth = Depends(verify_integration_key)


# ── Schemas ───────────────────────────────────────────────────────────────────

class IngestAuthEventRequest(BaseModel):
    event_type: str
    user_id: str | None = None
    username: str | None = None
    actor_ip: str | None = None
    timestamp: datetime
    severity: str = "low"
    details: dict = {}
    source_system: str = "ZTIG"


class IngestAuthEventBatchRequest(BaseModel):
    events: list[IngestAuthEventRequest]
    source_system: str = "ZTIG"


class PendingIncidentResponse(BaseModel):
    id: str
    title: str
    severity: str
    source: str
    description: str
    created_at: datetime
    requires_change: bool


class EscalateToCABRequest(BaseModel):
    incident_id: str
    requested_by: str
    change_reason: str
    urgency: str = "normal"   # normal | urgent | emergency


class EscalateToCABResponse(BaseModel):
    incident_id: str
    cab_rfc_reference: str
    status: str
    message: str


class AlertSummary(BaseModel):
    total_open: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    generated_at: datetime


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/events/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest auth events from ZTIG",
)
async def ingest_auth_events(
    payload: IngestAuthEventBatchRequest,
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Receive authentication events from ZTIG and store as security events."""
    created_ids = []
    for ev in payload.events:
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=f"auth.{ev.event_type}",
            source=ev.source_system,
            source_ip=ev.actor_ip,
            severity=ev.severity,
            description=(
                f"Auth event from ZTIG: {ev.event_type}"
                f"{f' by {ev.username}' if ev.username else ''}"
            ),
            raw_log=str(ev.details),
            processed=False,
            created_at=ev.timestamp.replace(tzinfo=None),
        )
        db.add(event)
        created_ids.append(event.id)
    await db.commit()
    return {"ingested": len(created_ids), "event_ids": created_ids}


@router.get(
    "/incidents/pending",
    response_model=list[PendingIncidentResponse],
    summary="Get pending high-severity incidents for CAB escalation",
)
async def get_pending_incidents(
    severity: str = Query("high", description="Minimum severity (high|critical)"),
    hours: int = Query(24, ge=1, le=168),
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Provide open high-severity alerts to CAB for RFC creation."""
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
    severity_filter = ["critical"] if severity == "critical" else ["high", "critical"]

    result = await db.execute(
        select(Alert).where(
            Alert.severity.in_(severity_filter),
            Alert.status == "open",
            Alert.created_at >= cutoff,
        ).order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()

    return [
        PendingIncidentResponse(
            id=a.id,
            title=a.title,
            severity=a.severity,
            source=a.source,
            description=a.description,
            created_at=a.created_at,
            requires_change=a.severity in ("high", "critical"),
        )
        for a in alerts
    ]


@router.post(
    "/incidents/{incident_id}/escalate-to-cab",
    response_model=EscalateToCABResponse,
    summary="Mark incident as escalated to CAB",
)
async def escalate_incident_to_cab(
    incident_id: str,
    payload: EscalateToCABRequest,
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Update alert status to indicate CAB escalation has occurred."""
    result = await db.execute(select(Alert).where(Alert.id == incident_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    alert.status = "escalated_to_cab"
    alert.acknowledged = True
    alert.acknowledged_by = payload.requested_by
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()

    rfc_ref = f"RFC-SIEM-{incident_id[:8].upper()}"
    return EscalateToCABResponse(
        incident_id=incident_id,
        cab_rfc_reference=rfc_ref,
        status="escalated",
        message=f"Incident escalated to CAB. RFC reference: {rfc_ref}",
    )


@router.get(
    "/alerts/summary",
    response_model=AlertSummary,
    summary="Get alert summary for GRC dashboard",
)
async def get_alert_summary(
    _: None = IntegrationAuth,
    db: AsyncSession = Depends(get_db),
):
    """Aggregate open alert counts by severity for GRC risk dashboard."""
    result = await db.execute(select(Alert).where(Alert.status == "open"))
    alerts = result.scalars().all()

    return AlertSummary(
        total_open=len(alerts),
        critical_count=sum(1 for a in alerts if a.severity == "critical"),
        high_count=sum(1 for a in alerts if a.severity == "high"),
        medium_count=sum(1 for a in alerts if a.severity == "medium"),
        low_count=sum(1 for a in alerts if a.severity == "low"),
        generated_at=datetime.now(UTC),
    )
