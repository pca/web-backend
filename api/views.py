"""
We use APIView in all endpoints instead of the magical
generic views in favor of code readability/visualization
of what's happening in each endpoint. It will also
help people with less/zero knowledge of the framework
contribute easily without knowing what those generic
views are for.
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from wca.utils import get_all_rankings, get_rankings, get_competitions


class ListCompetitions(APIView):
    """
    View to list all upcoming competitions in the Philippines.
    """

    def get(self, request, *args, **kwargs):
        competitions = get_competitions()
        data = {
            'results': competitions,
        }
        return Response(data)


class ListNationalRankings(APIView):
    """
    View to list the top 10 rankings of event(s) in national level.

    Args:
        events: A comma-separated list of events. If no `events`
            were requested, all rankings for all events will
            be returned.
    """

    def get(self, request, *args, **kwargs):
        events = request.query_params.get('events')
        rankings = {}

        if events:
            for event in events.split(','):
                best_rankings = get_rankings(event_type=event, rank_type='best', area='', area_filter='')
                average_rankings = get_rankings(event_type=event, rank_type='average', area='', area_filter='')
                rankings['single_{}'.format(event)] = best_rankings
                rankings['average_{}'.format(event)] = average_rankings
        else:
            rankings = get_all_rankings()

        data = {
            'results': rankings,
        }
        return Response(data)


class ListRegionalRankings(APIView):
    """
    View to list the top 10 rankings of event(s) in regional level.
    """

    def get(self, request, *args, **kwargs):
        return Response({})


class ListCityProvincialRankings(APIView):
    """
    View to list the top 10 rankings of event(s) in city/provincial level.
    """

    def get(self, request, *args, **kwargs):
        return Response({})
