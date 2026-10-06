from collections import defaultdict

from django.db.models import Case, IntegerField, Value, When
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema

from api.models import GrowthAnnualRecord, RegionalStrengthRecord, StatisticsSnapshot
from api.regions import REGION_CHOICES
from api.services.regional_growth import year_over_year
from api.statistics_serializers import (
    GrowthMetricResponseSerializer,
    PopularEventsResponseSerializer,
    RegionalStrengthEventResponseSerializer,
    RegionalStrengthRegionResponseSerializer,
    RegionalStrengthRegionsResponseSerializer,
)
from wca.models import Event


REGION_NAMES = dict(REGION_CHOICES)
RANK_TYPES = {
    RegionalStrengthRecord.RANK_SINGLE,
    RegionalStrengthRecord.RANK_AVERAGE,
}

REGIONAL_EVENT_METHODOLOGY = (
    "Each region uses its five best national ranks for this event. Empty slots "
    "use the worst national rank in the complete WCA export. Lower scores are "
    "better, and equal scores use standard competition ranking."
)
REGIONAL_REGION_METHODOLOGY = (
    "Every event uses the same five-slot regional score. Events are ordered by "
    "the region's placement, then official WCA event order."
)
GROWTH_METHODOLOGY = {
    GrowthAnnualRecord.METRIC_NEW_ATTENDEES: (
        "A Filipino competitor counts in the year and host region of their "
        "first-ever WCA competition, only when that first competition was in "
        "the Philippines and its coordinates could be classified."
    ),
    GrowthAnnualRecord.METRIC_ATTENDANCES: (
        "One Filipino competitor at one Philippine competition counts as one "
        "confirmed competition attendance, regardless of events or rounds."
    ),
    GrowthAnnualRecord.METRIC_ACTIVE_COMPETITORS: (
        "A Filipino competitor counts once per host region and year. The "
        "nationwide value counts each person only once per year."
    ),
    GrowthAnnualRecord.METRIC_POPULAR_EVENTS: (
        "Event participation counts each competitor-event-competition once, "
        "regardless of rounds. Unique competitors are reported separately."
    ),
}


class StatisticsUnavailable(APIException):
    status_code = 503
    default_detail = "Prepared statistics are not available yet."
    default_code = "statistics_unavailable"


def _active_snapshot():
    snapshot = StatisticsSnapshot.objects.filter(
        is_active=True,
        status=StatisticsSnapshot.STATUS_READY,
    ).first()
    if snapshot is None:
        raise StatisticsUnavailable()
    return snapshot


def _snapshot_metadata(snapshot):
    return {
        "id": snapshot.pk,
        "export_version": snapshot.export_version,
        "latest_year": snapshot.latest_year,
        "activated_at": snapshot.activated_at,
    }


def _rank_type(request):
    value = request.query_params.get("format", RegionalStrengthRecord.RANK_SINGLE)
    if value not in RANK_TYPES:
        raise exceptions.ParseError("format must be single or average")
    return value


def _strength_payload(record):
    return {
        "region_id": record.region_code,
        "region_name": REGION_NAMES[record.region_code],
        "placement": record.placement,
        "score": record.score,
        "contributor_count": record.contributor_count,
        "slots": record.slots,
    }


def _event_strength_payload(record):
    return {
        "event_id": record.event_id,
        "event_name": record.event.name,
        "placement": record.placement,
        "score": record.score,
        "contributor_count": record.contributor_count,
        "slots": record.slots,
    }


class RegionalStrengthByEventAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "format",
                str,
                enum=("single", "average"),
                description="WCA ranking result type.",
            )
        ],
        description="Prepared five-person regional strength for one WCA event.",
        responses=RegionalStrengthEventResponseSerializer,
    )
    def get(self, request, event_id):
        rank_type = _rank_type(request)
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise exceptions.NotFound("Event not found.")
        snapshot = _active_snapshot()
        records = list(
            RegionalStrengthRecord.objects.filter(
                snapshot=snapshot,
                event=event,
                rank_type=rank_type,
            ).order_by("placement", "region_code")
        )
        if not records:
            raise exceptions.NotFound("No ranking list exists for this event and format.")
        return Response(
            {
                "snapshot": _snapshot_metadata(snapshot),
                "event": {"id": event.id, "name": event.name},
                "format": rank_type,
                "methodology": REGIONAL_EVENT_METHODOLOGY,
                "coverage": snapshot.coverage.get("regional_strength", {}).get(
                    "{}:{}".format(rank_type, event.id), {}
                ),
                "regions": [_strength_payload(record) for record in records],
            }
        )


class RegionalStrengthByRegionAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "format",
                str,
                enum=("single", "average"),
                description="WCA ranking result type.",
            )
        ],
        description="Prepared event strengths for one PCA home region.",
        responses=RegionalStrengthRegionResponseSerializer,
    )
    def get(self, request, region_id):
        if region_id not in REGION_NAMES:
            raise exceptions.ParseError("Unknown region.")
        rank_type = _rank_type(request)
        snapshot = _active_snapshot()
        records = list(
            RegionalStrengthRecord.objects.filter(
                snapshot=snapshot,
                region_code=region_id,
                rank_type=rank_type,
            )
            .select_related("event")
            .order_by("placement", "event__rank", "event__name", "event_id")
        )
        if not records:
            raise exceptions.NotFound("No event strengths exist for this region and format.")
        strength_coverage = snapshot.coverage.get("regional_strength", {})
        return Response(
            {
                "snapshot": _snapshot_metadata(snapshot),
                "region": {"id": region_id, "name": REGION_NAMES[region_id]},
                "format": rank_type,
                "methodology": REGIONAL_REGION_METHODOLOGY,
                "coverage": {
                    record.event_id: strength_coverage.get(
                        "{}:{}".format(rank_type, record.event_id), {}
                    )
                    for record in records
                },
                "events": [_event_strength_payload(record) for record in records],
            }
        )


class RegionalStrengthRegionsAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "format",
                str,
                enum=("single", "average"),
                description="WCA ranking result type.",
            )
        ],
        description="Prepared event strengths grouped across every PCA home region.",
        responses=RegionalStrengthRegionsResponseSerializer,
    )
    def get(self, request):
        rank_type = _rank_type(request)
        snapshot = _active_snapshot()
        records = list(
            RegionalStrengthRecord.objects.filter(
                snapshot=snapshot,
                rank_type=rank_type,
            )
            .select_related("event")
            .order_by("region_code", "placement", "event__rank", "event__name")
        )
        grouped = defaultdict(list)
        for record in records:
            grouped[record.region_code].append(_event_strength_payload(record))
        return Response(
            {
                "snapshot": _snapshot_metadata(snapshot),
                "format": rank_type,
                "methodology": REGIONAL_REGION_METHODOLOGY,
                "regions": [
                    {
                        "region": {"id": region_id, "name": region_name},
                        "events": grouped[region_id],
                    }
                    for region_id, region_name in REGION_CHOICES
                ],
            }
        )


def _scope_order_expression():
    cases = [When(region_code="", then=Value(0))]
    cases.extend(
        When(region_code=code, then=Value(index))
        for index, (code, _name) in enumerate(REGION_CHOICES, start=1)
    )
    return Case(*cases, default=Value(999), output_field=IntegerField())


def _annual_series(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.region_code].append(record)

    scopes = ["", *(code for code, _label in REGION_CHOICES)]
    series = []
    for region_code in scopes:
        values = []
        previous = None
        for record in grouped.get(region_code, ()):
            absolute, percent = (None, None)
            if previous is not None:
                absolute, percent = year_over_year(record.value, previous)
            values.append(
                {
                    "year": record.year,
                    "value": record.value,
                    "change": absolute,
                    "percent_change": percent,
                }
            )
            previous = record.value
        series.append(
            {
                "region_id": region_code or "national",
                "region_name": REGION_NAMES.get(region_code, "Nationwide"),
                "values": values,
            }
        )
    return series


class GrowthMetricAPIView(APIView):
    metric = None

    @extend_schema(
        description="Prepared annual regional growth series.",
        responses=GrowthMetricResponseSerializer,
    )
    def get(self, request):
        snapshot = _active_snapshot()
        records = (
            GrowthAnnualRecord.objects.filter(
                snapshot=snapshot,
                metric=self.metric,
                event_id="",
            )
            .annotate(scope_order=_scope_order_expression())
            .order_by("scope_order", "year")
        )
        return Response(
            {
                "snapshot": _snapshot_metadata(snapshot),
                "metric": self.metric,
                "methodology": GROWTH_METHODOLOGY[self.metric],
                "coverage": snapshot.coverage.get("growth", {}),
                "series": _annual_series(records),
            }
        )


class NewAttendeesAPIView(GrowthMetricAPIView):
    metric = GrowthAnnualRecord.METRIC_NEW_ATTENDEES


class AttendancesAPIView(GrowthMetricAPIView):
    metric = GrowthAnnualRecord.METRIC_ATTENDANCES


class ActiveCompetitorsAPIView(GrowthMetricAPIView):
    metric = GrowthAnnualRecord.METRIC_ACTIVE_COMPETITORS


class PopularEventsAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "region",
                str,
                description="PCA region ID or national (default).",
            )
        ],
        description="Prepared event popularity for one host-region scope.",
        responses=PopularEventsResponseSerializer,
    )
    def get(self, request):
        requested_region = request.query_params.get("region", "national")
        if requested_region == "national":
            region_code = ""
            region_name = "Nationwide"
        elif requested_region in REGION_NAMES:
            region_code = requested_region
            region_name = REGION_NAMES[region_code]
        else:
            raise exceptions.ParseError("region must be national or a valid region ID")

        snapshot = _active_snapshot()
        event_order = {
            event_id: (rank, name)
            for event_id, rank, name in Event.objects.values_list("id", "rank", "name")
        }
        grouped = defaultdict(list)
        records = GrowthAnnualRecord.objects.filter(
            snapshot=snapshot,
            metric=GrowthAnnualRecord.METRIC_POPULAR_EVENTS,
            region_code=region_code,
        ).order_by("event_id", "year")
        for record in records:
            grouped[record.event_id].append(
                {
                    "year": record.year,
                    "participations": record.value,
                    "unique_competitors": record.unique_competitors,
                }
            )
        events = [
            {
                "event_id": event_id,
                "event_name": event_order[event_id][1],
                "values": values,
            }
            for event_id, values in grouped.items()
        ]
        events.sort(key=lambda item: (*event_order[item["event_id"]], item["event_id"]))
        return Response(
            {
                "snapshot": _snapshot_metadata(snapshot),
                "scope": {"id": requested_region, "name": region_name},
                "metric": GrowthAnnualRecord.METRIC_POPULAR_EVENTS,
                "methodology": GROWTH_METHODOLOGY[
                    GrowthAnnualRecord.METRIC_POPULAR_EVENTS
                ],
                "coverage": snapshot.coverage.get("growth", {}),
                "events": events,
            }
        )
