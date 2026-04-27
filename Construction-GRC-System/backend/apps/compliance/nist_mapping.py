from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from .models import Control

NIST_CSF_FUNCTIONS: dict[str, dict[str, str]] = {
    "GOVERN": {
        "id": "GV",
        "name": "GOVERN",
        "title": "Govern",
        "description": "Establish and monitor the organization's cybersecurity risk management strategy, expectations, and policy",
    },
    "IDENTIFY": {
        "id": "ID",
        "name": "IDENTIFY",
        "title": "Identify",
        "description": "Identify current cybersecurity risks to people, assets, data, and capabilities",
    },
    "PROTECT": {
        "id": "PR",
        "name": "PROTECT",
        "title": "Protect",
        "description": "Use safeguards to prevent or reduce cybersecurity risk",
    },
    "DETECT": {
        "id": "DE",
        "name": "DETECT",
        "title": "Detect",
        "description": "Find and analyze potential cybersecurity attacks and compromises",
    },
    "RESPOND": {
        "id": "RS",
        "name": "RESPOND",
        "title": "Respond",
        "description": "Respond to cybersecurity incidents by containing, neutralizing, and analyzing",
    },
    "RECOVER": {
        "id": "RC",
        "name": "RECOVER",
        "title": "Recover",
        "description": "Recover assets and operations after a cybersecurity incident",
    },
}

NIST_CSF_CATEGORIES: dict[str, list[dict[str, str]]] = {
    "GOVERN": [
        {"id": "GV.OC", "name": "Organizational Context"},
        {"id": "GV.RM", "name": "Risk Management Strategy"},
        {"id": "GV.RR", "name": "Roles, Responsibilities, and Authorities"},
        {"id": "GV.PO", "name": "Policy"},
        {"id": "GV.OV", "name": "Oversight"},
        {"id": "GV.SC", "name": "Cybersecurity Supply Chain Risk Management"},
    ],
    "IDENTIFY": [
        {"id": "ID.AM", "name": "Asset Management"},
        {"id": "ID.RA", "name": "Risk Assessment"},
        {"id": "ID.IM", "name": "Improvement"},
    ],
    "PROTECT": [
        {"id": "PR.AA", "name": "Identity Management, Authentication, and Access Control"},
        {"id": "PR.AW", "name": "Awareness and Training"},
        {"id": "PR.DS", "name": "Data Security"},
        {"id": "PR.PS", "name": "Platform Security"},
        {"id": "PR.IR", "name": "Technology Infrastructure Resilience"},
    ],
    "DETECT": [
        {"id": "DE.CM", "name": "Continuous Monitoring"},
        {"id": "DE.AE", "name": "Adverse Event Analysis"},
    ],
    "RESPOND": [
        {"id": "RS.MA", "name": "Incident Management"},
        {"id": "RS.CO", "name": "Incident Analysis"},
        {"id": "RS.MI", "name": "Incident Mitigation"},
        {"id": "RS.IM", "name": "Incident Improvements"},
    ],
    "RECOVER": [
        {"id": "RC.RP", "name": "Recovery Planning"},
        {"id": "RC.IM", "name": "Recovery Improvements"},
        {"id": "RC.CO", "name": "Recovery Communications"},
    ],
}

ISO_TO_NIST_MAPPING: dict[str, list[dict[str, str]]] = {
    "A.5.1": [{"function": "GOVERN", "category": "GV.PO"}, {"function": "GOVERN", "category": "GV.OV"}],
    "A.5.2": [{"function": "GOVERN", "category": "GV.RR"}],
    "A.5.3": [{"function": "GOVERN", "category": "GV.RR"}, {"function": "PROTECT", "category": "PR.AA"}],
    "A.5.4": [{"function": "GOVERN", "category": "GV.RR"}],
    "A.5.5": [{"function": "IDENTIFY", "category": "ID.RA"}],
    "A.5.6": [{"function": "IDENTIFY", "category": "ID.RA"}, {"function": "GOVERN", "category": "GV.OC"}],
    "A.5.7": [{"function": "IDENTIFY", "category": "ID.RA"}, {"function": "DETECT", "category": "DE.AE"}],
    "A.5.8": [{"function": "GOVERN", "category": "GV.OC"}],
    "A.5.9": [{"function": "IDENTIFY", "category": "ID.AM"}],
    "A.5.10": [{"function": "IDENTIFY", "category": "ID.AM"}, {"function": "PROTECT", "category": "PR.DS"}],
    "A.5.11": [{"function": "IDENTIFY", "category": "ID.AM"}],
    "A.5.12": [{"function": "IDENTIFY", "category": "ID.AM"}, {"function": "PROTECT", "category": "PR.DS"}],
    "A.5.13": [{"function": "IDENTIFY", "category": "ID.AM"}, {"function": "PROTECT", "category": "PR.DS"}],
    "A.5.14": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.5.15": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.5.16": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.5.17": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.5.18": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.5.19": [{"function": "GOVERN", "category": "GV.SC"}],
    "A.5.20": [{"function": "GOVERN", "category": "GV.SC"}],
    "A.5.21": [{"function": "GOVERN", "category": "GV.SC"}],
    "A.5.22": [{"function": "GOVERN", "category": "GV.SC"}, {"function": "DETECT", "category": "DE.CM"}],
    "A.5.23": [{"function": "GOVERN", "category": "GV.SC"}],
    "A.5.24": [{"function": "RESPOND", "category": "RS.MA"}],
    "A.5.25": [{"function": "DETECT", "category": "DE.AE"}, {"function": "RESPOND", "category": "RS.MA"}],
    "A.5.26": [{"function": "RESPOND", "category": "RS.MA"}],
    "A.5.27": [{"function": "RESPOND", "category": "RS.IM"}, {"function": "IDENTIFY", "category": "ID.IM"}],
    "A.5.28": [{"function": "RESPOND", "category": "RS.CO"}],
    "A.5.29": [{"function": "RECOVER", "category": "RC.RP"}, {"function": "GOVERN", "category": "GV.OC"}],
    "A.5.30": [{"function": "RECOVER", "category": "RC.RP"}, {"function": "PROTECT", "category": "PR.IR"}],
    "A.5.31": [{"function": "GOVERN", "category": "GV.OC"}, {"function": "GOVERN", "category": "GV.OV"}],
    "A.5.32": [{"function": "GOVERN", "category": "GV.OC"}],
    "A.5.33": [{"function": "PROTECT", "category": "PR.DS"}, {"function": "GOVERN", "category": "GV.OV"}],
    "A.5.34": [{"function": "PROTECT", "category": "PR.DS"}, {"function": "GOVERN", "category": "GV.OV"}],
    "A.5.35": [{"function": "GOVERN", "category": "GV.OV"}],
    "A.5.36": [{"function": "GOVERN", "category": "GV.OV"}, {"function": "GOVERN", "category": "GV.PO"}],
    "A.5.37": [{"function": "GOVERN", "category": "GV.PO"}],
    "A.6.1": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.6.2": [{"function": "GOVERN", "category": "GV.RR"}],
    "A.6.3": [{"function": "PROTECT", "category": "PR.AW"}],
    "A.6.4": [{"function": "GOVERN", "category": "GV.RR"}, {"function": "PROTECT", "category": "PR.AW"}],
    "A.6.5": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.6.6": [{"function": "PROTECT", "category": "PR.DS"}, {"function": "GOVERN", "category": "GV.PO"}],
    "A.6.7": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "PROTECT", "category": "PR.AA"}],
    "A.6.8": [{"function": "DETECT", "category": "DE.AE"}, {"function": "RESPOND", "category": "RS.MA"}],
    "A.7.1": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.2": [{"function": "PROTECT", "category": "PR.AA"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.7.3": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.4": [{"function": "DETECT", "category": "DE.CM"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.7.5": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.6": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.7": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.7.8": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.9": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.10": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.7.11": [{"function": "PROTECT", "category": "PR.IR"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.7.12": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.13": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.7.14": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.8.1": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.2": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.8.3": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.8.4": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.8.5": [{"function": "PROTECT", "category": "PR.AA"}],
    "A.8.6": [{"function": "PROTECT", "category": "PR.IR"}],
    "A.8.7": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "DETECT", "category": "DE.CM"}],
    "A.8.8": [{"function": "IDENTIFY", "category": "ID.RA"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.8.9": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.10": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.8.11": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.8.12": [{"function": "PROTECT", "category": "PR.DS"}, {"function": "DETECT", "category": "DE.CM"}],
    "A.8.13": [{"function": "PROTECT", "category": "PR.IR"}, {"function": "RECOVER", "category": "RC.RP"}],
    "A.8.14": [{"function": "PROTECT", "category": "PR.IR"}, {"function": "RECOVER", "category": "RC.RP"}],
    "A.8.15": [{"function": "DETECT", "category": "DE.CM"}, {"function": "RESPOND", "category": "RS.CO"}],
    "A.8.16": [{"function": "DETECT", "category": "DE.CM"}],
    "A.8.17": [{"function": "DETECT", "category": "DE.CM"}],
    "A.8.18": [{"function": "PROTECT", "category": "PR.AA"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.8.19": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.20": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.21": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.22": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.23": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "DETECT", "category": "DE.CM"}],
    "A.8.24": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.8.25": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.26": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.27": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.28": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.29": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "IDENTIFY", "category": "ID.RA"}],
    "A.8.30": [{"function": "GOVERN", "category": "GV.SC"}, {"function": "PROTECT", "category": "PR.PS"}],
    "A.8.31": [{"function": "PROTECT", "category": "PR.PS"}],
    "A.8.32": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "GOVERN", "category": "GV.OV"}],
    "A.8.33": [{"function": "PROTECT", "category": "PR.DS"}],
    "A.8.34": [{"function": "PROTECT", "category": "PR.PS"}, {"function": "GOVERN", "category": "GV.OV"}],
}


def _implementation_score(status: str) -> float:
    scores = {
        "verified": 1.0,
        "implemented": 0.75,
        "in_progress": 0.4,
        "not_started": 0.1,
    }
    return scores.get(status, 0.0)


def get_nist_framework_status(
    controls: QuerySet | list[Control],
    db: Any = None,
) -> dict[str, Any]:
    control_map = {}
    for c in controls:
        control_map[c.control_number] = c

    functions: dict[str, dict[str, Any]] = {}
    for func_name, func_info in NIST_CSF_FUNCTIONS.items():
        categories_data: dict[str, dict[str, Any]] = {}
        for cat in NIST_CSF_CATEGORIES.get(func_name, []):
            cat_id = cat["id"]
            mapped_controls = [
                iso_id
                for iso_id, mappings in ISO_TO_NIST_MAPPING.items()
                if any(m["category"] == cat_id for m in mappings)
            ]

            cat_controls_detail: list[dict[str, Any]] = []
            statuses = []
            for iso_id in mapped_controls:
                db_ctrl = control_map.get(iso_id)
                impl_status = db_ctrl.implementation_status if db_ctrl else "not_started"
                statuses.append(impl_status)
                cat_controls_detail.append(
                    {
                        "control_id": iso_id,
                        "implementation_status": impl_status,
                    }
                )

            implemented = sum(1 for s in statuses if s in ("implemented", "verified"))
            total = len(statuses)
            coverage_rate = round((implemented / total * 100), 1) if total > 0 else 0.0
            avg_score = (
                round(sum(_implementation_score(s) for s in statuses) / total * 100, 1)
                if total > 0
                else 0.0
            )

            categories_data[cat_id] = {
                "id": cat_id,
                "name": cat["name"],
                "total_controls": total,
                "implemented_controls": implemented,
                "coverage_rate": coverage_rate,
                "implementation_score": avg_score,
                "mapped_controls": cat_controls_detail,
            }

        total = sum(cat["total_controls"] for cat in categories_data.values())
        implemented = sum(cat["implemented_controls"] for cat in categories_data.values())
        coverage_rate = round((implemented / total * 100), 1) if total > 0 else 0.0
        avg_score = (
            round(
                sum(cat["implementation_score"] * cat["total_controls"] for cat in categories_data.values())
                / total,
                1,
            )
            if total > 0
            else 0.0
        )

        functions[func_name] = {
            "id": func_info["id"],
            "name": func_name,
            "title": func_info["title"],
            "description": func_info["description"],
            "total_controls": total,
            "implemented_controls": implemented,
            "coverage_rate": coverage_rate,
            "implementation_score": avg_score,
            "categories": categories_data,
        }

    return {
        "framework": "NIST CSF 2.0",
        "total_functions": 6,
        "total_categories": sum(len(v) for v in NIST_CSF_CATEGORIES.values()),
        "functions": functions,
    }


def get_nist_compliance_heatmap(
    controls: QuerySet | list[Control],
) -> list[dict[str, Any]]:
    framework_status = get_nist_framework_status(controls)

    heatmap: list[dict[str, Any]] = []
    for func_name, func_data in framework_status["functions"].items():
        for cat_id, cat_data in func_data["categories"].items():
            heatmap.append(
                {
                    "function": func_name,
                    "function_id": func_data["id"],
                    "function_title": func_data["title"],
                    "category_id": cat_id,
                    "category_name": cat_data["name"],
                    "total_controls": cat_data["total_controls"],
                    "implemented_controls": cat_data["implemented_controls"],
                    "coverage_rate": cat_data["coverage_rate"],
                    "implementation_score": cat_data["implementation_score"],
                    "risk_level": _risk_level(cat_data["implementation_score"]),
                }
            )

    return heatmap


def _risk_level(score: float) -> str:
    if score >= 75:
        return "low"
    if score >= 50:
        return "medium"
    if score >= 25:
        return "high"
    return "critical"
