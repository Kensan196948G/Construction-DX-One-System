from django.urls import path

from .views import audit_detail, audit_list, finding_detail, finding_list

urlpatterns = [
    path("", audit_list),
    path("<uuid:pk>/", audit_detail),
    path("<uuid:audit_pk>/findings/", finding_list),
    path("<uuid:audit_pk>/findings/<uuid:pk>/", finding_detail),
]
