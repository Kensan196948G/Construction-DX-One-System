import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.cab_meeting import CABMeeting
from app.schemas.cab_meeting import (
    CABMeetingCreate,
    CABMeetingListResponse,
    CABMeetingResponse,
)

router = APIRouter()


@router.get("/cab-meetings", response_model=CABMeetingListResponse)
async def list_meetings(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CABMeeting).order_by(CABMeeting.created_at.desc())
    if status:
        query = query.where(CABMeeting.status == status)

    result = await db.execute(query)
    meetings = result.scalars().all()

    return CABMeetingListResponse(
        data=[CABMeetingResponse.model_validate(m) for m in meetings],
        meta={"total": len(meetings)},
    )


@router.post("/cab-meetings", response_model=CABMeetingResponse, status_code=201)
async def create_meeting(payload: CABMeetingCreate, db: AsyncSession = Depends(get_db)):
    meeting = CABMeeting(
        id=str(uuid.uuid4()),
        title=payload.title,
        status=payload.status,
        meeting_date=payload.meeting_date,
        agenda=payload.agenda,
        attendees=payload.attendees,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return CABMeetingResponse.model_validate(meeting)


@router.get("/cab-meetings/{meeting_id}", response_model=CABMeetingResponse)
async def get_meeting(meeting_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CABMeeting).where(CABMeeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="CAB Meeting not found")
    return CABMeetingResponse.model_validate(meeting)


@router.patch("/cab-meetings/{meeting_id}/complete", response_model=CABMeetingResponse)
async def complete_meeting(
    meeting_id: str,
    minutes: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CABMeeting).where(CABMeeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="CAB Meeting not found")

    meeting.status = "completed"
    if minutes:
        meeting.minutes = minutes
    meeting.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(meeting)
    return CABMeetingResponse.model_validate(meeting)
