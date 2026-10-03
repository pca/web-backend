#!/usr/bin/env sh
set -eu

dir="$(dirname "$0")"

# The Django command uses the current WCA export API, imports in bounded-memory
# chunks, classifies host regions, and only activates a completed statistics
# snapshot. Arguments such as --force-download are forwarded unchanged.
python "$dir/manage.py" sync_wca_database "$@"
