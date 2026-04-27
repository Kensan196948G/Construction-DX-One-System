from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.exercise import Exercise
from app.models.incident import Incident
from app.models.system import ITSystem

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    # Incident counts by status
    inc_result = await db.execute(
        select(Incident.status, func.count(Incident.id)).group_by(Incident.status)
    )
    incident_by_status = {row[0]: row[1] for row in inc_result.all()}

    # Critical/high open incidents
    critical_result = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.severity.in_(["critical", "high"]),
            Incident.status.in_(["open", "investigating"]),
        )
    )
    critical_open = critical_result.scalar() or 0

    # System counts by status
    sys_result = await db.execute(
        select(ITSystem.status, func.count(ITSystem.id)).group_by(ITSystem.status)
    )
    systems_by_status = {row[0]: row[1] for row in sys_result.all()}

    total_systems = sum(systems_by_status.values())
    operational_systems = systems_by_status.get("operational", 0)

    # Exercise stats
    ex_result = await db.execute(
        select(Exercise.status, func.count(Exercise.id)).group_by(Exercise.status)
    )
    exercises_by_status = {row[0]: row[1] for row in ex_result.all()}

    return {
        "status": "success",
        "data": {
            "incidents": {
                "total": sum(incident_by_status.values()),
                "by_status": incident_by_status,
                "critical_open": critical_open,
            },
            "systems": {
                "total": total_systems,
                "by_status": systems_by_status,
                "availability_rate": (
                    round(operational_systems / total_systems, 4) if total_systems > 0 else 1.0
                ),
            },
            "exercises": {
                "total": sum(exercises_by_status.values()),
                "by_status": exercises_by_status,
            },
        },
    }
