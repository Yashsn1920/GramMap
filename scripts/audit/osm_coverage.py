"""S0.1: count OSM features of each asset category per candidate district.
One small Overpass 'out count' query per (district, category); resumable via the output JSON."""

import json
import os
import sys
import time

sys.path.insert(0, "scripts/audit")
from overpass import query

OUT = "data/samples/osm_coverage.json"
DISTRICTS = sys.argv[1:] or ["Bengaluru North", "Kolar"]
SETS = {
    "school": 'nwr["amenity"="school"]',
    "college": 'nwr["amenity"~"^(college|university)$"]',
    "health": 'nwr["amenity"~"^(hospital|clinic|doctors)$"]',
    "anganwadi": 'nwr["name"~"anganwadi|anganawadi",i]',
    "water_tower": 'nwr["man_made"~"^(water_tower|storage_tank)$"]',
    "well_pump": 'nwr["man_made"="water_well"]',
    "drinking_water": 'nwr["amenity"="drinking_water"]',
    "pond": 'nwr["natural"="water"]',
    "gov_office": 'nwr["office"="government"]',
    "post_office": 'nwr["amenity"="post_office"]',
    "bank": 'nwr["amenity"~"^(bank|atm)$"]',
    "village_place": 'node["place"~"^(village|hamlet)$"]',
}
out = json.load(open(OUT)) if os.path.exists(OUT) else {}
for d in DISTRICTS:
    out.setdefault(d, {})
    for key, sel in SETS.items():
        if key in out[d]:
            continue
        q = f'[out:json][timeout:180];area["name"="{d}"]["admin_level"="5"]["boundary"="administrative"]->.d;{sel}(area.d);out count;'
        res = query(q, timeout=240)
        out[d][key] = int(res["elements"][0]["tags"]["total"])
        json.dump(out, open(OUT, "w"), indent=1)
        time.sleep(2)
    print(d, out[d], flush=True)
