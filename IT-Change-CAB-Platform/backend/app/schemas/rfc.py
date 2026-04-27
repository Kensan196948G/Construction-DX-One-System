from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ChangeType = Literal["standard", "normal", "emergency"]
RFCStatus = Literal["draft", "submitted", "approved", "rejected", "implemented", "closed"]
PriorityLevel = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["low", "medium", "high"]


class RFCCreate(BaseModel):
    title: str
    description: str
    change_type: ChangeType = "normal"
    priority: PriorityLevel = "medium"
    risk_level: RiskLevel = "medium"
    requester: str | None = None
    affected_systems: str | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None


class RFCStatusUpdate(BaseModel):
    status: RFCStatus
    rejection_reason: str | None = None


class RFCResponse(BaseModel):
    id: str
    title: str
    description: str
    change_type: str
    status: str
    priority: str
    risk_level: str
    requester: str | None
    affected_systems: str | None
    planned_start: datetime | None
    planned_end: datetime | None
    cab_meeting_id: str | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RFCListResponse(BaseModel):
    status: str = "success"
    data: list[RFCResponse]
    meta: dict


class ImpactAnalysisRequest(BaseModel):
    title: str
    change_type: ChangeType = "normal"
    affected_systems: str | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None


class ImpactAnalysisDetail(BaseModel):
    area: str
    severity: str
    description: str
    score: float


class ImpactAnalysisResult(BaseModel):
    rfc_title: str
    change_type: str
    impact_score: float
    impact_level: str
    affected_system_count: int
    planned_duration_hours: float | None = None
    details: list[ImpactAnalysisDetail]
    freeze_period_conflicts: list[dict]


class ConflictDetectionResult(BaseModel):
    has_conflicts: bool
    total_conflicts: int
    conflicting_rfcs: list[dict]


class ChangeCalendarEntry(BaseModel):
    date: str
    items: list[dict]
