from django.urls import path

from api import views

app_name = 'api'
urlpatterns = [
    # Auth
    path('wca/authenticate/', views.WCAAuthenticate.as_view(), name='wca_authenticate'),

    # Locations
    path('regions/', views.ListRegions.as_view(), name='regions'),
    path('citiesprovinces/', views.ListCitiesProvinces.as_view(), name='citiesprovinces'),

    # Competitions
    path('competitions/', views.ListCompetitions.as_view(), name='competitions'),

    # Rankings
    path('rankings/national', views.ListNationalRankings.as_view(), name='national_rankings'),
    path('rankings/regional', views.ListRegionalRankings.as_view(), name='regional_rankings'),
    path('rankings/cityprovincial', views.ListCityProvincialRankings.as_view(), name='cityprovincial_rankings'),
]
