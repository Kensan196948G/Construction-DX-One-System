from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class LoginView(TokenObtainPairView):
    """Return access_token/refresh_token (frontend-compatible naming)."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            return Response({
                "access_token": data.get("access"),
                "refresh_token": data.get("refresh"),
            })
        return response


class RefreshView(TokenRefreshView):
    """Return access_token (frontend-compatible naming)."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response({"access_token": response.data.get("access")})
        return response
