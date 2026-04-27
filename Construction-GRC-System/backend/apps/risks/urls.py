from django.urls import path

from .views import risk_detail, risk_list, risk_report_excel

urlpatterns = [
    path("", risk_list),
    path("<uuid:pk>/", risk_detail),
    path("report/excel/", risk_report_excel),
]
