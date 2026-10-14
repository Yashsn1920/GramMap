"""S0.1: insert OSM and Overture count rows into the district comparison table of docs/source_audit.md."""

import json

ORDER = ["Bengaluru North", "Bengaluru South", "Bengaluru Urban", "Chikkaballapura", "Kolar"]
osm = json.load(open("data/samples/osm_coverage.json"))
ovt = json.load(open("data/samples/overture_district_counts.json"))


def row(label, src, key):
    cells = [f"{src[d][key]:,}" if key in src.get(d, {}) else "–" for d in ORDER]
    return f"| {label} | " + " | ".join(cells) + " |"


rows = [
    row("OSM schools", osm, "school"),
    row("OSM colleges", osm, "college"),
    row("OSM health (hospital/clinic/doctors)", osm, "health"),
    row("OSM anganwadis (by name)", osm, "anganwadi"),
    row("OSM water towers / tanks", osm, "water_tower"),
    row("OSM wells / pumps", osm, "well_pump"),
    row("OSM drinking water points", osm, "drinking_water"),
    row("OSM water bodies", osm, "pond"),
    row("OSM government offices", osm, "gov_office"),
    row("OSM post offices", osm, "post_office"),
    row("OSM banks / ATMs", osm, "bank"),
    row("OSM village / hamlet place nodes", osm, "village_place"),
    row("Overture schools", ovt, "school"),
    row("Overture colleges", ovt, "college"),
    row("Overture health", ovt, "health"),
    row("Overture banks / ATMs", ovt, "bank"),
    row("Overture government offices", ovt, "gov_office"),
]
note = (
    '\n\n"–" = not counted. OSM was counted only for the two finalists because Overpass was '
    "overloaded during the audit (about 20 s per query).\n\n"
    "**Key observation:** in the rural districts, OSM and Overture each list only about 25 to 115 schools, "
    "against 1,500 to 2,500 in KGIS. Open global sources alone would miss over 90% of rural schools. "
    "This is the main justification for the multi-source design and will be the headline chart "
    "in the 'value added by each source' evaluation (PRD Section 13.2)."
)

path = "docs/source_audit.md"
s = open(path).read()
assert "<!--OSM_OVERTURE_ROWS-->" in s
s = s.replace("<!--OSM_OVERTURE_ROWS-->", "\n".join(rows) + note)
open(path, "w").write(s)
print("audit table updated")
