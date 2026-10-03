"""Pure aggregation rules for historical regional growth statistics."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple


NATIONAL_SCOPE = ""
START_YEAR = 2007

NEW_ATTENDEES = "new_attendees"
ATTENDANCES = "attendances"
ACTIVE_COMPETITORS = "active_competitors"
POPULAR_EVENTS = "popular_events"


@dataclass(frozen=True)
class Participation:
    person_id: str
    competition_id: str
    year: int
    month: int
    day: int
    country_id: str
    region_code: Optional[str]
    event_id: str


@dataclass(frozen=True)
class AnnualGrowthValue:
    metric: str
    year: int
    region_code: str
    event_id: str
    value: int
    unique_competitors: Optional[int] = None


def _competition_key(row):
    return row.year, row.month, row.day, row.competition_id


def _add_standard_rows(records, metric, years, region_codes, values):
    for year in years:
        for region_code in (NATIONAL_SCOPE,) + tuple(region_codes):
            records.append(
                AnnualGrowthValue(
                    metric=metric,
                    year=year,
                    region_code=region_code,
                    event_id="",
                    value=len(values.get((region_code, year), ())),
                )
            )


def calculate_growth_statistics(
    participations: Iterable[Participation],
    region_codes: Sequence[str],
    event_ids: Sequence[str],
    latest_year: int,
    philippines_country_id: str = "Philippines",
    start_year: int = START_YEAR,
) -> Tuple[Tuple[AnnualGrowthValue, ...], dict]:
    """Aggregate all growth metrics from result-level participation rows."""
    if latest_year < start_year:
        raise ValueError("Latest year cannot be earlier than the history start year")
    if len(set(region_codes)) != len(region_codes):
        raise ValueError("Region codes must be unique")
    if len(set(event_ids)) != len(event_ids):
        raise ValueError("Event IDs must be unique")

    valid_regions = set(region_codes)
    valid_events = set(event_ids)
    rows = []
    for row in participations:
        if not row.person_id or not row.competition_id:
            continue
        if row.event_id not in valid_events:
            raise ValueError("Participation uses an unknown event ID")
        if row.region_code is not None and row.region_code not in valid_regions:
            raise ValueError("Participation uses an unknown region code")
        rows.append(row)

    years = tuple(range(start_year, latest_year + 1))
    first_by_person = {}
    for row in rows:
        current = first_by_person.get(row.person_id)
        if current is None or _competition_key(row) < _competition_key(current):
            first_by_person[row.person_id] = row

    new_attendees = defaultdict(set)
    new_attendees_unclassified = defaultdict(set)
    for person_id, first in first_by_person.items():
        if first.country_id != philippines_country_id:
            continue
        if first.region_code is None:
            new_attendees_unclassified[first.year].add(person_id)
            continue
        new_attendees[(NATIONAL_SCOPE, first.year)].add(person_id)
        new_attendees[(first.region_code, first.year)].add(person_id)

    attendance_keys = defaultdict(set)
    active_people = defaultdict(set)
    popular_participations = defaultdict(set)
    popular_people = defaultdict(set)
    assigned_competitions = set()
    unclassified_competitions = set()

    for row in rows:
        if row.country_id != philippines_country_id:
            continue
        attendance = (row.person_id, row.competition_id)
        popular = (row.person_id, row.event_id, row.competition_id)

        attendance_keys[(NATIONAL_SCOPE, row.year)].add(attendance)
        active_people[(NATIONAL_SCOPE, row.year)].add(row.person_id)
        popular_participations[(NATIONAL_SCOPE, row.year, row.event_id)].add(popular)
        popular_people[(NATIONAL_SCOPE, row.year, row.event_id)].add(row.person_id)

        competition = (row.competition_id, row.year)
        if row.region_code is None:
            unclassified_competitions.add(competition)
            continue

        assigned_competitions.add(competition)
        attendance_keys[(row.region_code, row.year)].add(attendance)
        active_people[(row.region_code, row.year)].add(row.person_id)
        popular_participations[(row.region_code, row.year, row.event_id)].add(popular)
        popular_people[(row.region_code, row.year, row.event_id)].add(row.person_id)

    records = []
    _add_standard_rows(records, NEW_ATTENDEES, years, region_codes, new_attendees)
    _add_standard_rows(records, ATTENDANCES, years, region_codes, attendance_keys)
    _add_standard_rows(
        records, ACTIVE_COMPETITORS, years, region_codes, active_people
    )
    for year in years:
        for region_code in (NATIONAL_SCOPE,) + tuple(region_codes):
            for event_id in event_ids:
                key = (region_code, year, event_id)
                records.append(
                    AnnualGrowthValue(
                        metric=POPULAR_EVENTS,
                        year=year,
                        region_code=region_code,
                        event_id=event_id,
                        value=len(popular_participations.get(key, ())),
                        unique_competitors=len(popular_people.get(key, ())),
                    )
                )

    coverage = {
        "assigned_competitions": len(assigned_competitions),
        "unclassified_competitions": len(unclassified_competitions),
        "new_attendees_unclassified": {
            str(year): len(people)
            for year, people in sorted(new_attendees_unclassified.items())
        },
    }
    return tuple(records), coverage


def year_over_year(current, previous):
    """Return absolute and percentage change; zero baselines have no percent."""
    absolute = current - previous
    percent = None if previous == 0 else (absolute * 100.0 / previous)
    return absolute, percent
