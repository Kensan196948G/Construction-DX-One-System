from django.urls import path

from .views import risk_detail, risk_list

urlpatterns = [
    path("", risk_list),
    path("<uuid:pk>/", risk_detail),
]
