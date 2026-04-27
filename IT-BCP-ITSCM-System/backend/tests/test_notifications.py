import pytest


@pytest.mark.asyncio
async def test_notification_send_teams(client):
    resp = await client.post(
        "/api/v1/notifications/test",
        json={"channel": "teams", "message": "Test alert"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel"] == "teams"
    assert data["status"] == "sent"
    assert data["message_id"]


@pytest.mark.asyncio
async def test_notification_send_email(client):
    resp = await client.post(
        "/api/v1/notifications/test",
        json={"channel": "email"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel"] == "email"
    assert data["status"] == "sent"


@pytest.mark.asyncio
async def test_notification_send_sms(client):
    resp = await client.post(
        "/api/v1/notifications/test",
        json={"channel": "sms", "message": "SMS alert"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel"] == "sms"


@pytest.mark.asyncio
async def test_notification_invalid_channel(client):
    resp = await client.post(
        "/api/v1/notifications/test",
        json={"channel": "slack"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_escalation(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Major incident", "description": "Critical", "severity": "critical"},
    )
    inc_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/notifications/escalate/{inc_id}",
        json={"level": 2, "reason": "Needs immediate attention"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "sent"


@pytest.mark.asyncio
async def test_escalation_not_found(client):
    resp = await client.post(
        "/api/v1/notifications/escalate/nonexistent-id",
        json={"level": 1},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_escalation_default_level(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Minor", "description": "Test", "severity": "low"},
    )
    inc_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/notifications/escalate/{inc_id}",
        json={},
    )
    assert resp.status_code == 200
