from django.urls import path

from api import views

urlpatterns = [
    # Locations
    path('regions/', views.ListRegions.as_view()),
    path('citiesprovinces/', views.ListCitiesProvinces.as_view()),

    # Competitions
    path('competitions/', views.ListCompetitions.as_view()),

    # Rankings
    path('rankings/national', views.ListNationalRankings.as_view()),
    path('rankings/regional', views.ListRegionalRankings.as_view()),
    path('rankings/cityprovincial', views.ListCityProvincialRankings.as_view()),
]
