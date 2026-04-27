import pytest

from app.models.notification import NotificationLog
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_send_email(db):
    service = NotificationService(db=db)
    result = await service.send_email(
        to="admin@example.com",
        subject="Test Alert",
        body="This is a test alert notification",
    )
    assert result["success"] is True
    assert result["channel"] == "email"
    assert result["recipient"] == "admin@example.com"
    assert result["notification_id"] is not None


@pytest.mark.asyncio
async def test_send_teams(db):
    service = NotificationService(db=db)
    result = await service.send_teams(
        title="Critical Alert",
        message="Security incident detected",
        severity="critical",
    )
    assert result["success"] is True
    assert result["channel"] == "teams"
    assert "card" in result
    assert result["card"]["title"] == "Critical Alert"


@pytest.mark.asyncio
async def test_send_sms(db):
    service = NotificationService(db=db)
    result = await service.send_sms(
        phone="+15551234567",
        message="ALERT: Suspicious activity detected at site A",
    )
    assert result["success"] is True
    assert result["channel"] == "sms"
    assert result["sid"] is not None


@pytest.mark.asyncio
async def test_alert_notification(db):
    from app.models.alert import Alert

    alert = Alert(
        title="Port Scan Detected",
        severity="high",
        source="firewall",
        description="Scan from 10.0.0.1",
        site="Site-A",
    )
    db.add(alert)
    await db.commit()

    service = NotificationService(db=db)
    results = await service.send_alert_notification(alert, channels=["email", "sms"])
    assert "email" in results
    assert "sms" in results
    assert results["email"]["success"] is True
    assert results["sms"]["success"] is True


@pytest.mark.asyncio
async def test_notification_history(db):
    service = NotificationService(db=db)
    await service.send_email(to="test@example.com", subject="Test", body="Body")
    await service.send_sms(phone="+15551112222", message="SMS test")

    history = await service.get_notification_history(limit=10)
    assert len(history) == 2
    assert history[0].channel in ("email", "sms")


@pytest.mark.asyncio
async def test_notification_history_filter_by_entity(db):
    service = NotificationService(db=db)
    log = NotificationLog(
        channel="email",
        recipient="admin@example.com",
        subject="Test",
        body="Body",
        status="sent",
        related_entity_type="alert",
        related_entity_id="alert-001",
    )
    db.add(log)
    await db.commit()

    history = await service.get_notification_history(entity_id="alert-001")
    assert len(history) == 1
    assert history[0].related_entity_id == "alert-001"


@pytest.mark.asyncio
async def test_notification_templates(client):
    payload = {
        "name": "critical_alert_email",
        "channel": "email",
        "subject_template": "CRITICAL: {{ title }}",
        "body_template": "Alert {{ title }} of severity {{ severity }} detected.",
    }
    resp = await client.post("/api/v1/notifications/templates", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "critical_alert_email"
    assert data["channel"] == "email"

    resp2 = await client.get("/api/v1/notifications/templates")
    assert resp2.status_code == 200
    assert len(resp2.json()["data"]) == 1


@pytest.mark.asyncio
async def test_send_notification_api(client):
    payload = {
        "channel": "email",
        "recipient": "admin@example.com",
        "subject": "Test API",
        "body": "Test body from API",
    }
    resp = await client.post("/api/v1/notifications/send", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["channel"] == "email"


@pytest.mark.asyncio
async def test_send_alert_notification_api(client):
    alert_resp = await client.post("/api/v1/alerts", json={
        "title": "API Alert Test",
        "severity": "critical",
        "source": "ids",
        "description": "Intrusion detected",
    })
    alert_id = alert_resp.json()["id"]

    resp = await client.post("/api/v1/notifications/alert", json={
        "alert_id": alert_id,
        "channels": ["email", "teams"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "email" in data["results"]
    assert "teams" in data["results"]


@pytest.mark.asyncio
async def test_get_notification_history_api(client):
    await client.post("/api/v1/notifications/send", json={
        "channel": "email",
        "recipient": "hist@example.com",
        "subject": "History Test",
        "body": "Check history",
    })
    resp = await client.get("/api/v1/notifications/history")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
