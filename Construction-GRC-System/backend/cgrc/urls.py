from django.urls import include, path
from apps.core.auth_views import LoginView, RefreshView

urlpatterns = [
    path("api/v1/auth/login/", LoginView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/risks/", include("apps.risks.urls")),
    path("api/v1/compliance/", include("apps.compliance.urls")),
    path("api/v1/audits/", include("apps.audits.urls")),
    path("api/v1/integration/", include("apps.integration.urls")),
]
