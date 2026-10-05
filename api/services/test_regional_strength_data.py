import pytest
from django.contrib.auth import get_user_model

from api.models import StatisticsSnapshot
from api.services.regional_strength_data import (
    build_regional_strength_records,
    load_event_strength_inputs,
)
from wca.models import BoundaryDataset, Event, RanksAverage, RanksSingle


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("rank_type", "rank_model"),
    (("single", RanksSingle), ("average", RanksAverage)),
)
def test_strength_inputs_use_complete_export_rankings_beyond_public_top_100(
    event,
    person,
    person_factory,
    rank_type,
    rank_model,
):
    get_user_model().objects.create_user(
        username="ranked-user",
        wca_id=person.id,
        region="NCR",
    )
    outside_top_100 = person_factory(
        id="2026TEST02",
        name="Rank 125",
        country=person.country,
    )
    rank_model.objects.create(
        person=person,
        event=event,
        best=1000,
        world_rank=1,
        continent_rank=1,
        country_rank=1,
    )
    rank_model.objects.create(
        person=outside_top_100,
        event=event,
        best=2000,
        world_rank=125,
        continent_rank=125,
        country_rank=125,
    )

    entries, worst_rank, coverage = load_event_strength_inputs(event.id, rank_type)

    assert worst_rank == 125
    assert [(entry.wca_id, entry.national_rank) for entry in entries] == [
        (person.id, 1)
    ]
    assert coverage == {
        "ranked_competitors": 2,
        "matched_home_region": 1,
        "missing_home_region": 1,
        "ambiguous_home_region": 0,
    }


@pytest.mark.django_db
def test_strength_inputs_exclude_ambiguous_duplicate_home_region_matches(
    event,
    person,
):
    User = get_user_model()
    User.objects.create_user(username="first-match", wca_id=person.id, region="NCR")
    User.objects.create_user(username="second-match", wca_id=person.id, region="07")
    RanksSingle.objects.create(
        person=person,
        event=event,
        best=1000,
        world_rank=1,
        continent_rank=1,
        country_rank=1,
    )

    entries, worst_rank, coverage = load_event_strength_inputs(event.id, "single")

    assert entries == ()
    assert worst_rank == 1
    assert coverage == {
        "ranked_competitors": 1,
        "matched_home_region": 0,
        "missing_home_region": 0,
        "ambiguous_home_region": 1,
    }


@pytest.mark.django_db
def test_strength_snapshot_includes_current_events_and_excludes_retired_events(
    event,
    person,
):
    event.rank = 10
    event.save(update_fields=("rank",))
    retired_event = Event.objects.create(
        id="magic",
        name="Magic",
        rank=997,
        format="time",
        cell_name="Magic",
    )
    get_user_model().objects.create_user(
        username="ranked-user",
        wca_id=person.id,
        region="NCR",
    )
    for ranked_event in (event, retired_event):
        RanksSingle.objects.create(
            person=person,
            event=ranked_event,
            best=1000,
            world_rank=1,
            continent_rank=1,
            country_rank=1,
        )
    boundary = BoundaryDataset.objects.create(
        version="strength-current-events-v1",
        source_url="https://example.com/regions.geojson",
        retrieved_on="2026-10-05",
        license="test",
        processing_notes="test fixture",
        checksum_sha256="1" * 64,
        feature_count=18,
    )
    snapshot = StatisticsSnapshot.objects.create(
        export_version="test-export",
        export_checksum="2" * 64,
        boundary_dataset=boundary,
        latest_year=2026,
    )

    coverage = build_regional_strength_records(snapshot)

    event_ids = set(
        snapshot.regional_strength_records.values_list("event_id", flat=True)
    )
    assert event.id in event_ids
    assert retired_event.id not in event_ids
    assert "single:{}".format(event.id) in coverage
    assert "single:{}".format(retired_event.id) not in coverage
