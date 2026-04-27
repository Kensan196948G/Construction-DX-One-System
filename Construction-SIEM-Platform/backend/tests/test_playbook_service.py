import pytest

from app.services.playbook_service import (
    evaluate_conditions,
    execute_playbook,
    get_available_playbooks,
    get_execution_logs,
    get_playbook,
    run_automated_response,
)


class TestPlaybookService:
    def test_get_available_playbooks(self):
        playbooks = get_available_playbooks()
        assert len(playbooks) == 3
        ids = [p["id"] for p in playbooks]
        assert "ransomware_response" in ids
        assert "brute_force_response" in ids
        assert "cad_exfiltration_response" in ids

    def test_get_playbook_found(self):
        pb = get_playbook("ransomware_response")
        assert pb is not None
        assert pb["name"] == "ランサムウェア対応プレイブック"

    def test_get_playbook_not_found(self):
        pb = get_playbook("nonexistent")
        assert pb is None

    def test_evaluate_conditions_match_rule_id(self):
        conditions = {"rule_id_pattern": "CST-004"}
        assert evaluate_conditions(conditions, {"rule_id": "CST-004"}) is True
        assert evaluate_conditions(conditions, {"matched_rule_id": "CST-004"}) is True

    def test_evaluate_conditions_no_match_rule_id(self):
        conditions = {"rule_id_pattern": "CST-004"}
        assert evaluate_conditions(conditions, {"rule_id": "GEN-001"}) is False

    def test_evaluate_conditions_match_regex(self):
        conditions = {"rule_id_pattern": "CST-00[16]"}
        assert evaluate_conditions(conditions, {"rule_id": "CST-001"}) is True
        assert evaluate_conditions(conditions, {"rule_id": "CST-006"}) is True
        assert evaluate_conditions(conditions, {"rule_id": "CST-004"}) is False

    def test_evaluate_conditions_no_event_data(self):
        conditions = {"rule_id_pattern": "CST-004"}
        assert evaluate_conditions(conditions, {}) is False

    def test_ransomware_playbook_builtin(self):
        pb = get_playbook("ransomware_response")
        assert pb is not None
        assert len(pb["actions"]) == 4
        action_types = [a["action"] for a in pb["actions"]]
        assert "create_alert" in action_types
        assert "notify" in action_types
        assert "isolate" in action_types
        assert "create_ticket" in action_types

    def test_brute_force_playbook_builtin(self):
        pb = get_playbook("brute_force_response")
        assert pb is not None
        assert len(pb["actions"]) == 3
        action_types = [a["action"] for a in pb["actions"]]
        assert "create_alert" in action_types
        assert "block_ip" in action_types
        assert "notify" in action_types

    def test_cad_exfiltration_playbook_builtin(self):
        pb = get_playbook("cad_exfiltration_response")
        assert pb is not None
        assert len(pb["actions"]) == 3
        action_types = [a["action"] for a in pb["actions"]]
        assert "create_alert" in action_types
        assert "notify" in action_types
        assert "create_ticket" in action_types


@pytest.mark.asyncio
async def test_run_create_alert(db):
    result = await run_automated_response("create_alert", {"title": "Test Alert", "severity": "high", "category": "test", "source": "pytest"}, db)
    assert result["success"] is True
    assert result["alert_id"] is not None


@pytest.mark.asyncio
async def test_run_notify(db):
    result = await run_automated_response("notify", {"team": "security", "method": "email"}, db)
    assert result["success"] is True
    assert result["team"] == "security"


@pytest.mark.asyncio
async def test_run_isolate(db):
    result = await run_automated_response("isolate", {"scope": "affected_systems"}, db)
    assert result["success"] is True


@pytest.mark.asyncio
async def test_run_block_ip(db):
    result = await run_automated_response("block_ip", {"target": "source_ip", "ip": "10.0.0.5"}, db)
    assert result["success"] is True


@pytest.mark.asyncio
async def test_run_create_ticket(db):
    result = await run_automated_response("create_ticket", {"service": "service_now", "priority": "high"}, db)
    assert result["success"] is True
    assert result["ticket_id"] is not None


@pytest.mark.asyncio
async def test_run_unknown_action(db):
    result = await run_automated_response("unknown_action", {}, db)
    assert result["success"] is False


@pytest.mark.asyncio
async def test_execute_playbook_full_flow(db):
    event_data = {
        "rule_id": "CST-004",
        "event_type": "file_encrypt",
        "source": "endpoint-01",
        "severity": "critical",
        "source_ip": "192.168.1.50",
    }
    result = await execute_playbook("ransomware_response", event_data, db)
    assert result["success"] is True
    assert result["playbook_id"] == "ransomware_response"
    assert len(result["actions"]) == 4
    assert result["log_id"] != ""


@pytest.mark.asyncio
async def test_execute_playbook_conditions_not_met(db):
    event_data = {"rule_id": "GEN-002", "severity": "low"}
    result = await execute_playbook("ransomware_response", event_data, db)
    assert result["success"] is True
    assert result["actions"] == []


@pytest.mark.asyncio
async def test_execute_playbook_not_found(db):
    result = await execute_playbook("nonexistent", {}, db)
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_execution_logs(db):
    from app.services.playbook_service import _execution_logs
    _execution_logs.clear()
    event_data = {"rule_id": "GEN-001", "severity": "high", "source": "firewall"}
    await execute_playbook("brute_force_response", event_data, db)
    logs = get_execution_logs()
    assert len(logs) >= 1
    assert logs[-1]["playbook_id"] == "brute_force_response"
