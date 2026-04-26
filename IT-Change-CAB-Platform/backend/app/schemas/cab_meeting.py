from datetime import datetime
from typing import Literal

from pydantic import BaseModel

MeetingStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]


class CABMeetingCreate(BaseModel):
    title: str
    status: MeetingStatus = "scheduled"
    meeting_date: datetime | None = None
    agenda: str | None = None
    attendees: str | None = None


class CABMeetingResponse(BaseModel):
    id: str
    title: str
    status: str
    meeting_date: datetime | None
    agenda: str | None
    attendees: str | None
    minutes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CABMeetingListResponse(BaseModel):
    status: str = "success"
    data: list[CABMeetingResponse]
    meta: dict
