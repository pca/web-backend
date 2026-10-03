"""Load and validate a versioned regional boundary snapshot."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Tuple

from api.regions import REGION_CHOICES


REQUIRED_METADATA = (
    "version",
    "source_url",
    "retrieved_on",
    "coordinate_system",
    "license",
    "attribution",
    "processing_notes",
    "geojson_checksum_sha256",
)
SUPPORTED_GEOMETRIES = {"Polygon", "MultiPolygon"}


@dataclass(frozen=True)
class BoundarySnapshot:
    features: Tuple[Mapping[str, Any], ...]
    metadata: Mapping[str, Any]
    checksum_sha256: str


def load_boundary_snapshot(geojson_path, metadata_path):
    """Load GeoJSON and provenance, rejecting incomplete or mismatched data."""
    geojson_path = Path(geojson_path)
    metadata_path = Path(metadata_path)
    with geojson_path.open(encoding="utf-8") as source_file:
        document = json.load(source_file)
    with metadata_path.open(encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)

    if document.get("type") != "FeatureCollection":
        raise ValueError("Boundary file must be a GeoJSON FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("Boundary file must contain region features")

    allowed_regions = {code for code, _label in REGION_CHOICES}
    found_regions = set()
    for feature in features:
        properties = feature.get("properties") or {}
        region_code = properties.get("region_code")
        geometry = feature.get("geometry") or {}
        if region_code not in allowed_regions:
            raise ValueError("Boundary feature uses an unknown PCA region code")
        if geometry.get("type") not in SUPPORTED_GEOMETRIES:
            raise ValueError("Boundary features must use Polygon or MultiPolygon")
        if not geometry.get("coordinates"):
            raise ValueError("Boundary feature geometry cannot be empty")
        found_regions.add(region_code)

    missing_regions = allowed_regions - found_regions
    if missing_regions:
        raise ValueError(
            "Boundary file is missing region codes: {}".format(
                ", ".join(sorted(missing_regions))
            )
        )

    missing_metadata = [key for key in REQUIRED_METADATA if not metadata.get(key)]
    if missing_metadata:
        raise ValueError(
            "Boundary metadata is missing: {}".format(", ".join(missing_metadata))
        )
    try:
        date.fromisoformat(metadata["retrieved_on"])
    except (TypeError, ValueError):
        raise ValueError("Boundary metadata retrieved_on must be an ISO date")
    if metadata["coordinate_system"] != "EPSG:4326":
        raise ValueError("Boundary coordinates must use EPSG:4326")

    checksum = hashlib.sha256(geojson_path.read_bytes()).hexdigest()
    if metadata["geojson_checksum_sha256"] != checksum:
        raise ValueError("Boundary GeoJSON checksum does not match its metadata")
    return BoundarySnapshot(tuple(features), metadata, checksum)
