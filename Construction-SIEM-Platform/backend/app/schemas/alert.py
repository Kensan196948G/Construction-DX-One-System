from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SeverityLevel = Literal["critical", "high", "medium", "low"]
AlertStatus = Literal["open", "processing", "closed"]


class AlertCreate(BaseModel):
    title: str
    severity: SeverityLevel = "low"
    source: str
    description: str
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    site: str | None = None


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


class AlertResponse(BaseModel):
    id: str
    title: str
    severity: str
    source: str
    description: str
    status: str
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    mitre_tactic: str | None
    mitre_technique: str | None
    site: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    status: str = "success"
    data: list[AlertResponse]
    meta: dict


class AlertSummaryItem(BaseModel):
    severity: str
    count: int


class AlertSummaryResponse(BaseModel):
    status: str = "success"
    data: list[AlertSummaryItem]
