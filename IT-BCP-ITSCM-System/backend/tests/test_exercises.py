import pytest


@pytest.mark.asyncio
async def test_list_exercises_empty(client):
    resp = await client.get("/api/v1/exercises")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_exercise(client):
    payload = {
        "title": "Q1 Tabletop Exercise",
        "exercise_type": "tabletop",
        "participants": 10,
        "description": "Quarterly BCP tabletop drill",
    }
    resp = await client.post("/api/v1/exercises", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Q1 Tabletop Exercise"
    assert data["exercise_type"] == "tabletop"
    assert data["status"] == "planned"
    assert data["participants"] == 10


@pytest.mark.asyncio
async def test_get_exercise(client):
    create_resp = await client.post(
        "/api/v1/exercises",
        json={"title": "Full DR Test", "exercise_type": "full"},
    )
    exercise_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/exercises/{exercise_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == exercise_id


@pytest.mark.asyncio
async def test_get_exercise_not_found(client):
    resp = await client.get("/api/v1/exercises/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_complete_exercise(client):
    create_resp = await client.post(
        "/api/v1/exercises",
        json={"title": "Functional Test", "exercise_type": "functional"},
    )
    exercise_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/exercises/{exercise_id}/complete",
        params={"results": "All recovery targets met within RTO"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_date"] is not None
    assert "recovery targets" in data["results"]


@pytest.mark.asyncio
async def test_filter_exercises_by_type(client):
    await client.post("/api/v1/exercises", json={"title": "TT1", "exercise_type": "tabletop"})
    await client.post("/api/v1/exercises", json={"title": "FT1", "exercise_type": "full"})

    resp = await client.get("/api/v1/exercises?exercise_type=tabletop")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["exercise_type"] == "tabletop"
