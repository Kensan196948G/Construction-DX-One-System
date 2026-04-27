import pytest

from apps.audits.tasks import generate_weekly_kpi_task, send_audit_reminders_task


@pytest.mark.django_db
def test_send_reminders():
    from datetime import date, timedelta

    from apps.audits.models import Audit

    Audit.objects.create(
        title="Upcoming Audit",
        planned_date=date.today() + timedelta(days=3),
        status="planned",
    )
    result = send_audit_reminders_task()
    assert "reminder_count" in result


@pytest.mark.django_db
def test_generate_weekly_kpi():
    result = generate_weekly_kpi_task()
    assert "compliance" in result
    assert "risks" in result
    assert "audits" in result
