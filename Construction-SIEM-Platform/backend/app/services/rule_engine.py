import ast
import re
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import DetectionRule

SEED_RULES: list[dict] = [
    {
        "rule_id": "CST-001",
        "name": "CAD/BIMファイル大量エクスポート",
        "description": "短時間に大量のCAD/BIMファイルがエクスポートされたことを検知",
        "rule_type": "sigma",
        "category": "cad_exfiltration",
        "severity": "high",
        "mitre_attack_id": "T1567",
        "rule_content": "detection:\n  field: event_type\n  pattern: file_export\n  condition: count > 50\n  timeframe: 5m\n",
    },
    {
        "rule_id": "CST-002",
        "name": "現場外デバイス接続",
        "description": "登録されていないデバイスが現場ネットワークに接続したことを検知",
        "rule_type": "sigma",
        "category": "unauthorized_access",
        "severity": "medium",
        "mitre_attack_id": "T1078",
        "rule_content": "detection:\n  field: event_type\n  pattern: device_connect\n  condition: device_registered == false\n",
    },
    {
        "rule_id": "CST-003",
        "name": "IoTデバイス異常通信",
        "description": "IoT/センサーデバイスが通常と異なる通信パターンを示したことを検知",
        "rule_type": "sigma",
        "category": "iot_anomaly",
        "severity": "high",
        "mitre_attack_id": "T1190",
        "rule_content": "detection:\n  field: source_type\n  pattern: iot_sensor\n  condition: bytes_sent > 1000000 or destination_port not in [80, 443, 8080]\n",
    },
    {
        "rule_id": "CST-004",
        "name": "ランサムウェア兆候",
        "description": "ランサムウェア感染を示すファイル操作パターンを検知",
        "rule_type": "sigma",
        "category": "ransomware",
        "severity": "critical",
        "mitre_attack_id": "T1486",
        "rule_content": "detection:\n  field: event_type\n  pattern: file_encrypt\n  condition: file_ext in ['.encrypted', '.locked', '.crypt']\n  threshold: 10\n",
    },
    {
        "rule_id": "CST-005",
        "name": "BIMサーバ不審アクセス",
        "description": "BIMサーバへの不審なアクセスパターンを検知",
        "rule_type": "sigma",
        "category": "server_anomaly",
        "severity": "high",
        "mitre_attack_id": "T1190",
        "rule_content": "detection:\n  field: destination\n  pattern: bim-server\n  condition: login_attempts > 5 or hour not in range(6, 20)\n",
    },
    {
        "rule_id": "CST-006",
        "name": "設計図外部送信疑い",
        "description": "設計図データが外部宛先に送信されたことを検知",
        "rule_type": "sigma",
        "category": "cad_exfiltration",
        "severity": "high",
        "mitre_attack_id": "T1048",
        "rule_content": "detection:\n  field: event_type\n  pattern: data_transfer\n  condition: destination_ip not in private_range or data_size > 100000000\n",
    },
    {
        "rule_id": "GEN-001",
        "name": "ブルートフォース攻撃",
        "description": "短時間の複数ログイン失敗を検知",
        "rule_type": "sigma",
        "category": "brute_force",
        "severity": "high",
        "mitre_attack_id": "T1110",
        "rule_content": "detection:\n  field: event_type\n  pattern: login_failed\n  condition: count > 10\n  timeframe: 5m\n",
    },
    {
        "rule_id": "GEN-002",
        "name": "特権エスカレーション",
        "description": "不審な特権昇格操作を検知",
        "rule_type": "sigma",
        "category": "privilege_escalation",
        "severity": "critical",
        "mitre_attack_id": "T1068",
        "rule_content": "detection:\n  field: event_type\n  pattern: privilege_change\n  condition: new_role in ['admin', 'root'] and prev_role not in ['admin', 'root']\n",
    },
    {
        "rule_id": "GEN-003",
        "name": "横展開（ラテラルムーブメント）",
        "description": "内部ネットワークでの横展開活動を検知",
        "rule_type": "sigma",
        "category": "lateral_movement",
        "severity": "critical",
        "mitre_attack_id": "T1021",
        "rule_content": "detection:\n  field: event_type\n  pattern: network_connection\n  condition: source_ip internal and dest_ip internal and dest_port in [22, 3389, 445, 5985]\n",
    },
    {
        "rule_id": "GEN-004",
        "name": "PowerShell悪用",
        "description": "悪意のあるPowerShell実行を検知",
        "rule_type": "yara",
        "category": "malware",
        "severity": "high",
        "mitre_attack_id": "T1059",
        "rule_content": "rule PowerShellMalicious {\n  strings:\n    $encoded = \"-EncodedCommand\" nocase\n    $bypass = \"-ExecutionPolicy Bypass\" nocase\n    $download = \"DownloadString\" nocase\n    $invoke = \"Invoke-Expression\" nocase\n  condition:\n    any of ($encoded, $bypass, $download, $invoke)\n}\n",
    },
    {
        "rule_id": "GEN-005",
        "name": "業務時間外の特権操作",
        "description": "業務時間外の特権アカウント操作を検知",
        "rule_type": "sigma",
        "category": "anomaly",
        "severity": "low",
        "mitre_attack_id": None,
        "rule_content": "detection:\n  field: event_type\n  pattern: admin_action\n  condition: hour not in range(7, 20)\n",
    },
]


async def seed_rules(db: AsyncSession) -> None:
    result = await db.execute(select(DetectionRule).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    for rule_data in SEED_RULES:
        rule = DetectionRule(**rule_data)
        db.add(rule)
    await db.commit()


def _parse_sigma_rule(rule_content: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in rule_content.split("\n"):
        stripped = line.strip()
        if not stripped or ":" not in stripped or stripped.startswith("-"):
            continue
        parts = stripped.split(":", 1)
        key = parts[0].strip()
        value = parts[1].strip()
        if value:
            parsed[key] = value
    return parsed


_SAFE_AST_NODES = frozenset({
    ast.Expression, ast.Compare, ast.BoolOp, ast.Name, ast.Constant,
    ast.BinOp, ast.UnaryOp, ast.List, ast.Tuple, ast.Load,
    ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq,
    ast.In, ast.NotIn, ast.Is, ast.IsNot,
    ast.And, ast.Or, ast.Not,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub,
    ast.IfExp,
})


def _safe_eval(expr: str, namespace: dict) -> bool:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
        for node in ast.walk(tree):
            if type(node) not in _SAFE_AST_NODES:
                return False
        result = eval(
            compile(tree, "<string>", "eval"),
            {"__builtins__": {}},
            namespace,
        )
        return bool(result)
    except Exception:
        return False


def _evaluate_sigma(rule_content: str, event_data: dict) -> bool:
    parsed = _parse_sigma_rule(rule_content)
    field = parsed.get("field", "")
    pattern = parsed.get("pattern", "")
    condition_str = parsed.get("condition", "")
    if not field:
        return False
    event_value = event_data.get(field, "")
    if isinstance(event_value, str) and pattern:
        if pattern.lower() not in event_value.lower():
            return False
    if condition_str:
        condition_str = condition_str.strip()
        if "in range" in condition_str:
            m = re.search(r"(\w+)\s+not in range\((\d+),\s*(\d+)\)", condition_str)
            if m:
                var, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
                val = event_data.get(var)
                if val is not None and lo <= int(val) < hi:
                    return False
                return True
            m = re.search(r"(\w+)\s+in range\((\d+),\s*(\d+)\)", condition_str)
            if m:
                var, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
                val = event_data.get(var)
                if val is None:
                    return False
                return lo <= int(val) < hi
        if "not in" in condition_str:
            m = re.search(r"(\w+)\s+not in\s+\[(.+)\]", condition_str)
            if m:
                var, list_str = m.group(1), m.group(2)
                lst = [x.strip().strip("'\"") for x in list_str.split(",")]
                val = event_data.get(var)
                if val is None:
                    return False
                return str(val) not in lst
        if "in [" in condition_str or "in [" in condition_str:
            m = re.search(r"(\w+)\s+in\s+\[(.+)\]", condition_str)
            if m:
                var, list_str = m.group(1), m.group(2)
                lst = [x.strip().strip("'\"") for x in list_str.split(",")]
                val = event_data.get(var)
                if val is None:
                    return False
                return str(val) in lst
        namespace = {"count": 0, "threshold": 0, "private_range": False}
        namespace.update(
            {k: v for k, v in event_data.items() if isinstance(v, int | float | str | bool)}
        )
        return _safe_eval(condition_str, namespace)
    return True


def _evaluate_yara(rule_content: str, event_data: dict) -> bool:
    yara_strings: list[str] = []
    condition_str = ""
    in_strings = False
    for line in rule_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("strings:"):
            in_strings = True
            continue
        if stripped.startswith("condition:"):
            in_strings = False
            condition_str = stripped[len("condition:"):].strip()
            continue
        if in_strings and "=" in stripped:
            m = re.search(r'"([^"]*)"', stripped)
            if m:
                yara_strings.append(m.group(1).lower())
    if not yara_strings:
        return False
    text_fields = " ".join(
        str(v) for v in event_data.values() if isinstance(v, str | bytes)
    ).lower()
    matched = [s for s in yara_strings if s.lower() in text_fields]
    if "any of" in condition_str and matched:
        return True
    if "all of" in condition_str and len(matched) == len(yara_strings):
        return True
    if matched:
        return True
    return False


def _evaluate_custom(rule_content: str, event_data: dict) -> bool:
    namespace: dict = {}
    namespace.update(event_data)
    return _safe_eval(rule_content.strip(), namespace)


def evaluate_rule(rule_content: str, rule_type: str, event_data: dict) -> bool:
    if rule_type == "sigma":
        return _evaluate_sigma(rule_content, event_data)
    if rule_type == "yara":
        return _evaluate_yara(rule_content, event_data)
    if rule_type == "custom":
        return _evaluate_custom(rule_content, event_data)
    return False


def check_rule(rule_content: str, rule_type: str, event_data: dict) -> bool:
    return evaluate_rule(rule_content, rule_type, event_data)


async def get_matching_rules(event_data: dict, db: AsyncSession) -> Sequence[DetectionRule]:
    result = await db.execute(
        select(DetectionRule).where(DetectionRule.is_active)
    )
    rules = result.scalars().all()
    matched: list[DetectionRule] = []
    for rule in rules:
        if evaluate_rule(rule.rule_content, rule.rule_type, event_data):
            matched.append(rule)
    return matched
