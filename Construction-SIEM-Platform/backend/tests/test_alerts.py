import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_alert(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/alerts",
        json={
            "title": "Brute Force Detected",
            "severity": "high",
            "risk_score": 85.0,
            "event_count": 50,
            "rule_name": "brute_force_rule",
            "mitre_technique": "T1110",
            "mitre_tactic": "Credential Access",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Brute Force Detected"
    assert data["status"] == "open"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_alerts_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_alerts_by_status(client: AsyncClient) -> None:
    await client.post("/api/v1/alerts", json={"title": "Alert A", "severity": "low"})
    response = await client.get("/api/v1/alerts?status=open")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_alert_by_id(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/alerts",
        json={"title": "Port Scan Alert", "severity": "medium"},
    )
    alert_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/alerts/{alert_id}")
    assert response.status_code == 200
    assert response.json()["id"] == alert_id


@pytest.mark.asyncio
async def test_get_alert_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/alerts/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_alert_status_to_investigating(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/alerts",
        json={"title": "Ransomware Detected", "severity": "critical", "risk_score": 99.0},
    )
    alert_id = create_res.json()["id"]

    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/status",
        json={"status": "investigating", "assigned_to": "analyst01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "investigating"
    assert data["assigned_to"] == "analyst01"


@pytest.mark.asyncio
async def test_update_alert_status_to_resolved(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/alerts",
        json={"title": "Test Alert", "severity": "low"},
    )
    alert_id = create_res.json()["id"]

    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/status",
        json={"status": "resolved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["resolved_at"] is not None
