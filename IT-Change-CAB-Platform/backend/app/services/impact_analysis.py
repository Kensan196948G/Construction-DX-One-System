import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.freeze_period import FreezePeriod
from app.models.rfc import RFC

CHANGE_TYPE_WEIGHTS = {
    "standard": 1,
    "normal": 2,
    "emergency": 5,
}


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


def _get_duration_hours(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    return (end - start).total_seconds() / 3600


def _get_duration_score(hours: float | None) -> float:
    if hours is None:
        return 0
    if hours < 1:
        return 0
    if hours <= 4:
        return 1
    if hours <= 12:
        return 3
    if hours <= 24:
        return 5
    return 8


def _get_system_score(count: int) -> float:
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 3
    return 5 + (count - 3) * 2


def _categorize_impact(score: float) -> str:
    if score <= 5:
        return "low"
    if score <= 15:
        return "medium"
    if score <= 30:
        return "high"
    return "critical"


async def analyze_impact(rfc_data: dict, db: AsyncSession) -> dict:
    change_type = rfc_data.get("change_type", "normal")
    affected_systems_str = rfc_data.get("affected_systems")
    planned_start = rfc_data.get("planned_start")
    planned_end = rfc_data.get("planned_end")

    systems = _parse_systems(affected_systems_str)
    system_count = len(systems)
    change_weight = CHANGE_TYPE_WEIGHTS.get(change_type, 2)
    system_score = _get_system_score(system_count)
    duration_hours = _get_duration_hours(planned_start, planned_end)
    duration_score = _get_duration_score(duration_hours)

    freeze_conflicts = []
    if planned_start and planned_end:
        result = await db.execute(
            select(FreezePeriod).where(
                FreezePeriod.is_active,
                FreezePeriod.start_date <= planned_end,
                FreezePeriod.end_date >= planned_start,
            )
        )
        for fp in result.scalars().all():
            freeze_conflicts.append({
                "freeze_period_id": fp.id,
                "name": fp.name,
                "start_date": fp.start_date.isoformat(),
                "end_date": fp.end_date.isoformat(),
            })

    freeze_score = 10 if freeze_conflicts else 0
    impact_score = system_score * change_weight + duration_score + freeze_score
    impact_level = _categorize_impact(impact_score)

    def _severity(score: float, thresholds: tuple[float, ...]) -> str:
        if score <= thresholds[0]:
            return "low"
        if score <= thresholds[1]:
            return "medium"
        if score <= thresholds[2]:
            return "high"
        return "critical"

    details = [
        {
            "area": "systems",
            "severity": _severity(system_score, (1, 3, 7)),
            "description": f"Affects {system_count} system(s)",
            "score": system_score,
        },
        {
            "area": "change_type",
            "severity": change_type,
            "description": f"Change type: {change_type} (weight: {change_weight})",
            "score": float(change_weight),
        },
        {
            "area": "duration",
            "severity": _severity(duration_score, (1, 3, 5)),
            "description": f"Duration: {duration_hours:.1f}h" if duration_hours else "No duration set",
            "score": duration_score,
        },
    ]

    if freeze_conflicts:
        details.append({
            "area": "freeze_period",
            "severity": "critical",
            "description": f"Conflicts with {len(freeze_conflicts)} freeze period(s)",
            "score": float(freeze_score),
        })

    return {
        "rfc_title": rfc_data.get("title", ""),
        "change_type": change_type,
        "impact_score": impact_score,
        "impact_level": impact_level,
        "affected_system_count": system_count,
        "planned_duration_hours": duration_hours,
        "details": details,
        "freeze_period_conflicts": freeze_conflicts,
    }


async def detect_conflicts(rfc_data: dict, db: AsyncSession) -> list[dict]:
    planned_start = rfc_data.get("planned_start")
    planned_end = rfc_data.get("planned_end")
    affected_systems_str = rfc_data.get("affected_systems", "")
    change_type = rfc_data.get("change_type", "normal")

    if not planned_start or not planned_end:
        return []

    systems = _parse_systems(affected_systems_str)
    rfc_id = rfc_data.get("id")

    query = select(RFC).where(
        RFC.planned_start.isnot(None),
        RFC.planned_end.isnot(None),
        RFC.planned_start <= planned_end,
        RFC.planned_end >= planned_start,
    )
    if rfc_id:
        query = query.where(RFC.id != rfc_id)

    result = await db.execute(query)
    overlapping = result.scalars().all()

    conflicts = []
    for other in overlapping:
        other_systems = _parse_systems(other.affected_systems)
        shared_systems = list(set(systems) & set(other_systems))
        overlap_details = []

        if shared_systems:
            overlap_details.append(f"Shared systems: {', '.join(shared_systems)}")
        else:
            overlap_details.append("Overlapping change window")

        if change_type == "emergency" and other.change_type == "emergency":
            overlap_details.append("Multiple emergency changes in same window")

        conflicts.append({
            "rfc_id": other.id,
            "title": other.title,
            "change_type": other.change_type,
            "status": other.status,
            "planned_start": other.planned_start.isoformat() if other.planned_start else None,
            "planned_end": other.planned_end.isoformat() if other.planned_end else None,
            "overlap_details": overlap_details,
            "shared_systems": shared_systems,
        })

    freeze_result = await db.execute(
        select(FreezePeriod).where(
            FreezePeriod.is_active,
            FreezePeriod.start_date <= planned_end,
            FreezePeriod.end_date >= planned_start,
        )
    )
    for fp in freeze_result.scalars().all():
        conflicts.append({
            "rfc_id": None,
            "title": f"[FREEZE] {fp.name}",
            "change_type": "freeze",
            "status": "active",
            "planned_start": fp.start_date.isoformat(),
            "planned_end": fp.end_date.isoformat(),
            "overlap_details": [f"Planned during freeze period: {fp.name}"],
            "shared_systems": [],
        })

    return conflicts


async def get_change_calendar(
    date_from: datetime,
    date_to: datetime,
    db: AsyncSession,
) -> list[dict]:
    result = await db.execute(
        select(RFC).where(
            RFC.planned_start.isnot(None),
            RFC.planned_start >= date_from,
            RFC.planned_start <= date_to,
        ).order_by(RFC.planned_start)
    )
    rfcs = result.scalars().all()

    freeze_result = await db.execute(
        select(FreezePeriod).where(
            FreezePeriod.is_active,
            FreezePeriod.start_date <= date_to,
            FreezePeriod.end_date >= date_from,
        )
    )
    freeze_periods = freeze_result.scalars().all()

    entries: list[dict] = []

    for rfc in rfcs:
        entries.append({
            "type": "rfc",
            "id": rfc.id,
            "title": rfc.title,
            "change_type": rfc.change_type,
            "status": rfc.status,
            "planned_start": rfc.planned_start.isoformat() if rfc.planned_start else None,
            "planned_end": rfc.planned_end.isoformat() if rfc.planned_end else None,
            "systems": _parse_systems(rfc.affected_systems),
        })

    for fp in freeze_periods:
        entries.append({
            "type": "freeze",
            "id": fp.id,
            "title": fp.name,
            "change_type": "freeze",
            "status": "active" if fp.is_active else "inactive",
            "planned_start": fp.start_date.isoformat(),
            "planned_end": fp.end_date.isoformat(),
            "systems": _parse_systems(fp.affected_systems),
        })

    entries.sort(key=lambda e: e.get("planned_start", ""))
    return entries


async def get_system_impact_map(db: AsyncSession) -> dict:
    result = await db.execute(
        select(RFC).where(
            RFC.planned_start.isnot(None),
            RFC.planned_end.isnot(None),
        )
    )
    rfcs = result.scalars().all()

    system_map: dict[str, list[dict]] = {}
    for rfc in rfcs:
        systems = _parse_systems(rfc.affected_systems)
        for sys in systems:
            if sys not in system_map:
                system_map[sys] = []
            system_map[sys].append({
                "rfc_id": rfc.id,
                "title": rfc.title,
                "change_type": rfc.change_type,
                "status": rfc.status,
                "planned_start": rfc.planned_start.isoformat() if rfc.planned_start else None,
                "planned_end": rfc.planned_end.isoformat() if rfc.planned_end else None,
            })

    return {
        "systems": system_map,
        "total_systems": len(system_map),
        "total_changes": len(rfcs),
    }


async def check_freeze_period_conflicts(
    date_from: datetime,
    date_to: datetime,
    db: AsyncSession,
) -> list[FreezePeriod]:
    result = await db.execute(
        select(FreezePeriod).where(
            FreezePeriod.is_active,
            FreezePeriod.start_date <= date_to,
            FreezePeriod.end_date >= date_from,
        )
    )
    return list(result.scalars().all())
