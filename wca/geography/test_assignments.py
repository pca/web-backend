import unittest
from types import SimpleNamespace

from .assignments import plan_assignments
from .test_classifier import polygon_feature, SQUARE


class AssignmentPlanningTests(unittest.TestCase):
    def setUp(self):
        self.competition = SimpleNamespace(
            id="Sample2026", latitude=11_000_000, longitude=121_000_000
        )
        self.features = (polygon_feature("07", SQUARE),)

    def test_new_assignment_is_planned_and_repeat_is_idempotent(self):
        first = plan_assignments([self.competition], self.features, "v1", {})[0]
        self.assertTrue(first.changed)
        self.assertEqual((first.region_code, first.status), ("07", "assigned"))

        existing = SimpleNamespace(
            boundary_dataset_id="v1",
            region_code="07",
            status="assigned",
            classified_latitude=self.competition.latitude,
            classified_longitude=self.competition.longitude,
        )
        repeated = plan_assignments(
            [self.competition], self.features, "v1", {self.competition.id: existing}
        )[0]
        self.assertFalse(repeated.changed)

    def test_coordinate_or_boundary_version_change_requires_reclassification(self):
        existing = SimpleNamespace(
            boundary_dataset_id="v1",
            region_code="07",
            status="assigned",
            classified_latitude=10_000_000,
            classified_longitude=self.competition.longitude,
        )
        changed_coordinates = plan_assignments(
            [self.competition], self.features, "v1", {self.competition.id: existing}
        )[0]
        changed_boundary = plan_assignments(
            [self.competition], self.features, "v2", {self.competition.id: existing}
        )[0]

        self.assertTrue(changed_coordinates.changed)
        self.assertTrue(changed_boundary.changed)

    def test_unclassifiable_competition_is_retained_in_audit_plan(self):
        self.competition.latitude = None
        plan = plan_assignments([self.competition], self.features, "v1", {})[0]
        self.assertTrue(plan.changed)
        self.assertIsNone(plan.region_code)
        self.assertEqual(plan.status, "missing_coordinates")


if __name__ == "__main__":
    unittest.main()
