import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.services.message_queue import message_queue

logger = logging.getLogger(__name__)


BUILTIN_PLAYBOOKS: list[dict] = [
    {
        "id": "ransomware_response",
        "name": "ランサムウェア対応プレイブック",
        "description": "CST-004検知時にアラート作成、セキュリティチーム通知、影響システム隔離",
        "trigger_event_type": "rule_match",
        "conditions": {"rule_id_pattern": "CST-004"},
        "actions": [
            {"action": "create_alert", "params": {"severity": "critical", "category": "ransomware"}},
            {"action": "notify", "params": {"team": "security", "method": "email"}},
            {"action": "isolate", "params": {"scope": "affected_systems"}},
            {"action": "create_ticket", "params": {"service": "service_now", "priority": "critical"}},
        ],
        "is_active": True,
    },
    {
        "id": "brute_force_response",
        "name": "ブルートフォース対応プレイブック",
        "description": "GEN-001検知時にアラート作成、送信元IPブロック、管理者通知",
        "trigger_event_type": "rule_match",
        "conditions": {"rule_id_pattern": "GEN-001"},
        "actions": [
            {"action": "create_alert", "params": {"severity": "high", "category": "brute_force"}},
            {"action": "block_ip", "params": {"target": "source_ip"}},
            {"action": "notify", "params": {"team": "admin", "method": "email"}},
        ],
        "is_active": True,
    },
    {
        "id": "cad_exfiltration_response",
        "name": "CADデータ外部送信対応プレイブック",
        "description": "CST-001/CST-006検知時にアラート作成、DLPチーム通知",
        "trigger_event_type": "rule_match",
        "conditions": {"rule_id_pattern": "CST-00[16]"},
        "actions": [
            {"action": "create_alert", "params": {"severity": "high", "category": "cad_exfiltration"}},
            {"action": "notify", "params": {"team": "dlp", "method": "email"}},
            {"action": "create_ticket", "params": {"service": "service_now", "priority": "high"}},
        ],
        "is_active": True,
    },
]

_execution_logs: list[dict] = []


def get_available_playbooks() -> list[dict]:
    return [p for p in BUILTIN_PLAYBOOKS if p["is_active"]]


def get_playbook(playbook_id: str) -> dict | None:
    for p in BUILTIN_PLAYBOOKS:
        if p["id"] == playbook_id:
            return p
    return None


def evaluate_conditions(conditions: dict, event_data: dict) -> bool:
    rule_id_pattern = conditions.get("rule_id_pattern", "")
    if rule_id_pattern:
        import re

        event_rule_id = event_data.get("rule_id", event_data.get("matched_rule_id", ""))
        if not event_rule_id:
            event_source = event_data.get("source", "")
            event_type = event_data.get("event_type", "")
            combined = f"{event_source} {event_type}"
            if re.search(rule_id_pattern, combined, re.IGNORECASE):
                return True
            return False
        if re.search(rule_id_pattern, event_rule_id):
            return True
        return False

    severity_min = conditions.get("severity_min")
    if severity_min:
        order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        event_sev = event_data.get("severity", "low")
        if order.get(event_sev, 0) < order.get(severity_min, 0):
            return False

    field_conditions = conditions.get("field_conditions", {})
    for field, expected in field_conditions.items():
        actual = event_data.get(field)
        if callable(expected):
            if not expected(actual):
                return False
        elif actual != expected:
            return False

    return True


async def run_automated_response(action: str, params: dict, db: AsyncSession) -> dict:
    if action == "create_alert":
        title = params.get("title", f"Playbook generated alert ({params.get('category', 'unknown')})")
        description = params.get("description", title)
        alert = Alert(
            title=title,
            severity=params.get("severity", "medium"),
            source=params.get("source", "playbook"),
            description=description,
            mitre_tactic=params.get("mitre_tactic"),
            mitre_technique=params.get("mitre_technique"),
            site=params.get("site"),
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        message_queue.publish("alerts", alert.id, {"title": alert.title, "severity": alert.severity})
        return {"success": True, "message": f"Alert created: {alert.id}", "alert_id": alert.id}

    if action == "notify":
        team = params.get("team", "unknown")
        method = params.get("method", "email")
        message = params.get("message", f"Notification sent to {team} via {method}")
        logger.info("NOTIFY: team=%s method=%s message=%s", team, method, message)
        return {"success": True, "message": message, "team": team, "method": method}

    if action == "isolate":
        scope = params.get("scope", "unknown")
        logger.info("ISOLATE: scope=%s", scope)
        return {"success": True, "message": f"System isolation initiated: {scope}", "scope": scope}

    if action == "block_ip":
        target = params.get("target", "source_ip")
        ip = params.get("ip", "unknown")
        logger.info("BLOCK_IP: target=%s ip=%s", target, ip)
        return {"success": True, "message": f"IP blocked on firewall: {ip or target}", "target": target}

    if action == "create_ticket":
        service = params.get("service", "default")
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        logger.info("TICKET: service=%s ticket_id=%s", service, ticket_id)
        message_queue.publish("playbook_triggers", ticket_id, {"service": service, "action": "ticket_created"})
        return {
            "success": True,
            "message": f"Ticket created in {service}: {ticket_id}",
            "ticket_id": ticket_id,
            "service": service,
        }

    return {"success": False, "message": f"Unknown action: {action}"}


async def execute_playbook(playbook_id: str, event_data: dict, db: AsyncSession) -> dict:
    playbook = get_playbook(playbook_id)
    if not playbook:
        return {
            "playbook_id": playbook_id,
            "playbook_name": "unknown",
            "success": False,
            "actions": [],
            "execution_time": datetime.now(UTC),
            "log_id": "",
            "error": f"Playbook not found: {playbook_id}",
        }

    if not evaluate_conditions(playbook["conditions"], event_data):
        return {
            "playbook_id": playbook_id,
            "playbook_name": playbook["name"],
            "success": True,
            "actions": [],
            "execution_time": datetime.now(UTC),
            "log_id": "",
            "message": "Conditions not met, no actions executed",
        }

    results = []
    all_success = True
    for action_def in playbook["actions"]:
        action = action_def["action"]
        params = dict(action_def.get("params", {}))
        for key, val in params.items():
            if isinstance(val, str) and val.startswith("event."):
                field = val[6:]
                params[key] = event_data.get(field, val)
        params["source"] = params.get("source", event_data.get("source", "playbook"))
        params["site"] = params.get("site", event_data.get("site"))
        params["mitre_tactic"] = params.get("mitre_tactic", event_data.get("mitre_tactic"))
        params["mitre_technique"] = params.get("mitre_technique", event_data.get("mitre_technique"))

        if action == "block_ip" and params.get("target") == "source_ip":
            params["ip"] = event_data.get("source_ip", "unknown")

        result = await run_automated_response(action, params, db)
        results.append(result)
        if not result.get("success", False):
            all_success = False

    log_id = str(uuid.uuid4())
    log_entry = {
        "id": log_id,
        "playbook_id": playbook_id,
        "playbook_name": playbook["name"],
        "trigger_event_type": playbook["trigger_event_type"],
        "event_data_summary": str({k: v for k, v in event_data.items() if k in ("rule_id", "event_type", "source", "severity")}),
        "actions": results,
        "success": all_success,
        "executed_at": datetime.now(UTC),
    }
    _execution_logs.append(log_entry)

    message_queue.publish("playbook_triggers", log_id, log_entry)

    return {
        "playbook_id": playbook_id,
        "playbook_name": playbook["name"],
        "success": all_success,
        "actions": [
            {"action": r.get("action", "unknown"), "success": r.get("success", False), "message": r.get("message", ""), "details": r}
            for r in results
        ],
        "execution_time": datetime.now(UTC),
        "log_id": log_id,
    }


def get_execution_logs(limit: int = 50) -> list[dict]:
    return list(_execution_logs[-limit:])


def clear_logs() -> None:
    _execution_logs.clear()
