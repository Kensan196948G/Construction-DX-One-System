from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from .models import Control

ISO27001_DOMAINS: dict[str, list[dict[str, str]]] = {
    "Organizational Controls": [
        {"control_id": "A.5.1", "title": "Policies for information security"},
        {"control_id": "A.5.2", "title": "Information security roles and responsibilities"},
        {"control_id": "A.5.3", "title": "Segregation of duties"},
        {"control_id": "A.5.4", "title": "Management responsibilities"},
        {"control_id": "A.5.5", "title": "Contact with authorities"},
        {"control_id": "A.5.6", "title": "Contact with special interest groups"},
        {"control_id": "A.5.7", "title": "Threat intelligence"},
        {"control_id": "A.5.8", "title": "Information security in project management"},
        {"control_id": "A.5.9", "title": "Inventory of information and other associated assets"},
        {"control_id": "A.5.10", "title": "Acceptable use of information and other associated assets"},
        {"control_id": "A.5.11", "title": "Return of assets"},
        {"control_id": "A.5.12", "title": "Classification of information"},
        {"control_id": "A.5.13", "title": "Labelling of information"},
        {"control_id": "A.5.14", "title": "Information transfer"},
        {"control_id": "A.5.15", "title": "Access control"},
        {"control_id": "A.5.16", "title": "Identity management"},
        {"control_id": "A.5.17", "title": "Authentication information"},
        {"control_id": "A.5.18", "title": "Access rights"},
        {"control_id": "A.5.19", "title": "Information security in supplier relationships"},
        {"control_id": "A.5.20", "title": "Addressing information security within supplier agreements"},
        {"control_id": "A.5.21", "title": "Managing information security in the ICT supply chain"},
        {"control_id": "A.5.22", "title": "Monitoring, review and change management of supplier services"},
        {"control_id": "A.5.23", "title": "Information security for use of cloud services"},
        {"control_id": "A.5.24", "title": "Information security incident management planning and preparation"},
        {"control_id": "A.5.25", "title": "Assessment and decision on information security events"},
        {"control_id": "A.5.26", "title": "Response to information security incidents"},
        {"control_id": "A.5.27", "title": "Learning from information security incidents"},
        {"control_id": "A.5.28", "title": "Collection of evidence"},
        {"control_id": "A.5.29", "title": "Information security during disruption"},
        {"control_id": "A.5.30", "title": "ICT readiness for business continuity"},
        {"control_id": "A.5.31", "title": "Legal, statutory, regulatory and contractual requirements"},
        {"control_id": "A.5.32", "title": "Intellectual property rights"},
        {"control_id": "A.5.33", "title": "Protection of records"},
        {"control_id": "A.5.34", "title": "Privacy and protection of PII"},
        {"control_id": "A.5.35", "title": "Independent review of information security"},
        {"control_id": "A.5.36", "title": "Compliance with policies and standards"},
        {"control_id": "A.5.37", "title": "Documented operating procedures"},
    ],
    "People Controls": [
        {"control_id": "A.6.1", "title": "Screening"},
        {"control_id": "A.6.2", "title": "Terms and conditions of employment"},
        {"control_id": "A.6.3", "title": "Information security awareness, education and training"},
        {"control_id": "A.6.4", "title": "Disciplinary process"},
        {"control_id": "A.6.5", "title": "Responsibilities after termination or change of employment"},
        {"control_id": "A.6.6", "title": "Confidentiality or non-disclosure agreements"},
        {"control_id": "A.6.7", "title": "Remote working"},
        {"control_id": "A.6.8", "title": "Information security event reporting"},
    ],
    "Physical Controls": [
        {"control_id": "A.7.1", "title": "Physical security perimeters"},
        {"control_id": "A.7.2", "title": "Physical entry controls"},
        {"control_id": "A.7.3", "title": "Securing offices, rooms and facilities"},
        {"control_id": "A.7.4", "title": "Physical security monitoring"},
        {"control_id": "A.7.5", "title": "Protecting against physical and environmental threats"},
        {"control_id": "A.7.6", "title": "Working in secure areas"},
        {"control_id": "A.7.7", "title": "Clear desk and clear screen"},
        {"control_id": "A.7.8", "title": "Equipment siting and protection"},
        {"control_id": "A.7.9", "title": "Security of assets off-premises"},
        {"control_id": "A.7.10", "title": "Storage media"},
        {"control_id": "A.7.11", "title": "Supporting utilities"},
        {"control_id": "A.7.12", "title": "Cabling security"},
        {"control_id": "A.7.13", "title": "Equipment maintenance"},
        {"control_id": "A.7.14", "title": "Secure disposal or re-use of equipment"},
    ],
    "Technological Controls": [
        {"control_id": "A.8.1", "title": "User endpoint devices"},
        {"control_id": "A.8.2", "title": "Privileged access rights"},
        {"control_id": "A.8.3", "title": "Information access restriction"},
        {"control_id": "A.8.4", "title": "Access to source code"},
        {"control_id": "A.8.5", "title": "Secure authentication"},
        {"control_id": "A.8.6", "title": "Capacity management"},
        {"control_id": "A.8.7", "title": "Protection against malware"},
        {"control_id": "A.8.8", "title": "Management of technical vulnerabilities"},
        {"control_id": "A.8.9", "title": "Configuration management"},
        {"control_id": "A.8.10", "title": "Information deletion"},
        {"control_id": "A.8.11", "title": "Data masking"},
        {"control_id": "A.8.12", "title": "Data leakage prevention"},
        {"control_id": "A.8.13", "title": "Information backup"},
        {"control_id": "A.8.14", "title": "Redundancy of information processing facilities"},
        {"control_id": "A.8.15", "title": "Logging"},
        {"control_id": "A.8.16", "title": "Monitoring activities"},
        {"control_id": "A.8.17", "title": "Clock synchronization"},
        {"control_id": "A.8.18", "title": "Use of privileged utility programs"},
        {"control_id": "A.8.19", "title": "Installation of software on operational systems"},
        {"control_id": "A.8.20", "title": "Networks security"},
        {"control_id": "A.8.21", "title": "Security of network services"},
        {"control_id": "A.8.22", "title": "Segregation of networks"},
        {"control_id": "A.8.23", "title": "Web filtering"},
        {"control_id": "A.8.24", "title": "Use of cryptography"},
        {"control_id": "A.8.25", "title": "Secure development life cycle"},
        {"control_id": "A.8.26", "title": "Application security requirements"},
        {"control_id": "A.8.27", "title": "Secure system architecture and engineering principles"},
        {"control_id": "A.8.28", "title": "Secure coding"},
        {"control_id": "A.8.29", "title": "Security testing in development and acceptance"},
        {"control_id": "A.8.30", "title": "Outsourced development"},
        {"control_id": "A.8.31", "title": "Separation of development, test and production environments"},
        {"control_id": "A.8.32", "title": "Change management"},
        {"control_id": "A.8.33", "title": "Test information"},
        {"control_id": "A.8.34", "title": "Protection of information systems during audit testing"},
    ],
}


def _get_control_map(controls: QuerySet | list[Control]) -> dict[str, Control]:
    return {c.control_number: c for c in controls}


def _get_control_status(
    control: Control | None,
) -> dict[str, str]:
    if control is None:
        return {
            "applicability_status": "not_defined",
            "implementation_status": "not_defined",
            "justification": "",
            "evidence": "",
        }
    return {
        "applicability_status": control.applicability,
        "implementation_status": control.implementation_status,
        "justification": control.justification,
        "evidence": control.description,
    }


def _calculate_compliance_rate(
    controls: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(controls)
    if total == 0:
        return {
            "total": 0,
            "implemented": 0,
            "in_progress": 0,
            "not_started": 0,
            "not_applicable": 0,
            "compliance_rate": 0.0,
        }

    implemented = sum(
        1
        for c in controls
        if c.get("implementation_status") in ("implemented", "verified")
        and c.get("applicability_status") == "applicable"
    )
    in_progress = sum(
        1
        for c in controls
        if c.get("implementation_status") == "in_progress"
        and c.get("applicability_status") == "applicable"
    )
    not_started = sum(
        1
        for c in controls
        if c.get("implementation_status") == "not_started"
        and c.get("applicability_status") == "applicable"
    )
    not_applicable = sum(
        1 for c in controls if c.get("applicability_status") == "not_applicable"
    )
    applicable = total - not_applicable
    compliance_rate = round((implemented / applicable * 100), 1) if applicable > 0 else 0.0

    return {
        "total": total,
        "applicable": applicable,
        "implemented": implemented,
        "in_progress": in_progress,
        "not_started": not_started,
        "not_applicable": not_applicable,
        "compliance_rate": compliance_rate,
    }


def generate_soa(
    controls: QuerySet | list[Control],
) -> dict[str, Any]:
    control_map = _get_control_map(controls)
    domains: dict[str, list[dict[str, Any]]] = {}
    overall: list[dict[str, Any]] = []

    for domain_name, domain_controls in ISO27001_DOMAINS.items():
        domain_entries: list[dict[str, Any]] = []
        for ref in domain_controls:
            db_control = control_map.get(ref["control_id"])
            entry: dict[str, Any] = {
                "control_id": ref["control_id"],
                "title": ref["title"],
                "domain": domain_name,
                **({} if db_control is None else {"id": str(db_control.id)}),
            }
            entry.update(_get_control_status(db_control))
            domain_entries.append(entry)
            overall.append(entry)
        domains[domain_name] = domain_entries

    domain_compliance: dict[str, dict[str, Any]] = {}
    for domain_name, entries in domains.items():
        domain_compliance[domain_name] = _calculate_compliance_rate(entries)

    overall_compliance = _calculate_compliance_rate(overall)

    return {
        "framework": "ISO 27001:2022",
        "standard": "ISO/IEC 27001:2022",
        "total_controls": 93,
        "generated_at": None,
        "domains": {
            name: {
                "controls": entries,
                "compliance": domain_compliance[name],
            }
            for name, entries in domains.items()
        },
        "overall_compliance": overall_compliance,
        "compliance_summary": {
            domain_name: domain_compliance[domain_name]["compliance_rate"]
            for domain_name in ISO27001_DOMAINS
        },
    }


def generate_soa_report(controls: QuerySet | list[Control]) -> dict[str, Any]:
    soa = generate_soa(controls)
    soa["generated_at"] = None

    report_data: dict[str, Any] = {
        "report_title": "Statement of Applicability",
        "report_type": "ISO 27001:2022 SoA",
        "standard": soa["standard"],
        "total_controls": soa["total_controls"],
        "overall_compliance_rate": soa["overall_compliance"]["compliance_rate"],
        "organization": {},
        "domains": [],
    }

    for domain_name, domain_data in soa["domains"].items():
        implemented_count = domain_data["compliance"]["implemented"]
        total_count = domain_data["compliance"]["total"]
        report_data["domains"].append(
            {
                "name": domain_name,
                "control_count": total_count,
                "implemented_count": implemented_count,
                "compliance_rate": domain_data["compliance"]["compliance_rate"],
                "controls": [
                    {
                        "control_id": c["control_id"],
                        "title": c["title"],
                        "applicability_status": c["applicability_status"],
                        "implementation_status": c["implementation_status"],
                        "justification": c["justification"],
                    }
                    for c in domain_data["controls"]
                ],
            }
        )

    report_data["compliance_summary"] = soa["compliance_summary"]
    return report_data
