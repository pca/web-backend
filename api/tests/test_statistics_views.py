from datetime import date
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils import timezone

from api.models import (
    GrowthAnnualRecord,
    RegionalStrengthRecord,
    StatisticsSnapshot,
)
from api.services.snapshots import build_and_activate_snapshot
from wca.models import BoundaryDataset


def boundary(version="test-boundaries-v1"):
    return BoundaryDataset.objects.create(
        version=version,
        source_url="https://example.org/boundaries",
        retrieved_on=date(2026, 10, 3),
        coordinate_system="EPSG:4326",
        license="Test license",
        attribution="Test source",
        processing_notes="Test processing",
        checksum_sha256=("a" if version.endswith("v1") else "b") * 64,
        feature_count=18,
    )


def snapshot(boundary_dataset, checksum="1" * 64, active=True):
    now = timezone.now()
    return StatisticsSnapshot.objects.create(
        export_version="2026-10-03",
        export_checksum=checksum,
        boundary_dataset=boundary_dataset,
        latest_year=2026,
        status=StatisticsSnapshot.STATUS_READY,
        is_active=active,
        coverage={"regional_strength": {}, "growth": {"assigned_competitions": 1}},
        completed_at=now,
        activated_at=now if active else None,
    )


@pytest.mark.django_db
def test_statistics_endpoint_reports_when_snapshot_is_not_ready(api_client, event):
    url = reverse(
        "api:statistics-regional-strength-event", kwargs={"event_id": event.id}
    )
    response = api_client.get(url)
    assert response.status_code == 503


@pytest.mark.django_db
def test_regional_strength_event_response_includes_five_slots(api_client, event):
    active = snapshot(boundary())
    RegionalStrengthRecord.objects.create(
        snapshot=active,
        event=event,
        rank_type="single",
        region_code="NCR",
        score=105,
        placement=1,
        contributor_count=4,
        slots=[
            {"wca_id": "A", "name": "A", "national_rank": 1, "is_penalty": False},
            {"wca_id": "B", "name": "B", "national_rank": 2, "is_penalty": False},
            {"wca_id": "C", "name": "C", "national_rank": 3, "is_penalty": False},
            {"wca_id": "D", "name": "D", "national_rank": 4, "is_penalty": False},
            {"wca_id": None, "name": None, "national_rank": 95, "is_penalty": True},
        ],
        content_hash="c" * 64,
    )
    url = reverse(
        "api:statistics-regional-strength-event", kwargs={"event_id": event.id}
    )
    response = api_client.get(url, {"format": "single"})

    assert response.status_code == 200
    data = response.json()
    assert data["snapshot"]["export_version"] == "2026-10-03"
    assert data["regions"][0]["region_id"] == "NCR"
    assert len(data["regions"][0]["slots"]) == 5
    assert data["regions"][0]["slots"][-1]["is_penalty"] is True


@pytest.mark.django_db
def test_regional_strength_rejects_invalid_format(api_client, event):
    snapshot(boundary())
    url = reverse(
        "api:statistics-regional-strength-event", kwargs={"event_id": event.id}
    )
    response = api_client.get(url, {"format": "median"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_regional_strength_rejects_unknown_event_and_region(api_client):
    snapshot(boundary())

    unknown_event = api_client.get(
        reverse(
            "api:statistics-regional-strength-event",
            kwargs={"event_id": "unknown"},
        )
    )
    unknown_region = api_client.get(
        reverse(
            "api:statistics-regional-strength-region",
            kwargs={"region_id": "99"},
        )
    )

    assert unknown_event.status_code == 404
    assert unknown_region.status_code == 400


@pytest.mark.django_db
def test_regional_strength_region_response_includes_event_coverage(api_client, event):
    dataset = boundary()
    active = snapshot(dataset)
    active.coverage = {
        "regional_strength": {
            "single:333": {
                "ranked_competitors": 100,
                "matched_home_region": 75,
            }
        },
        "growth": {},
    }
    active.save(update_fields=("coverage",))
    RegionalStrengthRecord.objects.create(
        snapshot=active,
        event=event,
        rank_type="single",
        region_code="NCR",
        score=15,
        placement=1,
        contributor_count=5,
        slots=[
            {
                "wca_id": "TEST{}".format(index),
                "name": "Test {}".format(index),
                "national_rank": index,
                "is_penalty": False,
            }
            for index in range(1, 6)
        ],
        content_hash="e" * 64,
    )

    response = api_client.get(
        reverse(
            "api:statistics-regional-strength-region",
            kwargs={"region_id": "NCR"},
        ),
        {"format": "single"},
    )

    assert response.status_code == 200
    assert response.json()["coverage"]["333"] == {
        "ranked_competitors": 100,
        "matched_home_region": 75,
    }


@pytest.mark.django_db
def test_regional_strength_regions_response_groups_every_region(api_client, event):
    active = snapshot(boundary())
    slots = [
        {
            "wca_id": "TEST{}".format(index),
            "name": "Test {}".format(index),
            "national_rank": index,
            "is_penalty": False,
        }
        for index in range(1, 6)
    ]
    RegionalStrengthRecord.objects.create(
        snapshot=active,
        event=event,
        rank_type="single",
        region_code="03",
        score=15,
        placement=1,
        contributor_count=5,
        slots=slots,
        content_hash="f" * 64,
    )

    response = api_client.get(
        reverse("api:statistics-regional-strength-regions"),
        {"format": "single"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["regions"]) == 18
    assert data["regions"][0] == {
        "region": {"id": "NCR", "name": "NCR (Luzon - Metro Manila)"},
        "events": [],
    }
    central_luzon = next(
        group for group in data["regions"] if group["region"]["id"] == "03"
    )
    assert central_luzon["events"][0]["score"] == 15
    assert central_luzon["events"][0]["slots"] == slots


@pytest.mark.django_db
def test_growth_response_includes_yoy_and_coverage(api_client):
    active = snapshot(boundary())
    for year, value in ((2007, 0), (2008, 5), (2009, 10)):
        GrowthAnnualRecord.objects.create(
            snapshot=active,
            metric=GrowthAnnualRecord.METRIC_ATTENDANCES,
            year=year,
            region_code="",
            event_id="",
            value=value,
            content_hash=str(year) * 16,
        )
    response = api_client.get(reverse("api:statistics-growth-attendances"))

    assert response.status_code == 200
    data = response.json()
    nationwide = data["series"][0]
    assert nationwide["region_id"] == "national"
    assert nationwide["values"][1]["change"] == 5
    assert nationwide["values"][1]["percent_change"] is None
    assert nationwide["values"][2]["percent_change"] == 100.0
    assert data["coverage"]["assigned_competitions"] == 1


@pytest.mark.django_db
def test_popular_events_validates_scope_and_returns_both_counts(api_client, event):
    active = snapshot(boundary())
    GrowthAnnualRecord.objects.create(
        snapshot=active,
        metric=GrowthAnnualRecord.METRIC_POPULAR_EVENTS,
        year=2026,
        region_code="07",
        event_id=event.id,
        value=20,
        unique_competitors=12,
        content_hash="d" * 64,
    )
    url = reverse("api:statistics-growth-popular-events")
    response = api_client.get(url, {"region": "07"})
    invalid = api_client.get(url, {"region": "99"})

    assert response.status_code == 200
    point = response.json()["events"][0]["values"][0]
    assert point == {
        "year": 2026,
        "participations": 20,
        "unique_competitors": 12,
    }
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_snapshot_failure_keeps_previous_snapshot_active():
    dataset = boundary()
    previous = snapshot(dataset)

    def fail(_snapshot):
        raise RuntimeError("deliberate test failure")

    with pytest.raises(RuntimeError, match="deliberate"):
        build_and_activate_snapshot(
            export_version="2026-10-10",
            export_checksum="2" * 64,
            boundary_dataset=dataset,
            latest_year=2026,
            builder=fail,
        )

    previous.refresh_from_db()
    failed = StatisticsSnapshot.objects.get(export_checksum="2" * 64)
    assert previous.is_active is True
    assert previous.status == StatisticsSnapshot.STATUS_READY
    assert failed.is_active is False
    assert failed.status == StatisticsSnapshot.STATUS_FAILED
    assert failed.error_message == "deliberate test failure"


@pytest.mark.django_db
def test_same_export_and_boundary_skips_rebuild():
    dataset = boundary()
    existing = snapshot(dataset)
    builder = Mock()

    result, built = build_and_activate_snapshot(
        export_version=existing.export_version,
        export_checksum=existing.export_checksum,
        boundary_dataset=dataset,
        latest_year=existing.latest_year,
        builder=builder,
    )

    assert result.pk == existing.pk
    assert built is False
    builder.assert_not_called()


@pytest.mark.django_db
def test_successful_snapshot_atomically_replaces_previous_active_snapshot():
    dataset = boundary()
    previous = snapshot(dataset)

    replacement, built = build_and_activate_snapshot(
        export_version="2026-10-10",
        export_checksum="9" * 64,
        boundary_dataset=dataset,
        latest_year=2026,
        builder=lambda _snapshot: {"verified": True},
    )

    previous.refresh_from_db()
    replacement.refresh_from_db()
    assert built is True
    assert previous.is_active is False
    assert replacement.is_active is True
    assert replacement.status == StatisticsSnapshot.STATUS_READY
    assert replacement.coverage == {"verified": True}


@pytest.mark.django_db
def test_openapi_schema_documents_all_statistics_endpoints(api_client):
    response = api_client.get(reverse("schema"))

    assert response.status_code == 200
    schema = response.json()
    expected_paths = {
        "/statistics/regional/strength/events/{event_id}/",
        "/statistics/regional/strength/regions/",
        "/statistics/regional/strength/regions/{region_id}/",
        "/statistics/growth/new-attendees/",
        "/statistics/growth/attendances/",
        "/statistics/growth/active-competitors/",
        "/statistics/growth/popular-events/",
    }
    assert expected_paths <= set(schema["paths"])
