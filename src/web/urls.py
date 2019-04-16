from django.urls import path

from web import views

app_name = 'web'
urlpatterns = [
    # Homepage
    path('', views.IndexView.as_view(), name='index'),

    # About pages
    path('about/summary/', views.SummaryView.as_view(), name='summary'),
    path('about/pca/', views.PCAView.as_view(), name='pca'),
    path('about/wca/', views.WCAView.as_view(), name='wca'),
    path('about/pca-organization/', views.PCAOrganizationView.as_view(), name='pca_organization'),
    path('about/history/', views.HistoryView.as_view(), name='history'),
    path('about/bylaws/', views.BylawsView.as_view(), name='bylaws'),
    path('about/rules-and-regulations/', views.RulesAndRegView.as_view(), name='rules_and_reg'),

    # Learn pages
    path('learn/beginners-guide/', views.BeginnersGuideView.as_view(), name='beginners_guide'),
    path('learn/links/', views.LinksView.as_view(), name='links'),
    path('learn/articles/', views.ArticlesView.as_view(), name='articles'),
    path('learn/faqs/', views.FAQsView.as_view(), name='faqs'),

    # Compete pages
    path('compete/about-wca-competitions/', views.AboutWCACompetitionsView.as_view(), name='about_wca_competitions'),
    path('compete/rankings/national/', views.NationalRankingsView.as_view(), name='national_rankings'),
    path('compete/rankings/regional/', views.RegionalRankingsView.as_view(), name='regional_rankings'),
    path('compete/rankings/cityprovincial/', views.CityProvincialRankingsView.as_view(), name='cityprovincial_rankings'),
    path('compete/competitions/', views.CompetitionsView.as_view(), name='competitions'),
    path('compete/wca-rules-and-regulations/', views.WCARulesAndRegView.as_view(), name='wca_rules_and_reg'),
    path('compete/how-to-organize-a-competition/', views.OrganizeACompetitionView.as_view(), name='organize_a_competition'),

    # Meet pages
    path('meet/cubemeets/', views.CubemeetsView.as_view(), name='cubemeets'),
    path('meet/organize-a-cubemeets/', views.OrganizeACubemeetView.as_view(), name='organize_a_cubemeet'),
    path('meet/events/', views.EventsView.as_view(), name='events'),
    path('meet/marketplace/', views.MarketplaceView.as_view(), name='marketplace'),
    path('meet/sponsoring-stores/', views.SponsoringStoresView.as_view(), name='sponsoring_stores'),

    # User profiles
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('wca/callback/', views.WCACallbackView.as_view(), name='wca_callback'),
]
