import unittest

from .regional_strength import (
    EventStrength,
    RankedCompetitor,
    calculate_event_strength,
    order_best_events,
)


REGIONS = (("01", "Region I"), ("07", "Region VII"), ("18", "Region XVIII"))


def competitor(wca_id, region_code, rank, name=None):
    return RankedCompetitor(wca_id, name or wca_id, region_code, rank)


class RegionalStrengthTests(unittest.TestCase):
    def test_all_regions_receive_exactly_five_slots_and_missing_penalties(self):
        results = calculate_event_strength(
            [
                competitor("A", "01", 1),
                competitor("B", "01", 5),
                competitor("C", "01", 9),
            ],
            REGIONS,
            worst_national_rank=100,
        )
        by_region = {result.region_code: result for result in results}

        self.assertEqual(len(by_region), 3)
        self.assertEqual(len(by_region["01"].slots), 5)
        self.assertEqual(by_region["01"].score, 215)
        self.assertEqual(by_region["01"].contributor_count, 3)
        self.assertEqual(
            [slot.is_penalty for slot in by_region["01"].slots],
            [False, False, False, True, True],
        )
        self.assertEqual(by_region["07"].score, 500)
        self.assertTrue(all(slot.is_penalty for slot in by_region["07"].slots))

    def test_uses_only_five_best_and_selects_fifth_place_tie_by_wca_id(self):
        results = calculate_event_strength(
            [
                competitor("FIRST", "01", 1),
                competitor("SECOND", "01", 2),
                competitor("THIRD", "01", 3),
                competitor("FOURTH", "01", 4),
                competitor("ZZZZ2026", "01", 5),
                competitor("AAAA2026", "01", 5),
                competitor("SIXTH", "01", 6),
            ],
            REGIONS,
            worst_national_rank=100,
        )
        region = next(result for result in results if result.region_code == "01")

        self.assertEqual(region.score, 15)
        self.assertEqual(
            [slot.wca_id for slot in region.slots],
            ["FIRST", "SECOND", "THIRD", "FOURTH", "AAAA2026"],
        )

    def test_equal_scores_use_standard_competition_ranking(self):
        entries = []
        for region_code, ranks in (
            ("01", (1, 2, 3, 4, 5)),
            ("07", (1, 2, 3, 4, 5)),
            ("18", (2, 3, 4, 5, 6)),
        ):
            entries.extend(
                competitor("{}-{}".format(region_code, index), region_code, rank)
                for index, rank in enumerate(ranks)
            )

        results = calculate_event_strength(entries, REGIONS, worst_national_rank=100)
        self.assertEqual(
            [(result.region_code, result.score, result.placement) for result in results],
            [("01", 15, 1), ("07", 15, 1), ("18", 20, 3)],
        )

    def test_duplicate_wca_id_is_not_counted_twice(self):
        results = calculate_event_strength(
            [competitor("A", "01", 1), competitor("A", "01", 1)],
            REGIONS,
            worst_national_rank=10,
        )
        region = next(result for result in results if result.region_code == "01")
        self.assertEqual(region.contributor_count, 1)
        self.assertEqual(region.score, 41)

    def test_rejects_invalid_or_inconsistent_rank_data(self):
        with self.assertRaisesRegex(ValueError, "positive integers"):
            calculate_event_strength(
                [competitor("A", "01", 0)], REGIONS, worst_national_rank=10
            )
        with self.assertRaisesRegex(ValueError, "unknown region"):
            calculate_event_strength(
                [competitor("A", "99", 1)], REGIONS, worst_national_rank=10
            )
        with self.assertRaisesRegex(ValueError, "exceed"):
            calculate_event_strength(
                [competitor("A", "01", 11)], REGIONS, worst_national_rank=10
            )

    def test_best_events_order_uses_placement_then_official_order(self):
        first, second, third = calculate_event_strength(
            [competitor("A", "01", 1)], REGIONS, worst_national_rank=10
        )
        events = [
            EventStrength("333", "3x3x3 Cube", 10, second),
            EventStrength("222", "2x2x2 Cube", 20, first),
            EventStrength("444", "4x4x4 Cube", 30, third),
        ]

        ordered = order_best_events(events)
        self.assertEqual([event.event_id for event in ordered], ["222", "333", "444"])


if __name__ == "__main__":
    unittest.main()
