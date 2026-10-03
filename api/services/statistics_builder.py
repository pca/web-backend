"""Compose all prepared-statistics sections for one staging snapshot."""

from .regional_growth_data import build_growth_records
from .regional_strength_data import build_regional_strength_records


def build_all_statistics(snapshot):
    return {
        "regional_strength": build_regional_strength_records(snapshot),
        "growth": build_growth_records(snapshot),
    }
