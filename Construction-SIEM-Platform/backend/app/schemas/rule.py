from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SeverityLevel = Literal["critical", "high", "medium", "low"]
RuleType = Literal["sigma", "yara", "custom"]


class RuleCreate(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_type: RuleType = "sigma"
    rule_content: str
    severity: SeverityLevel = "low"
    category: str = "general"
    mitre_attack_id: str | None = None


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rule_type: RuleType | None = None
    rule_content: str | None = None
    severity: SeverityLevel | None = None
    category: str | None = None
    is_active: bool | None = None
    mitre_attack_id: str | None = None


class RuleResponse(BaseModel):
    id: str
    rule_id: str
    name: str
    description: str
    rule_type: str
    rule_content: str
    severity: str
    category: str
    is_active: bool
    mitre_attack_id: str | None
    match_count: int
    last_matched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    status: str = "success"
    data: list[RuleResponse]
    meta: dict


class RuleTest(BaseModel):
    rule_content: str
    rule_type: RuleType = "sigma"
    event_data: dict


class RuleTestResult(BaseModel):
    matched: bool
    details: str | None = None


class RuleToggleResponse(BaseModel):
    status: str = "success"
    data: RuleResponse


class RuleStatsCategory(BaseModel):
    category: str
    count: int


class RuleStatsSeverity(BaseModel):
    severity: str
    count: int


class RuleStatsSummary(BaseModel):
    status: str = "success"
    total_rules: int
    active_rules: int
    by_severity: list[RuleStatsSeverity]
    by_category: list[RuleStatsCategory]
