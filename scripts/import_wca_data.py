import json
import math
from pathlib import Path

import pandas as pd
import numpy as np
from django.db import transaction

from wca.models import (
    Continent,
    Country,
    Event,
    Format,
    RoundType,
    Competition,
    Person,
    RanksAverage,
    RanksSingle,
    Result,
    Championship,
)

PH_ID = "Philippines"


@transaction.atomic
def import_continents():
    print("  importing continents")
    df = pd.read_csv("data/WCA_export_Continents.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        Continent.objects.update_or_create(
            id=row.id,
            defaults={
                "name": row.name,
                "record_name": row.recordName,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "zoom": row.zoom,
            },
        )


@transaction.atomic
def import_countries():
    print("  importing countries")
    df = pd.read_csv("data/WCA_export_Countries.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        Country.objects.update_or_create(
            id=row.id,
            defaults={
                "name": row.name,
                "continent_id": row.continentId,
                "iso2": row.iso2,
            },
        )


@transaction.atomic
def import_events():
    print("  importing events")
    df = pd.read_csv("data/WCA_export_Events.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        Event.objects.update_or_create(
            id=row.id,
            defaults={
                "name": row.name,
                "rank": row.rank,
                "format": row.format,
                "cell_name": row.cellName,
            },
        )


@transaction.atomic
def import_formats():
    print("  importing formats")
    df = pd.read_csv("data/WCA_export_Formats.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        Format.objects.update_or_create(
            id=row.id,
            defaults={
                "name": row.name,
                "sort_by": row.sort_by,
                "sort_by_second": row.sort_by_second,
                "expected_solve_count": row.expected_solve_count,
                "trim_fastest_n": row.trim_fastest_n,
                "trim_slowest_n": row.trim_slowest_n,
            },
        )


@transaction.atomic
def import_round_types():
    print("  importing round types")
    df = pd.read_csv("data/WCA_export_RoundTypes.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        RoundType.objects.update_or_create(
            id=row.id,
            defaults={
                "rank": row.rank,
                "name": row.name,
                "cell_name": row.cellName,
                "final": row.final,
            },
        )


@transaction.atomic
def import_competitions():
    df = pd.read_csv("data/WCA_export_Competitions.tsv", sep="\t")
    df = df.replace({np.nan: None})
    total_chunks = math.ceil(len(df) / 1000)

    for index, group in df.groupby(np.arange(len(df)) // 1000):
        print(f"  importing competitions chunk {index + 1}/{total_chunks}")
        with transaction.atomic():
            for row in group.itertuples():
                Competition.objects.update_or_create(
                    id=row.id,
                    defaults={
                        "name": row.name,
                        "city_name": row.cityName,
                        "country_id": row.countryId,
                        "information": row.information,
                        "year": row.year,
                        "month": row.month,
                        "day": row.day,
                        "end_month": row.endMonth,
                        "end_day": row.endDay,
                        "event_specs": row.eventSpecs,
                        "wca_delegate": row.wcaDelegate,
                        "organizer": row.organiser,
                        "venue": row.venue,
                        "venue_address": row.venueAddress,
                        "venue_details": row.venueDetails,
                        "external_website": row.external_website,
                        "cell_name": row.cellName,
                        "latitude": row.latitude,
                        "longitude": row.longitude,
                    },
                )


def get_persons_df():
    df = pd.read_csv("data/WCA_export_Persons.tsv", sep="\t")
    ph_df = df[df["countryId"] == PH_ID]
    ph_df = ph_df.replace({np.nan: None})
    return ph_df


@transaction.atomic
def import_persons():
    print("  importing persons")
    df = get_persons_df()

    for row in df.itertuples():
        Person.objects.update_or_create(
            id=row.id,
            defaults={
                "subid": row.subid,
                "name": row.name,
                "country_id": row.countryId,
                "gender": row.gender,
            },
        )


@transaction.atomic
def import_ranks_average():
    print("  importing ranks average")
    persons_df = get_persons_df()

    df = pd.read_csv("data/WCA_export_RanksAverage.tsv", sep="\t")
    ph_df = df[df["personId"].isin(persons_df["id"])]
    ph_df = ph_df.replace({np.nan: None})

    RanksAverage.objects.all().delete()

    for row in ph_df.itertuples():
        RanksAverage.objects.create(
            person_id=row.personId,
            event_id=row.eventId,
            best=row.best,
            world_rank=row.worldRank,
            continent_rank=row.continentRank,
            country_rank=row.countryRank,
        )


@transaction.atomic
def import_ranks_single():
    print("  importing ranks single")
    persons_df = get_persons_df()

    df = pd.read_csv("data/WCA_export_RanksSingle.tsv", sep="\t")
    ph_df = df[df["personId"].isin(persons_df["id"])]
    ph_df = ph_df.replace({np.nan: None})

    RanksSingle.objects.all().delete()

    for row in ph_df.itertuples():
        RanksSingle.objects.create(
            person_id=row.personId,
            event_id=row.eventId,
            best=row.best,
            world_rank=row.worldRank,
            continent_rank=row.continentRank,
            country_rank=row.countryRank,
        )


@transaction.atomic
def import_results():
    df = pd.read_csv("data/WCA_export_Results.tsv", sep="\t")
    ph_df = df[df["personCountryId"] == PH_ID]
    ph_df = ph_df.replace({np.nan: None})
    total_chunks = math.ceil(len(ph_df) / 1000)

    Result.objects.all().delete()

    for index, group in ph_df.groupby(np.arange(len(ph_df)) // 1000):
        print(f"  importing results chunk {index + 1}/{total_chunks}")
        with transaction.atomic():
            for row in group.itertuples():
                Result.objects.create(
                    competition_id=row.competitionId,
                    event_id=row.eventId,
                    round_type_id=row.roundTypeId,
                    pos=row.pos,
                    best=row.best,
                    average=row.average,
                    person_name=row.personName,
                    person_id=row.personId,
                    country_id=row.personCountryId,
                    format_id=row.formatId,
                    value1=row.value1,
                    value2=row.value2,
                    value3=row.value3,
                    value4=row.value4,
                    value5=row.value5,
                    regional_single_record=row.regionalSingleRecord,
                    regional_average_record=row.regionalAverageRecord,
                )


@transaction.atomic
def import_championships():
    print("  importing championships")
    df = pd.read_csv("data/WCA_export_championships.tsv", sep="\t")
    df = df.replace({np.nan: None})

    for row in df.itertuples():
        Championship.objects.update_or_create(
            id=row.id,
            defaults={
                "competition_id": row.competition_id,
                "championship_type": row.championship_type,
            },
        )


def start_import():
    import_continents()
    import_countries()
    import_events()
    import_formats()
    import_round_types()
    import_competitions()
    import_persons()
    import_ranks_average()
    import_ranks_single()
    import_results()
    import_championships()


def run():
    if Path("data/previous_metadata.json").is_file():
        with open("data/metadata.json") as metadata_file:
            metadata = json.load(metadata_file)
        with open("data/previous_metadata.json") as previous_metadata_file:
            previous_metadata = json.load(previous_metadata_file)
        if metadata["export_date"] == previous_metadata["export_date"]:
            print("Data is up-to-date.")
            return

    start_import()
