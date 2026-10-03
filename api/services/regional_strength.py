"""Pure calculation rules for regional-strength statistics."""

from dataclasses import dataclass, replace
from typing import Iterable, Optional, Sequence, Tuple


TEAM_SIZE = 5


@dataclass(frozen=True)
class RankedCompetitor:
    wca_id: str
    name: str
    region_code: str
    national_rank: int


@dataclass(frozen=True)
class ScoringSlot:
    national_rank: int
    wca_id: Optional[str] = None
    name: Optional[str] = None
    is_penalty: bool = False


@dataclass(frozen=True)
class RegionStrength:
    region_code: str
    region_name: str
    score: int
    placement: int
    contributor_count: int
    slots: Tuple[ScoringSlot, ...]


@dataclass(frozen=True)
class EventStrength:
    event_id: str
    event_name: str
    event_order: int
    region: RegionStrength


def _validate_rank(national_rank):
    if not isinstance(national_rank, int) or national_rank <= 0:
        raise ValueError("National ranks must be positive integers")


def _deduplicate_competitors(entries):
    """Keep one deterministic best row for each WCA ID."""
    by_wca_id = {}
    for entry in entries:
        _validate_rank(entry.national_rank)
        if not entry.wca_id:
            raise ValueError("Ranked competitors require a WCA ID")
        current = by_wca_id.get(entry.wca_id)
        candidate_key = (entry.national_rank, entry.name, entry.region_code)
        if current is None or candidate_key < (
            current.national_rank,
            current.name,
            current.region_code,
        ):
            by_wca_id[entry.wca_id] = entry
    return tuple(by_wca_id.values())


def calculate_event_strength(
    entries: Iterable[RankedCompetitor],
    regions: Sequence[Tuple[str, str]],
    worst_national_rank: int,
    team_size: int = TEAM_SIZE,
) -> Tuple[RegionStrength, ...]:
    """Return all regions ordered by standard-competition placement."""
    _validate_rank(worst_national_rank)
    if team_size <= 0:
        raise ValueError("Team size must be positive")

    region_names = dict(regions)
    if len(region_names) != len(regions):
        raise ValueError("Region codes must be unique")

    grouped = {code: [] for code in region_names}
    for entry in _deduplicate_competitors(entries):
        if entry.region_code not in grouped:
            raise ValueError("Ranked competitor uses an unknown region code")
        if entry.national_rank > worst_national_rank:
            raise ValueError("National rank cannot exceed the full-export worst rank")
        grouped[entry.region_code].append(entry)

    unplaced = []
    for region_code, region_name in regions:
        contributors = sorted(
            grouped[region_code], key=lambda item: (item.national_rank, item.wca_id)
        )[:team_size]
        slots = [
            ScoringSlot(
                national_rank=entry.national_rank,
                wca_id=entry.wca_id,
                name=entry.name,
            )
            for entry in contributors
        ]
        slots.extend(
            ScoringSlot(national_rank=worst_national_rank, is_penalty=True)
            for _missing in range(team_size - len(slots))
        )
        unplaced.append(
            RegionStrength(
                region_code=region_code,
                region_name=region_name,
                score=sum(slot.national_rank for slot in slots),
                placement=0,
                contributor_count=len(contributors),
                slots=tuple(slots),
            )
        )

    ordered = sorted(unplaced, key=lambda result: (result.score, result.region_code))
    placed = []
    previous_score = None
    previous_placement = 0
    for index, result in enumerate(ordered, start=1):
        placement = previous_placement if result.score == previous_score else index
        placed.append(replace(result, placement=placement))
        previous_score = result.score
        previous_placement = placement
    return tuple(placed)


def order_best_events(
    event_strengths: Iterable[EventStrength],
) -> Tuple[EventStrength, ...]:
    """Order a region's events by placement, official order, then name."""
    return tuple(
        sorted(
            event_strengths,
            key=lambda result: (
                result.region.placement,
                result.event_order,
                result.event_name,
            ),
        )
    )
