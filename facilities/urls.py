from django.urls import path

from . import views

app_name = "facilities"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("locations/", views.FacilityListView.as_view(), name="facility_list"),
    path("locations/<slug:slug>/", views.FacilityDetailView.as_view(), name="facility_detail"),
]
