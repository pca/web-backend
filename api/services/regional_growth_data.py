"""Database adapter and snapshot writer for regional growth statistics."""

import hashlib
import json

from django.db.models import Count, F, Q

from api.models import GrowthAnnualRecord
from api.regions import REGION_CHOICES
from wca.models import Competition, CompetitionRegionAssignment, Event, Result

from .regional_growth import Participation, calculate_growth_statistics
from .snapshot_records import sync_snapshot_records


def validate_competition_assignments(boundary_dataset):
    """Require a current PCA-owned assignment row for every Philippine event."""
    competitions = Competition.objects.filter(country_id="Philippines")
    total = competitions.count()
    matching = CompetitionRegionAssignment.objects.filter(
        competition__country_id="Philippines",
        boundary_dataset=boundary_dataset,
    ).filter(
        Q(classified_latitude=F("competition__latitude"))
        | Q(classified_latitude__isnull=True, competition__latitude__isnull=True),
        Q(classified_longitude=F("competition__longitude"))
        | Q(classified_longitude__isnull=True, competition__longitude__isnull=True),
    ).count()
    if matching != total:
        raise ValueError(
            "Competition-region assignments are incomplete or stale: {} of {} match boundary {}.".format(
                matching, total, boundary_dataset.version
            )
        )


def load_participations():
    """Yield result-level rows; pure aggregation performs all required dedupes."""
    rows = (
        Result.objects.filter(
            person_id__isnull=False,
            competition_id__isnull=False,
            event_id__isnull=False,
        )
        .order_by()
        .values_list(
            "person_id",
            "competition_id",
            "competition__year",
            "competition__month",
            "competition__day",
            "competition__country_id",
            "competition__region_assignment__region_code",
            "event_id",
        )
    )
    for values in rows.iterator(chunk_size=5000):
        yield Participation(*values)


def _record_hash(record):
    payload = {
        "metric": record.metric,
        "year": record.year,
        "region_code": record.region_code,
        "event_id": record.event_id,
        "value": record.value,
        "unique_competitors": record.unique_competitors,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_growth_records(snapshot):
    validate_competition_assignments(snapshot.boundary_dataset)
    event_ids = tuple(
        Event.objects.order_by("rank", "name", "id").values_list("id", flat=True)
    )
    region_codes = tuple(code for code, _label in REGION_CHOICES)
    values, coverage = calculate_growth_statistics(
        load_participations(),
        region_codes,
        event_ids,
        latest_year=snapshot.latest_year,
    )
    records = [
        GrowthAnnualRecord(
            snapshot=snapshot,
            metric=value.metric,
            year=value.year,
            region_code=value.region_code,
            event_id=value.event_id,
            value=value.value,
            unique_competitors=value.unique_competitors,
            content_hash=_record_hash(value),
        )
        for value in values
    ]
    sync_snapshot_records(
        model=GrowthAnnualRecord,
        snapshot=snapshot,
        desired_records=records,
        key_fields=("metric", "year", "region_code", "event_id"),
        update_fields=("value", "unique_competitors"),
        batch_size=1000,
    )

    outcomes = dict(
        CompetitionRegionAssignment.objects.filter(
            competition__country_id="Philippines",
            boundary_dataset=snapshot.boundary_dataset,
        )
        .values_list("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )
    coverage["classification_outcomes"] = outcomes
    return coverage
