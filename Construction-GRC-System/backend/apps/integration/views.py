"""Integration views for GRC: cross-system API endpoints."""
import json
from datetime import UTC, datetime

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.risks.models import Risk


def _verify_integration_key(request) -> bool:
    expected = getattr(settings, "INTEGRATION_API_KEY", "dev-integration-key-change-in-prod")
    return request.headers.get("X-Integration-Key") == expected


def _forbidden():
    return JsonResponse({"detail": "Invalid or missing integration API key"}, status=403)


@method_decorator(csrf_exempt, name="dispatch")
class RiskItemsView(View):
    """Provide open risk items to BCP for continuity planning."""

    def get(self, request):
        if not _verify_integration_key(request):
            return _forbidden()

        status_filter = request.GET.get("status", "open")
        min_score = float(request.GET.get("min_score", 0))
        risks = Risk.objects.filter(
            status__in=status_filter.split(","),
            risk_score__gte=min_score,
        ).values(
            "id", "title", "description", "category",
            "likelihood", "impact", "risk_score", "status", "owner",
            "created_at", "updated_at",
        )

        data = [
            {**r, "id": str(r["id"]),
             "created_at": r["created_at"].isoformat(),
             "updated_at": r["updated_at"].isoformat()}
            for r in risks
        ]
        return JsonResponse({"risk_items": data, "total": len(data)})


@method_decorator(csrf_exempt, name="dispatch")
class SecurityEventIngestView(View):
    """Receive security events from SIEM and create corresponding risks."""

    def post(self, request):
        if not _verify_integration_key(request):
            return _forbidden()

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)

        alerts = payload.get("alerts", [])
        created_count = 0
        for alert in alerts:
            severity = alert.get("severity", "low")
            if severity not in ("high", "critical"):
                continue
            impact = 5 if severity == "critical" else 4
            risk = Risk.objects.create(
                title=f"[SIEM] {alert.get('title', 'Security Alert')}",
                description=alert.get("description", ""),
                category="cyber_security",
                likelihood=3,
                impact=impact,
                owner="Security Team",
                status="open",
            )
            _ = risk
            created_count += 1

        return JsonResponse({"created_risks": created_count}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryPlanSyncView(View):
    """Receive recovery plan updates from BCP."""

    def post(self, request):
        if not _verify_integration_key(request):
            return _forbidden()

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON"}, status=400)

        risk_ids = payload.get("resolved_risk_ids", [])
        updated = Risk.objects.filter(id__in=risk_ids, status="open").update(
            status="mitigated"
        )
        return JsonResponse({"updated_risks": updated})


@method_decorator(csrf_exempt, name="dispatch")
class RiskSummaryView(View):
    """Aggregate risk summary for BCP and executive dashboard."""

    def get(self, request):
        if not _verify_integration_key(request):
            return _forbidden()

        all_risks = Risk.objects.all()
        by_status = {}
        by_category = {}
        for r in all_risks:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_category[r.category] = by_category.get(r.category, 0) + 1

        high_risks = [
            {"id": str(r.id), "title": r.title, "risk_score": r.risk_score, "status": r.status}
            for r in all_risks
            if r.risk_score >= 15
        ]

        return JsonResponse({
            "by_status": by_status,
            "by_category": by_category,
            "high_risk_items": high_risks,
            "total": all_risks.count(),
            "generated_at": datetime.now(UTC).isoformat(),
        })
