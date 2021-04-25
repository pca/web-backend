from django.urls import path
from dj_rest_auth.views import LogoutView

from . import views

app_name = "api"
urlpatterns = [
    path("auth/login/wca/", views.WCALoginView.as_view(), name="wca-login"),
    path("auth/logout/", LogoutView.as_view(), name="wca-logout"),
    path("user/", views.UserRetrieveAPIView.as_view(), name="user-retrieve"),
    path(
        "user/region-update-requests/",
        views.RegionUpdateRequestListCreateAPIView.as_view(),
        name="region-update-request-list",
    ),
    path("regions/", views.RegionListAPIView.as_view(), name="region-list"),
    path("events/", views.EventListAPIView.as_view(), name="event-list"),
    path("zones/", views.ZoneListAPIView.as_view(), name="zone-list"),
    path(
        "rankings/national-single/<str:event_id>/",
        views.NationalRankingSingleAPIView.as_view(),
        name="national-single-ranking",
    ),
    path(
        "rankings/national-average/<str:event_id>/",
        views.NationalRankingAverageAPIView.as_view(),
        name="national-average-ranking",
    ),
    path(
        "rankings/regional-single/<str:region_id>/<str:event_id>/",
        views.RegionalRankingSingleAPIView.as_view(),
        name="regional-single-ranking",
    ),
    path(
        "rankings/regional-average/<str:region_id>/<str:event_id>/",
        views.RegionalRankingAverageAPIView.as_view(),
        name="regional-average-ranking",
    ),
    path(
        "rankings/zonal-single/<str:zone_id>/<str:event_id>",
        views.ZonalRankingSingleAPIView.as_view(),
        name="zonal-single-ranking",
    ),
    path(
        "rankings/zonal-average/<str:zone_id>/<str:event_id>",
        views.ZonalRankingAverageAPIView.as_view(),
        name="zonal-average-ranking",
    ),
    path(
        "persons/<str:wca_id>/",
        views.PersonRetrieveAPIView.as_view(),
        name="person-retrieve",
    ),
    path("news/", views.NewsListAPIView.as_view(), name="news-list"),
]
