from django.urls import path

from . import views

app_name = "devices"

urlpatterns = [
    path("catalog/", views.DeviceCatalogView.as_view(), name="catalog"),
    path("catalog/<slug:slug>/", views.DeviceDetailView.as_view(), name="detail"),
    path("submit/", views.DeviceSubmissionView.as_view(), name="submit"),
    path("submit/estimate/", views.DeviceEstimateView.as_view(), name="estimate"),
    path("submit/success/", views.DeviceSubmissionSuccessView.as_view(), name="submission_success"),
]
