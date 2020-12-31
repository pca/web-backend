from django.urls import path
from rest_auth.views import LogoutView

from . import views

app_name = "api"
urlpatterns = [
    path("auth/login/wca/", views.WCALoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("user/", views.UserRetrieveAPIView.as_view()),
    path("user/region/", views.UserRegionUpdateAPIView.as_view()),
    path(
        "user/region-update-requests/",
        views.RegionUpdateRequestListCreateAPIView.as_view(),
    ),
    path("regions/", views.RegionListAPIView.as_view()),
    path("events/", views.EventListAPIView.as_view()),
    path(
        "rankings/national-single/<str:event_id>/",
        views.NationalRankingSingleAPIView.as_view(),
    ),
    path(
        "rankings/national-average/<str:event_id>/",
        views.NationalRankingAverageAPIView.as_view(),
    ),
    path(
        "rankings/regional-single/<str:region_id>/<str:event_id>/",
        views.RegionalRankingSingleAPIView.as_view(),
    ),
    path(
        "rankings/regional-average/<str:region_id>/<str:event_id>/",
        views.RegionalRankingAverageAPIView.as_view(),
    ),
]
