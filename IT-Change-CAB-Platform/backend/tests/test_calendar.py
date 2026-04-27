from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def _create_rfc(client, **kwargs):
    data = {"title": "Test RFC", "description": "test", "change_type": "normal"}
    data.update(kwargs)
    resp = await client.post("/api/v1/rfcs", json=data)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def _create_meeting(client, **kwargs):
    data = {"title": "CAB Meeting", "status": "scheduled"}
    data.update(kwargs)
    resp = await client.post("/api/v1/cab-meetings", json=data)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_calendar_events(client):
    now = datetime.utcnow()
    future_start = now + timedelta(days=1)
    future_end = future_start + timedelta(hours=2)

    await _create_rfc(
        client, planned_start=future_start.isoformat(), planned_end=future_end.isoformat()
    )

    meeting_date = now + timedelta(days=2)
    await _create_meeting(client, meeting_date=meeting_date.isoformat())

    resp = await client.get(f"/api/v1/calendar/events?year={now.year}&month={now.month}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2

    event_types = {e["event_type"] for e in data["data"]}
    assert "rfc" in event_types
    assert "cab_meeting" in event_types


@pytest.mark.asyncio
async def test_upcoming_changes(client):
    now = datetime.utcnow()
    future_start = now + timedelta(days=2)
    future_end = future_start + timedelta(hours=2)

    await _create_rfc(
        client, planned_start=future_start.isoformat(), planned_end=future_end.isoformat()
    )

    future_start2 = now + timedelta(days=10)
    future_end2 = future_start2 + timedelta(hours=2)

    await _create_rfc(
        client, planned_start=future_start2.isoformat(), planned_end=future_end2.isoformat()
    )

    resp = await client.get("/api/v1/calendar/upcoming?days=7")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["meta"]["total"] == 1

    resp2 = await client.get("/api/v1/calendar/upcoming?days=14")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_cab_schedule(client):
    now = datetime.utcnow()
    meeting_date = now + timedelta(days=3)
    meeting = await _create_meeting(
        client, meeting_date=meeting_date.isoformat(), agenda="Review RFCs"
    )

    rfc1 = await _create_rfc(client)
    await client.patch(f"/api/v1/rfcs/{rfc1['id']}/assign-meeting?meeting_id={meeting['id']}")

    rfc2 = await _create_rfc(client)
    await client.patch(f"/api/v1/rfcs/{rfc2['id']}/assign-meeting?meeting_id={meeting['id']}")

    resp = await client.get("/api/v1/calendar/cab-schedule")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["meta"]["total"] >= 1

    entry = data["data"][0]
    assert entry["rfc_count"] == 2
    assert entry["id"] == meeting["id"]
    assert entry["agenda"] == "Review RFCs"


@pytest.mark.asyncio
async def test_resource_calendar(client):
    now = datetime.utcnow()
    future_start = now + timedelta(days=1)
    future_end = future_start + timedelta(hours=2)

    await _create_rfc(
        client,
        affected_systems='["system-a", "system-b"]',
        planned_start=future_start.isoformat(),
        planned_end=future_end.isoformat(),
    )

    await _create_rfc(
        client,
        affected_systems='["system-b", "system-c"]',
        planned_start=future_start.isoformat(),
        planned_end=future_end.isoformat(),
    )

    resp = await client.get("/api/v1/calendar/resource/system-a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["total"] == 1

    resp2 = await client.get("/api/v1/calendar/resource/system-b")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["meta"]["total"] == 2

    resp3 = await client.get("/api/v1/calendar/resource/nonexistent")
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_calendar_events_empty(client):
    resp = await client.get("/api/v1/calendar/events?year=2026&month=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["meta"]["total"] == 0
    assert data["data"] == []


@pytest.mark.asyncio
async def test_upcoming_changes_empty(client):
    resp = await client.get("/api/v1/calendar/upcoming?days=14")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["meta"]["total"] == 0
    assert data["data"] == []
