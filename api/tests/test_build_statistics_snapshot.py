from datetime import date
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command


@patch(
    "api.management.commands.build_statistics_snapshot.timezone.localdate",
    return_value=date(2026, 10, 4),
)
@patch("api.management.commands.build_statistics_snapshot.BoundaryDataset.objects.get")
@patch("api.management.commands.build_statistics_snapshot.build_and_activate_snapshot")
def test_default_latest_year_stops_at_present_year(
    build_snapshot,
    get_boundary,
    _localdate,
):
    boundary = SimpleNamespace(version="test-boundaries")
    get_boundary.return_value = boundary
    build_snapshot.return_value = (SimpleNamespace(pk=1), True)

    call_command(
        "build_statistics_snapshot",
        export_version="v2.0.2:2026-10-03",
        export_checksum="a" * 64,
        boundary_version=boundary.version,
        stdout=StringIO(),
    )

    assert build_snapshot.call_args.kwargs["latest_year"] == 2026
