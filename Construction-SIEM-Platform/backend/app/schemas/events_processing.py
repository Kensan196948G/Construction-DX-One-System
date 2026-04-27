from datetime import datetime

from pydantic import BaseModel


class RawEventIngest(BaseModel):
    raw_log: str
    source_type: str
    source: str
    metadata: dict | None = None


class NormalizedEvent(BaseModel):
    id: str
    cef_formatted: str
    event_type: str
    source: str
    source_type: str
    severity: str
    description: str
    raw_log: str
    normalized_at: datetime


class BatchIngestRequest(BaseModel):
    events: list[RawEventIngest]


class BatchIngestResponse(BaseModel):
    status: str = "success"
    total: int
    succeeded: int
    failed: int
    errors: list[str]


class ProcessingStats(BaseModel):
    status: str = "success"
    total_ingested: int
    total_normalized: int
    by_source_type: dict[str, int]
    by_severity: dict[str, int]
    period_start: datetime
    period_end: datetime
