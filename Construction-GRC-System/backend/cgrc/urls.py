from django.urls import include, path

urlpatterns = [
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/risks/", include("apps.risks.urls")),
    path("api/v1/compliance/", include("apps.compliance.urls")),
    path("api/v1/audits/", include("apps.audits.urls")),
    path("api/v1/integration/", include("apps.integration.urls")),
]
