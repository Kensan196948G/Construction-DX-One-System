import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.freeze_period import FreezePeriod
from app.schemas.freeze_period import (
    FreezePeriodConflictCheck,
    FreezePeriodCreate,
    FreezePeriodListResponse,
    FreezePeriodRead,
    FreezePeriodUpdate,
)
from app.services import impact_analysis as svc

router = APIRouter()


@router.post("/freeze-periods", response_model=FreezePeriodRead, status_code=201)
async def create_freeze_period(
    payload: FreezePeriodCreate,
    db: AsyncSession = Depends(get_db),
):
    fp = FreezePeriod(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_active=payload.is_active,
        affected_systems=payload.affected_systems,
        reason=payload.reason,
        created_by=payload.created_by,
    )
    db.add(fp)
    await db.commit()
    await db.refresh(fp)
    return FreezePeriodRead.model_validate(fp)


@router.get("/freeze-periods", response_model=FreezePeriodListResponse)
async def list_freeze_periods(
    is_active: bool | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(FreezePeriod).order_by(FreezePeriod.created_at.desc())
    if is_active is not None:
        query = query.where(FreezePeriod.is_active == is_active)
    if date_from:
        query = query.where(FreezePeriod.end_date >= date_from)
    if date_to:
        query = query.where(FreezePeriod.start_date <= date_to)

    result = await db.execute(query)
    periods = result.scalars().all()

    return FreezePeriodListResponse(
        data=[FreezePeriodRead.model_validate(p) for p in periods],
        meta={"total": len(periods)},
    )


@router.get("/freeze-periods/check", response_model=FreezePeriodConflictCheck)
async def check_freeze_conflict(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
):
    conflicting = await svc.check_freeze_period_conflicts(date_from, date_to, db)
    return FreezePeriodConflictCheck(
        has_conflict=len(conflicting) > 0,
        conflicting_periods=[FreezePeriodRead.model_validate(c) for c in conflicting],
    )


@router.get("/freeze-periods/{fp_id}", response_model=FreezePeriodRead)
async def get_freeze_period(fp_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FreezePeriod).where(FreezePeriod.id == fp_id))
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="Freeze period not found")
    return FreezePeriodRead.model_validate(fp)


@router.put("/freeze-periods/{fp_id}", response_model=FreezePeriodRead)
async def update_freeze_period(
    fp_id: str,
    payload: FreezePeriodUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FreezePeriod).where(FreezePeriod.id == fp_id))
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="Freeze period not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fp, field, value)

    fp.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(fp)
    return FreezePeriodRead.model_validate(fp)


@router.delete("/freeze-periods/{fp_id}", status_code=204)
async def delete_freeze_period(fp_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FreezePeriod).where(FreezePeriod.id == fp_id))
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="Freeze period not found")

    await db.delete(fp)
    await db.commit()
