import json
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

VALID_TOPICS = frozenset({"security_events", "alerts", "anomaly_scores", "playbook_triggers"})


class MessageQueue:
    def __init__(self) -> None:
        self._topics: dict[str, list[dict]] = defaultdict(list)
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self._audit_log: list[dict] = []

    def publish(self, topic: str, key: str, value: Any) -> dict:
        if topic not in VALID_TOPICS:
            msg = f"Invalid topic: {topic}. Valid: {', '.join(VALID_TOPICS)}"
            logger.warning(msg)
            return {"success": False, "error": msg}

        message = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "key": key,
            "value": value if isinstance(value, dict) else {"data": value},
            "published_at": datetime.now(UTC).isoformat(),
        }
        self._topics[topic].append(message)

        entry = {
            "type": "publish",
            "topic": topic,
            "key": key,
            "message_id": message["id"],
            "timestamp": message["published_at"],
        }
        self._audit_log.append(entry)
        logger.info("Published to %s: key=%s id=%s", topic, key, message["id"])

        for callback in self._subscriptions.get(topic, []):
            try:
                callback(message)
            except Exception as e:
                logger.error("Callback error on topic %s: %s", topic, e)

        return {"success": True, "message_id": message["id"]}

    def consume(self, topic: str, callback: Callable[[dict], Any]) -> None:
        if topic not in VALID_TOPICS:
            msg = f"Invalid topic: {topic}. Valid: {', '.join(VALID_TOPICS)}"
            logger.warning(msg)
            return
        self._subscriptions[topic].append(callback)
        logger.info("Subscribed to %s", topic)

    def get_messages(self, topic: str, limit: int = 100) -> list[dict]:
        return list(self._topics.get(topic, []))[-limit:]

    def get_audit_log(self, limit: int = 200) -> list[dict]:
        return list(self._audit_log[-limit:])

    def clear(self) -> None:
        self._topics.clear()
        self._subscriptions.clear()
        self._audit_log.clear()


_SEVERITY_MAP = {
    "emerg": "critical",
    "alert": "critical",
    "crit": "critical",
    "critical": "critical",
    "high": "high",
    "err": "high",
    "error": "high",
    "medium": "medium",
    "warning": "medium",
    "warn": "medium",
    "low": "low",
    "notice": "low",
    "info": "low",
    "debug": "low",
}


class EventNormalizer:
    def normalize_event(self, raw_event: dict | str, source_type: str) -> dict:
        if source_type == "syslog":
            return self._normalize_syslog(raw_event)
        if source_type == "windows_event":
            return self._normalize_windows_event(raw_event)
        if source_type == "graph_api":
            return self._normalize_graph_api(raw_event)
        if source_type == "snmp":
            return self._normalize_snmp(raw_event)
        if source_type == "custom":
            return self._normalize_custom(raw_event)
        msg = f"Unknown source_type: {source_type}"
        raise ValueError(msg)

    def _normalize_syslog(self, raw: dict | str) -> dict:
        if isinstance(raw, str):
            parts = raw.split(None, 5)
            raw_data = {}
            if len(parts) >= 6:
                raw_data = {
                    "timestamp": parts[0] + " " + parts[1],
                    "host": parts[2],
                    "process": parts[3].strip(":"),
                    "message": parts[5],
                }
            else:
                raw_data = {"message": raw}
        else:
            raw_data = raw

        message = raw_data.get("message", "")
        severity_str = raw_data.get("severity", "info").lower()
        severity = _SEVERITY_MAP.get(severity_str, "low")

        normalized = {
            "event_type": "syslog_event",
            "source": raw_data.get("host", "unknown"),
            "source_type": "syslog",
            "severity": severity,
            "description": message,
            "source_ip": raw_data.get("source_ip"),
            "destination_ip": raw_data.get("destination_ip"),
        }
        normalized["cef_formatted"] = self._to_cef(
            vendor="Syslog",
            product="Generic",
            version="1.0",
            signature_id="SYSLOG",
            name=normalized["event_type"],
            severity=severity,
            ext={"message": message},
        )
        return normalized

    def _normalize_windows_event(self, raw: dict | str) -> dict:
        raw_data = raw if isinstance(raw, dict) else {"raw": str(raw)}
        event_id = raw_data.get("event_id", "0")
        severity_str = raw_data.get("severity", "info").lower()
        severity = _SEVERITY_MAP.get(severity_str, "low")

        normalized = {
            "event_type": f"windows_event_{event_id}",
            "source": raw_data.get("computer", "unknown"),
            "source_type": "windows_event",
            "severity": severity,
            "description": raw_data.get("message", str(raw)),
            "source_ip": raw_data.get("source_ip"),
            "destination_ip": raw_data.get("destination_ip"),
        }
        normalized["cef_formatted"] = self._to_cef(
            vendor="Microsoft",
            product="Windows",
            version="10.0",
            signature_id=f"WIN-EVENT-{event_id}",
            name=normalized["event_type"],
            severity=severity,
            ext={"event_id": event_id, "computer": raw_data.get("computer", "")},
        )
        return normalized

    def _normalize_graph_api(self, raw: dict | str) -> dict:
        raw_data = raw if isinstance(raw, dict) else {"raw": str(raw)}
        audit_log = raw_data.get("auditLog", raw_data)
        if isinstance(audit_log, str):
            try:
                audit_log = json.loads(audit_log)
            except (json.JSONDecodeError, TypeError):
                audit_log = {"raw": str(audit_log)}

        activity = audit_log.get("activity", "graph_api_call")
        severity_str = audit_log.get("severity", "info").lower()
        severity = _SEVERITY_MAP.get(severity_str, "low")

        normalized = {
            "event_type": f"graph_api_{activity}",
            "source": audit_log.get("initiatedBy", {}).get("user", {}).get("id", "unknown")
            if isinstance(audit_log, dict)
            else "unknown",
            "source_type": "graph_api",
            "severity": severity,
            "description": audit_log.get("detail", str(raw)),
            "source_ip": audit_log.get("ipAddress") if isinstance(audit_log, dict) else None,
            "destination_ip": None,
        }
        normalized["cef_formatted"] = self._to_cef(
            vendor="Microsoft",
            product="GraphAPI",
            version="1.0",
            signature_id=f"GRAPH-{activity.upper()}",
            name=normalized["event_type"],
            severity=severity,
            ext={"activity": activity, "detail": audit_log.get("detail", "") if isinstance(audit_log, dict) else ""},
        )
        return normalized

    def _normalize_snmp(self, raw: dict | str) -> dict:
        raw_data = raw if isinstance(raw, dict) else {"raw": str(raw)}
        trap_oid = raw_data.get("oid", "1.3.6.1.6.3.1.1.5")
        severity_str = raw_data.get("severity", "warning").lower()
        severity = _SEVERITY_MAP.get(severity_str, "medium")

        normalized = {
            "event_type": f"snmp_trap_{trap_oid.replace('.', '_')}",
            "source": raw_data.get("agent", "unknown"),
            "source_type": "snmp",
            "severity": severity,
            "description": raw_data.get("message", str(raw)),
            "source_ip": raw_data.get("agent_ip"),
            "destination_ip": None,
        }
        normalized["cef_formatted"] = self._to_cef(
            vendor="SNMP",
            product="Trap",
            version="2c",
            signature_id=f"SNMP-{trap_oid}",
            name=normalized["event_type"],
            severity=severity,
            ext={"oid": trap_oid, "agent": raw_data.get("agent", "")},
        )
        return normalized

    def _normalize_custom(self, raw: dict | str) -> dict:
        raw_data = raw if isinstance(raw, dict) else {"raw": str(raw)}
        event_type = raw_data.get("event_type", "custom_event")
        severity_str = raw_data.get("severity", "info").lower()
        severity = _SEVERITY_MAP.get(severity_str, "low")
        source = raw_data.get("source", "custom")

        normalized = {
            "event_type": event_type,
            "source": source,
            "source_type": "custom",
            "severity": severity,
            "description": raw_data.get("description", raw_data.get("message", str(raw))),
            "source_ip": raw_data.get("source_ip"),
            "destination_ip": raw_data.get("destination_ip"),
        }
        normalized["cef_formatted"] = self._to_cef(
            vendor=raw_data.get("vendor", "Custom"),
            product=raw_data.get("product", "Generic"),
            version=raw_data.get("version", "1.0"),
            signature_id=raw_data.get("signature_id", "CUSTOM-001"),
            name=normalized["event_type"],
            severity=severity,
            ext={k: str(v) for k, v in raw_data.items() if k not in ("event_type", "severity", "source")},
        )
        return normalized

    @staticmethod
    def _to_cef(
        vendor: str,
        product: str,
        version: str,
        signature_id: str,
        name: str,
        severity: str,
        ext: dict | None = None,
    ) -> str:
        sev_map = {"critical": 10, "high": 8, "medium": 5, "low": 3}
        sev_num = sev_map.get(severity, 5)
        ext_str = " ".join(f"{k}={v}" for k, v in (ext or {}).items())
        return f"CEF:0|{vendor}|{product}|{version}|{signature_id}|{name}|{sev_num}|{ext_str}".strip()


message_queue = MessageQueue()
event_normalizer = EventNormalizer()
