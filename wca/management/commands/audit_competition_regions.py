import json
from collections import Counter

from django.core.management.base import BaseCommand

from wca.models import Competition, CompetitionRegionAssignment


class Command(BaseCommand):
    help = "Report automatic host-region assignment coverage and stale coordinates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            dest="output_format",
        )

    def handle(self, *args, **options):
        competitions = Competition.objects.filter(country_id="Philippines")
        total = competitions.count()
        assignments = CompetitionRegionAssignment.objects.filter(
            competition__country_id="Philippines"
        ).select_related("competition", "boundary_dataset")

        statuses = Counter()
        versions = Counter()
        stale_coordinates = 0
        assigned = 0
        for assignment in assignments.iterator(chunk_size=1000):
            statuses[assignment.status] += 1
            versions[assignment.boundary_dataset_id] += 1
            if assignment.status == CompetitionRegionAssignment.STATUS_ASSIGNED:
                assigned += 1
            if (
                assignment.classified_latitude != assignment.competition.latitude
                or assignment.classified_longitude != assignment.competition.longitude
            ):
                stale_coordinates += 1

        assignment_count = sum(statuses.values())
        payload = {
            "philippine_competitions": total,
            "with_assignment": assignment_count,
            "without_assignment": total - assignment_count,
            "assigned": assigned,
            "unclassified": assignment_count - assigned,
            "stale_coordinate_assignments": stale_coordinates,
            "boundary_versions": dict(sorted(versions.items())),
            "outcomes": dict(sorted(statuses.items())),
        }
        payload["assigned_coverage_percent"] = (
            round(assigned * 100.0 / total, 2) if total else None
        )

        if options["output_format"] == "json":
            self.stdout.write(json.dumps(payload, sort_keys=True))
            return

        self.stdout.write("Philippine competition-region coverage audit")
        self.stdout.write("Competitions: {}".format(total))
        self.stdout.write("Assignments: {}".format(assignment_count))
        self.stdout.write("Assigned: {}".format(assigned))
        self.stdout.write("Unclassified: {}".format(assignment_count - assigned))
        self.stdout.write("No assignment: {}".format(total - assignment_count))
        self.stdout.write("Stale coordinate assignments: {}".format(stale_coordinates))
        self.stdout.write("Assigned coverage: {}%".format(payload["assigned_coverage_percent"]))
        self.stdout.write("Boundary versions: {}".format(payload["boundary_versions"]))
        self.stdout.write("Classification outcomes: {}".format(payload["outcomes"]))
