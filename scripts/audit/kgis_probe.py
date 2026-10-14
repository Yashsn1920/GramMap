"""S0.1: list layers of key KGIS services and test a count query in a small test box."""

import sys

import requests

H = {"User-Agent": "Mozilla/5.0 (GramMap college project)"}
BASE = "https://kgis.ksrsac.in"
SERVICES = sys.argv[1:] or [
    "kgismaps2/Boundaries/Village_Dynamic",
    "kgismaps/Education/Education_New",
    "kgismaps/Health/Health",
    "kgismaps2/GP_Utility/GP_Utility",
    "kgismaps2/RDPR_WS/RDPR_WS",
    "kgismaps2/GovtBuildings/GovtBuildings",
    "kgismaps2/Village_Ward_Census/Village_Ward_Census",
    "kgismaps2/Water_Utility/Water_Utility",
    "kgismaps2/PWD/PWD",
    "kgismaps2/GramaOne/GramaOne",
]
ENV = "77.45,13.25,77.60,13.35"  # around Doddaballapura, Bengaluru North
for s in SERVICES:
    srv, rest = s.split("/", 1)
    url = f"{BASE}/{srv}/rest/services/{rest}/MapServer"
    try:
        meta = requests.get(url + "?f=json", headers=H, timeout=60).json()
    except Exception as e:
        print("##", s, "ERR", e)
        continue
    print("##", s, "| caps:", meta.get("capabilities"), "| maxRecords:", meta.get("maxRecordCount"))
    for lyr in meta.get("layers", []):
        if lyr.get("subLayerIds"):
            continue
        q = {
            "where": "1=1",
            "geometry": ENV,
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "returnCountOnly": "true",
            "f": "json",
        }
        try:
            c = requests.get(f"{url}/{lyr['id']}/query", params=q, headers=H, timeout=60).json()
            n = c.get("count", c.get("error", {}).get("message"))
        except Exception as e:
            n = f"ERR {type(e).__name__}"
        print(f"   [{lyr['id']}] {lyr['name']}: {n}")
