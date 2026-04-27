import json

import pytest

from app.services.iot_agent import IoTLightweightAgent


@pytest.fixture
def agent():
    return IoTLightweightAgent(max_buffer_size=100, retention_seconds=3600)


class TestIoTAgent:
    def test_collect_event(self, agent):
        result = agent.collect_event(
            device_id="sensor-001",
            event_type="temperature",
            payload={"temperature": 35.5, "battery_level": 85.0, "signal_strength": -60},
        )
        assert result["status"] == "success"
        assert result["device_id"] == "sensor-001"
        assert result["event_type"] == "temperature"
        assert result["buffered"] is True

    def test_collect_event_tracks_device_status(self, agent):
        agent.collect_event("sensor-002", "vibration", {"vibration": 0.5})
        status = agent.get_device_status("sensor-002")
        assert status["online"] is True
        assert status["buffer_size"] == 1
        assert status["total_events_collected"] == 1

    def test_batch_events(self, agent):
        events = [
            {"device_id": "dev-1", "event_type": "temp", "payload": {"v": 30}},
            {"device_id": "dev-2", "event_type": "humidity", "payload": {"v": 60}},
        ]
        batched = agent.batch_events(events)
        assert len(batched) == 2
        assert batched[0]["device_id"] == "dev-1"
        assert batched[1]["device_id"] == "dev-2"

    def test_compress_and_decompress(self, agent):
        original = {"device": "sensor-01", "reading": 42.5, "timestamp": "2024-01-01T00:00:00"}
        compressed = agent.compress_log(original)
        assert isinstance(compressed, bytes)

        decompressed = agent.decompress_log(compressed)
        assert json.loads(decompressed) == original

    def test_compress_string(self, agent):
        data = "SENSOR_LOG:2024-01-01T00:00:00,device=sensor-01,temperature=35.5"
        compressed = agent.compress_log(data)
        assert isinstance(compressed, bytes)
        decompressed = agent.decompress_log(compressed)
        assert decompressed == data

    def test_buffer_offline(self, agent):
        events = [
            {"device_id": "offline-dev-1", "event_type": "temp", "payload": {"v": 25}},
            {"device_id": "offline-dev-1", "event_type": "humidity", "payload": {"v": 70}},
            {"device_id": "offline-dev-2", "event_type": "vibration", "payload": {"v": 0.1}},
        ]
        result = agent.buffer_offline(events)
        assert result["status"] == "success"
        assert result["buffered"] == 3
        assert result["device_count"] == 2

        status = agent.get_device_status("offline-dev-1")
        assert status["buffer_size"] == 2

    def test_flush_buffer(self, agent):
        agent.collect_event("flush-dev", "test", {"data": 1})
        agent.collect_event("flush-dev", "test", {"data": 2})
        assert agent.get_device_status("flush-dev")["buffer_size"] == 2

        flushed = agent.flush_buffer()
        assert len(flushed) == 2
        assert "flushed_at" in flushed[0]
        assert agent.get_device_status("flush-dev")["buffer_size"] == 0

    def test_flush_specific_device(self, agent):
        agent.collect_event("dev-a", "test", {"d": 1})
        agent.collect_event("dev-b", "test", {"d": 2})
        agent.collect_event("dev-b", "test", {"d": 3})

        flushed = agent.flush_buffer(device_id="dev-b")
        assert len(flushed) == 2
        assert agent.get_device_status("dev-a")["buffer_size"] == 1
        assert agent.get_device_status("dev-b")["buffer_size"] == 0

    def test_get_device_status_unknown(self, agent):
        status = agent.get_device_status("nonexistent")
        assert status["online"] is False
        assert status["last_seen"] is None
        assert status["buffer_size"] == 0
        assert status["total_events_collected"] == 0

    def test_get_buffer_stats(self, agent):
        stats = agent.get_buffer_stats()
        assert stats["total_buffered"] == 0
        assert stats["device_count"] == 0
        assert stats["max_buffer_size"] == 100
        assert stats["retention_seconds"] == 3600

        agent.collect_event("stat-dev", "test", {"v": 1})
        stats = agent.get_buffer_stats()
        assert stats["total_buffered"] == 1
        assert stats["device_count"] == 1

    def test_get_device_status_marks_offline_after_timeout(self, agent):
        agent.collect_event("timeout-dev", "test", {"v": 1})
        agent._device_status["timeout-dev"]["last_seen_ts"] = 0.0
        status = agent.get_device_status("timeout-dev")
        assert status["online"] is False


@pytest.mark.asyncio
async def test_ingest_iot_event_api(client):
    payload = {
        "device_id": "api-sensor-01",
        "event_type": "temperature",
        "payload": {"temperature": 36.2, "battery_level": 90.0},
    }
    resp = await client.post("/api/v1/iot/events", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["device_id"] == "api-sensor-01"
    assert data["event_type"] == "temperature"
    assert data["buffered"] is True


@pytest.mark.asyncio
async def test_iot_batch_api(client):
    payload = {
        "events": [
            {"device_id": "batch-1", "event_type": "temp", "payload": {"v": 30}},
            {"device_id": "batch-1", "event_type": "humidity", "payload": {"v": 65}},
        ]
    }
    resp = await client.post("/api/v1/iot/events/batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] == 2
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_iot_flush_api(client):
    await client.post("/api/v1/iot/events", json={
        "device_id": "flush-api", "event_type": "test", "payload": {"v": 1},
    })
    resp = await client.post("/api/v1/iot/events/flush")
    assert resp.status_code == 200
    data = resp.json()
    assert data["flushed"] >= 1


@pytest.mark.asyncio
async def test_iot_device_status_api(client):
    await client.post("/api/v1/iot/events", json={
        "device_id": "status-dev", "event_type": "test", "payload": {"battery_level": 75.0},
    })
    resp = await client.get("/api/v1/iot/status/status-dev")
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == "status-dev"
    assert data["total_events_collected"] == 1


@pytest.mark.asyncio
async def test_iot_buffer_stats_api(client):
    resp = await client.get("/api/v1/iot/buffer/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_buffered" in data
    assert "device_count" in data
