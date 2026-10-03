import csv
import json
from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from wca.management.commands.import_wca_data import Command, EXPORT_FILES
from wca.models import (
    BoundaryDataset,
    Competition,
    CompetitionRegionAssignment,
    Continent,
    Event,
    Person,
    RanksAverage,
    RanksSingle,
    Result,
)


def write_tsv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_export(directory, *, export_version="2.0.2", latitude=14600000):
    (directory / "metadata.json").write_text(
        json.dumps(
            {
                "export_date": "2026-10-03 00:00:28 UTC",
                "export_format_version": export_version,
            }
        ),
        encoding="utf-8",
    )
    write_tsv(
        directory / EXPORT_FILES["continents"],
        ["id", "name", "record_name"],
        [{"id": "_Asia", "name": "Asia", "record_name": "AsR"}],
    )
    write_tsv(
        directory / EXPORT_FILES["countries"],
        ["id", "name", "continent_id", "iso2"],
        [
            {
                "id": "Philippines",
                "name": "Philippines",
                "continent_id": "_Asia",
                "iso2": "PH",
            },
            {
                "id": "USA",
                "name": "United States",
                "continent_id": "_North America",
                "iso2": "US",
            },
        ],
    )
    # The second country refers to a continent that is irrelevant to the
    # filtered Philippine rows. Point it at Asia to keep this tiny fixture valid.
    countries_path = directory / EXPORT_FILES["countries"]
    countries_text = countries_path.read_text(encoding="utf-8")
    countries_path.write_text(
        countries_text.replace("_North America", "_Asia"), encoding="utf-8"
    )
    write_tsv(
        directory / EXPORT_FILES["events"],
        ["id", "name", "rank", "format"],
        [{"id": "333", "name": "3x3x3 Cube", "rank": 10, "format": "time"}],
    )
    write_tsv(
        directory / EXPORT_FILES["formats"],
        [
            "id",
            "name",
            "sort_by",
            "sort_by_second",
            "expected_solve_count",
            "trim_fastest_n",
            "trim_slowest_n",
        ],
        [
            {
                "id": "a",
                "name": "Average of 5",
                "sort_by": "average",
                "sort_by_second": "best",
                "expected_solve_count": 5,
                "trim_fastest_n": 1,
                "trim_slowest_n": 1,
            }
        ],
    )
    write_tsv(
        directory / EXPORT_FILES["round_types"],
        ["id", "rank", "name", "cell_name", "final"],
        [{"id": "f", "rank": 10, "name": "Final", "cell_name": "Final", "final": 1}],
    )
    competition_columns = [
        "id",
        "name",
        "information",
        "external_website",
        "venue",
        "city_name",
        "country_id",
        "venue_address",
        "venue_details",
        "cell_name",
        "cancelled",
        "event_specs",
        "delegates",
        "organizers",
        "year",
        "month",
        "day",
        "end_year",
        "end_month",
        "end_day",
        "latitude_microdegrees",
        "longitude_microdegrees",
    ]
    write_tsv(
        directory / EXPORT_FILES["competitions"],
        competition_columns,
        [
            {
                "id": "PhilippineOpen2026",
                "name": "Philippine Open 2026",
                "information": "",
                "external_website": "",
                "venue": "Test Hall",
                "city_name": "Manila",
                "country_id": "Philippines",
                "venue_address": "Test Address",
                "venue_details": "Second floor",
                "cell_name": "Philippine Open 2026",
                "cancelled": 0,
                "event_specs": "333",
                "delegates": "2020TEST01",
                "organizers": "2020TEST01",
                "year": 2026,
                "month": 10,
                "day": 3,
                "end_year": 2026,
                "end_month": 10,
                "end_day": 4,
                "latitude_microdegrees": latitude,
                "longitude_microdegrees": 121000000,
            },
            {
                "id": "ForeignOpen2025",
                "name": "Foreign Open 2025",
                "information": "",
                "external_website": "",
                "venue": "Other Hall",
                "city_name": "Somewhere",
                "country_id": "USA",
                "venue_address": "",
                "venue_details": "",
                "cell_name": "Foreign Open 2025",
                "cancelled": 0,
                "event_specs": "333",
                "delegates": "",
                "organizers": "",
                "year": 2025,
                "month": 1,
                "day": 2,
                "end_year": 2025,
                "end_month": 1,
                "end_day": 2,
                "latitude_microdegrees": 40000000,
                "longitude_microdegrees": -75000000,
            },
        ],
    )
    write_tsv(
        directory / EXPORT_FILES["persons"],
        ["name", "gender", "wca_id", "sub_id", "country_id"],
        [
            {
                "name": "Juan Test",
                "gender": "m",
                "wca_id": "2020TEST01",
                "sub_id": 1,
                "country_id": "Philippines",
            },
            {
                "name": "Foreign Test",
                "gender": "f",
                "wca_id": "2020OTHR01",
                "sub_id": 1,
                "country_id": "USA",
            },
        ],
    )
    rank_columns = [
        "best",
        "person_id",
        "event_id",
        "world_rank",
        "continent_rank",
        "country_rank",
    ]
    rank_rows = [
        {
            "best": 1234,
            "person_id": "2020TEST01",
            "event_id": "333",
            "world_rank": 500,
            "continent_rank": 100,
            "country_rank": 5,
        },
        {
            "best": 1100,
            "person_id": "2020OTHR01",
            "event_id": "333",
            "world_rank": 400,
            "continent_rank": 80,
            "country_rank": 20,
        },
    ]
    write_tsv(directory / EXPORT_FILES["ranks_average"], rank_columns, rank_rows)
    write_tsv(directory / EXPORT_FILES["ranks_single"], rank_columns, rank_rows)
    result_columns = [
        "id",
        "pos",
        "best",
        "average",
        "competition_id",
        "round_type_id",
        "event_id",
        "person_name",
        "person_id",
        "format_id",
        "regional_single_record",
        "regional_average_record",
        "person_country_id",
    ]
    write_tsv(
        directory / EXPORT_FILES["results"],
        result_columns,
        [
            {
                "id": 101,
                "pos": 1,
                "best": 1200,
                "average": 1400,
                "competition_id": "PhilippineOpen2026",
                "round_type_id": "f",
                "event_id": "333",
                "person_name": "Juan Test",
                "person_id": "2020TEST01",
                "format_id": "a",
                "regional_single_record": "NR",
                "regional_average_record": "",
                "person_country_id": "Philippines",
            },
            {
                "id": 202,
                "pos": 2,
                "best": 1100,
                "average": 1300,
                "competition_id": "ForeignOpen2025",
                "round_type_id": "f",
                "event_id": "333",
                "person_name": "Foreign Test",
                "person_id": "2020OTHR01",
                "format_id": "a",
                "regional_single_record": "",
                "regional_average_record": "",
                "person_country_id": "USA",
            },
        ],
    )
    write_tsv(
        directory / EXPORT_FILES["result_attempts"],
        ["value", "attempt_number", "result_id"],
        [
            {"value": 1200, "attempt_number": 1, "result_id": 101},
            {"value": 1300, "attempt_number": 2, "result_id": 101},
            {"value": -1, "attempt_number": 3, "result_id": 101},
            {"value": 1500, "attempt_number": 4, "result_id": 101},
            {"value": 1400, "attempt_number": 5, "result_id": 101},
            {"value": 1100, "attempt_number": 1, "result_id": 202},
        ],
    )
    write_tsv(
        directory / EXPORT_FILES["championships"],
        ["id", "competition_id", "championship_type"],
        [
            {
                "id": 1,
                "competition_id": "PhilippineOpen2026",
                "championship_type": "PH",
            }
        ],
    )


@pytest.mark.django_db
def test_imports_v2_export_and_reconstructs_five_attempts(tmp_path):
    write_export(tmp_path)

    call_command("import_wca_data", data_dir=str(tmp_path))

    continent = Continent.objects.get(id="_Asia")
    assert continent.latitude is None
    assert continent.longitude is None
    assert continent.zoom is None
    assert Event.objects.get(id="333").cell_name == "3x3x3 Cube"
    assert list(Person.objects.values_list("id", flat=True)) == ["2020TEST01"]
    assert RanksSingle.objects.get().country_rank == 5
    assert RanksAverage.objects.get().country_rank == 5

    result = Result.objects.get()
    assert result.wca_result_id == 101
    assert [result.value1, result.value2, result.value3, result.value4, result.value5] == [
        1200,
        1300,
        -1,
        1500,
        1400,
    ]
    assert (tmp_path / "imported_metadata.json").is_file()


@pytest.mark.django_db
def test_same_export_skips_and_force_reimport_preserves_region_assignment(tmp_path):
    write_export(tmp_path)
    call_command("import_wca_data", data_dir=str(tmp_path))

    competition = Competition.objects.get(id="PhilippineOpen2026")
    dataset = BoundaryDataset.objects.create(
        version="test-boundaries",
        source_url="https://example.test/regions.geojson",
        retrieved_on=date(2026, 10, 1),
        license="Test only",
        processing_notes="Fixture",
        checksum_sha256="a" * 64,
        feature_count=18,
    )
    assignment = CompetitionRegionAssignment.objects.create(
        competition=competition,
        boundary_dataset=dataset,
        region_code="13",
        status=CompetitionRegionAssignment.STATUS_ASSIGNED,
        classified_latitude=14600000,
        classified_longitude=121000000,
    )

    Competition.objects.filter(pk=competition.pk).update(name="Local marker")
    output = StringIO()
    call_command("import_wca_data", data_dir=str(tmp_path), stdout=output)
    assert "already imported" in output.getvalue()
    assert Competition.objects.get(pk=competition.pk).name == "Local marker"

    write_export(tmp_path, latitude=14700000)
    call_command("import_wca_data", data_dir=str(tmp_path), force=True)

    competition.refresh_from_db()
    assignment.refresh_from_db()
    assert competition.latitude == 14700000
    assert assignment.region_code == "13"
    assert assignment.classified_latitude == 14600000


def test_rejects_unknown_export_major_version(tmp_path):
    write_export(tmp_path, export_version="3.0.0")
    command = Command()
    command.dump_dir = tmp_path

    with pytest.raises(CommandError, match="Unsupported WCA export format"):
        command.load_and_validate_metadata()
