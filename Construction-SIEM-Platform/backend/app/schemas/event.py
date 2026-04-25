from datetime import datetime

from pydantic import BaseModel, Field


class SecurityEventCreate(BaseModel):
    event_type: str = Field(..., max_length=64)
    severity: str = Field(default="info", pattern="^(info|low|medium|high|critical)$")
    source_ip: str | None = Field(default=None, max_length=45)
    source_hostname: str | None = Field(default=None, max_length=256)
    destination_ip: str | None = Field(default=None, max_length=45)
    destination_port: int | None = Field(default=None, ge=1, le=65535)
    occurred_at: datetime
    raw_log: str | None = None
    log_source: str | None = Field(default=None, max_length=64)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    correlation_id: str | None = None


class SecurityEventRead(SecurityEventCreate):
    id: str
    ingested_at: datetime
    is_processed: bool

    model_config = {"from_attributes": True}


class SecurityEventBulkCreate(BaseModel):
    events: list[SecurityEventCreate] = Field(..., min_length=1, max_length=1000)
