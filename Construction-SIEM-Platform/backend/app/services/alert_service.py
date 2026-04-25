from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertStatusUpdate


async def create_alert(db: AsyncSession, payload: AlertCreate) -> Alert:
    alert = Alert(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        risk_score=payload.risk_score,
        event_count=payload.event_count,
        rule_name=payload.rule_name,
        correlation_id=payload.correlation_id,
        assigned_to=payload.assigned_to,
        mitre_technique=payload.mitre_technique,
        mitre_tactic=payload.mitre_tactic,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


async def list_alerts(
    db: AsyncSession,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.detected_at.desc())
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_alert(db: AsyncSession, alert_id: str) -> Alert | None:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalar_one_or_none()


async def update_alert_status(
    db: AsyncSession, alert_id: str, payload: AlertStatusUpdate
) -> Alert | None:
    alert = await get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = payload.status
    if payload.assigned_to is not None:
        alert.assigned_to = payload.assigned_to
    if payload.status == "resolved":
        alert.resolved_at = datetime.now(UTC)
    await db.flush()
    return alert
