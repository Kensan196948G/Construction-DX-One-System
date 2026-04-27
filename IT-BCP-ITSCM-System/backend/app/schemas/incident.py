from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SeverityLevel = Literal["critical", "high", "medium", "low"]
IncidentStatus = Literal["open", "investigating", "resolved", "closed"]


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: SeverityLevel = "low"
    affected_systems: str | None = None
    rto_deadline: datetime | None = None


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    bcp_activated: bool
    rto_deadline: datetime | None
    rto_achieved: bool
    affected_systems: str | None
    recovery_time_minutes: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    status: str = "success"
    data: list[IncidentResponse]
    meta: dict
