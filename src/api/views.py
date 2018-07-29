"""
We use APIView in all endpoints instead of the magical generic views in
favor of code readability/visualization of what's happening in each
endpoint. It will also help people with less/zero knowledge of the framework
contribute easily without knowing what those generic views are for.
"""
import phgeograpy
import requests
from django.conf import settings
from django.contrib.auth import login
from django.http import Http404
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from pca.models import WCAProfile, PCAProfile, User
from wca.client import WCAClient


class WCAMixin:
    """
    WCA Mixin object delivers the wca_client to every views
    """
    def __init__(self):
        self.wca_client = WCAClient()


class WCAAuthenticate(WCAMixin, APIView):
    """
    Authenticates the `code` returned by the WCA login page.

    Args:
        code: The `code` retured by the WCA login page.
    """

    def post(self, request, *args, **kwargs):
        data = request.POST
        code = data.get('code')

        # Get access token
        host = self.request.get_host()
        access_token_uri = self.wca_client.access_token_uri(host, code)
        response = requests.post(access_token_uri)
        access_token = response.json().get('access_token')

        # Get WCA Profile
        response = requests.get(settings.WCA_API_URI + 'me', headers={
            'Authorization': 'Bearer {}'.format(access_token),
        })
        profile = response.json()
        profile_data = profile.get('me')

        if not profile_data:
            return Response({
                'message': 'Unauthorized.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        wca_profile = WCAProfile.objects.filter(wca_pk=profile_data['id']).first()

        if not wca_profile:
            user = User.objects.create_user(
                username=str(profile_data['id']),  # Default username is wca_pk
                password=get_random_string(64),  # Generate random password
            )
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
            PCAProfile.objects.create(user=user)

        login(self.request, wca_profile.user)
        return Response({
            'message': 'Authenticated.',
        })


class ListRegions(WCAMixin, APIView):
    """
    View to list all supported (with rankings) regions in the Philippines.
    """

    def get(self, request, *args, **kwargs):
        regions = phgeograpy.regions()
        results = []

        for region in regions:
            results.append({
                'id': region.slug,
                'name': region.name,
                'description': region.description,
            })

        data = {
            'results': results,
        }
        return Response(data)


class ListCitiesProvinces(WCAMixin, APIView):
    """
    View to list all supported (with rankings) cities in Metro Manila
    and provinces (excluding Metro Manila) all over the Philippines.
    """

    def get(self, request, *args, **kwargs):
        results = []

        # Get cities in Metro Manila
        region = phgeograpy.regions('ncr')
        province = region.provinces()[0]
        cities = province.municipalities()

        for city in cities:
            results.append({
                'id': city.slug,
                'name': city.name,
            })

        # Get provinces
        provinces = phgeograpy.provinces()

        for province in provinces:
            # Exclude Metro Manila
            if province.slug != 'metro_manila':
                results.append({
                    'id': province.slug,
                    'name': province.name,
                })

        data = {
            'results': results,
        }
        return Response(data)


class ListCompetitions(WCAMixin, APIView):
    """
    View to list all upcoming competitions in the Philippines.
    """

    def get(self, request, *args, **kwargs):
        data = {
            'results': self.wca_client.competitions(),
        }
        return Response(data)


class ListNationalRankings(WCAMixin, APIView):
    """
    View to list the top 10 rankings of event(s) in national level.

    Args:
        events: A comma-separated list of events. If no `events`
            were requested, all rankings for all events will
            be returned.
        type: Ranking type can be `all`, `single`, or `average`.
    """

    def get(self, request, *args, **kwargs):
        events = request.query_params.get('events')
        rank_type = request.query_params.get('type')
        rankings = {}

        if events:
            events = events.split(',')

            for event in events:
                if rank_type == 'single' or rank_type == 'all':
                    best_rankings = self.wca_client.rankings(event, 'best', 'national')
                    rankings['single_{}'.format(event)] = best_rankings

                if rank_type == 'average' or rank_type == 'all':
                    average_rankings = self.wca_client.rankings(event, 'average', 'nationa')
                    rankings['average_{}'.format(event)] = average_rankings
        else:
            rankings = self.wca_client.all_rankings('national')

        data = {
            'results': rankings,
        }
        return Response(data)


class ListRegionalRankings(WCAMixin, APIView):
    """
    View to list the top 10 rankings of event(s) in regional level.

    Args:
        q: Filters the rankings by this given region.
            `q` should be the region id.
    """

    def get(self, request, *args, **kwargs):
        region = request.query_params.get('q')

        if not region:
            raise Http404

        try:
            region = phgeograpy.regions(region)
        except Exception:
            raise Http404

        rankings = self.wca_client.all_rankings('regional', query=region)

        data = {
            'results': rankings,
        }
        return Response(data)


class ListCityProvincialRankings(WCAMixin, APIView):
    """
    View to list the top 10 rankings of event(s) in city/provincial level.
    Cities are within Metro Manila and provinces excludes Metro Manila.

    Args:
        q: Filters the rankings by this given city/province.
            `q` should be the city/province id.
    """

    def get(self, request, *args, **kwargs):
        cityprovince = request.query_params.get('q')

        if not cityprovince:
            raise Http404

        # TODO: Validate city/province id

        rankings = self.wca_client.all_rankings('cityprovincial', query=cityprovince)

        data = {
            'results': rankings,
        }
        return Response(data)
