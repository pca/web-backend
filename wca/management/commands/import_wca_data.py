import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wca.models import (
    Championship,
    Competition,
    Continent,
    Country,
    Event,
    Format,
    Person,
    RanksAverage,
    RanksSingle,
    Result,
    RoundType,
)

log = logging.getLogger(__name__)

PH_ID = "Philippines"
DUMP_DIR = Path(settings.BASE_DIR) / "data" / "extracted"
SUPPORTED_EXPORT_MAJOR = "2"
READ_CHUNK_SIZE = 100_000
WRITE_BATCH_SIZE = 2_000

EXPORT_FILES = {
    "continents": "WCA_export_continents.tsv",
    "countries": "WCA_export_countries.tsv",
    "events": "WCA_export_events.tsv",
    "formats": "WCA_export_formats.tsv",
    "round_types": "WCA_export_round_types.tsv",
    "competitions": "WCA_export_competitions.tsv",
    "persons": "WCA_export_persons.tsv",
    "ranks_average": "WCA_export_ranks_average.tsv",
    "ranks_single": "WCA_export_ranks_single.tsv",
    "results": "WCA_export_results.tsv",
    "result_attempts": "WCA_export_result_attempts.tsv",
    "championships": "WCA_export_championships.tsv",
}


def _clean(value):
    """Convert pandas/numpy empty values into ordinary Python values."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _optional_int(value):
    value = _clean(value)
    return None if value in (None, "") else int(value)


def _text(value):
    value = _clean(value)
    return None if value in (None, "") else str(value)


def _batches(values, batch_size):
    values = list(values)
    for index in range(0, len(values), batch_size):
        yield values[index : index + batch_size]


class Command(BaseCommand):
    help = "Import the WCA v2 public results export"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dump_dir = DUMP_DIR
        self._philippine_person_ids = None

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Import even when this exact export was already imported.",
        )
        parser.add_argument(
            "--step",
            type=int,
            default=1,
            help="Starting import step, for resuming a previously interrupted import.",
        )
        parser.add_argument(
            "--data-dir",
            default=str(DUMP_DIR),
            help="Directory containing the extracted WCA v2 TSV files.",
        )

    def handle(self, *args, **options):
        self.dump_dir = Path(options["data_dir"])
        self._philippine_person_ids = None
        metadata = self.load_and_validate_metadata()
        imported_metadata_path = self.dump_dir / "imported_metadata.json"

        if not options["force"] and imported_metadata_path.is_file():
            with imported_metadata_path.open(encoding="utf-8") as metadata_file:
                imported_metadata = json.load(metadata_file)
            if self._same_export(metadata, imported_metadata):
                self.stdout.write("Skipped: this WCA export is already imported.")
                return

        self.start_import(options["step"])
        self._write_imported_metadata(metadata, imported_metadata_path)
        self.stdout.write(self.style.SUCCESS("WCA data import successful."))

    def load_and_validate_metadata(self):
        metadata_path = self.dump_dir / "metadata.json"
        try:
            with metadata_path.open(encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError("Unable to read WCA export metadata: {}".format(error))

        version = str(metadata.get("export_format_version", "")).lstrip("v")
        if not metadata.get("export_date") or not version:
            raise CommandError(
                "WCA metadata must contain export_date and export_format_version."
            )
        if version.split(".", 1)[0] != SUPPORTED_EXPORT_MAJOR:
            raise CommandError(
                "Unsupported WCA export format {}. This importer supports major version {}."
                .format(version, SUPPORTED_EXPORT_MAJOR)
            )

        missing_files = [
            filename
            for filename in EXPORT_FILES.values()
            if not (self.dump_dir / filename).is_file()
        ]
        if missing_files:
            raise CommandError(
                "WCA export is missing required file(s): {}".format(
                    ", ".join(sorted(missing_files))
                )
            )
        return metadata

    @staticmethod
    def _same_export(metadata, imported_metadata):
        return (
            metadata.get("export_date") == imported_metadata.get("export_date")
            and metadata.get("export_format_version")
            == imported_metadata.get("export_format_version")
        )

    @staticmethod
    def _write_imported_metadata(metadata, destination):
        temporary_path = destination.with_suffix(".json.tmp")
        with temporary_path.open("w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=2, sort_keys=True)
            metadata_file.write("\n")
        temporary_path.replace(destination)

    def export_path(self, table_name):
        return self.dump_dir / EXPORT_FILES[table_name]

    def read_table(self, table_name, **kwargs):
        return pd.read_csv(
            self.export_path(table_name),
            sep="\t",
            low_memory=False,
            **kwargs,
        )

    def start_import(self, step=1):
        steps = [
            self.import_continents,
            self.import_countries,
            self.import_events,
            self.import_formats,
            self.import_round_types,
            self.import_competitions,
            self.import_persons,
            self.import_ranks_average,
            self.import_ranks_single,
            self.import_results,
            self.import_championships,
        ]
        if step < 1 or step > len(steps):
            raise CommandError("--step must be between 1 and {}.".format(len(steps)))
        for step_func in steps[step - 1 :]:
            step_func()

    @transaction.atomic
    def import_continents(self):
        log.info("  importing continents")
        for row in self.read_table("continents").itertuples(index=False):
            Continent.objects.update_or_create(
                id=row.id,
                defaults={
                    "name": row.name,
                    "record_name": _text(row.record_name),
                    "latitude": None,
                    "longitude": None,
                    "zoom": None,
                },
            )

    @transaction.atomic
    def import_countries(self):
        log.info("  importing countries")
        for row in self.read_table("countries").itertuples(index=False):
            Country.objects.update_or_create(
                id=row.id,
                defaults={
                    "name": row.name,
                    "continent_id": _text(row.continent_id),
                    "iso2": _text(row.iso2),
                },
            )

    @transaction.atomic
    def import_events(self):
        log.info("  importing events")
        for row in self.read_table("events").itertuples(index=False):
            Event.objects.update_or_create(
                id=row.id,
                defaults={
                    "name": row.name,
                    "rank": int(row.rank),
                    "format": row.format,
                    # cell_name was removed in v2. The ordinary event name is
                    # the closest compatible value for the existing frontend.
                    "cell_name": row.name,
                },
            )

    @transaction.atomic
    def import_formats(self):
        log.info("  importing formats")
        for row in self.read_table("formats").itertuples(index=False):
            Format.objects.update_or_create(
                id=row.id,
                defaults={
                    "name": row.name,
                    "sort_by": row.sort_by,
                    "sort_by_second": row.sort_by_second,
                    "expected_solve_count": int(row.expected_solve_count),
                    "trim_fastest_n": int(row.trim_fastest_n),
                    "trim_slowest_n": int(row.trim_slowest_n),
                },
            )

    @transaction.atomic
    def import_round_types(self):
        log.info("  importing round types")
        for row in self.read_table("round_types").itertuples(index=False):
            RoundType.objects.update_or_create(
                id=row.id,
                defaults={
                    "rank": int(row.rank),
                    "name": row.name,
                    "cell_name": row.cell_name,
                    "final": int(row.final),
                },
            )

    def import_competitions(self):
        log.info("  importing competitions")
        rows = self.read_table("competitions")
        chunk_count = max(1, (len(rows) + WRITE_BATCH_SIZE - 1) // WRITE_BATCH_SIZE)
        for chunk_number, group in enumerate(
            np.array_split(rows, chunk_count), start=1
        ):
            log.info("  importing competitions chunk %s", chunk_number)
            with transaction.atomic():
                for row in group.itertuples(index=False):
                    Competition.objects.update_or_create(
                        id=row.id,
                        defaults={
                            "name": row.name,
                            "city_name": row.city_name,
                            "country_id": row.country_id,
                            "information": _text(row.information),
                            "year": int(row.year),
                            "month": int(row.month),
                            "day": int(row.day),
                            "end_month": int(row.end_month),
                            "end_day": int(row.end_day),
                            "event_specs": _text(row.event_specs),
                            "wca_delegate": _text(row.delegates),
                            "organizer": _text(row.organizers),
                            "venue": _text(row.venue),
                            "venue_address": _text(row.venue_address),
                            "venue_details": _text(row.venue_details),
                            "external_website": _text(row.external_website),
                            "cell_name": row.cell_name,
                            "latitude": _optional_int(row.latitude_microdegrees),
                            "longitude": _optional_int(row.longitude_microdegrees),
                        },
                    )

    def iter_philippine_person_chunks(self):
        columns = ["name", "gender", "wca_id", "sub_id", "country_id"]
        for chunk in self.read_table(
            "persons",
            usecols=columns,
            dtype={"wca_id": str, "country_id": str},
            chunksize=READ_CHUNK_SIZE,
        ):
            yield chunk[chunk["country_id"] == PH_ID]

    def get_philippine_person_ids(self):
        if self._philippine_person_ids is None:
            self._philippine_person_ids = {
                str(wca_id)
                for chunk in self.iter_philippine_person_chunks()
                for wca_id in chunk["wca_id"]
            }
        return self._philippine_person_ids

    @transaction.atomic
    def import_persons(self):
        log.info("  importing Philippine persons")
        for chunk in self.iter_philippine_person_chunks():
            for row in chunk.itertuples(index=False):
                Person.objects.update_or_create(
                    id=row.wca_id,
                    defaults={
                        "subid": int(row.sub_id),
                        "name": _text(row.name),
                        "country_id": row.country_id,
                        "gender": _text(row.gender),
                    },
                )

    def _import_ranks(self, table_name, model):
        person_ids = self.get_philippine_person_ids()
        with transaction.atomic():
            model.objects.all().delete()
            for chunk in self.read_table(
                table_name,
                dtype={"person_id": str, "event_id": str},
                chunksize=READ_CHUNK_SIZE,
            ):
                philippine_rows = chunk[chunk["person_id"].isin(person_ids)]
                records = [
                    model(
                        person_id=row.person_id,
                        event_id=row.event_id,
                        best=int(row.best),
                        world_rank=int(row.world_rank),
                        continent_rank=int(row.continent_rank),
                        country_rank=int(row.country_rank),
                    )
                    for row in philippine_rows.itertuples(index=False)
                ]
                if records:
                    model.objects.bulk_create(records, batch_size=WRITE_BATCH_SIZE)

    def import_ranks_average(self):
        log.info("  importing Philippine average ranks")
        self._import_ranks("ranks_average", RanksAverage)

    def import_ranks_single(self):
        log.info("  importing Philippine single ranks")
        self._import_ranks("ranks_single", RanksSingle)

    @transaction.atomic
    def import_results(self):
        """Import Philippine results, then attach attempts from the v2 join table."""
        log.info("  importing Philippine results")
        Result.objects.all().delete()
        selected_result_ids = set()

        for chunk_number, chunk in enumerate(
            self.read_table(
                "results",
                dtype={
                    "competition_id": str,
                    "event_id": str,
                    "round_type_id": str,
                    "person_id": str,
                    "person_country_id": str,
                    "format_id": str,
                },
                chunksize=READ_CHUNK_SIZE,
            ),
            start=1,
        ):
            philippine_rows = chunk[chunk["person_country_id"] == PH_ID]
            records = []
            for row in philippine_rows.itertuples(index=False):
                wca_result_id = int(row.id)
                selected_result_ids.add(wca_result_id)
                records.append(
                    Result(
                        wca_result_id=wca_result_id,
                        competition_id=row.competition_id,
                        event_id=row.event_id,
                        round_type_id=row.round_type_id,
                        pos=int(row.pos),
                        best=int(row.best),
                        average=int(row.average),
                        person_name=_text(row.person_name),
                        person_id=row.person_id,
                        country_id=row.person_country_id,
                        format_id=row.format_id,
                        value1=0,
                        value2=0,
                        value3=0,
                        value4=0,
                        value5=0,
                        regional_single_record=_text(row.regional_single_record),
                        regional_average_record=_text(row.regional_average_record),
                    )
                )
            if records:
                Result.objects.bulk_create(records, batch_size=WRITE_BATCH_SIZE)
            log.info(
                "  processed results file chunk %s (%s Philippine rows)",
                chunk_number,
                len(records),
            )

        self._import_result_attempts(selected_result_ids)

    def _import_result_attempts(self, selected_result_ids):
        log.info("  attaching individual attempts to Philippine results")
        if not selected_result_ids:
            return

        update_fields = ["value1", "value2", "value3", "value4", "value5"]
        for chunk_number, chunk in enumerate(
            self.read_table(
                "result_attempts",
                dtype={"result_id": "int64", "attempt_number": "int8"},
                chunksize=READ_CHUNK_SIZE,
            ),
            start=1,
        ):
            attempts = chunk[chunk["result_id"].isin(selected_result_ids)]
            if attempts.empty:
                continue

            attempt_result_ids = {int(value) for value in attempts["result_id"]}
            results_by_wca_id = {}
            for result_id_batch in _batches(attempt_result_ids, 500):
                for result in Result.objects.filter(
                    wca_result_id__in=result_id_batch
                ):
                    results_by_wca_id[result.wca_result_id] = result

            for row in attempts.itertuples(index=False):
                attempt_number = int(row.attempt_number)
                if not 1 <= attempt_number <= 5:
                    raise CommandError(
                        "WCA result {} has invalid attempt number {}.".format(
                            row.result_id, attempt_number
                        )
                    )
                result = results_by_wca_id.get(int(row.result_id))
                if result is not None:
                    setattr(result, "value{}".format(attempt_number), int(row.value))

            Result.objects.bulk_update(
                list(results_by_wca_id.values()),
                update_fields,
                batch_size=500,
            )
            log.info(
                "  processed result-attempt chunk %s (%s Philippine attempts)",
                chunk_number,
                len(attempts),
            )

    @transaction.atomic
    def import_championships(self):
        log.info("  importing championships")
        for row in self.read_table("championships").itertuples(index=False):
            Championship.objects.update_or_create(
                id=int(row.id),
                defaults={
                    "competition_id": row.competition_id,
                    "championship_type": row.championship_type,
                },
            )
