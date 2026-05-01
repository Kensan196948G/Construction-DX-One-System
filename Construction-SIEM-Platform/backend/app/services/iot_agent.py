import gzip
import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class IoTLightweightAgent:
    def __init__(self, max_buffer_size: int = 10000, retention_seconds: int = 86400):
        self.max_buffer_size = max_buffer_size
        self.retention_seconds = retention_seconds
        self._buffer: dict[str, list[dict]] = defaultdict(list)
        self._device_status: dict[str, dict] = {}
        self._event_counters: dict[str, int] = defaultdict(int)

    def collect_event(self, device_id: str, event_type: str, payload: dict | object) -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            "event_type": event_type,
            "payload": payload if isinstance(payload, dict) else payload.model_dump(),
            "timestamp": datetime.now(UTC).isoformat(),
            "collected_at": time.time(),
        }
        self._event_counters[device_id] += 1

        if device_id not in self._device_status:
            self._device_status[device_id] = {
                "device_id": device_id,
                "online": True,
                "last_seen": event["timestamp"],
                "last_seen_ts": event["collected_at"],
                "battery_level": payload.get("battery_level") if isinstance(payload, dict) else 100.0,
                "signal_strength": payload.get("signal_strength") if isinstance(payload, dict) else -50,
            }
        else:
            self._device_status[device_id]["last_seen"] = event["timestamp"]
            self._device_status[device_id]["last_seen_ts"] = event["collected_at"]
            self._device_status[device_id]["online"] = True
            if isinstance(payload, dict):
                if "battery_level" in payload:
                    self._device_status[device_id]["battery_level"] = payload["battery_level"]
                if "signal_strength" in payload:
                    self._device_status[device_id]["signal_strength"] = payload["signal_strength"]

        self._buffer[device_id].append(event)
        self._trim_buffer(device_id)

        return {
            "status": "success",
            "event_id": event["id"],
            "device_id": device_id,
            "event_type": event_type,
            "timestamp": event["timestamp"],
            "buffered": True,
        }

    def batch_events(self, events: list[dict]) -> list[dict]:
        batched = []
        for event in events:
            if not isinstance(event, dict):
                try:
                    event = event.model_dump()
                except AttributeError:
                    continue
            ev = {
                "device_id": event.get("device_id", "unknown"),
                "event_type": event.get("event_type", "unknown"),
                "payload": event.get("payload", {}),
                "timestamp": event.get("timestamp", datetime.now(UTC).isoformat()),
            }
            batched.append(ev)
        return batched

    @staticmethod
    def compress_log(data: str | dict | bytes) -> bytes:
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return gzip.compress(data)

    @staticmethod
    def decompress_log(compressed: bytes) -> str:
        return gzip.decompress(compressed).decode("utf-8")

    def buffer_offline(self, events: list[dict]) -> dict:
        device_groups: dict[str, list[dict]] = defaultdict(list)
        for event in events:
            if not isinstance(event, dict):
                try:
                    event = event.model_dump()
                except AttributeError:
                    continue
            device_id = event.get("device_id", "unknown")
            ev = {
                "id": str(uuid.uuid4()),
                "device_id": device_id,
                "event_type": event.get("event_type", "unknown"),
                "payload": event.get("payload", {}),
                "timestamp": event.get("timestamp", datetime.now(UTC).isoformat()),
                "collected_at": time.time(),
                "offline_buffered": True,
            }
            device_groups[device_id].append(ev)

        total = 0
        for device_id, dev_events in device_groups.items():
            if device_id not in self._device_status:
                self._device_status[device_id] = {
                    "device_id": device_id, "online": False, "last_seen": None,
                    "last_seen_ts": None,
                    "battery_level": None, "signal_strength": None,
                }
            else:
                self._device_status[device_id]["online"] = False
            self._buffer[device_id].extend(dev_events)
            self._trim_buffer(device_id)
            total += len(dev_events)

        return {
            "status": "success",
            "buffered": total,
            "device_count": len(device_groups),
            "message": f"Buffered {total} events across {len(device_groups)} devices",
        }

    def flush_buffer(self, device_id: str | None = None) -> list[dict]:
        flushed = []
        devices = [device_id] if device_id else list(self._buffer.keys())
        for dev_id in devices:
            events = self._buffer.pop(dev_id, [])
            for ev in events:
                ev.pop("offline_buffered", None)
                ev["flushed_at"] = datetime.now(UTC).isoformat()
            flushed.extend(events)
            if dev_id in self._device_status:
                self._device_status[dev_id]["online"] = True
                self._device_status[dev_id]["last_seen"] = datetime.now(UTC).isoformat()
                self._device_status[dev_id]["last_seen_ts"] = time.time()
        return flushed

    def get_device_status(self, device_id: str) -> dict:
        status = self._device_status.get(device_id)
        if status is None:
            return {
                "device_id": device_id,
                "online": False,
                "last_seen": None,
                "buffer_size": 0,
                "total_events_collected": 0,
                "battery_level": None,
                "signal_strength": None,
            }
        online = status.get("online", False)
        last_ts = status.get("last_seen_ts")
        if last_ts is not None and online and time.time() - last_ts > 300:
            online = False
        buffer_size = len(self._buffer.get(device_id, []))
        return {
            "device_id": device_id,
            "online": online,
            "last_seen": status.get("last_seen"),
            "buffer_size": buffer_size,
            "total_events_collected": self._event_counters.get(device_id, 0),
            "battery_level": status.get("battery_level"),
            "signal_strength": status.get("signal_strength"),
        }

    def get_buffer_stats(self) -> dict:
        total = sum(len(events) for events in self._buffer.values())
        device_count = len(self._buffer)
        oldest = None
        for events in self._buffer.values():
            for ev in events:
                ts = ev.get("collected_at") or ev.get("timestamp", "")
                if isinstance(ts, int | float):
                    if oldest is None or ts < oldest:
                        oldest = ts
        oldest_str = datetime.fromtimestamp(oldest).isoformat() if oldest else None
        return {
            "total_buffered": total,
            "device_count": device_count,
            "oldest_buffer": oldest_str,
            "max_buffer_size": self.max_buffer_size,
            "retention_seconds": self.retention_seconds,
        }

    def _trim_buffer(self, device_id: str) -> None:
        events = self._buffer[device_id]
        cutoff = time.time() - self.retention_seconds
        events[:] = [e for e in events if (e.get("collected_at") or 0) >= cutoff]
        if len(events) > self.max_buffer_size:
            events[: len(events) - self.max_buffer_size] = []


_agent_instance: IoTLightweightAgent | None = None


def get_iot_agent() -> IoTLightweightAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = IoTLightweightAgent()
    return _agent_instance
