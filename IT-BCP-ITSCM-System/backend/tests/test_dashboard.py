import pytest


@pytest.mark.asyncio
async def test_dashboard_empty(client):
    resp = await client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["incidents"]["total"] == 0
    assert data["systems"]["total"] == 0
    assert data["systems"]["availability_rate"] == 1.0
    assert data["exercises"]["total"] == 0


@pytest.mark.asyncio
async def test_dashboard_with_data(client):
    # Create incidents
    await client.post(
        "/api/v1/incidents",
        json={"title": "Major outage", "description": "DC down", "severity": "critical"},
    )
    await client.post(
        "/api/v1/incidents",
        json={"title": "Minor issue", "description": "Low priority", "severity": "low"},
    )

    # Create systems
    await client.post("/api/v1/systems", json={"name": "ERP", "tier": "tier1"})
    sys_resp = await client.post(
        "/api/v1/systems", json={"name": "Legacy", "tier": "tier3"}
    )
    sys_id = sys_resp.json()["id"]
    await client.patch(f"/api/v1/systems/{sys_id}/status?status=offline")

    # Create exercise
    await client.post(
        "/api/v1/exercises",
        json={"title": "Q1 Drill", "exercise_type": "tabletop"},
    )

    resp = await client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["incidents"]["total"] == 2
    assert data["incidents"]["critical_open"] == 1
    assert data["systems"]["total"] == 2
    assert data["systems"]["availability_rate"] == 0.5
    assert data["exercises"]["total"] == 1
