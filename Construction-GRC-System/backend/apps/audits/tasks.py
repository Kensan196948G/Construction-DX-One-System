import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Avg

logger = logging.getLogger(__name__)


@shared_task
def send_audit_reminders_task():
    from .models import Audit

    upcoming = Audit.objects.filter(
        planned_date__gte=date.today(),
        planned_date__lte=date.today() + timedelta(days=7),
        status__in=("planned", "in_progress"),
    )
    count = 0
    for audit in upcoming.iterator():
        open_findings = audit.findings.filter(status__in=("open", "in_remediation")).count()
        logger.info(
            "Audit reminder: '%s' planned for %s (status=%s, open_findings=%s)",
            audit.title, audit.planned_date, audit.status, open_findings,
        )
        count += 1

    logger.info("Audit reminders sent: %s audits approaching deadline", count)
    return {"reminder_count": count}


@shared_task
def generate_weekly_kpi_task():
    from apps.compliance.models import Control
    from apps.risks.models import Risk

    from .models import Audit, Finding

    total_controls = Control.objects.count()
    implemented = Control.objects.filter(
        implementation_status__in=("implemented", "verified"), applicability="applicable"
    ).count()
    applicable = Control.objects.filter(applicability="applicable").count()
    compliance_rate = round(implemented / applicable * 100, 1) if applicable > 0 else 0.0

    total_risks = Risk.objects.count()
    open_risks = Risk.objects.filter(status="open").count()
    avg_risk_score = Risk.objects.aggregate(avg=Avg("risk_score")).get("avg") or 0.0

    total_audits = Audit.objects.count()
    completed_audits = Audit.objects.filter(status="completed").count()
    total_findings = Finding.objects.count()
    open_findings = Finding.objects.filter(status__in=("open", "in_remediation")).count()

    kpi = {
        "compliance": {
            "total_controls": total_controls,
            "compliance_rate": compliance_rate,
        },
        "risks": {
            "total_risks": total_risks,
            "open_risks": open_risks,
            "average_risk_score": round(avg_risk_score, 2),
        },
        "audits": {
            "total_audits": total_audits,
            "completed_audits": completed_audits,
            "total_findings": total_findings,
            "open_findings": open_findings,
        },
    }

    logger.info("Weekly KPI report generated: %s", kpi)
    return kpi
