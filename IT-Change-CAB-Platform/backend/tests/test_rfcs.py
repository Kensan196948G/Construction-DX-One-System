import pytest


@pytest.mark.asyncio
async def test_list_rfcs_empty(client):
    resp = await client.get("/api/v1/rfcs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_rfc(client):
    payload = {
        "title": "Upgrade core switch firmware",
        "description": "Apply security patch to all core switches",
        "change_type": "normal",
        "priority": "high",
        "risk_level": "medium",
        "requester": "network-team",
    }
    resp = await client.post("/api/v1/rfcs", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Upgrade core switch firmware"
    assert data["status"] == "draft"
    assert data["change_type"] == "normal"
    assert data["priority"] == "high"
    assert data["id"]


@pytest.mark.asyncio
async def test_get_rfc(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "DB migration", "description": "Migrate to new schema"},
    )
    rfc_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/rfcs/{rfc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == rfc_id


@pytest.mark.asyncio
async def test_get_rfc_not_found(client):
    resp = await client.get("/api/v1/rfcs/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_rfc_status_approve(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Deploy new service", "description": "Blue-green deployment"},
    )
    rfc_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/rfcs/{rfc_id}/status",
        json={"status": "submitted"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"

    resp2 = await client.patch(
        f"/api/v1/rfcs/{rfc_id}/status",
        json={"status": "approved"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_rfc_with_reason(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "Risky change", "description": "High risk during peak hours"},
    )
    rfc_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/rfcs/{rfc_id}/status",
        json={"status": "rejected", "rejection_reason": "Risk too high during business hours"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert "Risk too high" in data["rejection_reason"]


@pytest.mark.asyncio
async def test_assign_meeting(client):
    create_resp = await client.post(
        "/api/v1/rfcs",
        json={"title": "OS patch rollout", "description": "Monthly patch cycle"},
    )
    rfc_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/rfcs/{rfc_id}/assign-meeting",
        params={"meeting_id": "mtg-001"},
    )
    assert resp.status_code == 200
    assert resp.json()["cab_meeting_id"] == "mtg-001"


@pytest.mark.asyncio
async def test_filter_rfcs_by_status(client):
    await client.post("/api/v1/rfcs", json={"title": "RFC A", "description": "desc"})
    create_resp = await client.post(
        "/api/v1/rfcs", json={"title": "RFC B", "description": "desc"}
    )
    rfc_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/rfcs/{rfc_id}/status", json={"status": "submitted"})

    resp = await client.get("/api/v1/rfcs?status=submitted")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "submitted"


@pytest.mark.asyncio
async def test_filter_rfcs_by_priority(client):
    await client.post(
        "/api/v1/rfcs",
        json={"title": "High P", "description": "urgent", "priority": "high"},
    )
    await client.post(
        "/api/v1/rfcs",
        json={"title": "Low P", "description": "routine", "priority": "low"},
    )

    resp = await client.get("/api/v1/rfcs?priority=high")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1
