from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "calculate_compliance_rate": {
        "task": "apps.compliance.tasks.calculate_compliance_rate_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "update_risk_scores": {
        "task": "apps.risks.tasks.update_risk_scores_task",
        "schedule": crontab(hour=3, minute=0),
    },
    "send_audit_reminders": {
        "task": "apps.audits.tasks.send_audit_reminders_task",
        "schedule": crontab(hour=9, minute=0, day_of_week="1-5"),
    },
    "generate_weekly_kpi": {
        "task": "apps.audits.tasks.generate_weekly_kpi_task",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    "cleanup_expired_sessions": {
        "task": "apps.core.tasks.cleanup_expired_sessions_task",
        "schedule": crontab(minute=0),
    },
    "sync_siem_security_events": {
        "task": "apps.compliance.tasks.sync_siem_security_events_task",
        "schedule": crontab(minute="*/15"),
    },
}
