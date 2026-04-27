from datetime import datetime

from pydantic import BaseModel


class MatchedRuleInfo(BaseModel):
    rule_id: str
    name: str
    severity: str
    category: str


class EntityHistoryEntry(BaseModel):
    alert_id: str
    title: str
    severity: str
    source: str
    created_at: datetime


class AlertEnrichment(BaseModel):
    alert_id: str
    related_events_count: int
    matched_rules: list[MatchedRuleInfo]
    entity_history: list[EntityHistoryEntry]
    correlated_alerts_count: int
    calculated_severity: str
    enrichment_timestamp: datetime


class AlertCorrelation(BaseModel):
    alert_id: str
    title: str
    severity: str
    source: str
    correlation_reason: str
    created_at: datetime


class AlertTimelineEntry(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    details: dict | None = None
