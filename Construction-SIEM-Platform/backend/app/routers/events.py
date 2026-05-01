from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.event import SecurityEvent
from app.schemas.event import (
    SecurityEventCreate,
    SecurityEventListResponse,
    SecurityEventResponse,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=SecurityEventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    processed: bool | None = None,
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(SecurityEvent)
    count_query = select(func.count()).select_from(SecurityEvent)

    if severity:
        query = query.where(SecurityEvent.severity == severity)
        count_query = count_query.where(SecurityEvent.severity == severity)
    if processed is not None:
        query = query.where(SecurityEvent.processed == processed)
        count_query = count_query.where(SecurityEvent.processed == processed)
    if source:
        query = query.where(SecurityEvent.source == source)
        count_query = count_query.where(SecurityEvent.source == source)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(SecurityEvent.created_at.desc()).offset(offset).limit(per_page))
    events = result.scalars().all()

    return SecurityEventListResponse(
        data=[SecurityEventResponse.model_validate(e) for e in events],
        meta={"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page},
    )


@router.get("/{event_id}", response_model=SecurityEventResponse)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return SecurityEventResponse.model_validate(event)


@router.post("", response_model=SecurityEventResponse, status_code=201)
async def create_event(payload: SecurityEventCreate, db: AsyncSession = Depends(get_db)):
    event = SecurityEvent(**payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return SecurityEventResponse.model_validate(event)


@router.patch("/{event_id}/mark-processed", response_model=SecurityEventResponse)
async def mark_processed(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.processed = True
    event.processed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(event)
    return SecurityEventResponse.model_validate(event)
