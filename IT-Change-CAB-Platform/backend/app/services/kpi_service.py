from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cab_meeting import CABMeeting
from app.models.rfc import RFC


def _business_days_between(start: datetime, end: datetime) -> float:
    if start.date() >= end.date():
        return 0.0
    business = 0
    current = start.date() + timedelta(days=1)
    while current <= end.date():
        if current.weekday() < 5:
            business += 1
        current += timedelta(days=1)
    return float(business)


def _metric_status(
    value: float, target: float, warning: float, lower_is_better: bool = False
) -> str:
    if lower_is_better:
        if value <= target:
            return "healthy"
        if value <= warning:
            return "warning"
        return "critical"
    if value >= target:
        return "healthy"
    if value >= warning:
        return "warning"
    return "critical"


async def calculate_kpi_metrics(db: AsyncSession) -> dict:
    result = await db.execute(select(RFC))
    all_rfcs = result.scalars().all()
    total = len(all_rfcs)

    implemented = [r for r in all_rfcs if r.status in ("implemented", "closed")]
    total_implemented = len(implemented)
    closed = [r for r in all_rfcs if r.status == "closed"]
    completed = len(closed)

    success_rate = (completed / total_implemented * 100) if total_implemented > 0 else 0.0

    approved = [r for r in all_rfcs if r.status == "approved" and r.created_at and r.updated_at]
    avg_lead_time = (
        sum(_business_days_between(r.created_at, r.updated_at) for r in approved) / len(approved)
        if approved
        else 0.0
    )

    rollback_count = len(
        [
            r
            for r in all_rfcs
            if r.status == "rejected"
            and r.rejection_reason
            and "rollback" in r.rejection_reason.lower()
        ]
    )
    rollback_rate = (rollback_count / total_implemented * 100) if total_implemented > 0 else 0.0

    emergency = len([r for r in all_rfcs if r.change_type == "emergency"])
    emergency_ratio = (emergency / total * 100) if total > 0 else 0.0

    pir_rate = (completed / completed * 100) if completed > 0 else 100.0

    return {
        "change_success_rate": {
            "name": "change_success_rate",
            "value": round(success_rate, 2),
            "target": 95.0,
            "unit": "percent",
            "status": _metric_status(success_rate, 95.0, 90.0),
        },
        "cab_approval_lead_time": {
            "name": "cab_approval_lead_time",
            "value": round(avg_lead_time, 2),
            "target": 5.0,
            "unit": "days",
            "status": _metric_status(avg_lead_time, 5.0, 7.0, lower_is_better=True),
        },
        "rollback_rate": {
            "name": "rollback_rate",
            "value": round(rollback_rate, 2),
            "target": 5.0,
            "unit": "percent",
            "status": _metric_status(rollback_rate, 5.0, 10.0, lower_is_better=True),
        },
        "emergency_change_ratio": {
            "name": "emergency_change_ratio",
            "value": round(emergency_ratio, 2),
            "target": 10.0,
            "unit": "percent",
            "status": _metric_status(emergency_ratio, 10.0, 20.0, lower_is_better=True),
        },
        "pir_completion_rate": {
            "name": "pir_completion_rate",
            "value": round(pir_rate, 2),
            "target": 100.0,
            "unit": "percent",
            "status": _metric_status(pir_rate, 100.0, 90.0),
        },
    }


async def get_kpi_trend(db: AsyncSession, days: int = 30) -> list[dict]:
    result = await db.execute(select(RFC).order_by(RFC.created_at))
    all_rfcs = result.scalars().all()

    today = datetime.utcnow().date()
    trends: dict[str, list[dict]] = {
        "change_success_rate": [],
        "cab_approval_lead_time": [],
        "rollback_rate": [],
        "emergency_change_ratio": [],
        "pir_completion_rate": [],
    }

    for i in range(days, 0, -1):
        day = today - timedelta(days=i)
        rfcs_up_to = [r for r in all_rfcs if r.created_at and r.created_at.date() <= day]

        t = len(rfcs_up_to)
        implemented = [r for r in rfcs_up_to if r.status in ("implemented", "closed")]
        ti = len(implemented)
        closed = [r for r in rfcs_up_to if r.status == "closed"]
        c = len(closed)

        date_str = day.isoformat()
        trends["change_success_rate"].append(
            {"date": date_str, "value": round((c / ti * 100) if ti > 0 else 0.0, 2)}
        )

        approved_list = [
            r for r in rfcs_up_to if r.status == "approved" and r.created_at and r.updated_at
        ]
        lt = (
            sum(_business_days_between(r.created_at, r.updated_at) for r in approved_list)
            / len(approved_list)
            if approved_list
            else 0.0
        )
        trends["cab_approval_lead_time"].append({"date": date_str, "value": round(lt, 2)})

        rb = len(
            [
                r
                for r in rfcs_up_to
                if r.status == "rejected"
                and r.rejection_reason
                and "rollback" in r.rejection_reason.lower()
            ]
        )
        trends["rollback_rate"].append(
            {"date": date_str, "value": round((rb / ti * 100) if ti > 0 else 0.0, 2)}
        )

        em = len([r for r in rfcs_up_to if r.change_type == "emergency"])
        trends["emergency_change_ratio"].append(
            {"date": date_str, "value": round((em / t * 100) if t > 0 else 0.0, 2)}
        )

        trends["pir_completion_rate"].append(
            {"date": date_str, "value": round((c / c * 100) if c > 0 else 100.0, 2)}
        )

    return [{"metric": k, "data": v} for k, v in trends.items()]


async def get_sla_compliance(db: AsyncSession) -> dict:
    result = await db.execute(select(RFC))
    all_rfcs = result.scalars().all()

    items = []
    for ct in ("standard", "normal", "emergency"):
        ct_rfcs = [r for r in all_rfcs if r.change_type == ct]
        total = len(ct_rfcs)
        met = len([r for r in ct_rfcs if r.status == "closed"])
        compliance = (met / total * 100) if total > 0 else 100.0
        items.append(
            {
                "change_type": ct,
                "total": total,
                "met": met,
                "compliance_percent": round(compliance, 2),
            }
        )

    overall_total = sum(i["total"] for i in items)
    overall_met = sum(i["met"] for i in items)
    overall = (overall_met / overall_total * 100) if overall_total > 0 else 100.0

    return {"items": items, "overall": round(overall, 2)}


async def get_kpi_alerts(db: AsyncSession) -> list[dict]:
    metrics = await calculate_kpi_metrics(db)
    alerts = []

    thresholds = {
        "change_success_rate": (95.0, 90.0, False, "percent"),
        "cab_approval_lead_time": (5.0, 7.0, True, "days"),
        "rollback_rate": (5.0, 10.0, True, "percent"),
        "emergency_change_ratio": (10.0, 20.0, True, "percent"),
        "pir_completion_rate": (100.0, 90.0, False, "percent"),
    }

    for name, (target, warn, lower, unit) in thresholds.items():
        val = metrics[name]["value"]
        if lower:
            if val > warn:
                alerts.append(
                    {
                        "metric": name,
                        "value": val,
                        "threshold": target,
                        "severity": "critical",
                        "message": f"{name} is {val:.1f}{unit}, exceeding critical threshold {warn:.1f}{unit}",
                    }
                )
            elif val > target:
                alerts.append(
                    {
                        "metric": name,
                        "value": val,
                        "threshold": target,
                        "severity": "warning",
                        "message": f"{name} is {val:.1f}{unit}, exceeding target {target:.1f}{unit}",
                    }
                )
        else:
            if val < warn:
                alerts.append(
                    {
                        "metric": name,
                        "value": val,
                        "threshold": target,
                        "severity": "critical",
                        "message": f"{name} is {val:.1f}{unit}, below critical threshold {warn:.1f}{unit}",
                    }
                )
            elif val < target:
                alerts.append(
                    {
                        "metric": name,
                        "value": val,
                        "threshold": target,
                        "severity": "warning",
                        "message": f"{name} is {val:.1f}{unit}, below target {target:.1f}{unit}",
                    }
                )

    return alerts


async def get_dashboard_summary(db: AsyncSession) -> dict:
    return {
        "metrics": await calculate_kpi_metrics(db),
        "alerts": await get_kpi_alerts(db),
        "trends": await get_kpi_trend(db),
        "sla": await get_sla_compliance(db),
        "cab_efficiency": await get_cab_efficiency_metrics(db),
    }


async def get_cab_efficiency_metrics(db: AsyncSession) -> dict:
    meeting_result = await db.execute(select(CABMeeting))
    meetings = meeting_result.scalars().all()
    total_meetings = len(meetings)

    rfc_result = await db.execute(select(RFC).where(RFC.cab_meeting_id.isnot(None)))
    reviewed = rfc_result.scalars().all()
    total_rfcs_reviewed = len(reviewed)

    avg_rfcs = round(total_rfcs_reviewed / total_meetings, 2) if total_meetings > 0 else 0.0

    all_rfcs_result = await db.execute(select(RFC))
    all_rfcs = all_rfcs_result.scalars().all()
    submitted = len(
        [
            r
            for r in all_rfcs
            if r.status in ("submitted", "approved", "rejected", "implemented", "closed")
        ]
    )
    approved = len([r for r in all_rfcs if r.status in ("approved", "implemented", "closed")])
    approval_rate = round(approved / submitted * 100, 2) if submitted > 0 else 0.0

    approved_list = [
        r
        for r in all_rfcs
        if r.status in ("approved", "implemented", "closed") and r.created_at and r.updated_at
    ]
    if approved_list:
        avg_days = sum(
            (r.updated_at.date() - r.created_at.date()).days for r in approved_list
        ) / len(approved_list)
    else:
        avg_days = None

    return {
        "total_meetings": total_meetings,
        "total_rfcs_reviewed": total_rfcs_reviewed,
        "avg_rfcs_per_meeting": avg_rfcs,
        "approval_rate": approval_rate,
        "avg_approval_days": avg_days,
    }
