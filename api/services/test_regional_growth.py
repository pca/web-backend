import unittest

from .regional_growth import (
    ACTIVE_COMPETITORS,
    ATTENDANCES,
    NEW_ATTENDEES,
    POPULAR_EVENTS,
    Participation,
    calculate_growth_statistics,
    year_over_year,
)


REGIONS = ("01", "07")
EVENTS = ("333", "222")


def row(
    person,
    competition,
    year,
    region="01",
    event="333",
    country="Philippines",
    month=1,
    day=1,
):
    return Participation(
        person,
        competition,
        year,
        month,
        day,
        country,
        region,
        event,
    )


def value(records, metric, year, region="", event=""):
    return next(
        record
        for record in records
        if (
            record.metric,
            record.year,
            record.region_code,
            record.event_id,
        )
        == (metric, year, region, event)
    )


class RegionalGrowthTests(unittest.TestCase):
    def test_new_attendee_requires_first_ever_competition_to_be_in_philippines(self):
        records, _coverage = calculate_growth_statistics(
            [
                row("FOREIGN-FIRST", "Foreign2020", 2020, country="Japan", region=None),
                row("FOREIGN-FIRST", "Philippines2021", 2021),
                row("LOCAL-FIRST", "Philippines2021", 2021, region="07"),
            ],
            REGIONS,
            EVENTS,
            latest_year=2021,
            start_year=2020,
        )
        self.assertEqual(value(records, NEW_ATTENDEES, 2021).value, 1)
        self.assertEqual(value(records, NEW_ATTENDEES, 2021, "07").value, 1)
        self.assertEqual(value(records, NEW_ATTENDEES, 2021, "01").value, 0)

    def test_unclassified_first_philippine_competition_is_reported_not_guessed(self):
        records, coverage = calculate_growth_statistics(
            [row("A", "Unknown2021", 2021, region=None)],
            REGIONS,
            EVENTS,
            latest_year=2021,
            start_year=2021,
        )
        self.assertEqual(value(records, NEW_ATTENDEES, 2021).value, 0)
        self.assertEqual(value(records, NEW_ATTENDEES, 2021, "01").value, 0)
        self.assertEqual(coverage["new_attendees_unclassified"], {"2021": 1})

    def test_attendance_deduplicates_rounds_and_events_per_competition(self):
        records, _coverage = calculate_growth_statistics(
            [
                row("A", "Comp2021", 2021, event="333"),
                row("A", "Comp2021", 2021, event="333"),
                row("A", "Comp2021", 2021, event="222"),
                row("A", "Another2021", 2021, event="333"),
            ],
            REGIONS,
            EVENTS,
            latest_year=2021,
            start_year=2021,
        )
        self.assertEqual(value(records, ATTENDANCES, 2021).value, 2)
        self.assertEqual(value(records, ATTENDANCES, 2021, "01").value, 2)

    def test_active_people_deduplicate_per_region_and_nationwide(self):
        records, _coverage = calculate_growth_statistics(
            [
                row("TRAVELER", "Luzon2021", 2021, region="01"),
                row("TRAVELER", "Visayas2021", 2021, region="07"),
                row("TRAVELER", "VisayasAgain2021", 2021, region="07"),
            ],
            REGIONS,
            EVENTS,
            latest_year=2021,
            start_year=2021,
        )
        self.assertEqual(value(records, ACTIVE_COMPETITORS, 2021).value, 1)
        self.assertEqual(value(records, ACTIVE_COMPETITORS, 2021, "01").value, 1)
        self.assertEqual(value(records, ACTIVE_COMPETITORS, 2021, "07").value, 1)

    def test_popular_events_count_participations_and_unique_reach_separately(self):
        records, _coverage = calculate_growth_statistics(
            [
                row("A", "One2021", 2021),
                row("A", "One2021", 2021),
                row("A", "Two2021", 2021),
                row("B", "Two2021", 2021),
            ],
            REGIONS,
            EVENTS,
            latest_year=2021,
            start_year=2021,
        )
        result = value(records, POPULAR_EVENTS, 2021, "01", "333")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unique_competitors, 2)

    def test_zero_fills_every_year_region_and_event(self):
        records, _coverage = calculate_growth_statistics(
            [], REGIONS, EVENTS, latest_year=2008
        )
        self.assertEqual(value(records, ATTENDANCES, 2007, "07").value, 0)
        popular = value(records, POPULAR_EVENTS, 2008, "01", "222")
        self.assertEqual((popular.value, popular.unique_competitors), (0, 0))

    def test_yoy_percentage_is_unavailable_for_zero_baseline(self):
        self.assertEqual(year_over_year(5, 0), (5, None))
        self.assertEqual(year_over_year(15, 10), (5, 50.0))


if __name__ == "__main__":
    unittest.main()
