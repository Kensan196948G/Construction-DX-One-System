from django.urls import path

from .views import control_detail, control_list

urlpatterns = [
    path("", control_list),
    path("<uuid:pk>/", control_detail),
]
