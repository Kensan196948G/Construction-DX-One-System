import pytest

from apps.core.tasks import cleanup_expired_sessions_task


@pytest.mark.django_db
def test_cleanup_sessions():
    result = cleanup_expired_sessions_task()
    assert "deleted_count" in result
