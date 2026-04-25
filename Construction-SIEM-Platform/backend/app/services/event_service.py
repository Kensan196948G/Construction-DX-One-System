from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import SecurityEvent
from app.schemas.event import SecurityEventCreate


async def ingest_event(db: AsyncSession, payload: SecurityEventCreate) -> SecurityEvent:
    event = SecurityEvent(
        event_type=payload.event_type,
        severity=payload.severity,
        source_ip=payload.source_ip,
        source_hostname=payload.source_hostname,
        destination_ip=payload.destination_ip,
        destination_port=payload.destination_port,
        occurred_at=payload.occurred_at,
        raw_log=payload.raw_log,
        log_source=payload.log_source,
        risk_score=payload.risk_score,
        correlation_id=payload.correlation_id,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def bulk_ingest(db: AsyncSession, payloads: list[SecurityEventCreate]) -> list[SecurityEvent]:
    events = [
        SecurityEvent(
            event_type=p.event_type,
            severity=p.severity,
            source_ip=p.source_ip,
            source_hostname=p.source_hostname,
            destination_ip=p.destination_ip,
            destination_port=p.destination_port,
            occurred_at=p.occurred_at,
            raw_log=p.raw_log,
            log_source=p.log_source,
            risk_score=p.risk_score,
            correlation_id=p.correlation_id,
        )
        for p in payloads
    ]
    db.add_all(events)
    await db.flush()
    return events


async def list_events(
    db: AsyncSession,
    severity: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SecurityEvent]:
    stmt = select(SecurityEvent).order_by(SecurityEvent.occurred_at.desc())
    if severity:
        stmt = stmt.where(SecurityEvent.severity == severity)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_event(db: AsyncSession, event_id: str) -> SecurityEvent | None:
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    return result.scalar_one_or_none()


async def mark_processed(db: AsyncSession, event_id: str) -> SecurityEvent | None:
    event = await get_event(db, event_id)
    if event:
        event.is_processed = True
        await db.flush()
    return event
