import pytest

EVENT_PAYLOAD = {
    "event_type": "port_scan",
    "source": "firewall",
    "source_ip": "192.168.1.100",
    "destination_ip": "10.0.0.1",
    "severity": "high",
    "description": "Suspicious port scan detected",
    "site": "東京建設現場A",
}


@pytest.mark.asyncio
async def test_create_event(client):
    resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "port_scan"
    assert data["severity"] == "high"
    assert data["processed"] is False


@pytest.mark.asyncio
async def test_list_events_empty(client):
    resp = await client.get("/api/v1/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_events(client):
    await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    await client.post("/api/v1/events", json={**EVENT_PAYLOAD, "severity": "critical"})
    resp = await client.get("/api/v1/events")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_events_filter_severity(client):
    await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    await client.post("/api/v1/events", json={**EVENT_PAYLOAD, "severity": "critical"})
    resp = await client.get("/api/v1/events?severity=critical")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_event(client):
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    event_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


@pytest.mark.asyncio
async def test_get_event_not_found(client):
    resp = await client.get("/api/v1/events/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_event_processed(client):
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    event_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/events/{event_id}/mark-processed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] is True
    assert data["processed_at"] is not None


@pytest.mark.asyncio
async def test_list_events_filter_processed(client):
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD)
    event_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/events/{event_id}/mark-processed")
    await client.post("/api/v1/events", json=EVENT_PAYLOAD)

    resp = await client.get("/api/v1/events?processed=true")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1

    resp2 = await client.get("/api/v1/events?processed=false")
    assert resp2.status_code == 200
    assert resp2.json()["meta"]["total"] == 1
