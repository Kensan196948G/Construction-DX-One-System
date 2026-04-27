
from pydantic import BaseModel


class IoCCheckRequest(BaseModel):
    value: str
    ioc_type: str


class IoCMatchDetail(BaseModel):
    ioc_value: str
    ioc_type: str
    threat_type: str
    confidence: float
    severity: str
    description: str
    source: str
    first_seen: str
    last_seen: str


class IoCCheckResponse(BaseModel):
    status: str = "success"
    ioc_value: str
    ioc_type: str
    malicious: bool
    matches: list[IoCMatchDetail]
    risk_score: float


class IoCReportResponse(BaseModel):
    status: str = "success"
    ioc_value: str
    ioc_type: str
    risk_score: float
    total_matches: int
    matches: list[IoCMatchDetail]
    summary: str


class CorrelateEventRequest(BaseModel):
    event_data: dict


class CorrelateEventMatch(BaseModel):
    field: str
    value: str
    ioc_type: str
    match: IoCMatchDetail


class CorrelateEventResponse(BaseModel):
    status: str = "success"
    matches: list[CorrelateEventMatch]
    total_matches: int
    risk_score: float


class RecentThreatItem(BaseModel):
    ioc_value: str
    ioc_type: str
    threat_type: str
    confidence: float
    severity: str
    last_seen: str


class RecentThreatsResponse(BaseModel):
    status: str = "success"
    data: list[RecentThreatItem]
