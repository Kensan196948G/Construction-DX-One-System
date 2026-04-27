import pytest

from apps.compliance.tasks import calculate_compliance_rate_task, sync_siem_security_events_task


@pytest.mark.django_db
def test_calculate_compliance_rate():
    from apps.compliance.models import Control

    Control.objects.create(
        control_number="A.5.1",
        title="Policy",
        domain="Organizational Controls",
        applicability="applicable",
        implementation_status="implemented",
    )
    Control.objects.create(
        control_number="A.5.2",
        title="Roles",
        domain="Organizational Controls",
        applicability="applicable",
        implementation_status="not_started",
    )
    Control.objects.create(
        control_number="A.5.3",
        title="Segregation",
        domain="Organizational Controls",
        applicability="not_applicable",
        implementation_status="not_started",
    )

    result = calculate_compliance_rate_task()
    assert "domains" in result
    assert result["total_controls"] == 3


@pytest.mark.django_db
def test_sync_siem_events():
    result = sync_siem_security_events_task()
    assert result["status"] == "ok"
