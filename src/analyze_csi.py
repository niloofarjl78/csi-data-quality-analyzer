import argparse
from pathlib import Path
import pandas as pd

try:
    import geopandas as gpd
except ImportError:
    raise SystemExit("geopandas is required. Run: pip install -r requirements.txt")

from .utils import (
    list_vector_layers,
    read_layer,
    basic_layer_stats,
    geometry_stats,
    missingness_stats,
    unita_volumetrica_height_stats,
    safe_write_csv,
    safe_write_md,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="CSI Data Quality Analyzer: schema, geometry, missingness, and 3D readiness."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to CSI data folder or GeoPackage file",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Folder where results will be saved",
    )
    parser.add_argument(
        "--uv-layer-name",
        default=None,
        help="Exact UNITA_VOLUMETRICA layer name (if GeoPackage)",
    )
    parser.add_argument(
        "--write-report-md",
        action="store_true",
        help="Write a Markdown summary report",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)

    layers = list_vector_layers(input_path)

    if not layers:
        raise SystemExit("No vector layers found.")

    layer_results = []

    for layer in layers:
        gdf = read_layer(layer)
        row = {}
        row.update(basic_layer_stats(layer, gdf))
        row.update(geometry_stats(gdf))
        row.update(missingness_stats(gdf))
        layer_results.append(row)

    df_layers = pd.DataFrame(layer_results)
    safe_write_csv(df_layers, output_path / "summary_layers.csv")

    uv_layers = [
        l for l in layers
        if args.uv_layer_name and l.get("layer_name") == args.uv_layer_name
        or (not args.uv_layer_name and "unita" in (l.get("layer_name") or "").lower())
    ]

    if uv_layers:
        uv_stats = []
        for uv in uv_layers:
            gdf_uv = read_layer(uv)
            uv_stats.append(unita_volumetrica_height_stats(gdf_uv, uv))
        df_uv = pd.DataFrame(uv_stats)
        safe_write_csv(df_uv, output_path / "summary_unita_volumetrica.csv")
    else:
        df_uv = None

    if args.write_report_md:
        lines = [
            "# CSI Data Quality Report\n",
            f"Input path: `{input_path}`\n",
            "## Layer summary\n",
            df_layers.to_markdown(index=False),
        ]

        if df_uv is not None:
            lines.extend([
                "\n## UNITA_VOLUMETRICA 3D readiness\n",
                df_uv.to_markdown(index=False),
            ])

        safe_write_md("\n".join(lines), output_path / "report.md")

    print("Analysis completed.")
    print(f"Results saved in: {output_path.resolve()}")


if __name__ == "__main__":
    main()
