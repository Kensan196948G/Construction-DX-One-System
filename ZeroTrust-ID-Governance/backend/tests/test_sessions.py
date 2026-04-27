import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.services.session_service import session_manager


async def _create_test_user(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="SSEMP01",
        username="sessionuser",
        email="sessionuser@miraikensetu.co.jp",
        display_name="セッションユーザー",
        hashed_password=get_password_hash("testpass123"),
        user_type="regular",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


class TestSessionManager:

    def test_create_session(self):
        sid = session_manager.create_session("user-1", ip="127.0.0.1", user_agent="test-agent")
        assert sid is not None
        assert isinstance(sid, str)

    def test_validate_valid_session(self):
        sid = session_manager.create_session("user-2", ip="127.0.0.1")
        assert session_manager.validate_session(sid) is True

    def test_validate_invalid_session(self):
        assert session_manager.validate_session("nonexistent") is False

    def test_invalidate_session(self):
        sid = session_manager.create_session("user-3", ip="127.0.0.1")
        assert session_manager.validate_session(sid) is True
        session_manager.invalidate_session(sid)
        assert session_manager.validate_session(sid) is False

    def test_invalidate_user_sessions(self):
        sid1 = session_manager.create_session("user-4", ip="127.0.0.1")
        sid2 = session_manager.create_session("user-4", ip="192.168.1.1")
        sid3 = session_manager.create_session("user-5", ip="10.0.0.1")

        session_manager.invalidate_user_sessions("user-4")
        assert session_manager.validate_session(sid1) is False
        assert session_manager.validate_session(sid2) is False
        assert session_manager.validate_session(sid3) is True

    def test_get_active_sessions(self):
        session_manager.invalidate_user_sessions("user-6")
        sid1 = session_manager.create_session("user-6", ip="127.0.0.1")
        sid2 = session_manager.create_session("user-6", ip="192.168.1.1")

        active = session_manager.get_active_sessions("user-6")
        assert len(active) == 2
        session_ids = {s["session_id"] for s in active}
        assert sid1 in session_ids
        assert sid2 in session_ids

    def test_cleanup_expired_sessions(self):
        sid = session_manager.create_session("user-cleanup", ip="127.0.0.1")
        session_manager.invalidate_session(sid)
        count = session_manager.cleanup_expired_sessions()
        assert count >= 1
        assert session_manager.validate_session(sid) is False


@pytest.mark.asyncio
async def test_login_creates_session(client: AsyncClient, db_session: AsyncSession):
    user, _ = await _create_test_user(db_session)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "sessionuser", "password": "testpass123"},
    )
    assert login_resp.status_code == 200

    token = login_resp.json()["access_token"]
    sessions_resp = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions_resp.status_code == 200
    data = sessions_resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_logout_invalidates_sessions(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_test_user(db_session)

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 204

    sessions_resp = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions_resp.status_code == 200
    data = sessions_resp.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_invalidate_all_sessions(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_test_user(db_session)

    delete_resp = await client.delete(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    sessions_resp = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions_resp.status_code == 200
    data = sessions_resp.json()
    assert data["total"] == 0
