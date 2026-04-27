from datetime import datetime

from pydantic import BaseModel


class IncidentTrendPoint(BaseModel):
    date: str
    open: int = 0
    resolved: int = 0
    critical: int = 0


class IncidentReportTimeline(BaseModel):
    event: str
    timestamp: datetime | None


class ExecutiveSummary(BaseModel):
    generated_at: datetime
    active_incidents: dict
    system_health: dict
    bcp_activation_count: int
    rto_compliance_rate: float
    recent_exercises: list[dict]
    readiness_score: int


class IncidentReport(BaseModel):
    incident_id: str
    title: str
    severity: str
    status: str
    description: str
    timeline: list[IncidentReportTimeline]
    systems_affected: list[str]
    bcp_activated: bool
    rto_deadline: datetime | None
    rto_achieved: bool
    recovery_time_minutes: int | None
    root_cause_analysis: str
    created_at: datetime
    updated_at: datetime


class WeeklyKPIReport(BaseModel):
    generated_at: datetime
    incident_trends: list[IncidentTrendPoint]
    drill_completion_rate: float
    system_availability_rate: float
    rto_rpo_compliance_trend: dict


class BCPReadinessReport(BaseModel):
    generated_at: datetime
    plan_coverage: dict
    drill_completion_rate: float
    recovery_capability_score: float
    gaps_and_recommendations: list[str]
