import json
from collections import Counter
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from wca.geography.assignments import plan_assignments
from wca.geography.dataset import load_boundary_snapshot
from wca.models import BoundaryDataset, Competition, CompetitionRegionAssignment


DEFAULT_BOUNDARY_PATH = (
    Path(settings.BASE_DIR)
    / "wca"
    / "geography"
    / "boundaries"
    / "philippines-regions.geojson"
)


class Command(BaseCommand):
    help = "Classify Philippine competitions using the versioned boundary snapshot."

    def add_arguments(self, parser):
        parser.add_argument("--boundaries", default=str(DEFAULT_BOUNDARY_PATH))
        parser.add_argument("--metadata", default=None)
        parser.add_argument("--competition-id", action="append", default=[])
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist classifications. Without this flag the command is a dry run.",
        )

    def handle(self, *args, **options):
        boundaries_path = Path(options["boundaries"])
        metadata_path = Path(
            options["metadata"]
            or boundaries_path.with_name("philippines-regions.metadata.json")
        )
        try:
            snapshot = load_boundary_snapshot(boundaries_path, metadata_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise CommandError("Unable to load boundary snapshot: {}".format(error))

        competitions = Competition.objects.filter(country_id="Philippines").order_by("id")
        if options["competition_id"]:
            competitions = competitions.filter(id__in=options["competition_id"])
        competitions = list(competitions)
        existing = {
            assignment.competition_id: assignment
            for assignment in CompetitionRegionAssignment.objects.filter(
                competition_id__in=[competition.id for competition in competitions]
            )
        }
        plans = plan_assignments(
            competitions,
            snapshot.features,
            snapshot.metadata["version"],
            existing,
        )
        changed = [plan for plan in plans if plan.changed]
        status_counts = Counter(plan.status for plan in plans)

        if options["apply"]:
            self._apply(snapshot, changed, existing)
            self.stdout.write(
                self.style.SUCCESS(
                    "Saved {} changed assignment(s); {} unchanged.".format(
                        len(changed), len(plans) - len(changed)
                    )
                )
            )
        else:
            self.stdout.write(
                "Dry run: {} Philippine competition(s), {} assignment(s) would change, {} unchanged.".format(
                    len(plans), len(changed), len(plans) - len(changed)
                )
            )
        self.stdout.write("Classification outcomes: {}".format(dict(status_counts)))
        if not options["apply"]:
            self.stdout.write("No records were changed. Re-run with --apply to persist.")

    @transaction.atomic
    def _apply(self, snapshot, plans, existing):
        metadata = snapshot.metadata
        dataset, created = BoundaryDataset.objects.get_or_create(
            version=metadata["version"],
            defaults={
                "source_url": metadata["source_url"],
                "retrieved_on": date.fromisoformat(metadata["retrieved_on"]),
                "coordinate_system": metadata["coordinate_system"],
                "license": metadata["license"],
                "attribution": metadata["attribution"],
                "processing_notes": metadata["processing_notes"],
                "checksum_sha256": snapshot.checksum_sha256,
                "feature_count": len(snapshot.features),
            },
        )
        if not created and dataset.checksum_sha256 != snapshot.checksum_sha256:
            raise CommandError(
                "Boundary version {} already exists with another checksum; use a new version.".format(
                    dataset.version
                )
            )
        if not created and any(
            (
                dataset.source_url != metadata["source_url"],
                dataset.retrieved_on != date.fromisoformat(metadata["retrieved_on"]),
                dataset.coordinate_system != metadata["coordinate_system"],
                dataset.license != metadata["license"],
                dataset.attribution != metadata["attribution"],
                dataset.processing_notes != metadata["processing_notes"],
                dataset.feature_count != len(snapshot.features),
            )
        ):
            raise CommandError(
                "Boundary version {} already exists with different provenance metadata; use a new version.".format(
                    dataset.version
                )
            )

        new_rows = []
        changed_rows = []
        for plan in plans:
            assignment = existing.get(plan.competition_id)
            if assignment is None:
                new_rows.append(
                    CompetitionRegionAssignment(
                        competition_id=plan.competition_id,
                        boundary_dataset=dataset,
                        region_code=plan.region_code,
                        status=plan.status,
                        classified_latitude=plan.latitude,
                        classified_longitude=plan.longitude,
                    )
                )
            else:
                assignment.boundary_dataset = dataset
                assignment.region_code = plan.region_code
                assignment.status = plan.status
                assignment.classified_latitude = plan.latitude
                assignment.classified_longitude = plan.longitude
                assignment.classified_at = timezone.now()
                changed_rows.append(assignment)
        if new_rows:
            CompetitionRegionAssignment.objects.bulk_create(new_rows, batch_size=500)
        if changed_rows:
            CompetitionRegionAssignment.objects.bulk_update(
                changed_rows,
                (
                    "boundary_dataset",
                    "region_code",
                    "status",
                    "classified_latitude",
                    "classified_longitude",
                    "classified_at",
                ),
                batch_size=500,
            )
