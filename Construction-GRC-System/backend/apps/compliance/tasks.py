import logging

from celery import shared_task
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


@shared_task
def calculate_compliance_rate_task():
    from .models import Control

    domains = (
        Control.objects.values("domain")
        .annotate(
            total=Count("id"),
            implemented=Count("id", filter=Q(implementation_status__in=("implemented", "verified"), applicability="applicable")),
            in_progress=Count("id", filter=Q(implementation_status="in_progress", applicability="applicable")),
            not_started=Count("id", filter=Q(implementation_status="not_started", applicability="applicable")),
            not_applicable=Count("id", filter=Q(applicability="not_applicable")),
        )
    )
    for entry in domains:
        applicable = entry["total"] - entry["not_applicable"]
        rate = round(entry["implemented"] / applicable * 100, 1) if applicable > 0 else 0.0
        logger.info(
            "Compliance rate [%s]: %s%% (%s/%s implemented)",
            entry["domain"], rate, entry["implemented"], applicable,
        )

    total = domains.aggregate(total=Count("id"))
    logger.info("Compliance rate calculation completed for %s domains", len(domains))
    return {"domains": list(domains), "total_controls": total["total"]}


@shared_task
def sync_siem_security_events_task():
    logger.info("SIEM security events sync started")
    logger.info("SIEM security events sync completed (placeholder)")
    return {"status": "ok", "message": "SIEM sync placeholder"}
