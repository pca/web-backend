"""Deterministic point-in-polygon classification for competition venues.

The functions in this module deliberately have no Django or third-party GIS
dependency so the geometry rules can be tested independently of the database.
GeoJSON coordinates are longitude first, latitude second.
"""

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple


COORDINATE_SCALE = 1_000_000
_BOUNDARY_EPSILON = 1e-12
_BOUNDARY_PROBE_DISTANCE = 1e-7

INSIDE = "inside"
OUTSIDE = "outside"
BOUNDARY = "boundary"


@dataclass(frozen=True)
class CoordinateAssignment:
    region_code: Optional[str]
    status: str


def microdegrees_to_point(
    latitude_microdegrees: Optional[int], longitude_microdegrees: Optional[int]
) -> Optional[Tuple[float, float]]:
    """Return a valid GeoJSON point (longitude, latitude), or None."""
    if latitude_microdegrees is None or longitude_microdegrees is None:
        return None

    latitude = latitude_microdegrees / COORDINATE_SCALE
    longitude = longitude_microdegrees / COORDINATE_SCALE
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None

    return longitude, latitude


def _point_on_segment(point, start, end):
    x, y = point
    x1, y1 = start
    x2, y2 = end
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > _BOUNDARY_EPSILON:
        return False
    return (
        min(x1, x2) - _BOUNDARY_EPSILON <= x <= max(x1, x2) + _BOUNDARY_EPSILON
        and min(y1, y2) - _BOUNDARY_EPSILON <= y <= max(y1, y2) + _BOUNDARY_EPSILON
    )


def _ring_relation(point, ring):
    if len(ring) < 4:
        raise ValueError("GeoJSON polygon rings must contain at least four points")

    inside = False
    previous = ring[-1]
    for current in ring:
        if _point_on_segment(point, previous, current):
            return BOUNDARY

        x, y = point
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            intersection_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if intersection_x > x:
                inside = not inside
        previous = current

    return INSIDE if inside else OUTSIDE


def _polygon_relation(point, rings):
    if not rings:
        raise ValueError("GeoJSON polygons must contain an exterior ring")

    exterior = _ring_relation(point, rings[0])
    if exterior != INSIDE:
        return exterior

    for hole in rings[1:]:
        relation = _ring_relation(point, hole)
        if relation == BOUNDARY:
            return BOUNDARY
        if relation == INSIDE:
            return OUTSIDE

    return INSIDE


def _geometry_relation(point, geometry):
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Polygon":
        return _polygon_relation(point, coordinates)
    if geometry_type == "MultiPolygon":
        relations = [_polygon_relation(point, polygon) for polygon in coordinates]
        if INSIDE in relations:
            return INSIDE
        if BOUNDARY in relations:
            return BOUNDARY
        return OUTSIDE

    raise ValueError("Only Polygon and MultiPolygon GeoJSON geometries are supported")


def _region_relation(point, geometries):
    """Classify a point against the union of all shapes for one region."""
    relations = [_geometry_relation(point, geometry) for geometry in geometries]
    if INSIDE in relations:
        return INSIDE
    if BOUNDARY not in relations:
        return OUTSIDE

    # A border shared by adjacent province polygons is internal to the region.
    # Probe a small neighborhood and only treat it as interior when every
    # direction is covered by one of that region's polygons. True regional
    # boundaries, polygon vertices, and small data gaps remain unassigned.
    for step in range(16):
        angle = step * (2 * math.pi / 16)
        probe = (
            point[0] + _BOUNDARY_PROBE_DISTANCE * math.cos(angle),
            point[1] + _BOUNDARY_PROBE_DISTANCE * math.sin(angle),
        )
        if not any(
            _geometry_relation(probe, geometry) != OUTSIDE for geometry in geometries
        ):
            return BOUNDARY
    return INSIDE


def classify_coordinates(
    latitude_microdegrees: Optional[int],
    longitude_microdegrees: Optional[int],
    region_features: Iterable[Mapping[str, Any]],
) -> CoordinateAssignment:
    """Classify WCA microdegree coordinates against region GeoJSON features.

    Each feature must have ``properties.region_code`` and a Polygon or
    MultiPolygon ``geometry``. Multiple features may describe one region (for
    example, separate province polygons). Boundary and cross-region overlap
    cases remain explicitly unassigned for audit rather than being guessed.
    """
    if latitude_microdegrees is None or longitude_microdegrees is None:
        return CoordinateAssignment(None, "missing_coordinates")

    point = microdegrees_to_point(latitude_microdegrees, longitude_microdegrees)
    if point is None:
        return CoordinateAssignment(None, "invalid_coordinates")

    region_geometries = defaultdict(list)
    for feature in region_features:
        properties = feature.get("properties") or {}
        region_code = properties.get("region_code")
        geometry = feature.get("geometry")
        if not region_code or not geometry:
            raise ValueError("Boundary features require region_code and geometry")
        region_geometries[region_code].append(geometry)

    region_relations = {
        region_code: _region_relation(point, geometries)
        for region_code, geometries in region_geometries.items()
    }

    interior_regions = {
        region_code
        for region_code, relation in region_relations.items()
        if relation == INSIDE
    }
    boundary_regions = {
        region_code
        for region_code, relation in region_relations.items()
        if relation == BOUNDARY
    }

    if len(interior_regions) > 1:
        return CoordinateAssignment(None, "overlapping_regions")

    if len(interior_regions) == 1:
        region_code = next(iter(interior_regions))
        if boundary_regions - {region_code}:
            return CoordinateAssignment(None, "overlapping_regions")
        return CoordinateAssignment(region_code, "assigned")

    if boundary_regions:
        return CoordinateAssignment(None, "boundary")

    return CoordinateAssignment(None, "outside_boundary")
