from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import exceptions
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wca_allauth.views import WorldCubeAssociationOAuth2Adapter

from wca.models import Event, Person, Result
from wca.serializers import EventSerializer, PersonSerializer, ResultSerializer

from . import app_settings
from .filters import LimitFilter
from .models import RegionUpdateRequest
from .serializers import (
    NewsSerializer,
    RegionSerializer,
    RegionUpdateRequestSerializer,
    UserDetailSerializer,
    WCALoginSerializer,
    ZoneSerializer,
)
from .utils import get_facebook_posts

User = get_user_model()

PH_COUNTRY_ID = "Philippines"
WCA_PROVIDER = "worldcubeassociation"


class WCALoginView(SocialLoginView):
    """ Login with WCA oauth authorization code """

    serializer_class = WCALoginSerializer
    adapter_class = WorldCubeAssociationOAuth2Adapter
    client_class = OAuth2Client
    callback_url = app_settings.WCA_DEFAULT_CALLBACK_URL

    def post(self, request, *agrs, **kwargs):
        self.serializer = self.get_serializer(data=self.request.data)
        callback_url = self.serializer.initial_data.get("callback_url")
        if callback_url:
            self.callback_url = callback_url
        self.serializer.is_valid(raise_exception=True)
        self.login()
        return self.get_response()


class UserRetrieveAPIView(RetrieveAPIView):
    """ Retrieve authenticated user """

    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.none()

    def get_object(self):
        return self.request.user


class RegionListAPIView(APIView):
    """ List regions in the Philippines """

    serializer_class = RegionSerializer
    action = "list"

    def get(self, request, *args, **kwargs):
        regions = [{"id": r_id, "name": name} for r_id, name in User.REGION_CHOICES]
        return Response(regions)


class ZoneListAPIView(APIView):
    """ List region zones in the Philippines """

    serializer_class = ZoneSerializer
    action = "list"

    def get(self, request, *args, **kwargs):
        zones = [{"id": zone_id, "name": name} for zone_id, name in User.ZONE_CHOICES]
        return Response(zones)


class EventListAPIView(ListAPIView):
    """ List of official WCA events """

    serializer_class = EventSerializer
    queryset = Event.objects.order_by("rank")


class RankingBaseAPIView(ListAPIView):
    serializer_class = ResultSerializer
    filter_backends = [LimitFilter]
    rank_type = None

    def add_region(self, queryset):
        region = User.objects.filter(wca_id=OuterRef("person_id")).values("region")[:1]
        return queryset.annotate(region=Subquery(region))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["rank_type"] = self.rank_type
        return context

    def get_event(self):
        event_id = self.kwargs.get("event_id")
        event = Event.objects.filter(pk=event_id).first()
        if not event:
            raise exceptions.NotFound("Event not found.")
        return event

    def get_ranked_results(self, event, value_field, wca_ids=None):
        filters = {
            "country_id": PH_COUNTRY_ID,
            "event": event,
            "{}__gt".format(value_field): 0,
        }
        if wca_ids is not None:
            filters["person_id__in"] = wca_ids
        best_for_person = (
            Result.objects.filter(person_id=OuterRef("person_id"), **filters)
            .order_by(value_field, "id")
            .values("id")[:1]
        )
        results = (
            Result.objects.filter(**filters)
            .annotate(best_result_id=Subquery(best_for_person))
            .filter(id=F("best_result_id"))
            .select_related("event", "person", "competition")
            .order_by(value_field, "person_id")
        )
        return self.add_region(results)


class NationalRankingSingleAPIView(RankingBaseAPIView):
    """ Official single national rankings """

    rank_type = "best"

    def get_queryset(self):
        event = self.get_event()
        return self.get_ranked_results(event, "best")


class NationalRankingAverageAPIView(RankingBaseAPIView):
    """ Official average national rankings """

    rank_type = "average"

    def get_queryset(self):
        event = self.get_event()
        return self.get_ranked_results(event, "average")


class ZonalRankingBaseAPIView(RankingBaseAPIView):
    def get_zone(self):
        valid_zones = [zone_id for zone_id, _ in User.ZONE_CHOICES]
        zone = self.kwargs.get("zone_id")
        if zone not in valid_zones:
            raise exceptions.ParseError(
                f"Invalid zone. Valid zones are: {', '.join(valid_zones)}"
            )
        return zone

    def get_wca_ids(self):
        zone = self.get_zone()
        zone_regions = User.ZONE_REGIONS.get(zone)
        wca_ids = User.objects.filter(
            region__in=zone_regions,
            socialaccount__provider=WCA_PROVIDER,
            wca_id__isnull=False,
        ).values_list("wca_id")
        return wca_ids


class ZonalRankingSingleAPIView(ZonalRankingBaseAPIView):
    """ Unofficial single zonal rankings """

    rank_type = "best"

    def get_queryset(self):
        event = self.get_event()
        wca_ids = self.get_wca_ids()
        return self.get_ranked_results(event, "best", wca_ids)


class ZonalRankingAverageAPIView(ZonalRankingBaseAPIView):
    """ Unofficial average zonal rankings """

    rank_type = "average"

    def get_queryset(self):
        event = self.get_event()
        wca_ids = self.get_wca_ids()
        return self.get_ranked_results(event, "average", wca_ids)


class RegionalRankingSingleAPIView(RankingBaseAPIView):
    """ Unofficial single regional rankings """

    rank_type = "best"

    def get_queryset(self):
        region = self.kwargs.get("region_id")
        event = self.get_event()
        wca_ids = User.objects.filter(
            region=region, socialaccount__provider=WCA_PROVIDER, wca_id__isnull=False
        ).values_list("wca_id")
        return self.get_ranked_results(event, "best", wca_ids)


class RegionalRankingAverageAPIView(RankingBaseAPIView):
    """ Unofficial average regional rankings """

    rank_type = "average"

    def get_queryset(self):
        region = self.kwargs.get("region_id")
        event = self.get_event()
        wca_ids = User.objects.filter(
            region=region, socialaccount__provider=WCA_PROVIDER, wca_id__isnull=False
        ).values_list("wca_id")
        return self.get_ranked_results(event, "average", wca_ids)


class RegionUpdateRequestListCreateAPIView(ListCreateAPIView):
    serializer_class = RegionUpdateRequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """ List region-update-requests of the user """
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Create a region-update-request.

        A region-update-request can only be created once per year.
        """
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return RegionUpdateRequest.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def create(self, request, *args, **kwargs):
        last_request = request.user.region_update_requests.order_by(
            "-created_at"
        ).first()

        if last_request and last_request.created_at.year == timezone.now().year:
            self.permission_denied(request, message="You can only request once a year.")

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PersonRetrieveAPIView(RetrieveAPIView):
    """ Retrieve WCA profile and statistics """

    serializer_class = PersonSerializer

    def get_object(self):
        wca_id = self.kwargs.get("wca_id")
        return Person.objects.get(id=wca_id)


class NewsListAPIView(APIView):
    """ News Feed from Facebook Page """

    serializer_class = NewsSerializer
    action = "list"

    @method_decorator(cache_page(60 * 10))
    def get(self, request, *args, **kwargs):
        posts = get_facebook_posts()
        serializer = NewsSerializer(data=posts, many=True)
        serializer.is_valid()
        return Response(serializer.data)
