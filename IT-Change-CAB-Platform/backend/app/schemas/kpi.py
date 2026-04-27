from pydantic import BaseModel


class KPIMetric(BaseModel):
    name: str
    value: float
    target: float
    unit: str
    status: str


class KPITrendPoint(BaseModel):
    date: str
    value: float


class KPITrend(BaseModel):
    metric: str
    data: list[KPITrendPoint]


class KPIAlert(BaseModel):
    metric: str
    value: float
    threshold: float
    severity: str
    message: str


class SLAComplianceItem(BaseModel):
    change_type: str
    total: int
    met: int
    compliance_percent: float


class SLACompliance(BaseModel):
    items: list[SLAComplianceItem]
    overall: float


class CABEfficiency(BaseModel):
    total_meetings: int
    total_rfcs_reviewed: int
    avg_rfcs_per_meeting: float
    approval_rate: float
    avg_approval_days: float | None = None


class DashboardSummary(BaseModel):
    metrics: dict
    alerts: list[KPIAlert]
    trends: list[KPITrend]
    sla: SLACompliance
    cab_efficiency: CABEfficiency
