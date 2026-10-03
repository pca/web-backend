import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from api.regions import REGION_CHOICES
from .dataset import load_boundary_snapshot


RING = [[120, 10], [122, 10], [122, 12], [120, 12], [120, 10]]
METADATA = {
    "version": "test-v1",
    "source_url": "https://example.org/regions",
    "retrieved_on": "2026-10-03",
    "coordinate_system": "EPSG:4326",
    "license": "Test license",
    "attribution": "Test source",
    "processing_notes": "Test processing",
    "geojson_checksum_sha256": "set-by-fixture",
}


class BoundarySnapshotTests(unittest.TestCase):
    def write_snapshot(self, directory, codes=None, metadata=None):
        codes = codes or [code for code, _label in REGION_CHOICES]
        geojson_path = Path(directory) / "regions.geojson"
        metadata_path = Path(directory) / "regions.metadata.json"
        document = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"region_code": code},
                    "geometry": {"type": "Polygon", "coordinates": [RING]},
                }
                for code in codes
            ],
        }
        geojson_path.write_text(json.dumps(document), encoding="utf-8")
        expected_checksum = hashlib.sha256(geojson_path.read_bytes()).hexdigest()
        effective_metadata = dict(metadata if metadata is not None else METADATA)
        if effective_metadata.get("geojson_checksum_sha256") == "set-by-fixture":
            effective_metadata["geojson_checksum_sha256"] = expected_checksum
        metadata_path.write_text(
            json.dumps(effective_metadata),
            encoding="utf-8",
        )
        return geojson_path, metadata_path

    def test_loads_complete_snapshot_and_computes_file_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            geojson_path, metadata_path = self.write_snapshot(directory)
            result = load_boundary_snapshot(geojson_path, metadata_path)

        self.assertEqual(len(result.features), len(REGION_CHOICES))
        self.assertEqual(result.metadata["version"], "test-v1")
        self.assertEqual(len(result.checksum_sha256), 64)

    def test_rejects_missing_region_and_invalid_coordinates_metadata(self):
        all_codes = [code for code, _label in REGION_CHOICES]
        with tempfile.TemporaryDirectory() as directory:
            geojson_path, metadata_path = self.write_snapshot(
                directory, codes=all_codes[:-1]
            )
            with self.assertRaisesRegex(ValueError, "missing region codes"):
                load_boundary_snapshot(geojson_path, metadata_path)

        with tempfile.TemporaryDirectory() as directory:
            invalid_metadata = dict(METADATA, coordinate_system="EPSG:3857")
            geojson_path, metadata_path = self.write_snapshot(
                directory, metadata=invalid_metadata
            )
            with self.assertRaisesRegex(ValueError, "EPSG:4326"):
                load_boundary_snapshot(geojson_path, metadata_path)

    def test_rejects_unrecognized_region_code(self):
        codes = [code for code, _label in REGION_CHOICES]
        codes[-1] = "99"
        with tempfile.TemporaryDirectory() as directory:
            geojson_path, metadata_path = self.write_snapshot(directory, codes=codes)
            with self.assertRaisesRegex(ValueError, "unknown PCA region code"):
                load_boundary_snapshot(geojson_path, metadata_path)

    def test_rejects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            metadata = dict(METADATA, geojson_checksum_sha256="0" * 64)
            geojson_path, metadata_path = self.write_snapshot(
                directory, metadata=metadata
            )
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_boundary_snapshot(geojson_path, metadata_path)


if __name__ == "__main__":
    unittest.main()
