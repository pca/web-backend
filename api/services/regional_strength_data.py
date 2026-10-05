"""Database adapter and snapshot writer for regional-strength calculations."""

import hashlib
import json
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Max

from api.models import RegionalStrengthRecord
from api.regions import REGION_CHOICES
from wca.models import Event, RanksAverage, RanksSingle

from .regional_strength import RankedCompetitor, calculate_event_strength
from .snapshot_records import sync_snapshot_records


RANK_MODELS = {
    RegionalStrengthRecord.RANK_SINGLE: RanksSingle,
    RegionalStrengthRecord.RANK_AVERAGE: RanksAverage,
}

# WCA exports keep retired events at the end of the event list with ranks in
# the 990s. Match the frontend's active-event list so Regional Statistics only
# prepares current events, while Growth Statistics can still show full history.
CURRENT_EVENT_RANK_CUTOFF = 990


def _home_regions_by_wca_id(wca_ids):
    """Return only unambiguous PCA home-region matches."""
    User = get_user_model()
    regions_by_wca_id = defaultdict(set)
    for wca_id, region_code in User.objects.filter(
        wca_id__in=wca_ids,
        region__isnull=False,
    ).values_list("wca_id", "region"):
        if region_code:
            regions_by_wca_id[wca_id].add(region_code)

    resolved = {
        wca_id: next(iter(region_codes))
        for wca_id, region_codes in regions_by_wca_id.items()
        if len(region_codes) == 1
    }
    ambiguous = {
        wca_id for wca_id, region_codes in regions_by_wca_id.items() if len(region_codes) > 1
    }
    return resolved, ambiguous


def load_event_strength_inputs(event_id, rank_type):
    """Load complete export ranks and PCA home-region matches for one event."""
    try:
        rank_model = RANK_MODELS[rank_type]
    except KeyError:
        raise ValueError("Rank type must be single or average")

    rank_rows = list(
        rank_model.objects.filter(event_id=event_id, country_rank__gt=0)
        .order_by("country_rank", "person_id")
        .values("person_id", "person__name", "country_rank")
    )
    if not rank_rows:
        return (), None, {
            "ranked_competitors": 0,
            "matched_home_region": 0,
            "missing_home_region": 0,
            "ambiguous_home_region": 0,
        }

    worst_rank = rank_model.objects.filter(
        event_id=event_id, country_rank__gt=0
    ).aggregate(value=Max("country_rank"))["value"]
    wca_ids = {row["person_id"] for row in rank_rows}
    home_regions, ambiguous = _home_regions_by_wca_id(wca_ids)
    entries = tuple(
        RankedCompetitor(
            wca_id=row["person_id"],
            name=row["person__name"] or row["person_id"],
            region_code=home_regions[row["person_id"]],
            national_rank=row["country_rank"],
        )
        for row in rank_rows
        if row["person_id"] in home_regions
    )
    return entries, worst_rank, {
        "ranked_competitors": len(wca_ids),
        "matched_home_region": len({entry.wca_id for entry in entries}),
        "missing_home_region": len(wca_ids - set(home_regions) - ambiguous),
        "ambiguous_home_region": len(ambiguous),
    }


def _slot_payload(slot):
    return {
        "wca_id": slot.wca_id,
        "name": slot.name,
        "national_rank": slot.national_rank,
        "is_penalty": slot.is_penalty,
    }


def _record_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_regional_strength_records(snapshot):
    """Populate every valid event/rank type for a staging snapshot."""
    coverage = {}
    records = []
    events = Event.objects.filter(rank__lt=CURRENT_EVENT_RANK_CUTOFF).order_by(
        "rank", "name", "id"
    )
    for event in events.iterator():
        for rank_type in RANK_MODELS:
            entries, worst_rank, match_coverage = load_event_strength_inputs(
                event.id, rank_type
            )
            coverage["{}:{}".format(rank_type, event.id)] = match_coverage
            if worst_rank is None:
                continue
            results = calculate_event_strength(
                entries,
                REGION_CHOICES,
                worst_national_rank=worst_rank,
            )
            for result in results:
                slots = [_slot_payload(slot) for slot in result.slots]
                payload = {
                    "score": result.score,
                    "placement": result.placement,
                    "contributor_count": result.contributor_count,
                    "slots": slots,
                }
                records.append(
                    RegionalStrengthRecord(
                        snapshot=snapshot,
                        event=event,
                        rank_type=rank_type,
                        region_code=result.region_code,
                        score=result.score,
                        placement=result.placement,
                        contributor_count=result.contributor_count,
                        slots=slots,
                        content_hash=_record_hash(payload),
                    )
                )
    sync_snapshot_records(
        model=RegionalStrengthRecord,
        snapshot=snapshot,
        desired_records=records,
        key_fields=("event_id", "rank_type", "region_code"),
        update_fields=("score", "placement", "contributor_count", "slots"),
        batch_size=500,
    )
    return coverage
