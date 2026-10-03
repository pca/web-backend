import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from api.models import StatisticsSnapshot
from wca.geography.dataset import load_boundary_snapshot
from wca.management.commands.assign_competition_regions import (
    DEFAULT_BOUNDARY_PATH,
)
from wca.management.commands.import_wca_data import SUPPORTED_EXPORT_MAJOR
from wca.models import BoundaryDataset


EXPORT_API_URL = "https://www.worldcubeassociation.org/api/v0/export/public"
DEFAULT_DATA_DIRECTORY = Path(settings.BASE_DIR) / "data"
STATE_FILENAME = "imported_wca_metadata.json"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
# The current TSV archive expands to several times its compressed size. This
# conservative check leaves room for both the archive and extracted files.
MINIMUM_FREE_SPACE_MULTIPLIER = 8


def _normalized_timestamp(value):
    value = str(value).strip().replace(" UTC", "+00:00")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _same_export(export_info, imported_state):
    try:
        same_date = _normalized_timestamp(
            export_info["export_date"]
        ) == _normalized_timestamp(imported_state["export_date"])
    except (KeyError, TypeError, ValueError):
        return False
    api_version = str(export_info.get("export_version", "")).lstrip("v")
    imported_version = str(
        imported_state.get("export_format_version", "")
    ).lstrip("v")
    return same_date and api_version == imported_version


def _safe_extract(archive_path, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            try:
                member_path.relative_to(destination)
            except ValueError:
                raise CommandError(
                    "WCA archive contains an unsafe path: {}".format(member.filename)
                )
        archive.extractall(destination)


class Command(BaseCommand):
    help = (
        "Download and import a new WCA v2 export, classify competition regions, "
        "and refresh prepared statistics."
    )

    def add_arguments(self, parser):
        parser.add_argument("--api-url", default=EXPORT_API_URL)
        parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIRECTORY))
        parser.add_argument(
            "--force-download",
            action="store_true",
            help="Download and import even when the export date is unchanged.",
        )

    def handle(self, *args, **options):
        data_directory = Path(options["data_dir"])
        data_directory.mkdir(parents=True, exist_ok=True)
        state_path = data_directory / STATE_FILENAME
        export_info = self._fetch_export_info(options["api_url"])
        imported_state = self._read_state(state_path)

        if (
            not options["force_download"]
            and imported_state
            and _same_export(export_info, imported_state)
        ):
            if self._statistics_are_ready(imported_state):
                self.stdout.write(
                    "Skipped: this WCA export and boundary snapshot are already ready."
                )
                return
            self.stdout.write(
                "WCA data is current; retrying regional classification and statistics."
            )
            self._refresh_statistics(imported_state)
            return

        archive_size = self._validate_export_info(export_info)
        self._check_free_space(data_directory, archive_size)
        archive_path = data_directory / "WCA_export_v2.tsv.zip.part"

        try:
            checksum = self._download_archive(
                export_info["tsv_url"], archive_path, archive_size
            )
            with tempfile.TemporaryDirectory(
                prefix="wca-extract-", dir=data_directory
            ) as extracted_directory:
                _safe_extract(archive_path, extracted_directory)
                metadata = self._validate_archive_metadata(
                    Path(extracted_directory), export_info
                )
                call_command(
                    "import_wca_data",
                    data_dir=extracted_directory,
                    force=True,
                )

            imported_state = dict(metadata)
            imported_state["archive_sha256"] = checksum
            self._write_state(state_path, imported_state)
            self._refresh_statistics(imported_state)
        finally:
            if archive_path.exists():
                archive_path.unlink()

        self.stdout.write(
            self.style.SUCCESS(
                "WCA import, regional classification, and statistics refresh completed."
            )
        )

    def _fetch_export_info(self, api_url):
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            export_info = response.json()
        except (requests.RequestException, ValueError) as error:
            raise CommandError("Unable to read the WCA export API: {}".format(error))
        return export_info

    def _validate_export_info(self, export_info):
        missing = [
            field
            for field in (
                "export_date",
                "export_version",
                "tsv_url",
                "tsv_filesize_bytes",
            )
            if not export_info.get(field)
        ]
        if missing:
            raise CommandError(
                "WCA export API is missing: {}".format(", ".join(missing))
            )
        version = str(export_info["export_version"]).lstrip("v")
        if version.split(".", 1)[0] != SUPPORTED_EXPORT_MAJOR:
            raise CommandError(
                "Unsupported WCA export format {}. Review the importer before syncing."
                .format(export_info["export_version"])
            )
        try:
            archive_size = int(export_info["tsv_filesize_bytes"])
        except (TypeError, ValueError):
            raise CommandError("WCA export API returned an invalid TSV file size.")
        if archive_size <= 0:
            raise CommandError("WCA export API returned an invalid TSV file size.")
        return archive_size

    def _check_free_space(self, data_directory, archive_size):
        free_bytes = shutil.disk_usage(data_directory).free
        required_bytes = archive_size * MINIMUM_FREE_SPACE_MULTIPLIER
        if free_bytes < required_bytes:
            raise CommandError(
                "Not enough free disk space for a safe WCA import: {:.1f} GB free, "
                "about {:.1f} GB required.".format(
                    free_bytes / (1024**3), required_bytes / (1024**3)
                )
            )

    def _download_archive(self, url, destination, expected_size):
        digest = hashlib.sha256()
        downloaded_size = 0
        try:
            with requests.get(url, stream=True, timeout=(30, 300)) as response:
                response.raise_for_status()
                with destination.open("wb") as archive_file:
                    for chunk in response.iter_content(DOWNLOAD_CHUNK_SIZE):
                        if not chunk:
                            continue
                        archive_file.write(chunk)
                        digest.update(chunk)
                        downloaded_size += len(chunk)
        except (OSError, requests.RequestException) as error:
            raise CommandError("Unable to download the WCA TSV export: {}".format(error))
        if downloaded_size != expected_size:
            raise CommandError(
                "WCA TSV download size mismatch: expected {}, received {} bytes."
                .format(expected_size, downloaded_size)
            )
        return digest.hexdigest()

    def _validate_archive_metadata(self, extracted_directory, export_info):
        metadata_path = extracted_directory / "metadata.json"
        try:
            with metadata_path.open(encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
            metadata_date = _normalized_timestamp(metadata["export_date"])
            api_date = _normalized_timestamp(export_info["export_date"])
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise CommandError("Invalid WCA archive metadata: {}".format(error))
        archive_version = str(metadata.get("export_format_version", "")).lstrip("v")
        api_version = str(export_info["export_version"]).lstrip("v")
        if metadata_date != api_date or archive_version != api_version:
            raise CommandError("Downloaded WCA archive does not match the export API.")
        return metadata

    def _refresh_statistics(self, imported_state):
        checksum = imported_state.get("archive_sha256")
        if not checksum or len(checksum) != 64:
            raise CommandError(
                "Imported WCA state has no valid archive checksum for statistics."
            )
        call_command("assign_competition_regions", apply=True)
        snapshot = load_boundary_snapshot(
            DEFAULT_BOUNDARY_PATH,
            DEFAULT_BOUNDARY_PATH.with_name("philippines-regions.metadata.json"),
        )
        call_command(
            "build_statistics_snapshot",
            export_version="{}:{}".format(
                imported_state["export_format_version"],
                imported_state["export_date"],
            ),
            export_checksum=checksum,
            boundary_version=snapshot.metadata["version"],
        )

    def _statistics_are_ready(self, imported_state):
        checksum = imported_state.get("archive_sha256")
        if not checksum:
            return False
        try:
            snapshot = load_boundary_snapshot(
                DEFAULT_BOUNDARY_PATH,
                DEFAULT_BOUNDARY_PATH.with_name("philippines-regions.metadata.json"),
            )
            boundary_dataset = BoundaryDataset.objects.get(
                version=snapshot.metadata["version"]
            )
        except (OSError, ValueError, json.JSONDecodeError, BoundaryDataset.DoesNotExist):
            return False
        return StatisticsSnapshot.objects.filter(
            export_checksum=checksum,
            boundary_dataset=boundary_dataset,
            status=StatisticsSnapshot.STATUS_READY,
        ).exists()

    @staticmethod
    def _read_state(state_path):
        if not state_path.is_file():
            return None
        try:
            with state_path.open(encoding="utf-8") as state_file:
                return json.load(state_file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError("Unable to read prior WCA import state: {}".format(error))

    @staticmethod
    def _write_state(state_path, state):
        temporary_path = state_path.with_suffix(".json.tmp")
        with temporary_path.open("w", encoding="utf-8") as state_file:
            json.dump(state, state_file, indent=2, sort_keys=True)
            state_file.write("\n")
        temporary_path.replace(state_path)
