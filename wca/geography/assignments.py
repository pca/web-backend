"""Pure planning helpers for idempotent competition-region assignment."""

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Tuple

from .classifier import classify_coordinates


@dataclass(frozen=True)
class PlannedAssignment:
    competition_id: str
    region_code: Optional[str]
    status: str
    latitude: Optional[int]
    longitude: Optional[int]
    changed: bool


def plan_assignments(
    competitions: Iterable[Any],
    features: Iterable[Mapping[str, Any]],
    boundary_version: str,
    existing_by_competition: Mapping[str, Any],
) -> Tuple[PlannedAssignment, ...]:
    """Classify competitions and identify rows needing an idempotent update."""
    features = tuple(features)
    plans = []
    for competition in competitions:
        result = classify_coordinates(
            competition.latitude, competition.longitude, features
        )
        existing = existing_by_competition.get(competition.id)
        changed = existing is None or any(
            (
                existing.boundary_dataset_id != boundary_version,
                existing.region_code != result.region_code,
                existing.status != result.status,
                existing.classified_latitude != competition.latitude,
                existing.classified_longitude != competition.longitude,
            )
        )
        plans.append(
            PlannedAssignment(
                competition_id=competition.id,
                region_code=result.region_code,
                status=result.status,
                latitude=competition.latitude,
                longitude=competition.longitude,
                changed=changed,
            )
        )
    return tuple(plans)
