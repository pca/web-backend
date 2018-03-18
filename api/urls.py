from django.urls import path

from api import views

urlpatterns = [
    path('competitions/', views.ListCompetitions.as_view()),
    path('rankings/national', views.ListNationalRankings.as_view()),
    path('rankings/regional', views.ListRegionalRankings.as_view()),
    path('rankings/cityprovincial', views.ListCityProvincialRankings.as_view()),
]
