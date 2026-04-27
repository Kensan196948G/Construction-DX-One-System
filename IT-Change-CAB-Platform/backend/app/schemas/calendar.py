from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    title: str
    event_type: str
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None
    change_type: str | None = None
    systems: list[str] = []


class UpcomingChange(BaseModel):
    id: str
    title: str
    change_type: str
    status: str
    planned_start: str | None = None
    planned_end: str | None = None
    days_until_start: int | None = None


class CABScheduleEntry(BaseModel):
    id: str
    title: str
    meeting_date: str | None = None
    status: str
    agenda: str | None = None
    rfc_count: int = 0
