import logging

from celery import shared_task
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions_task():
    count, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
    logger.info("Expired sessions cleaned up: %s deleted", count)
    return {"deleted_count": count}
