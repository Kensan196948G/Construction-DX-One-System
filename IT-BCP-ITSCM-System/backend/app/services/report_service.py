import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.models.incident import Incident
from app.models.system import ITSystem

logger = logging.getLogger(__name__)


async def generate_executive_summary(db: AsyncSession) -> dict:
    now = datetime.now(UTC)

    inc_by_severity = await db.execute(
        select(Incident.severity, func.count(Incident.id))
        .where(Incident.status.in_(["open", "investigating"]))
        .group_by(Incident.severity)
    )
    severity_breakdown = {row[0]: row[1] for row in inc_by_severity.all()}
    critical_count = severity_breakdown.get("critical", 0) + severity_breakdown.get("high", 0)
    total_active = sum(severity_breakdown.values())

    sys_by_status = await db.execute(
        select(ITSystem.status, func.count(ITSystem.id)).group_by(ITSystem.status)
    )
    systems_by_status = {row[0]: row[1] for row in sys_by_status.all()}

    sys_by_tier = await db.execute(
        select(ITSystem.tier, func.count(ITSystem.id)).group_by(ITSystem.tier)
    )
    systems_by_tier = {row[0]: row[1] for row in sys_by_tier.all()}

    total_systems = sum(systems_by_status.values())
    degraded = systems_by_status.get("degraded", 0)
    down = systems_by_status.get("offline", 0)

    bcp_count = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.bcp_activated.is_(True),
            Incident.status.in_(["open", "investigating"]),
        )
    )
    bcp_activation_count = bcp_count.scalar() or 0

    resolved_total = await db.execute(
        select(func.count(Incident.id)).where(Incident.status == "resolved")
    )
    total_resolved = resolved_total.scalar() or 0
    rto_met = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.status == "resolved", Incident.rto_achieved.is_(True)
        )
    )
    rto_met_count = rto_met.scalar() or 0
    rto_compliance_rate = round(rto_met_count / total_resolved, 4) if total_resolved > 0 else 1.0

    thirty_days_ago = now - timedelta(days=30)
    ex_result = await db.execute(
        select(Exercise)
        .where(Exercise.completed_date >= thirty_days_ago.date())
        .order_by(Exercise.completed_date.desc())
    )
    recent_exercises = [
        {
            "title": ex.title,
            "type": ex.exercise_type,
            "completed_date": ex.completed_date.isoformat() if ex.completed_date else None,
            "participants": ex.participants,
        }
        for ex in ex_result.scalars().all()
    ]

    sys_avail_rate = (total_systems - degraded - down) / total_systems if total_systems > 0 else 1.0

    total_ex = (await db.execute(select(func.count(Exercise.id)))).scalar() or 0
    completed_ex = (
        await db.execute(
            select(func.count(Exercise.id)).where(Exercise.status == "completed")
        )
    ).scalar() or 0
    drill_rate = completed_ex / total_ex if total_ex > 0 else 1.0

    total_inc = (await db.execute(select(func.count(Incident.id)))).scalar() or 0
    bcp_inc = (
        await db.execute(
            select(func.count(Incident.id)).where(Incident.bcp_activated.is_(True))
        )
    ).scalar() or 0
    bcp_coverage = bcp_inc / total_inc if total_inc > 0 else 1.0

    readiness_score = min(
        100,
        int(
            sys_avail_rate * 30 + drill_rate * 20 + bcp_coverage * 20 + rto_compliance_rate * 30
        ),
    )

    return {
        "generated_at": now,
        "active_incidents": {
            "total": total_active,
            "critical_high": critical_count,
            "severity_breakdown": severity_breakdown,
        },
        "system_health": {
            "total": total_systems,
            "degraded": degraded,
            "down": down,
            "by_tier": systems_by_tier,
            "availability_rate": round(sys_avail_rate, 4),
        },
        "bcp_activation_count": bcp_activation_count,
        "rto_compliance_rate": rto_compliance_rate,
        "recent_exercises": recent_exercises,
        "readiness_score": readiness_score,
    }


async def generate_incident_report(db: AsyncSession, incident_id: str) -> dict | None:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        return None

    systems_affected = []
    if incident.affected_systems:
        systems_affected = [s.strip() for s in incident.affected_systems.split(",") if s.strip()]

    timeline = []
    timeline.append({"event": "Incident created", "timestamp": incident.created_at})

    if incident.bcp_activated:
        timeline.append({"event": "BCP activated", "timestamp": incident.updated_at})

    if incident.recovery_time_minutes is not None:
        resolved_at = incident.created_at + timedelta(minutes=incident.recovery_time_minutes)
        timeline.append({"event": "Incident resolved", "timestamp": resolved_at})
    elif incident.updated_at and incident.updated_at != incident.created_at:
        timeline.append({"event": f"Status updated to {incident.status}", "timestamp": incident.updated_at})

    timeline.sort(key=lambda x: x["timestamp"] or datetime.min)

    root_cause = (
        "Root cause analysis not yet performed"
        if incident.status != "resolved"
        else "Root cause analysis pending further investigation"
    )

    return {
        "incident_id": incident.id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "description": incident.description,
        "timeline": timeline,
        "systems_affected": systems_affected,
        "bcp_activated": incident.bcp_activated,
        "rto_deadline": incident.rto_deadline,
        "rto_achieved": incident.rto_achieved,
        "recovery_time_minutes": incident.recovery_time_minutes,
        "root_cause_analysis": root_cause,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }


async def generate_weekly_kpi_report(db: AsyncSession) -> dict:
    now = datetime.now(UTC)
    seven_days_ago = now - timedelta(days=7)

    inc_all = await db.execute(
        select(Incident)
        .where(Incident.created_at >= seven_days_ago)
        .order_by(Incident.created_at.asc())
    )
    incidents = inc_all.scalars().all()

    daily_trends: dict[str, dict] = defaultdict(lambda: {"open": 0, "resolved": 0, "critical": 0})
    for inc in incidents:
        day_key = inc.created_at.strftime("%Y-%m-%d")
        if inc.status in ("open", "investigating"):
            daily_trends[day_key]["open"] += 1
        elif inc.status == "resolved":
            daily_trends[day_key]["resolved"] += 1
        if inc.severity in ("critical", "high"):
            daily_trends[day_key]["critical"] += 1

    trend_data = [
        {"date": d, **daily_trends[d]} for d in sorted(daily_trends.keys())
    ]

    total_drills = (await db.execute(select(func.count(Exercise.id)))).scalar() or 0
    completed_drills = (
        await db.execute(
            select(func.count(Exercise.id)).where(Exercise.status == "completed")
        )
    ).scalar() or 0
    drill_rate = round(completed_drills / total_drills, 4) if total_drills > 0 else 1.0

    total_systems = (await db.execute(select(func.count(ITSystem.id)))).scalar() or 0
    operational_systems = (
        await db.execute(
            select(func.count(ITSystem.id)).where(ITSystem.status == "operational")
        )
    ).scalar() or 0
    avail_rate = round(operational_systems / total_systems, 4) if total_systems > 0 else 1.0

    resolved_incidents = await db.execute(
        select(Incident).where(
            Incident.status == "resolved",
            Incident.created_at >= seven_days_ago,
        )
    )
    resolved_list = resolved_incidents.scalars().all()
    rto_total = len(resolved_list)
    rto_compliant = sum(1 for i in resolved_list if i.rto_achieved)
    rto_rate = round(rto_compliant / rto_total, 4) if rto_total > 0 else 1.0

    return {
        "generated_at": now,
        "incident_trends": trend_data,
        "drill_completion_rate": drill_rate,
        "system_availability_rate": avail_rate,
        "rto_rpo_compliance_trend": {
            "period_days": 7,
            "total_resolved": rto_total,
            "rto_compliant": rto_compliant,
            "rto_compliance_rate": rto_rate,
        },
    }


async def generate_bcp_readiness_report(db: AsyncSession) -> dict:
    now = datetime.now(UTC)

    total_systems = (await db.execute(select(func.count(ITSystem.id)))).scalar() or 0

    bcp_incidents = await db.execute(
        select(Incident).where(Incident.bcp_activated.is_(True))
    )
    bcp_system_names: set[str] = set()
    for inc in bcp_incidents.scalars().all():
        if inc.affected_systems:
            for s in inc.affected_systems.split(","):
                bcp_system_names.add(s.strip().lower())

    covered = 0
    if bcp_system_names:
        all_systems = await db.execute(select(ITSystem.name))
        covered = sum(1 for name in all_systems.scalars().all() if name.lower() in bcp_system_names)

    plan_coverage = {
        "total_systems": total_systems,
        "covered_by_bcp": covered,
        "coverage_rate": round(covered / total_systems, 4) if total_systems > 0 else 0.0,
    }

    total_drills = (await db.execute(select(func.count(Exercise.id)))).scalar() or 0
    completed_drills = (
        await db.execute(
            select(func.count(Exercise.id)).where(Exercise.status == "completed")
        )
    ).scalar() or 0
    drill_rate = round(completed_drills / total_drills, 4) if total_drills > 0 else 1.0

    systems_result = await db.execute(select(ITSystem))
    all_systems_list = systems_result.scalars().all()

    tier_scores = {"tier1": 1.0, "tier2": 0.8, "tier3": 0.5}
    if all_systems_list:
        total_capability = sum(
            tier_scores.get(s.tier, 0.5)
            for s in all_systems_list
            if s.status != "offline"
        )
        recovery_capability = round(total_capability / len(all_systems_list), 4)
    else:
        recovery_capability = 1.0

    gaps: list[str] = []
    total_degraded_or_down = sum(
        1 for s in all_systems_list if s.status in ("degraded", "offline")
    )
    if total_degraded_or_down > 0:
        gaps.append(f"{total_degraded_or_down} system(s) are currently degraded or offline")

    if total_drills == 0:
        gaps.append("No drills or exercises have been conducted")
    elif drill_rate < 0.7:
        gaps.append(f"Drill completion rate ({drill_rate:.0%}) is below 70% target")

    if plan_coverage["coverage_rate"] < 0.5:
        gaps.append(f"BCP plan coverage ({plan_coverage['coverage_rate']:.0%}) is below 50%")

    if not gaps:
        gaps.append("No significant gaps identified")

    return {
        "generated_at": now,
        "plan_coverage": plan_coverage,
        "drill_completion_rate": drill_rate,
        "recovery_capability_score": recovery_capability,
        "gaps_and_recommendations": gaps,
    }
