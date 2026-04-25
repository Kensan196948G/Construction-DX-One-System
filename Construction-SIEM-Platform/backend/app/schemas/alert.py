from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    title: str = Field(..., max_length=256)
    description: str | None = None
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    event_count: int = Field(default=1, ge=1)
    rule_name: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = None
    assigned_to: str | None = Field(default=None, max_length=64)
    mitre_technique: str | None = Field(default=None, max_length=32)
    mitre_tactic: str | None = Field(default=None, max_length=64)


class AlertStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|false_positive)$")
    assigned_to: str | None = Field(default=None, max_length=64)


class AlertRead(AlertCreate):
    id: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}
