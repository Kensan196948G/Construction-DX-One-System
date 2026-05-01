import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.system import ITSystem
from app.schemas.system import ITSystemCreate, ITSystemListResponse, ITSystemResponse

router = APIRouter()


@router.get("/systems", response_model=ITSystemListResponse)
async def list_systems(
    tier: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ITSystem).order_by(ITSystem.created_at.desc())
    if tier:
        query = query.where(ITSystem.tier == tier)
    if status:
        query = query.where(ITSystem.status == status)

    result = await db.execute(query)
    systems = result.scalars().all()

    return ITSystemListResponse(
        data=[ITSystemResponse.model_validate(s) for s in systems],
        meta={"total": len(systems)},
    )


@router.post("/systems", response_model=ITSystemResponse, status_code=201)
async def create_system(payload: ITSystemCreate, db: AsyncSession = Depends(get_db)):
    system = ITSystem(
        id=str(uuid.uuid4()),
        name=payload.name,
        tier=payload.tier,
        status=payload.status,
        rto_minutes=payload.rto_minutes,
        rpo_minutes=payload.rpo_minutes,
        description=payload.description,
        owner=payload.owner,
    )
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return ITSystemResponse.model_validate(system)


@router.get("/systems/{system_id}", response_model=ITSystemResponse)
async def get_system(system_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ITSystem).where(ITSystem.id == system_id))
    system = result.scalar_one_or_none()
    if not system:
        raise HTTPException(status_code=404, detail="IT System not found")
    return ITSystemResponse.model_validate(system)


@router.patch("/systems/{system_id}/status", response_model=ITSystemResponse)
async def update_system_status(
    system_id: str,
    status: str = Query(..., description="operational | degraded | offline"),
    db: AsyncSession = Depends(get_db),
):
    if status not in ("operational", "degraded", "offline"):
        raise HTTPException(status_code=400, detail="Invalid status value")

    result = await db.execute(select(ITSystem).where(ITSystem.id == system_id))
    system = result.scalar_one_or_none()
    if not system:
        raise HTTPException(status_code=404, detail="IT System not found")

    system.status = status
    system.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(system)
    return ITSystemResponse.model_validate(system)
