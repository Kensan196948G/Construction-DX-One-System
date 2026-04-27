from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import calendar_service as svc

router = APIRouter()


@router.get("/calendar/events")
async def get_calendar_events(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    events = await svc.get_calendar_events(year, month, db)
    return {"status": "success", "data": events, "meta": {"total": len(events)}}


@router.get("/calendar/upcoming")
async def get_upcoming_changes(
    days: int = Query(14, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    changes = await svc.get_upcoming_changes(days, db)
    return {"status": "success", "data": changes, "meta": {"total": len(changes)}}


@router.get("/calendar/cab-schedule")
async def get_cab_schedule(db: AsyncSession = Depends(get_db)):
    schedule = await svc.get_cab_schedule(db)
    return {"status": "success", "data": schedule, "meta": {"total": len(schedule)}}


@router.get("/calendar/resource/{system}")
async def get_resource_calendar(
    system: str,
    db: AsyncSession = Depends(get_db),
):
    entries = await svc.get_resource_calendar(system, db)
    return {"status": "success", "data": entries, "meta": {"total": len(entries)}}
