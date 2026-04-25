from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.event import SecurityEventBulkCreate, SecurityEventCreate, SecurityEventRead
from app.services import event_service

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=SecurityEventRead, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    payload: SecurityEventCreate, db: AsyncSession = Depends(get_db)
) -> SecurityEventRead:
    event = await event_service.ingest_event(db, payload)
    return SecurityEventRead.model_validate(event)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_ingest(payload: SecurityEventBulkCreate, db: AsyncSession = Depends(get_db)) -> dict:
    events = await event_service.bulk_ingest(db, payload.events)
    return {"ingested": len(events)}


@router.get("", response_model=list[SecurityEventRead])
async def list_events(
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[SecurityEventRead]:
    events = await event_service.list_events(db, severity=severity, limit=limit, offset=offset)
    return [SecurityEventRead.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=SecurityEventRead)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)) -> SecurityEventRead:
    event = await event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return SecurityEventRead.model_validate(event)


@router.patch("/{event_id}/processed", response_model=SecurityEventRead)
async def mark_processed(event_id: str, db: AsyncSession = Depends(get_db)) -> SecurityEventRead:
    event = await event_service.mark_processed(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return SecurityEventRead.model_validate(event)
