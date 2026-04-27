from django.urls import path

from .views import (
    control_detail,
    control_list,
    framework_compliance_rates,
    nist_csf_heatmap,
    nist_csf_status,
    soa_download,
    soa_list,
)

urlpatterns = [
    path("", control_list),
    path("<uuid:pk>/", control_detail),
    path("soa/", soa_list),
    path("soa/download/", soa_download),
    path("nist-csf/", nist_csf_status),
    path("nist-csf/heatmap/", nist_csf_heatmap),
    path("frameworks/", framework_compliance_rates),
]
