import re

from django.core.management.base import BaseCommand, CommandError

from api.services.snapshots import build_and_activate_snapshot
from api.services.statistics_builder import build_all_statistics
from wca.models import BoundaryDataset, Competition


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class Command(BaseCommand):
    help = "Build and atomically activate prepared regional statistics."

    def add_arguments(self, parser):
        parser.add_argument("--export-version", required=True)
        parser.add_argument("--export-checksum", required=True)
        parser.add_argument("--boundary-version", required=True)
        parser.add_argument("--latest-year", type=int)

    def handle(self, *args, **options):
        checksum = options["export_checksum"].lower()
        if not SHA256_PATTERN.fullmatch(checksum):
            raise CommandError("--export-checksum must be a 64-character SHA-256")
        try:
            boundary_dataset = BoundaryDataset.objects.get(
                version=options["boundary_version"]
            )
        except BoundaryDataset.DoesNotExist:
            raise CommandError("Unknown boundary dataset version")

        latest_year = options["latest_year"]
        if latest_year is None:
            latest_year = (
                Competition.objects.order_by("-year")
                .values_list("year", flat=True)
                .first()
            )
        if latest_year is None:
            raise CommandError("No competitions are available to determine latest year")

        try:
            snapshot, built = build_and_activate_snapshot(
                export_version=options["export_version"],
                export_checksum=checksum,
                boundary_dataset=boundary_dataset,
                latest_year=latest_year,
                builder=build_all_statistics,
            )
        except Exception as error:
            raise CommandError("Statistics snapshot build failed: {}".format(error))

        if built:
            self.stdout.write(
                self.style.SUCCESS(
                    "Built and activated statistics snapshot {}.".format(snapshot.pk)
                )
            )
        else:
            self.stdout.write(
                "Skipped: this export and boundary already have ready snapshot {}.".format(
                    snapshot.pk
                )
            )
