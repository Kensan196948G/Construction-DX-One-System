import pytest


@pytest.mark.asyncio
async def test_list_meetings_empty(client):
    resp = await client.get("/api/v1/cab-meetings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_meeting(client):
    payload = {
        "title": "Weekly CAB - April",
        "status": "scheduled",
        "agenda": "Review Q1 infrastructure changes",
        "attendees": "CTO, Network Lead, Security Lead",
    }
    resp = await client.post("/api/v1/cab-meetings", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Weekly CAB - April"
    assert data["status"] == "scheduled"
    assert data["id"]


@pytest.mark.asyncio
async def test_get_meeting(client):
    create_resp = await client.post(
        "/api/v1/cab-meetings",
        json={"title": "Emergency CAB"},
    )
    meeting_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/cab-meetings/{meeting_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == meeting_id


@pytest.mark.asyncio
async def test_get_meeting_not_found(client):
    resp = await client.get("/api/v1/cab-meetings/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_complete_meeting(client):
    create_resp = await client.post(
        "/api/v1/cab-meetings",
        json={"title": "Monthly CAB Review"},
    )
    meeting_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/cab-meetings/{meeting_id}/complete",
        params={"minutes": "All 3 RFCs approved. Next meeting scheduled for May."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "RFCs approved" in data["minutes"]


@pytest.mark.asyncio
async def test_filter_meetings_by_status(client):
    await client.post("/api/v1/cab-meetings", json={"title": "Meeting A"})
    resp2 = await client.post(
        "/api/v1/cab-meetings",
        json={"title": "Meeting B", "status": "scheduled"},
    )
    meeting_id = resp2.json()["id"]
    await client.patch(f"/api/v1/cab-meetings/{meeting_id}/complete")

    resp = await client.get("/api/v1/cab-meetings?status=completed")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "completed"
