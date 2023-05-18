import json
import logging
import math

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
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
DUMP_DIR = settings.BASE_DIR.joinpath("data/extracted/")


class Command(BaseCommand):
    help = "Import data from WCA"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Force import without checking metadata if files are already imported.",
        )
        parser.add_argument(
            "--step",
            type=int,
            default=1,
            help="Starting import step.",
        )

    def handle(self, *args, **options):
        previous_metadata = DUMP_DIR.joinpath("previous_metadata.json")
        print(options)

        if not options["force"] and previous_metadata.is_file():
            with open(DUMP_DIR.joinpath("metadata.json")) as metadata_file:
                metadata = json.load(metadata_file)
            with open(previous_metadata) as previous_metadata_file:
                previous_metadata = json.load(previous_metadata_file)
            if metadata["export_date"] == previous_metadata["export_date"]:
                log.info("Data is up-to-date.")
                return

        self.start_import(options["step"])

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

        for step_func in steps[step - 1 :]:
            step_func()

        log.info("Data import successful!")

    @transaction.atomic
    def import_continents(self):
        log.info("  importing continents")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Continents.tsv"), sep="\t")
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
    def import_countries(self):
        log.info("  importing countries")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Countries.tsv"), sep="\t")
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
    def import_events(self):
        log.info("  importing events")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Events.tsv"), sep="\t")
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
    def import_formats(self):
        log.info("  importing formats")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Formats.tsv"), sep="\t")
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
    def import_round_types(self):
        log.info("  importing round types")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_RoundTypes.tsv"), sep="\t")
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
    def import_competitions(self):
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Competitions.tsv"), sep="\t")
        df = df.replace({np.nan: None})
        total_chunks = math.ceil(len(df) / 1000)

        for index, group in df.groupby(np.arange(len(df)) // 1000):
            log.info(f"  importing competitions chunk {index + 1}/{total_chunks}")
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

    def get_persons_df(self):
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Persons.tsv"), sep="\t")
        ph_df = df[df["countryId"] == PH_ID]
        ph_df = ph_df.replace({np.nan: None})
        return ph_df

    @transaction.atomic
    def import_persons(self):
        log.info("  importing persons")
        df = self.get_persons_df()

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
    def import_ranks_average(self):
        log.info("  importing ranks average")
        persons_df = self.get_persons_df()

        df = pd.read_csv(
            DUMP_DIR.joinpath("WCA_export_RanksAverage.tsv"),
            sep="\t",
            dtype={"eventId": str},
        )
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
    def import_ranks_single(self):
        log.info("  importing ranks single")
        persons_df = self.get_persons_df()

        df = pd.read_csv(
            DUMP_DIR.joinpath("WCA_export_RanksSingle.tsv"),
            sep="\t",
            dtype={"eventId": str},
        )
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
    def import_results(self):
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_Results.tsv"), sep="\t")
        ph_df = df[df["personCountryId"] == PH_ID]
        ph_df = ph_df.replace({np.nan: None})
        total_chunks = math.ceil(len(ph_df) / 1000)

        Result.objects.all().delete()

        for index, group in ph_df.groupby(np.arange(len(ph_df)) // 1000):
            log.info(f"  importing results chunk {index + 1}/{total_chunks}")
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
    def import_championships(self):
        log.info("  importing championships")
        df = pd.read_csv(DUMP_DIR.joinpath("WCA_export_championships.tsv"), sep="\t")
        df = df.replace({np.nan: None})

        for row in df.itertuples():
            Championship.objects.update_or_create(
                id=row.id,
                defaults={
                    "competition_id": row.competition_id,
                    "championship_type": row.championship_type,
                },
            )
