#!/usr/bin/env sh

dir="$(dirname "$0")"

echo "Downloading WCA Database"
curl https://www.worldcubeassociation.org/results/misc/WCA_export.tsv.zip -o "$dir/data/WCA_export.tsv.zip"

if [ -e "$dir/data/metadata.json" ]
then
    mv "$dir/data/metadata.json" "$dir/data/previous_metadata.json"
fi

echo "Unzipping archive"
unzip -o "$dir/data/WCA_export.tsv.zip" -d "$dir/data/"

echo "Importing WCA data"
python "$dir/manage.py" runscript import_wca_data
