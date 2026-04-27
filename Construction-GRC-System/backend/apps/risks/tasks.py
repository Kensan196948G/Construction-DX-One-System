import logging
from datetime import date

from celery import shared_task
from django.core.exceptions import FieldError

logger = logging.getLogger(__name__)


@shared_task
def update_risk_scores_task():
    from .models import Risk

    try:
        overdue_risks = Risk.objects.filter(next_review_date__lt=date.today())
        count = 0
        for risk in overdue_risks.iterator():
            logger.warning(
                "Risk overdue for review: %s (score=%s, next_review=%s)",
                risk.title, risk.risk_score, risk.next_review_date,
            )
            count += 1
    except FieldError:
        logger.warning("Risk model has no 'next_review_date' field — skipping overdue check")
        count = 0

    logger.info("Risk review check completed: %s overdue risks found", count)
    return {"overdue_count": count}
