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
from pca.mixins import ClientMixin


class WCAAuthenticate(ClientMixin, APIView):
    """
    Authenticates the `code` returned by the WCA login page.

    Args:
        code: The `code` retured by the WCA login page.
    """

    def post(self, request, *args, **kwargs):
        data = request.POST
        code = data.get('code')

        host = self.request.get_host()
        profile_data = self.pca_client.get_wca_profile(host, code)

        if not profile_data:
            return Response({
                'message': 'Unauthorized.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        wca_profile = WCAProfile.objects.filter(wca_pk=profile_data['id']).first()

        if not wca_profile:
            wca_profile = self.pca_client.create_user(profile_data)

        login(self.request, wca_profile.user)
        return Response({
            'message': 'Authenticated.',
        })


class ListRegions(ClientMixin, APIView):
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


class ListCitiesProvinces(ClientMixin, APIView):
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


class ListCompetitions(ClientMixin, APIView):
    """
    View to list all upcoming competitions in the Philippines.
    """

    def get(self, request, *args, **kwargs):
        data = {
            'results': self.wca_client.competitions(),
        }
        return Response(data)


class ListNationalRankings(ClientMixin, APIView):
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
                    average_rankings = self.wca_client.rankings(event, 'average', 'national')
                    rankings['average_{}'.format(event)] = average_rankings
        else:
            rankings = self.wca_client.all_rankings('national')

        data = {
            'results': rankings,
        }
        return Response(data)


class ListRegionalRankings(ClientMixin, APIView):
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


class ListCityProvincialRankings(ClientMixin, APIView):
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
