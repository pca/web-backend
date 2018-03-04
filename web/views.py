import requests
from datetime import datetime

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from wca.utils import get_all_rankings, enqueue_ranking_computation
from wca.utils import wca_authorize_uri, wca_access_token_uri, get_competitions
from web.constants import LOCATION_DIRECTORY, REGION_CHOICES, CITIES_PROVINCES
from web.constants import NCR, CITY_OF_MANILA
from web.forms import PCAProfileForm
from web.models import User, PCAProfile, WCAProfile


class AuthenticateMixin:
    """
    Ensures that users are authenticated.
    We redirect guests to the login page if they aren't logged in.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('web:index')
        return super(AuthenticateMixin, self).dispatch(request, *args, **kwargs)


class ContentMixin:
    """
    Sets WCA/PCA related data into the view's context.
    """
    page = ''

    def get_context_data(self, **kwargs):
        context = super(ContentMixin, self).get_context_data(**kwargs)
        context['wca_login_uri'] = wca_authorize_uri()
        context['page'] = self.page
        return context


class UserLogoutView(LogoutView):
    next_page = 'web:index'


class IndexView(ContentMixin, TemplateView):
    template_name = 'pages/index.html'
    page = 'index'


class ProfileView(AuthenticateMixin, ContentMixin, TemplateView):
    template_name = 'pages/profile.html'
    page = 'profile'

    def get(self, request, *args, **kwargs):
        request.session['profile_region'] = request.user.pcaprofile.region
        request.session['profile_city_province'] = request.user.pcaprofile.city_province
        return super(ProfileView, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = PCAProfileForm(request.POST, instance=request.user.pcaprofile)
        if form.is_valid():
            form.save()
            # Check for updated region/city/province data
            previous_region = request.session.get('profile_region')
            updated_region = form.cleaned_data.get('region')
            if previous_region != updated_region:
                # Recompute regional rankings
                enqueue_ranking_computation(area='regional', area_filter=previous_region)
                enqueue_ranking_computation(area='regional', area_filter=updated_region)
            previous_city_province = request.session.get('profile_city_province')
            updated_city_province = form.cleaned_data.get('city_province')
            if previous_city_province != updated_city_province:
                # Recompute city/provincial rankings
                enqueue_ranking_computation(area='cityprovincial', area_filter=previous_city_province)
                enqueue_ranking_computation(area='cityprovincial', area_filter=updated_city_province)
        return redirect('web:profile')

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['form'] = PCAProfileForm(instance=self.request.user.pcaprofile)
        context['location_directory'] = LOCATION_DIRECTORY
        return context


class CompetitionsView(ContentMixin, TemplateView):
    template_name = 'pages/competitions.html'
    page = 'competitions'

    def get_context_data(self, **kwargs):
        context = super(CompetitionsView, self).get_context_data(**kwargs)
        competitions = get_competitions()
        upcoming_competitions = []
        # Filter upcoming competitions
        for competition in competitions:
            start_date = datetime.strptime(competition['start_date'], "%Y-%m-%d")
            if start_date > datetime.today():
                upcoming_competitions.insert(0, competition)
        context['upcoming_competitions'] = upcoming_competitions
        return context


class NationalRankingsView(ContentMixin, TemplateView):
    template_name = 'pages/rankings/national.html'
    page = 'rankings_national'

    def get_context_data(self, **kwargs):
        context = super(NationalRankingsView, self).get_context_data(**kwargs)
        context['all_rankings'] = get_all_rankings(area='national')
        return context


class RegionalRankingsView(ContentMixin, TemplateView):
    template_name = 'pages/rankings/regional.html'
    page = 'rankings_regional'

    def get_context_data(self, **kwargs):
        region_key = self.request.GET.get('region', NCR)
        region = LOCATION_DIRECTORY.get(region_key)
        # Validate region
        if not region:
            raise Http404
        context = super(RegionalRankingsView, self).get_context_data(**kwargs)
        context['region'] = {
            'key': region_key,
            'label': region['label'],
        }
        context['region_choices'] = REGION_CHOICES
        context['all_rankings'] = get_all_rankings(area='regional', area_filter=region)
        return context


class CityProvincialRankingsView(ContentMixin, TemplateView):
    template_name = 'pages/rankings/city_provincial.html'
    page = 'rankings_cityprovincial'

    def get_context_data(self, **kwargs):
        cityprovince = self.request.GET.get('cityprovince', CITY_OF_MANILA)
        if cityprovince not in CITIES_PROVINCES:
            raise Http404
        context = super(CityProvincialRankingsView, self).get_context_data(**kwargs)
        context['cityprovince'] = cityprovince
        context['cityprovince_choices'] = CITIES_PROVINCES
        context['all_rankings'] = get_all_rankings(area='cityprovincial', area_filter=cityprovince)
        return context


class WCACallbackView(RedirectView):
    """
    Validates WCA user, creates a PCA user and a WCA profile
    if the user is new. Otherwise, we just do authentication.
    """

    def get_redirect_url(self, *args, **kwargs):
        data = self.request.GET
        code = data.get('code')
        redirect_uri = 'web:index'
        print('WCA Callback: {}'.format(data))

        # Get access token
        access_token_uri = wca_access_token_uri(code)
        response = requests.post(access_token_uri)
        access_token = response.json().get('access_token')

        # Get WCA Profile
        response = requests.get(settings.WCA_API_URI + 'me', headers={
            'Authorization': 'Bearer {}'.format(access_token),
        })
        profile = response.json()
        profile_data = profile.get('me')
        if not profile_data:
            raise Http404
        print('WCA Profile: {}'.format(profile))

        # Check if WCAProfile is already saved, create if not.
        wca_profile = WCAProfile.objects.filter(wca_pk=profile_data['id']).first()
        if not wca_profile:
            # Create user
            user = User.objects.create_user(
                username=str(profile_data['id']),  # Default username is wca_pk
                password=get_random_string(64),  # Generate random password
            )
            # Create WCA profile
            wca_profile = WCAProfile.objects.create(
                user=user,
                wca_pk=profile_data['id'],
                wca_id=profile_data['wca_id'],
                name=profile_data['name'],
                gender=profile_data['gender'],
                country_iso2=profile_data['country_iso2'],
                delegate_status=profile_data['delegate_status'],
                avatar_url=profile_data['avatar']['url'],
                avatar_thumb_url=profile_data['avatar']['thumb_url'],
                is_default_avatar=profile_data['avatar']['is_default'],
                wca_created_at=profile_data['created_at'],
                wca_updated_at=profile_data['updated_at'],
            )
            # Create PCA profile
            PCAProfile.objects.create(
                user=user,
            )
            # Redirect new users to their profile page
            redirect_uri = 'web:profile'

        # Login the user
        login(self.request, wca_profile.user)

        return reverse(redirect_uri)
