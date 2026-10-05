"""Versioned statistics-snapshot lifecycle and atomic activation."""

from django.db import transaction
from django.utils import timezone

from api.models import StatisticsSnapshot


class SnapshotBuildSkipped(Exception):
    """Internal signal used only when callers need explicit skip control."""


def build_and_activate_snapshot(
    *,
    export_version,
    export_checksum,
    boundary_dataset,
    latest_year,
    builder,
):
    """Build one input version and atomically replace the active snapshot.

    ``builder`` receives the staging snapshot and returns coverage metadata.
    An already-ready snapshot for the same export and boundary is returned
    unchanged. Failed builds retain the previously active snapshot.
    """
    with transaction.atomic():
        snapshot = (
            StatisticsSnapshot.objects.select_for_update()
            .filter(
                export_checksum=export_checksum,
                boundary_dataset=boundary_dataset,
            )
            .first()
        )
        if snapshot and snapshot.status == StatisticsSnapshot.STATUS_READY:
            return snapshot, False
        if snapshot is None:
            snapshot = StatisticsSnapshot.objects.create(
                export_version=export_version,
                export_checksum=export_checksum,
                boundary_dataset=boundary_dataset,
                latest_year=latest_year,
            )
        else:
            snapshot.export_version = export_version
            snapshot.latest_year = latest_year
            snapshot.status = StatisticsSnapshot.STATUS_BUILDING
            snapshot.is_active = False
            snapshot.coverage = {}
            snapshot.error_message = ""
            snapshot.completed_at = None
            snapshot.activated_at = None
            snapshot.save(
                update_fields=(
                    "export_version",
                    "latest_year",
                    "status",
                    "is_active",
                    "coverage",
                    "error_message",
                    "completed_at",
                    "activated_at",
                )
            )

    try:
        with transaction.atomic():
            snapshot = StatisticsSnapshot.objects.select_for_update().get(
                pk=snapshot.pk
            )
            coverage = builder(snapshot) or {}
            now = timezone.now()
            snapshot.status = StatisticsSnapshot.STATUS_READY
            snapshot.coverage = coverage
            snapshot.error_message = ""
            snapshot.completed_at = now

            StatisticsSnapshot.objects.filter(is_active=True).exclude(
                pk=snapshot.pk
            ).update(is_active=False)
            snapshot.is_active = True
            snapshot.activated_at = now
            snapshot.save(
                update_fields=(
                    "status",
                    "coverage",
                    "error_message",
                    "completed_at",
                    "is_active",
                    "activated_at",
                )
            )
    except Exception as error:
        StatisticsSnapshot.objects.filter(pk=snapshot.pk).update(
            status=StatisticsSnapshot.STATUS_FAILED,
            is_active=False,
            error_message=str(error),
            completed_at=timezone.now(),
        )
        raise

    return snapshot, True
