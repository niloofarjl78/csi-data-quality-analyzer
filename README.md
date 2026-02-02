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