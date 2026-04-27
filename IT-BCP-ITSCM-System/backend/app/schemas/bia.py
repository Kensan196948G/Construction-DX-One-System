from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

CriticalityLevel = Literal["critical", "high", "medium", "low"]
ProcessStatus = Literal["active", "archived"]


class BusinessProcessCreate(BaseModel):
    process_name: str
    description: str | None = None
    department: str | None = None
    criticality: CriticalityLevel = "medium"
    rto_minutes: int = 240
    rpo_minutes: int = 60
    recovery_priority: int = 10
    dependencies: list[str] | None = None
    peak_business_hours: dict | None = None
    legal_requirement: bool = False
    financial_impact_per_hour: float | None = None
    status: ProcessStatus = "active"
    last_reviewed_at: datetime | None = None


class BusinessProcessUpdate(BaseModel):
    process_name: str | None = None
    description: str | None = None
    department: str | None = None
    criticality: CriticalityLevel | None = None
    rto_minutes: int | None = None
    rpo_minutes: int | None = None
    recovery_priority: int | None = None
    dependencies: list[str] | None = None
    peak_business_hours: dict | None = None
    legal_requirement: bool | None = None
    financial_impact_per_hour: float | None = None
    status: ProcessStatus | None = None
    last_reviewed_at: datetime | None = None


class BusinessProcessRead(BaseModel):
    id: str
    process_name: str
    description: str | None
    department: str | None
    criticality: str
    rto_minutes: int
    rpo_minutes: int
    recovery_priority: int
    dependencies: list | None
    peak_business_hours: dict | None
    legal_requirement: bool
    financial_impact_per_hour: float | None
    status: str
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessProcessListResponse(BaseModel):
    status: str = "success"
    data: list[BusinessProcessRead]
    meta: dict


class BIARevisionCreate(BaseModel):
    version: int
    reviewed_by: str
    review_date: date
    changes_summary: str | None = None
    next_review_date: date


class BIARevisionRead(BaseModel):
    id: str
    version: int
    reviewed_by: str
    review_date: date
    changes_summary: str | None
    next_review_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class BIARevisionListResponse(BaseModel):
    status: str = "success"
    data: list[BIARevisionRead]
    meta: dict


class BIADashboardSummary(BaseModel):
    total_processes: int
    critical_count: int
    high_count: int
    by_department: dict
    by_priority: dict
