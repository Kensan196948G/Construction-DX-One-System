from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SeverityLevel = Literal["critical", "high", "medium", "low"]


class SecurityEventCreate(BaseModel):
    event_type: str
    source: str
    source_ip: str | None = None
    destination_ip: str | None = None
    severity: SeverityLevel = "low"
    description: str
    raw_log: str | None = None
    site: str | None = None


class SecurityEventResponse(BaseModel):
    id: str
    event_type: str
    source: str
    source_ip: str | None
    destination_ip: str | None
    severity: str
    description: str
    raw_log: str | None
    processed: bool
    processed_at: datetime | None
    site: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SecurityEventListResponse(BaseModel):
    status: str = "success"
    data: list[SecurityEventResponse]
    meta: dict
