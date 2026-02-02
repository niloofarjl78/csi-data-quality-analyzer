from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import geopandas as gpd


def list_vector_layers(input_path: Path) -> List[Dict[str, Any]]:
    """
    Discover vector layers.
    Supports:
      - Folder containing .shp and/or .gpkg files
      - Single .shp
      - Single .gpkg (multi-layer supported if fiona is installed)
    Returns list of dicts with keys: source, path, driver, layer_name
    """
    input_path = Path(input_path)
    layers: List[Dict[str, Any]] = []

    if input_path.is_dir():
        for p in sorted(input_path.rglob("*")):
            if p.suffix.lower() == ".shp":
                layers.append({
                    "source": p.name,
                    "path": p,
                    "driver": "ESRI Shapefile",
                    "layer_name": p.stem
                })
            elif p.suffix.lower() == ".gpkg":
                layers.extend(_gpkg_layers(p))
        return layers

    # Single file
    if input_path.suffix.lower() == ".shp":
        return [{
            "source": input_path.name,
            "path": input_path,
            "driver": "ESRI Shapefile",
            "layer_name": input_path.stem
        }]

    if input_path.suffix.lower() == ".gpkg":
        return _gpkg_layers(input_path)

    return []


def _gpkg_layers(gpkg_path: Path) -> List[Dict[str, Any]]:
    """
    List layers inside a GeoPackage. If fiona isn't available, returns one entry without layer_name.
    """
    try:
        import fiona
        names = fiona.listlayers(gpkg_path)
        return [{
            "source": gpkg_path.name,
            "path": gpkg_path,
            "driver": "GPKG",
            "layer_name": n
        } for n in names]
    except Exception:
        # fallback: geopandas can read default layer
        return [{
            "source": gpkg_path.name,
            "path": gpkg_path,
            "driver": "GPKG",
            "layer_name": None
        }]


def read_layer(layer_ref: Dict[str, Any]) -> gpd.GeoDataFrame:
    path = layer_ref["path"]
    layer_name = layer_ref.get("layer_name")
    try:
        if layer_name:
            return gpd.read_file(path, layer=layer_name)
        return gpd.read_file(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read layer: {path} (layer={layer_name})\n{e}") from e


def basic_layer_stats(layer_ref: Dict[str, Any], gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    return {
        "source": layer_ref.get("source"),
        "layer_name": layer_ref.get("layer_name"),
        "path": str(layer_ref.get("path")),
        "n_features": int(len(gdf)),
        "n_fields": int(len(gdf.columns)),
        "crs": str(gdf.crs) if gdf.crs else None,
    }


def geometry_stats(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    geom = gdf.geometry
    geom_types = geom.geom_type.value_counts(dropna=False).to_dict()
    pct_empty = float((geom.is_empty | geom.isna()).mean() * 100.0)
    try:
        pct_invalid = float((~geom.is_valid).mean() * 100.0)
    except Exception:
        pct_invalid = None

    return {
        "geom_types": "; ".join([f"{k}:{v}" for k, v in geom_types.items()]) if geom_types else None,
        "pct_empty_geom": round(pct_empty, 2),
        "pct_invalid_geom": round(pct_invalid, 2) if pct_invalid is not None else None,
    }


def missingness_stats(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    cols = [c for c in gdf.columns if c != "geometry"]
    if not cols:
        return {"pct_missing_any": None, "top_missing_fields": None}

    df = gdf[cols]
    missing_any = df.isna().any(axis=1)
    pct_missing_any = float(missing_any.mean() * 100.0)

    missing_pct = (df.isna().mean() * 100.0).sort_values(ascending=False)
    top = missing_pct.head(5)
    top_missing_fields = "; ".join([f"{idx}:{val:.1f}%" for idx, val in top.items()])

    return {
        "pct_missing_any": round(pct_missing_any, 2),
        "top_missing_fields": top_missing_fields,
    }


def unita_volumetrica_height_stats(gdf: gpd.GeoDataFrame, layer_ref: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specialized: 3D readiness for UNITA_VOLUMETRICA.
    Treat QT_GRONDA and QT_SUOLO equal to 0 as missing (common encoding).
    """
    out = {
        "source": layer_ref.get("source"),
        "layer_name": layer_ref.get("layer_name"),
        "n_features": int(len(gdf)),
    }

    required = ["QT_GRONDA", "QT_SUOLO", "ALTEZZA_VO"]
    present = [f for f in required if f in gdf.columns]
    missing = [f for f in required if f not in gdf.columns]

    out["height_fields_present"] = ", ".join(present) if present else None
    out["height_fields_missing"] = ", ".join(missing) if missing else None

    if "QT_GRONDA" in gdf.columns and "QT_SUOLO" in gdf.columns:
        qt_gronda = pd.to_numeric(gdf["QT_GRONDA"], errors="coerce")
        qt_suolo = pd.to_numeric(gdf["QT_SUOLO"], errors="coerce")

        gronda_missing = qt_gronda.isna() | (qt_gronda == 0)
        suolo_missing = qt_suolo.isna() | (qt_suolo == 0)
        height_available = ~(gronda_missing | suolo_missing)

        out["pct_height_available"] = round(float(height_available.mean() * 100.0), 2)
        out["pct_qt_gronda_zero_or_null"] = round(float(gronda_missing.mean() * 100.0), 2)
        out["pct_qt_suolo_zero_or_null"] = round(float(suolo_missing.mean() * 100.0), 2)
    else:
        out["pct_height_available"] = None
        out["pct_qt_gronda_zero_or_null"] = None
        out["pct_qt_suolo_zero_or_null"] = None

    if "ALTEZZA_VO" in gdf.columns:
        altezza = pd.to_numeric(gdf["ALTEZZA_VO"], errors="coerce")
        out["pct_altezza_null"] = round(float(altezza.isna().mean() * 100.0), 2)
    else:
        out["pct_altezza_null"] = None

    out["note"] = "3D readiness treats 0 elevation values as missing."
    return out


def safe_write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def safe_write_md(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
