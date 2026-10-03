from pathlib import Path

from django.conf import settings

from .classifier import classify_coordinates
from .dataset import load_boundary_snapshot


BOUNDARY_DIRECTORY = (
    Path(settings.BASE_DIR) / "wca" / "geography" / "boundaries"
)


def test_current_snapshot_contains_all_regions_and_expected_checksum():
    snapshot = load_boundary_snapshot(
        BOUNDARY_DIRECTORY / "philippines-regions.geojson",
        BOUNDARY_DIRECTORY / "philippines-regions.metadata.json",
    )

    assert len(snapshot.features) == 18
    assert snapshot.checksum_sha256 == (
        "573fe398479e114de0738e6614a9889f99726e302c3c7c47b879a83005eed709"
    )


def test_current_snapshot_classifies_sample_cities_across_island_groups():
    snapshot = load_boundary_snapshot(
        BOUNDARY_DIRECTORY / "philippines-regions.geojson",
        BOUNDARY_DIRECTORY / "philippines-regions.metadata.json",
    )
    samples = {
        "Manila": (14_599_500, 120_984_200, "NCR"),
        "Baguio": (16_402_300, 120_596_000, "CAR"),
        "Iloilo": (10_720_200, 122_562_100, "06"),
        "Cebu": (10_315_700, 123_885_400, "07"),
        "Bacolod": (10_676_500, 122_950_900, "18"),
        "Dumaguete": (9_306_800, 123_305_400, "18"),
        "Davao": (7_190_700, 125_455_300, "11"),
    }

    for city, (latitude, longitude, expected_region) in samples.items():
        assignment = classify_coordinates(latitude, longitude, snapshot.features)
        assert assignment.status == "assigned", city
        assert assignment.region_code == expected_region, city
