import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cab_meeting import CABMeeting
from app.models.freeze_period import FreezePeriod
from app.models.rfc import RFC


def _parse_systems(affected_systems: str | None) -> list[str]:
    if not affected_systems:
        return []
    try:
        systems = json.loads(affected_systems)
        if isinstance(systems, list):
            return [s.strip() for s in systems if s.strip()]
    except (json.JSONDecodeError, TypeError):
        pass
    return [s.strip() for s in affected_systems.split(",") if s.strip()]


async def get_calendar_events(year: int, month: int, db: AsyncSession) -> list[dict]:
    month_start = datetime(year, month, 1)
    month_end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    rfc_result = await db.execute(
        select(RFC)
        .where(
            RFC.planned_start.isnot(None),
            RFC.planned_start >= month_start,
            RFC.planned_start < month_end,
        )
        .order_by(RFC.planned_start)
    )
    rfcs = rfc_result.scalars().all()

    meeting_result = await db.execute(
        select(CABMeeting)
        .where(
            CABMeeting.meeting_date.isnot(None),
            CABMeeting.meeting_date >= month_start,
            CABMeeting.meeting_date < month_end,
        )
        .order_by(CABMeeting.meeting_date)
    )
    meetings = meeting_result.scalars().all()

    freeze_result = await db.execute(
        select(FreezePeriod).where(
            FreezePeriod.start_date < month_end,
            FreezePeriod.end_date >= month_start,
        )
    )
    freezes = freeze_result.scalars().all()

    events: list[dict] = []
    for rfc in rfcs:
        events.append(
            {
                "id": rfc.id,
                "title": rfc.title,
                "event_type": "rfc",
                "start_date": rfc.planned_start.isoformat() if rfc.planned_start else None,
                "end_date": rfc.planned_end.isoformat() if rfc.planned_end else None,
                "status": rfc.status,
                "change_type": rfc.change_type,
                "systems": _parse_systems(rfc.affected_systems),
            }
        )
    for meeting in meetings:
        events.append(
            {
                "id": meeting.id,
                "title": meeting.title,
                "event_type": "cab_meeting",
                "start_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
                "end_date": None,
                "status": meeting.status,
                "change_type": None,
                "systems": [],
            }
        )
    for fp in freezes:
        events.append(
            {
                "id": fp.id,
                "title": fp.name,
                "event_type": "freeze",
                "start_date": fp.start_date.isoformat(),
                "end_date": fp.end_date.isoformat(),
                "status": "active" if fp.is_active else "inactive",
                "change_type": None,
                "systems": _parse_systems(fp.affected_systems),
            }
        )

    return events


async def get_upcoming_changes(days: int, db: AsyncSession) -> list[dict]:
    now = datetime.utcnow()
    future = now + timedelta(days=days)

    result = await db.execute(
        select(RFC)
        .where(
            RFC.planned_start.isnot(None),
            RFC.planned_start >= now,
            RFC.planned_start <= future,
        )
        .order_by(RFC.planned_start)
    )
    rfcs = result.scalars().all()

    changes: list[dict] = []
    for rfc in rfcs:
        days_until = (rfc.planned_start.date() - now.date()).days if rfc.planned_start else None
        changes.append(
            {
                "id": rfc.id,
                "title": rfc.title,
                "change_type": rfc.change_type,
                "status": rfc.status,
                "planned_start": rfc.planned_start.isoformat() if rfc.planned_start else None,
                "planned_end": rfc.planned_end.isoformat() if rfc.planned_end else None,
                "days_until_start": days_until,
            }
        )

    return changes


async def get_cab_schedule(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(CABMeeting)
        .where(
            CABMeeting.status == "scheduled",
        )
        .order_by(CABMeeting.meeting_date.asc().nullslast())
    )
    meetings = result.scalars().all()

    schedule: list[dict] = []
    for meeting in meetings:
        rfc_result = await db.execute(select(RFC).where(RFC.cab_meeting_id == meeting.id))
        rfcs = rfc_result.scalars().all()
        schedule.append(
            {
                "id": meeting.id,
                "title": meeting.title,
                "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
                "status": meeting.status,
                "agenda": meeting.agenda,
                "rfc_count": len(rfcs),
            }
        )

    return schedule


async def get_resource_calendar(system: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(RFC).where(
            RFC.planned_start.isnot(None),
            RFC.planned_end.isnot(None),
        )
    )
    rfcs = result.scalars().all()

    entries: list[dict] = []
    for rfc in rfcs:
        systems = _parse_systems(rfc.affected_systems)
        if system in systems:
            entries.append(
                {
                    "id": rfc.id,
                    "title": rfc.title,
                    "change_type": rfc.change_type,
                    "status": rfc.status,
                    "planned_start": rfc.planned_start.isoformat() if rfc.planned_start else None,
                    "planned_end": rfc.planned_end.isoformat() if rfc.planned_end else None,
                    "systems": systems,
                }
            )

    return entries
