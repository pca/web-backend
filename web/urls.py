from django.urls import path

from web.views import (
    CompetitionsView, IndexView, ProfileView, NationalRankingsView,
    RegionalRankingsView, CityProvincialRankingsView,
    WCACallbackView, UserLogoutView,
)

app_name = 'web'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('competitions/', CompetitionsView.as_view(), name='competitions'),
    path('rankings/national/', NationalRankingsView.as_view(), name='national_rankings'),
    path('rankings/regional/', RegionalRankingsView.as_view(), name='regional_rankings'),
    path('rankings/cityprovincial/', CityProvincialRankingsView.as_view(), name='cityprovincial_rankings'),
    path('wca/callback/', WCACallbackView.as_view(), name='wca_callback'),
]
