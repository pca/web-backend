import unittest

from .classifier import classify_coordinates, microdegrees_to_point


def polygon_feature(region_code, coordinates):
    return {
        "type": "Feature",
        "properties": {"region_code": region_code},
        "geometry": {"type": "Polygon", "coordinates": coordinates},
    }


SQUARE = [[(120, 10), (122, 10), (122, 12), (120, 12), (120, 10)]]


class MicrodegreeConversionTests(unittest.TestCase):
    def test_returns_geojson_longitude_then_latitude(self):
        self.assertEqual(
            microdegrees_to_point(14_599_500, 121_473_700),
            (121.4737, 14.5995),
        )

    def test_rejects_missing_and_out_of_range_coordinates(self):
        self.assertIsNone(microdegrees_to_point(None, 121_000_000))
        self.assertIsNone(microdegrees_to_point(91_000_000, 121_000_000))
        self.assertIsNone(microdegrees_to_point(14_000_000, 181_000_000))


class CoordinateClassificationTests(unittest.TestCase):
    def test_assigns_point_inside_polygon(self):
        assignment = classify_coordinates(
            11_000_000, 121_000_000, [polygon_feature("07", SQUARE)]
        )
        self.assertEqual((assignment.region_code, assignment.status), ("07", "assigned"))

    def test_leaves_missing_invalid_and_outside_points_unassigned(self):
        feature = polygon_feature("07", SQUARE)
        self.assertEqual(
            classify_coordinates(None, 121_000_000, [feature]).status,
            "missing_coordinates",
        )
        self.assertEqual(
            classify_coordinates(91_000_000, 121_000_000, [feature]).status,
            "invalid_coordinates",
        )
        self.assertEqual(
            classify_coordinates(13_000_000, 121_000_000, [feature]).status,
            "outside_boundary",
        )

    def test_leaves_boundary_points_unassigned(self):
        assignment = classify_coordinates(
            11_000_000, 120_000_000, [polygon_feature("07", SQUARE)]
        )
        self.assertEqual((assignment.region_code, assignment.status), (None, "boundary"))

    def test_leaves_overlapping_region_interiors_unassigned(self):
        features = [
            polygon_feature("07", SQUARE),
            polygon_feature("18", [[(120.5, 10.5), (121.5, 10.5), (121.5, 11.5), (120.5, 11.5), (120.5, 10.5)]]),
        ]
        assignment = classify_coordinates(11_000_000, 121_000_000, features)
        self.assertEqual(
            (assignment.region_code, assignment.status), (None, "overlapping_regions")
        )

    def test_ignores_shared_boundaries_between_shapes_in_same_region(self):
        left = [[(120, 10), (121, 10), (121, 12), (120, 12), (120, 10)]]
        right = [[(121, 10), (122, 10), (122, 12), (121, 12), (121, 10)]]
        assignment = classify_coordinates(
            11_000_000,
            121_000_000,
            [polygon_feature("07", left), polygon_feature("07", right)],
        )
        self.assertEqual((assignment.region_code, assignment.status), ("07", "assigned"))

    def test_respects_polygon_holes_and_multipolygons(self):
        polygon_with_hole = [
            SQUARE[0],
            [(120.5, 10.5), (121.5, 10.5), (121.5, 11.5), (120.5, 11.5), (120.5, 10.5)],
        ]
        hole_result = classify_coordinates(
            11_000_000, 121_000_000, [polygon_feature("07", polygon_with_hole)]
        )
        self.assertEqual(hole_result.status, "outside_boundary")

        multipolygon = {
            "type": "Feature",
            "properties": {"region_code": "07"},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [SQUARE, [[(123, 10), (124, 10), (124, 12), (123, 12), (123, 10)]]],
            },
        }
        multi_result = classify_coordinates(
            11_000_000, 123_500_000, [multipolygon]
        )
        self.assertEqual((multi_result.region_code, multi_result.status), ("07", "assigned"))


if __name__ == "__main__":
    unittest.main()
