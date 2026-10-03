# Philippine regional boundary snapshot

`philippines-regions.geojson` is the fixed 18-region boundary snapshot used to
classify the host region of Philippine WCA competitions. The application uses
this same current map for the complete history beginning in 2007. It does not
attempt to reconstruct historical regional boundaries.

## Source and permitted use

The source is the 2024 region layer from
[geoph](https://github.com/jronnybravo/geoph), pinned to commit
`135776d2b1acedad84e3a09292e2b759c89507dd`. Geoph combines the official PSA
Philippine Standard Geographic Code roster with NAMRIA/OCHA-HDX geometry and
publishes the result under CC BY 4.0.

Required attribution:

> Philippine administrative boundaries (geoph), synthesized from PSA PSGC and
> NAMRIA/OCHA-HDX COD-AB data — CC BY 4.0.

This is an unofficial analytical boundary dataset. It must not be presented as
a legal, cadastral, or survey-grade government boundary product. That
limitation is appropriate here because the feature classifies public event
coordinates for descriptive statistics and reports uncertain cases instead of
guessing.

## Conversion record

- Input files: `boundaries/2024/regions.shp`, `.shx`, and `.dbf`
- Input coordinate system: EPSG:4326
- Region catalog: 18 PSGC regions, including Negros Island Region
- Output: GeoJSON `FeatureCollection` with one `MultiPolygon` per region
- Output properties: `region_code`, `source_pcode`, and `source_name`
- Coordinates rounded to six decimal places
- Features sorted by source PSGC pcode for reproducible output

The full source revision, retrieval date, processing notes, and source/output
checksums are recorded in `philippines-regions.metadata.json`.
