from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_create_freeze_period(client):
    resp = await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "年末年始フリーズ",
            "description": "Annual year-end freeze",
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=37)).isoformat(),
            "is_active": True,
            "reason": "年末年始のため",
            "created_by": "admin",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "年末年始フリーズ"
    assert data["is_active"] is True
    assert data["id"]


@pytest.mark.asyncio
async def test_list_freeze_periods(client):
    await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "Freeze A",
            "start_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
        },
    )
    await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "Freeze B",
            "is_active": False,
            "start_date": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=25)).isoformat(),
        },
    )

    resp = await client.get("/api/v1/freeze-periods")
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["total"] == 2

    resp2 = await client.get("/api/v1/freeze-periods?is_active=true")
    assert resp2.status_code == 200
    assert resp2.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_freeze_period(client):
    create_resp = await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "Get test freeze",
            "start_date": (datetime.utcnow() + timedelta(days=40)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
        },
    )
    fp_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/freeze-periods/{fp_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fp_id
    assert resp.json()["name"] == "Get test freeze"


@pytest.mark.asyncio
async def test_get_freeze_period_not_found(client):
    resp = await client.get("/api/v1/freeze-periods/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_freeze_period(client):
    create_resp = await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "Original name",
            "start_date": (datetime.utcnow() + timedelta(days=50)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=55)).isoformat(),
        },
    )
    fp_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/freeze-periods/{fp_id}",
        json={"name": "Updated name", "is_active": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_freeze_period_not_found(client):
    resp = await client.put(
        "/api/v1/freeze-periods/nonexistent-id",
        json={"name": "Nope"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_freeze_period(client):
    create_resp = await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "To delete",
            "start_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=65)).isoformat(),
        },
    )
    fp_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/freeze-periods/{fp_id}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/freeze-periods/{fp_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_freeze_period_not_found(client):
    resp = await client.delete("/api/v1/freeze-periods/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_check_freeze_conflict(client):
    await client.post(
        "/api/v1/freeze-periods",
        json={
            "name": "Summer freeze",
            "start_date": (datetime.utcnow() + timedelta(days=100)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=107)).isoformat(),
        },
    )

    resp = await client.get(
        "/api/v1/freeze-periods/check",
        params={
            "date_from": (datetime.utcnow() + timedelta(days=102)).isoformat(),
            "date_to": (datetime.utcnow() + timedelta(days=105)).isoformat(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_conflict"] is True
    assert len(data["conflicting_periods"]) == 1
    assert data["conflicting_periods"][0]["name"] == "Summer freeze"

    resp2 = await client.get(
        "/api/v1/freeze-periods/check",
        params={
            "date_from": (datetime.utcnow() + timedelta(days=200)).isoformat(),
            "date_to": (datetime.utcnow() + timedelta(days=207)).isoformat(),
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["has_conflict"] is False
