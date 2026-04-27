import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.services.audit_service import get_chain_stats, log_action, verify_chain


async def _create_admin(db: AsyncSession) -> tuple[User, str]:
    user = User(
        employee_id="ADM001",
        username="auditadmin",
        email="auditadmin@miraikensetu.co.jp",
        display_name="監査管理者",
        hashed_password=get_password_hash("adminpass123"),
        user_type="admin",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


@pytest.mark.asyncio
async def test_log_action_creates_entry(db_session: AsyncSession):
    entry = await log_action(
        db_session, action="test_action", actor_id="actor1", result="success",
    )
    assert entry.id is not None
    assert entry.id >= 1
    assert entry.action == "test_action"
    assert entry.hash is not None
    assert len(entry.hash) == 64
    assert entry.prev_hash is None


@pytest.mark.asyncio
async def test_hash_chain_integrity(db_session: AsyncSession):
    e1 = await log_action(db_session, action="action1", actor_id="u1", result="success")
    e2 = await log_action(db_session, action="action2", actor_id="u2", result="success")
    e3 = await log_action(db_session, action="action3", actor_id="u3", result="success")

    assert e1.prev_hash is None
    assert e2.prev_hash == e1.hash
    assert e3.prev_hash == e2.hash


@pytest.mark.asyncio
async def test_verify_chain_valid(db_session: AsyncSession):
    await log_action(db_session, action="login", actor_id="u1", result="success")
    await log_action(db_session, action="logout", actor_id="u1", result="success")

    result = await verify_chain(db_session)
    assert result["valid"] is True
    assert result["total_entries"] == 2
    assert result["checked_entries"] == 2


@pytest.mark.asyncio
async def test_tamper_detection(db_session: AsyncSession):
    await log_action(db_session, action="first", actor_id="u1", result="success")
    e2 = await log_action(db_session, action="second", actor_id="u2", result="success")

    e2.action = "tampered_action"
    await db_session.commit()

    result = await verify_chain(db_session)
    assert result["valid"] is False
    assert result["broken_at"] is not None


@pytest.mark.asyncio
async def test_tamper_prev_hash_detection(db_session: AsyncSession):
    await log_action(db_session, action="first", actor_id="u1", result="success")
    e2 = await log_action(db_session, action="second", actor_id="u2", result="success")

    e2.prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    await db_session.commit()

    result = await verify_chain(db_session)
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_verify_empty_chain(db_session: AsyncSession):
    result = await verify_chain(db_session)
    assert result["valid"] is True
    assert result["total_entries"] == 0


@pytest.mark.asyncio
async def test_audit_log_list(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    await log_action(db_session, action="test_list", actor_id=str(user.id), result="success")

    response = await client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_audit_log_filter(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    uid = str(user.id)
    await log_action(db_session, action="login", actor_id=uid, result="success")
    await log_action(db_session, action="logout", actor_id=uid, result="success")

    response = await client.get(
        "/api/v1/audit/logs?action=login",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(r["action"] == "login" for r in data)


@pytest.mark.asyncio
async def test_chain_stats(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    uid = str(user.id)
    await log_action(db_session, action="login", actor_id=uid, result="success")
    await log_action(db_session, action="logout", actor_id=uid, result="success")

    stats = await get_chain_stats(db_session)
    assert stats["total_entries"] == 2
    assert "login" in stats["action_breakdown"]
    assert stats["first_entry_at"] is not None
    assert stats["last_entry_at"] is not None


@pytest.mark.asyncio
async def test_verify_chain_endpoint(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    uid = str(user.id)
    await log_action(db_session, action="test", actor_id=uid, result="success")

    response = await client.get(
        "/api/v1/audit/verify/chain",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["total_entries"] >= 1


@pytest.mark.asyncio
async def test_verify_entry_endpoint(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    entry = await log_action(db_session, action="test", actor_id=str(user.id), result="success")

    response = await client.get(
        f"/api/v1/audit/verify/{entry.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient, db_session: AsyncSession):
    user, token = await _create_admin(db_session)
    uid = str(user.id)
    await log_action(db_session, action="test", actor_id=uid, result="success")

    response = await client.get(
        "/api/v1/audit/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_entries"] >= 1
    assert "action_breakdown" in data
