import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.event import SecurityEvent
from app.schemas.events_processing import (
    BatchIngestRequest,
    BatchIngestResponse,
    NormalizedEvent,
    ProcessingStats,
    RawEventIngest,
)
from app.services.message_queue import event_normalizer, message_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events_processing"])


@router.post("/ingest", response_model=NormalizedEvent, status_code=201)
async def ingest_raw_event(payload: RawEventIngest, db: AsyncSession = Depends(get_db)):
    try:
        normalized = event_normalizer.normalize_event(
            payload.raw_log, payload.source_type
        )
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

    event = SecurityEvent(
        event_type=normalized.get("event_type", "unknown"),
        source=normalized.get("source", payload.source),
        source_ip=normalized.get("source_ip"),
        destination_ip=normalized.get("destination_ip"),
        severity=normalized.get("severity", "low"),
        description=normalized.get("description", "")[:500],
        raw_log=payload.raw_log,
        site=payload.metadata.get("site") if payload.metadata else None,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    message_queue.publish(
        "security_events",
        event.id,
        {
            "event_id": event.id,
            "event_type": event.event_type,
            "severity": event.severity,
            "source": event.source,
            "normalized": normalized,
        },
    )

    return NormalizedEvent(
        id=event.id,
        cef_formatted=normalized.get("cef_formatted", ""),
        event_type=event.event_type,
        source=event.source,
        source_type=payload.source_type,
        severity=event.severity,
        description=event.description,
        raw_log=payload.raw_log,
        normalized_at=event.created_at,
    )


@router.post("/ingest/batch", response_model=BatchIngestResponse)
async def ingest_raw_events_batch(
    payload: BatchIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    succeeded = 0
    errors: list[str] = []
    for i, raw_event in enumerate(payload.events):
        try:
            normalized = event_normalizer.normalize_event(
                raw_event.raw_log, raw_event.source_type
            )
            event = SecurityEvent(
                event_type=normalized.get("event_type", "unknown"),
                source=normalized.get("source", raw_event.source),
                source_ip=normalized.get("source_ip"),
                destination_ip=normalized.get("destination_ip"),
                severity=normalized.get("severity", "low"),
                description=normalized.get("description", "")[:500],
                raw_log=raw_event.raw_log,
                site=raw_event.metadata.get("site") if raw_event.metadata else None,
            )
            db.add(event)
            succeeded += 1
        except Exception as e:
            errors.append(f"Event {i}: {e!s}")

    await db.commit()

    return BatchIngestResponse(
        total=len(payload.events),
        succeeded=succeeded,
        failed=len(payload.events) - succeeded,
        errors=errors,
    )


@router.get("/processing/stats", response_model=ProcessingStats)
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(UTC)
    window_start = now - timedelta(hours=24)

    total_result = await db.execute(
        select(func.count()).select_from(SecurityEvent)
        .where(SecurityEvent.created_at >= window_start)
    )
    total_ingested = total_result.scalar_one()

    normalized_result = await db.execute(
        select(func.count()).select_from(SecurityEvent)
        .where(SecurityEvent.processed, SecurityEvent.created_at >= window_start)
    )
    total_normalized = normalized_result.scalar_one()

    by_source = await db.execute(
        select(SecurityEvent.source, func.count().label("count"))
        .where(SecurityEvent.created_at >= window_start)
        .group_by(SecurityEvent.source)
    )
    by_source_type = {row[0]: row[1] for row in by_source.all()}

    by_severity = await db.execute(
        select(SecurityEvent.severity, func.count().label("count"))
        .where(SecurityEvent.created_at >= window_start)
        .group_by(SecurityEvent.severity)
    )
    by_severity_dict = {row[0]: row[1] for row in by_severity.all()}

    return ProcessingStats(
        total_ingested=total_ingested,
        total_normalized=total_normalized,
        by_source_type=by_source_type,
        by_severity=by_severity_dict,
        period_start=window_start,
        period_end=now,
    )
