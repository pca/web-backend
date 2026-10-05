from datetime import date

import pytest

from api.models import GrowthAnnualRecord, StatisticsSnapshot
from api.services.snapshot_records import sync_snapshot_records
from wca.models import BoundaryDataset


def growth_record(snapshot, *, year, value, content_hash, region_code=""):
    return GrowthAnnualRecord(
        snapshot=snapshot,
        metric=GrowthAnnualRecord.METRIC_ATTENDANCES,
        year=year,
        region_code=region_code,
        event_id="",
        value=value,
        content_hash=content_hash,
    )


@pytest.mark.django_db
def test_sync_snapshot_records_writes_only_changed_rows_and_removes_stale_rows():
    boundary = BoundaryDataset.objects.create(
        version="sync-test-boundaries",
        source_url="https://example.test/boundaries",
        retrieved_on=date(2026, 10, 4),
        license="Test",
        processing_notes="Test",
        checksum_sha256="a" * 64,
        feature_count=18,
    )
    snapshot = StatisticsSnapshot.objects.create(
        export_version="test-export",
        export_checksum="b" * 64,
        boundary_dataset=boundary,
        latest_year=2026,
    )
    unchanged = growth_record(
        snapshot, year=2024, value=10, content_hash="1" * 64
    )
    changed = growth_record(snapshot, year=2025, value=20, content_hash="2" * 64)
    stale = growth_record(snapshot, year=2023, value=5, content_hash="3" * 64)
    GrowthAnnualRecord.objects.bulk_create([unchanged, changed, stale])
    original_ids = {
        record.year: record.pk
        for record in GrowthAnnualRecord.objects.filter(snapshot=snapshot)
    }

    counts = sync_snapshot_records(
        model=GrowthAnnualRecord,
        snapshot=snapshot,
        desired_records=[
            growth_record(snapshot, year=2024, value=10, content_hash="1" * 64),
            growth_record(snapshot, year=2025, value=25, content_hash="4" * 64),
            growth_record(snapshot, year=2026, value=30, content_hash="5" * 64),
        ],
        key_fields=("metric", "year", "region_code", "event_id"),
        update_fields=("value", "unique_competitors"),
        batch_size=100,
    )

    rows = {
        record.year: record
        for record in GrowthAnnualRecord.objects.filter(snapshot=snapshot)
    }
    assert counts == {"created": 1, "updated": 1, "unchanged": 1, "deleted": 1}
    assert set(rows) == {2024, 2025, 2026}
    assert rows[2024].pk == original_ids[2024]
    assert rows[2025].pk == original_ids[2025]
    assert rows[2025].value == 25
    assert rows[2025].content_hash == "4" * 64


@pytest.mark.django_db
def test_sync_snapshot_records_rejects_duplicate_desired_keys():
    boundary = BoundaryDataset.objects.create(
        version="duplicate-test-boundaries",
        source_url="https://example.test/boundaries",
        retrieved_on=date(2026, 10, 4),
        license="Test",
        processing_notes="Test",
        checksum_sha256="c" * 64,
        feature_count=18,
    )
    snapshot = StatisticsSnapshot.objects.create(
        export_version="duplicate-test-export",
        export_checksum="d" * 64,
        boundary_dataset=boundary,
        latest_year=2026,
    )
    duplicate = growth_record(snapshot, year=2026, value=1, content_hash="e" * 64)

    with pytest.raises(ValueError, match="duplicate key"):
        sync_snapshot_records(
            model=GrowthAnnualRecord,
            snapshot=snapshot,
            desired_records=[duplicate, duplicate],
            key_fields=("metric", "year", "region_code", "event_id"),
            update_fields=("value", "unique_competitors"),
            batch_size=100,
        )
