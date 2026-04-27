from app.services.rule_engine import (
    _evaluate_custom,
    _evaluate_sigma,
    _evaluate_yara,
    check_rule,
    evaluate_rule,
)

SIGMA_RULE = """detection:
  field: event_type
  pattern: login_failed
  condition: count > 5
"""

YARA_RULE = """rule PowerShellMalicious {
  strings:
    $encoded = "-EncodedCommand" nocase
    $bypass = "-ExecutionPolicy Bypass" nocase
    $download = "DownloadString" nocase
    $invoke = "Invoke-Expression" nocase
  condition:
    any of ($encoded, $bypass, $download, $invoke)
}
"""

CUSTOM_RULE = "event_type == 'malicious' and severity > 3"


class TestSigmaRuleEvaluation:
    def test_sigma_match_pattern_and_condition(self):
        event = {"event_type": "login_failed", "count": 10}
        assert _evaluate_sigma(SIGMA_RULE, event) is True

    def test_sigma_no_match_pattern(self):
        event = {"event_type": "login_success", "count": 10}
        assert _evaluate_sigma(SIGMA_RULE, event) is False

    def test_sigma_no_match_condition(self):
        event = {"event_type": "login_failed", "count": 3}
        assert _evaluate_sigma(SIGMA_RULE, event) is False

    def test_sigma_empty_field(self):
        rule = "detection:\n  condition: x > 1\n"
        assert _evaluate_sigma(rule, {}) is False

    def test_sigma_range_condition_match(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: hour in range(8, 18)\n"
        event = {"event_type": "test", "hour": 10}
        assert _evaluate_sigma(rule, event) is True

    def test_sigma_range_condition_no_match(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: hour in range(8, 18)\n"
        event = {"event_type": "test", "hour": 20}
        assert _evaluate_sigma(rule, event) is False

    def test_sigma_not_in_range(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: hour not in range(7, 20)\n"
        event = {"event_type": "test", "hour": 3}
        assert _evaluate_sigma(rule, event) is True

    def test_sigma_in_list_match(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: status in ['open', 'active']\n"
        event = {"event_type": "test", "status": "open"}
        assert _evaluate_sigma(rule, event) is True

    def test_sigma_in_list_no_match(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: status in ['open', 'active']\n"
        event = {"event_type": "test", "status": "closed"}
        assert _evaluate_sigma(rule, event) is False

    def test_sigma_not_in_list(self):
        rule = "detection:\n  field: event_type\n  pattern: test\n  condition: role not in ['admin', 'root']\n"
        event = {"event_type": "test", "role": "user"}
        assert _evaluate_sigma(rule, event) is True


class TestYaraRuleEvaluation:
    def test_yara_match(self):
        event = {"raw_log": "powershell -ExecutionPolicy Bypass -EncodedCommand XYZ"}
        assert _evaluate_yara(YARA_RULE, event) is True

    def test_yara_no_match(self):
        event = {"raw_log": "normal command execution"}
        assert _evaluate_yara(YARA_RULE, event) is False

    def test_yara_match_encoded(self):
        event = {"command": "Invoke-Expression -Command 'test'"}
        assert _evaluate_yara(YARA_RULE, event) is True

    def test_yara_no_strings_block(self):
        rule = "rule Empty { condition: false }"
        event = {"raw_log": "test"}
        assert _evaluate_yara(rule, event) is False


class TestCustomRuleEvaluation:
    def test_custom_match(self):
        event = {"event_type": "malicious", "severity": 5}
        assert _evaluate_custom(CUSTOM_RULE, event) is True

    def test_custom_no_match(self):
        event = {"event_type": "benign", "severity": 2}
        assert _evaluate_custom(CUSTOM_RULE, event) is False

    def test_custom_invalid_syntax(self):
        assert _evaluate_custom("import os", {}) is False

    def test_custom_unsafe_access_blocked(self):
        assert _evaluate_custom("__import__('os').system('id')", {}) is False

    def test_custom_string_equality(self):
        event = {"event_type": "malicious"}
        assert _evaluate_custom("event_type == 'malicious'", event) is True


class TestEvaluateRule:
    def test_sigma_through_evaluate(self):
        event = {"event_type": "login_failed", "count": 10}
        assert evaluate_rule(SIGMA_RULE, "sigma", event) is True

    def test_yara_through_evaluate(self):
        event = {"raw_log": "powershell -ExecutionPolicy Bypass"}
        assert evaluate_rule(YARA_RULE, "yara", event) is True

    def test_custom_through_evaluate(self):
        event = {"event_type": "malicious", "severity": 5}
        assert evaluate_rule(CUSTOM_RULE, "custom", event) is True

    def test_unknown_type(self):
        assert evaluate_rule("test", "unknown", {}) is False


class TestCheckRule:
    def test_check_rule_match(self):
        event = {"event_type": "login_failed", "count": 10}
        assert check_rule(SIGMA_RULE, "sigma", event) is True

    def test_check_rule_no_match(self):
        event = {"event_type": "login_success", "count": 3}
        assert check_rule(SIGMA_RULE, "sigma", event) is False
