from django.urls import path

from web import views

app_name = 'web'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('competitions/', views.CompetitionsView.as_view(), name='competitions'),
    path('rankings/national/', views.NationalRankingsView.as_view(), name='national_rankings'),
    path('rankings/regional/', views.RegionalRankingsView.as_view(), name='regional_rankings'),
    path('rankings/cityprovincial/', views.CityProvincialRankingsView.as_view(), name='cityprovincial_rankings'),
    path('wca/callback/', views.WCACallbackView.as_view(), name='wca_callback'),
]
