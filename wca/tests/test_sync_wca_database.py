import hashlib
import json
import zipfile
from io import BytesIO, StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command as django_call_command
from django.core.management.base import CommandError

from wca.management.commands import sync_wca_database


EXPORT_INFO = {
    "export_date": "2026-10-03T00:00:28Z",
    "export_version": "v2.0.2",
    "tsv_url": "https://example.test/WCA_export_v2.tsv.zip",
    "tsv_filesize_bytes": 123,
}
ARCHIVE_METADATA = {
    "export_date": "2026-10-03 00:00:28 UTC",
    "export_format_version": "2.0.2",
}


def make_archive_bytes(metadata=None):
    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(
            "metadata.json", json.dumps(metadata or ARCHIVE_METADATA)
        )
    return archive_buffer.getvalue()


def test_same_export_accepts_equivalent_utc_date_formats():
    state = dict(ARCHIVE_METADATA, archive_sha256="a" * 64)
    assert sync_wca_database._same_export(EXPORT_INFO, state)


def test_safe_extract_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")

    with pytest.raises(CommandError, match="unsafe path"):
        sync_wca_database._safe_extract(archive_path, tmp_path / "extract")


@pytest.mark.django_db
def test_new_export_imports_then_refreshes_statistics(tmp_path, monkeypatch):
    archive_bytes = make_archive_bytes()
    archive_checksum = hashlib.sha256(archive_bytes).hexdigest()
    imported_calls = []
    refreshed_states = []

    monkeypatch.setattr(
        sync_wca_database.Command,
        "_fetch_export_info",
        lambda self, _url: dict(EXPORT_INFO),
    )
    monkeypatch.setattr(
        sync_wca_database.Command,
        "_check_free_space",
        lambda self, _directory, _size: None,
    )

    def download(_self, _url, destination, _expected_size):
        destination.write_bytes(archive_bytes)
        return archive_checksum

    monkeypatch.setattr(sync_wca_database.Command, "_download_archive", download)
    monkeypatch.setattr(
        sync_wca_database.Command,
        "_refresh_statistics",
        lambda self, state: refreshed_states.append(state),
    )
    monkeypatch.setattr(
        sync_wca_database,
        "call_command",
        lambda name, **options: imported_calls.append((name, options)),
    )

    django_call_command("sync_wca_database", data_dir=str(tmp_path))

    assert imported_calls[0][0] == "import_wca_data"
    assert imported_calls[0][1]["force"] is True
    assert refreshed_states[0]["archive_sha256"] == archive_checksum
    persisted_state = json.loads(
        (tmp_path / sync_wca_database.STATE_FILENAME).read_text(encoding="utf-8")
    )
    assert persisted_state == refreshed_states[0]
    assert not (tmp_path / "WCA_export_v2.tsv.zip.part").exists()


@pytest.mark.django_db
def test_current_export_retries_only_missing_statistics(tmp_path, monkeypatch):
    state = dict(ARCHIVE_METADATA, archive_sha256="b" * 64)
    (tmp_path / sync_wca_database.STATE_FILENAME).write_text(
        json.dumps(state), encoding="utf-8"
    )
    refreshed_states = []

    monkeypatch.setattr(
        sync_wca_database.Command,
        "_fetch_export_info",
        lambda self, _url: dict(EXPORT_INFO),
    )
    monkeypatch.setattr(
        sync_wca_database.Command,
        "_statistics_are_ready",
        lambda self, _state: False,
    )
    monkeypatch.setattr(
        sync_wca_database.Command,
        "_refresh_statistics",
        lambda self, current_state: refreshed_states.append(current_state),
    )
    monkeypatch.setattr(
        sync_wca_database.Command,
        "_download_archive",
        lambda *args, **kwargs: pytest.fail("current export must not redownload"),
    )

    django_call_command("sync_wca_database", data_dir=str(tmp_path))

    assert refreshed_states == [state]


def test_free_space_guard_reports_required_capacity(tmp_path, monkeypatch):
    command = sync_wca_database.Command()
    monkeypatch.setattr(
        sync_wca_database.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=100),
    )

    with pytest.raises(CommandError, match="Not enough free disk space"):
        command._check_free_space(tmp_path, archive_size=100)


def test_refresh_runs_classification_before_snapshot(monkeypatch):
    command = sync_wca_database.Command()
    calls = []
    monkeypatch.setattr(
        sync_wca_database,
        "call_command",
        lambda name, **options: calls.append((name, options)),
    )

    command._refresh_statistics(
        dict(ARCHIVE_METADATA, archive_sha256="c" * 64)
    )

    assert calls[0] == ("assign_competition_regions", {"apply": True})
    assert calls[1][0] == "build_statistics_snapshot"
    assert calls[1][1]["export_checksum"] == "c" * 64
    assert calls[1][1]["boundary_version"] == (
        "geoph-1.0-current-2024-135776d2"
    )
