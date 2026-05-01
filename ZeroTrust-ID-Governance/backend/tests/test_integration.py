"""Tests for ZTIG integration API endpoints."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

INTEGRATION_KEY = "dev-integration-key-change-in-prod"
HEADERS = {"X-Integration-Key": INTEGRATION_KEY}


@pytest.mark.anyio
async def test_identity_summary_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/identity-summary")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_identity_summary_wrong_key(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/identity-summary",
        headers={"X-Integration-Key": "wrong-key"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_identity_summary_empty_db(client: AsyncClient):
    resp = await client.get("/api/v1/integration/identity-summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] == 0
    assert data["active_users"] == 0
    assert data["privileged_users"] == 0
    assert "generated_at" in data


@pytest.mark.anyio
async def test_auth_events_recent_requires_key(client: AsyncClient):
    resp = await client.get("/api/v1/integration/auth-events/recent")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_auth_events_recent_empty(client: AsyncClient):
    resp = await client.get("/api/v1/integration/auth-events/recent", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["events"] == []
    assert data["total_count"] == 0
    assert data["period_hours"] == 1


@pytest.mark.anyio
async def test_auth_events_recent_custom_hours(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=6", headers=HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["period_hours"] == 6


@pytest.mark.anyio
async def test_auth_events_recent_hours_out_of_range(client: AsyncClient):
    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=99", headers=HEADERS
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_webhook_notify_requires_key(client: AsyncClient):
    resp = await client.post("/api/v1/integration/webhook/notify", json={"event": "test"})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_notify_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/integration/webhook/notify",
        json={"event": "test", "source": "SIEM"},
        headers=HEADERS,
    )
    assert resp.status_code == 204


@pytest.mark.anyio
async def test_identity_summary_with_users(
    client: AsyncClient, db_session: AsyncSession
):
    """Cover lines 81-96: identity summary with actual users and a privileged role."""
    from app.models.user import Role, User, UserRole

    user_active = User(
        id=str(uuid.uuid4()),
        employee_id="EMP001",
        username="active_user",
        email="active@example.com",
        display_name="Active User",
        hashed_password="hashed",
        status="active",
        user_type="regular",
    )
    user_external = User(
        id=str(uuid.uuid4()),
        employee_id="EMP002",
        username="external_user",
        email="external@example.com",
        display_name="External User",
        hashed_password="hashed",
        status="inactive",
        user_type="external",
    )
    db_session.add_all([user_active, user_external])

    role = Role(
        id=str(uuid.uuid4()),
        name="AdminRole",
        permissions={},
        is_privileged=True,
    )
    db_session.add(role)
    await db_session.flush()

    db_session.add(UserRole(user_id=user_active.id, role_id=role.id))
    await db_session.commit()

    resp = await client.get("/api/v1/integration/identity-summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] == 2
    assert data["active_users"] == 1
    assert data["inactive_users"] == 1
    assert data["privileged_users"] == 1
    assert data["external_users"] == 1
    assert "generated_at" in data


@pytest.mark.anyio
async def test_auth_events_with_data(client: AsyncClient, db_session: AsyncSession):
    """Cover lines 126-141: auth events list comprehension with actual log entries."""
    from app.models.user import AuditLog

    log = AuditLog(
        action="login_failed",
        actor_ip="192.168.1.10",
        payload={"username": "testuser"},
        hash="abc123hash",
    )
    db_session.add(log)
    await db_session.commit()

    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=24", headers=HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 1
    assert data["events"][0]["severity"] == "high"
    assert data["events"][0]["actor_ip"] == "192.168.1.10"


@pytest.mark.anyio
async def test_auth_events_event_type_filter(
    client: AsyncClient, db_session: AsyncSession
):
    """Cover line 122: event_type query filter branch."""
    from app.models.user import AuditLog

    db_session.add(AuditLog(action="login_failed", hash="h1"))
    db_session.add(AuditLog(action="logout", hash="h2"))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/integration/auth-events/recent?event_type=logout", headers=HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    events = data["events"]
    assert all(e["event_type"] == "logout" for e in events)


@pytest.mark.anyio
async def test_auth_events_severity_classification(
    client: AsyncClient, db_session: AsyncSession
):
    """Cover lines 161-170: _classify_severity for all severity levels."""
    from app.models.user import AuditLog

    db_session.add(AuditLog(action="admin_login", hash="h_crit"))
    db_session.add(AuditLog(action="mfa_failed", hash="h_high"))
    db_session.add(AuditLog(action="session_expired", hash="h_med"))
    db_session.add(AuditLog(action="user_created", hash="h_low"))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/integration/auth-events/recent?hours=24", headers=HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    severities = {e["event_type"]: e["severity"] for e in data["events"]}
    assert severities["admin_login"] == "critical"
    assert severities["mfa_failed"] == "high"
    assert severities["session_expired"] == "medium"
    assert severities["user_created"] == "low"
