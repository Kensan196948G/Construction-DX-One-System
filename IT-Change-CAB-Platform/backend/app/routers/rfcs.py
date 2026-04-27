import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rfc import RFC
from app.schemas.rfc import RFCCreate, RFCListResponse, RFCResponse, RFCStatusUpdate

router = APIRouter()


@router.get("/rfcs", response_model=RFCListResponse)
async def list_rfcs(
    status: str | None = Query(None),
    change_type: str | None = Query(None),
    priority: str | None = Query(None),
    risk_level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(RFC).order_by(RFC.created_at.desc())
    if status:
        query = query.where(RFC.status == status)
    if change_type:
        query = query.where(RFC.change_type == change_type)
    if priority:
        query = query.where(RFC.priority == priority)
    if risk_level:
        query = query.where(RFC.risk_level == risk_level)

    result = await db.execute(query)
    rfcs = result.scalars().all()

    return RFCListResponse(
        data=[RFCResponse.model_validate(r) for r in rfcs],
        meta={"total": len(rfcs)},
    )


@router.post("/rfcs", response_model=RFCResponse, status_code=201)
async def create_rfc(payload: RFCCreate, db: AsyncSession = Depends(get_db)):
    rfc = RFC(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        change_type=payload.change_type,
        priority=payload.priority,
        risk_level=payload.risk_level,
        requester=payload.requester,
        affected_systems=payload.affected_systems,
        planned_start=payload.planned_start,
        planned_end=payload.planned_end,
    )
    db.add(rfc)
    await db.commit()
    await db.refresh(rfc)
    return RFCResponse.model_validate(rfc)


@router.get("/rfcs/{rfc_id}", response_model=RFCResponse)
async def get_rfc(rfc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")
    return RFCResponse.model_validate(rfc)


@router.patch("/rfcs/{rfc_id}/status", response_model=RFCResponse)
async def update_rfc_status(
    rfc_id: str,
    payload: RFCStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    rfc.status = payload.status
    if payload.rejection_reason:
        rfc.rejection_reason = payload.rejection_reason
    rfc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rfc)
    return RFCResponse.model_validate(rfc)


@router.patch("/rfcs/{rfc_id}/assign-meeting", response_model=RFCResponse)
async def assign_meeting(
    rfc_id: str,
    meeting_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    rfc.cab_meeting_id = meeting_id
    rfc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rfc)
    return RFCResponse.model_validate(rfc)
