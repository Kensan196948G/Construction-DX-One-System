from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

NOW = datetime.now(UTC).isoformat()


@pytest.mark.asyncio
async def test_ingest_event(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/events",
        json={
            "event_type": "login_failure",
            "severity": "medium",
            "source_ip": "192.168.1.100",
            "occurred_at": NOW,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "login_failure"
    assert data["severity"] == "medium"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_events_with_severity_filter(client: AsyncClient) -> None:
    for sev in ["low", "medium", "high"]:
        await client.post(
            "/api/v1/events",
            json={"event_type": "port_scan", "severity": sev, "occurred_at": NOW},
        )
    response = await client.get("/api/v1/events?severity=high")
    assert response.status_code == 200
    events = response.json()
    assert all(e["severity"] == "high" for e in events)


@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/events",
        json={"event_type": "brute_force", "severity": "high", "occurred_at": NOW},
    )
    event_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_ingest(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/events/bulk",
        json={
            "events": [
                {"event_type": f"event_{i}", "severity": "low", "occurred_at": NOW}
                for i in range(5)
            ]
        },
    )
    assert response.status_code == 201
    assert response.json()["ingested"] == 5


@pytest.mark.asyncio
async def test_mark_event_processed(client: AsyncClient) -> None:
    create_res = await client.post(
        "/api/v1/events",
        json={"event_type": "sql_injection", "severity": "critical", "occurred_at": NOW},
    )
    event_id = create_res.json()["id"]

    response = await client.patch(f"/api/v1/events/{event_id}/processed")
    assert response.status_code == 200
    assert response.json()["is_processed"] is True
