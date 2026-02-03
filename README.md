# CSI Data Quality Analyzer

Python tool to assess data completeness and 3D-readiness of municipal building datasets (CSI).

## What it does
- Scans all vector layers (Shapefile / GeoPackage)
- Reports:
  - feature count, CRS, and number of fields
  - geometry types and empty/invalid geometries
  - missing attribute values
- Performs a specific 3D-readiness check for `020101_UNITA_VOLUMETRICA`
  - evaluates availability of height attributes (QT_GRONDA, QT_SUOLO, ALTEZZA_VO)
  - treats `0` values in elevation fields as missing (common in municipal data)

## Installation
```bash
pip install -r requirements.txt

##Usage
python src/analyze_csi.py --input "PATH_TO_CSI_FOLDER" --write-report-md

python src/analyze_csi.py --input "PATH_TO_CSI.gpkg" --uv-layer-name 020101_UNITA_VOLUMETRICA --write-report-md

Output

Files are saved in the output/ folder:

summary_layers.csv

summary_unita_volumetrica.csv

report.md (optional)

Why this matters
Urban Digital Twin workflows require reliable and consistent data.
This tool provides a reproducible way to assess data quality and 3D readiness
before attempting 2D/3D city modeling or semantic integration.

## Results (CSI sample – Circoscrizione 7)

The tool was applied to the CSI edificato GeoPackage (6 layers, 17,565 buildings).

- All layers show valid polygon geometries (0% empty or invalid).
- Vertical attributes are present in `020101_UNITA_VOLUMETRICA`, but not complete.
- Approximately **81%** of buildings have sufficient height information for 3D extrusion.
- About **19%** of buildings have missing or zero roof elevation values (`QT_GRONDA`), limiting reliable 3D representation.

These results confirm that CSI data is geometrically robust but partially limited in vertical completeness, impacting 3D city model generation.

## Methodological context

This tool was developed as part of a master’s thesis focusing on the integration of municipal GIS datasets
(CSI and BDTRE) within a standardized semantic framework inspired by FIWARE.

The analysis supports decisions related to:
- 2D and 3D city model generation
- identification of data gaps
- semantic interoperability assessment
