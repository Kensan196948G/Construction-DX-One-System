from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_analyze_impact_low(client):
    resp = await client.post(
        "/api/v1/impact/analyze",
        json={
            "title": "Minor config change",
            "change_type": "standard",
            "affected_systems": "web-server",
            "planned_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["impact_level"] in ("low", "medium")
    assert data["affected_system_count"] == 1
    assert data["change_type"] == "standard"


@pytest.mark.asyncio
async def test_analyze_impact_high(client):
    resp = await client.post(
        "/api/v1/impact/analyze",
        json={
            "title": "Major infrastructure upgrade",
            "change_type": "emergency",
            "affected_systems": "web-server,db-server,cache-server,api-gateway,load-balancer",
            "planned_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(hours=25)).isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["impact_level"] in ("high", "critical")
    assert data["affected_system_count"] == 5
    assert data["change_type"] == "emergency"
    assert data["impact_score"] >= 20


@pytest.mark.asyncio
async def test_detect_conflicts_no_conflict(client):
    await client.post(
        "/api/v1/rfcs",
        json={
            "title": "Existing change",
            "description": "Test",
            "planned_start": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=10, hours=2)).isoformat(),
            "affected_systems": "web-server",
        },
    )

    resp = await client.post(
        "/api/v1/impact/detect-conflicts",
        json={
            "title": "New change next week",
            "change_type": "normal",
            "affected_systems": "db-server",
            "planned_start": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=20, hours=2)).isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_conflicts"] is False
    assert data["total_conflicts"] == 0


@pytest.mark.asyncio
async def test_detect_conflicts_with_conflict(client):
    await client.post(
        "/api/v1/rfcs",
        json={
            "title": "Existing DB migration",
            "description": "Test migration",
            "planned_start": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=5, hours=3)).isoformat(),
            "affected_systems": "db-server,cache-server",
        },
    )

    resp = await client.post(
        "/api/v1/impact/detect-conflicts",
        json={
            "title": "New DB update",
            "change_type": "normal",
            "affected_systems": "db-server,web-server",
            "planned_start": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=5, hours=2)).isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_conflicts"] is True
    assert data["total_conflicts"] >= 1
    assert any("db-server" in str(c.get("shared_systems", [])) for c in data["conflicting_rfcs"])


@pytest.mark.asyncio
async def test_change_calendar(client):
    start = datetime.utcnow() + timedelta(days=2)
    end = start + timedelta(hours=2)
    await client.post(
        "/api/v1/rfcs",
        json={
            "title": "Calendar test change",
            "description": "Test",
            "planned_start": start.isoformat(),
            "planned_end": end.isoformat(),
            "affected_systems": "web-server",
        },
    )

    date_from = (datetime.utcnow() + timedelta(days=1)).isoformat()
    date_to = (datetime.utcnow() + timedelta(days=7)).isoformat()
    resp = await client.get(
        "/api/v1/impact/change-calendar",
        params={"date_from": date_from, "date_to": date_to},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_system_impact_map(client):
    await client.post(
        "/api/v1/rfcs",
        json={
            "title": "System map test",
            "description": "Test",
            "planned_start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "planned_end": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
            "affected_systems": "web-server,db-server",
        },
    )

    resp = await client.get("/api/v1/impact/system-map")
    assert resp.status_code == 200
    data = resp.json()
    assert "systems" in data
    assert data["total_systems"] >= 1
    assert data["total_changes"] >= 1
