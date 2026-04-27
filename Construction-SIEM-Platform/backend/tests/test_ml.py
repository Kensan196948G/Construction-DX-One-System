import pytest

MODEL_PAYLOAD = {
    "model_name": "ueba-user-behavior",
    "model_type": "ueba",
    "algorithm": "isolation_forest",
    "target": "user_behavior",
    "parameters": {"zscore_threshold": 2.5},
}


@pytest.mark.asyncio
async def test_create_model(client):
    resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["model_name"] == "ueba-user-behavior"
    assert data["model_type"] == "ueba"
    assert data["algorithm"] == "isolation_forest"
    assert data["is_active"] is True
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_model_duplicate(client):
    await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_models(client):
    await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    await client.post(
        "/api/v1/ml/models",
        json={**MODEL_PAYLOAD, "model_name": "netflow-detector", "model_type": "netflow_anomaly"},
    )
    resp = await client.get("/api/v1/ml/models")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_models_filter_type(client):
    await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    await client.post(
        "/api/v1/ml/models",
        json={**MODEL_PAYLOAD, "model_name": "netflow-detector", "model_type": "netflow_anomaly"},
    )
    resp = await client.get("/api/v1/ml/models?model_type=netflow_anomaly")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["model_type"] == "netflow_anomaly"


@pytest.mark.asyncio
async def test_get_model(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/ml/models/{model_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == model_id


@pytest.mark.asyncio
async def test_get_model_not_found(client):
    resp = await client.get("/api/v1/ml/models/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_train_model(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    resp = await client.post(f"/api/v1/ml/models/{model_id}/train")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "training_time_seconds" in data
    assert data["metrics"] is not None


@pytest.mark.asyncio
async def test_train_model_not_found(client):
    resp = await client.post("/api/v1/ml/models/nonexistent-id/train")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_predict_normal(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-001",
            "features": {"login_count": 5, "file_access_count": 25, "network_connections": 12, "failed_logins": 1},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "anomaly_score" in data
    assert "is_anomaly" in data
    assert "explanation" in data


@pytest.mark.asyncio
async def test_predict_anomaly(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-002",
            "features": {"login_count": 999, "file_access_count": 9999, "network_connections": 999, "failed_logins": 999},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_anomaly"] is True
    assert data["anomaly_score"] > 0.5


@pytest.mark.asyncio
async def test_predict_no_numeric_features(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-003",
            "features": {"string_val": "hello"},
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_anomalies(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-001",
            "features": {"login_count": 5, "file_access_count": 25},
        },
    )
    resp = await client.get("/api/v1/ml/anomalies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_anomalies_filter(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-001",
            "features": {"login_count": 5, "file_access_count": 25},
        },
    )
    resp = await client.get("/api/v1/ml/anomalies?entity_type=user")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    resp2 = await client.get("/api/v1/ml/anomalies?entity_type=device")
    assert resp2.json() == []


@pytest.mark.asyncio
async def test_anomaly_stats(client):
    create_resp = await client.post("/api/v1/ml/models", json=MODEL_PAYLOAD)
    model_id = create_resp.json()["id"]
    await client.post(
        f"/api/v1/ml/models/{model_id}/predict",
        json={
            "entity_type": "user",
            "entity_id": "user-001",
            "features": {"login_count": 5, "file_access_count": 25},
        },
    )
    resp = await client.get("/api/v1/ml/anomalies/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scores"] >= 1
    assert "total_anomalies" in data
    assert "anomaly_rate" in data
    assert "by_entity_type" in data
    assert "average_score" in data
    assert "max_score" in data
