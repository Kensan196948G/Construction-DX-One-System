from datetime import datetime

from pydantic import BaseModel


class FreezePeriodCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    affected_systems: str | None = None
    reason: str | None = None
    created_by: str | None = None


class FreezePeriodUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    affected_systems: str | None = None
    reason: str | None = None
    created_by: str | None = None


class FreezePeriodRead(BaseModel):
    id: str
    name: str
    description: str | None
    start_date: datetime
    end_date: datetime
    is_active: bool
    affected_systems: str | None
    reason: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FreezePeriodListResponse(BaseModel):
    status: str = "success"
    data: list[FreezePeriodRead]
    meta: dict


class FreezePeriodConflictCheck(BaseModel):
    has_conflict: bool
    conflicting_periods: list[FreezePeriodRead]
