from django.urls import path

from .views import RecoveryPlanSyncView, RiskItemsView, RiskSummaryView, SecurityEventIngestView

urlpatterns = [
    path("risk-items/", RiskItemsView.as_view()),
    path("risk-summary/", RiskSummaryView.as_view()),
    path("security-events/", SecurityEventIngestView.as_view()),
    path("recovery-plans/sync/", RecoveryPlanSyncView.as_view()),
]
