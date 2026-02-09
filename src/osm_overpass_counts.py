import requests
import csv
from datetime import date

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# If this endpoint fails, switch to:
# OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def overpass_count(query: str) -> int:
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=180)

    # If server is overloaded or returns HTML
    if not r.ok or not r.text.strip():
        raise RuntimeError("Overpass returned empty or invalid response")

    # Try to parse JSON safely
    try:
        data = r.json()
    except ValueError:
        print("---- Overpass raw response (first 500 chars) ----")
        print(r.text[:500])
        raise RuntimeError("Overpass did not return JSON")

    elements = data.get("elements", [])
    if not elements:
        return 0

    tags = elements[0].get("tags", {})
    return int(tags.get("total", 0))


def make_query_total(s, w, n, e) -> str:
    return f"""
    [out:json][timeout:120];
    nwr["building"]({s},{w},{n},{e});
    out count;
    """

def make_query_height(s, w, n, e) -> str:
    return f"""
    [out:json][timeout:120];
    nwr["building"]["height"]({s},{w},{n},{e});
    out count;
    """

def make_query_levels(s, w, n, e) -> str:
    return f"""
    [out:json][timeout:120];
    nwr["building"]["building:levels"]({s},{w},{n},{e});
    out count;
    """

if __name__ == "__main__":
    # Put bbox here: south, west, north, east (EPSG:4326 / lat-lon)
    # You can copy it from Overpass Turbo map (Export -> Query -> it shows numbers),
    # or tell me and I’ll show how to extract it.
    SOUTH = 45.08
    WEST  = 7.68
    NORTH = 45.10
    EAST  = 7.71

    total = overpass_count(make_query_total(SOUTH, WEST, NORTH, EAST))
    with_height = overpass_count(make_query_height(SOUTH, WEST, NORTH, EAST))
    with_levels = overpass_count(make_query_levels(SOUTH, WEST, NORTH, EAST))

    out_path = "docs/examples/osm_height_summary.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["area", "bbox_south", "bbox_west", "bbox_north", "bbox_east",
                         "total_buildings", "with_height", "with_levels", "date"])
        writer.writerow(["c7_bbox", SOUTH, WEST, NORTH, EAST, total, with_height, with_levels, str(date.today())])

    print("Wrote:", out_path)
    print("total_buildings:", total)
    print("with_height:", with_height)
    print("with_levels:", with_levels)
