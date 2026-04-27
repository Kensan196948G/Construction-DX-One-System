import pytest

from apps.risks.tasks import update_risk_scores_task


@pytest.mark.django_db
def test_update_risk_scores():
    from apps.risks.models import Risk

    Risk.objects.create(title="Test Risk", likelihood=3, impact=4, status="open")
    result = update_risk_scores_task()
    assert "overdue_count" in result
    assert result["overdue_count"] >= 0
