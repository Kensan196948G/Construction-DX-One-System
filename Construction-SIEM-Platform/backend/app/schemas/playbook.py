from datetime import datetime

from pydantic import BaseModel


class PlaybookRead(BaseModel):
    id: str
    name: str
    description: str
    trigger_event_type: str
    conditions: dict
    actions: list[dict]
    is_active: bool


class PlaybookExecuteRequest(BaseModel):
    playbook_id: str
    event_data: dict


class ActionResult(BaseModel):
    action: str
    success: bool
    message: str
    details: dict | None = None


class PlaybookExecutionResult(BaseModel):
    playbook_id: str
    playbook_name: str
    success: bool
    actions: list[ActionResult]
    execution_time: datetime
    log_id: str


class PlaybookLogRead(BaseModel):
    id: str
    playbook_id: str
    playbook_name: str
    trigger_event_type: str
    event_data_summary: str
    actions: list[ActionResult]
    success: bool
    executed_at: datetime
