"""S0.1: count official KGIS features inside each candidate district polygon."""

import json

import duckdb
import requests

H = {"User-Agent": "Mozilla/5.0 (GramMap college project)"}
B = "https://kgis.ksrsac.in"
LAYERS = {
    "villages": "kgismaps2/rest/services/Boundaries/Village_Dynamic/MapServer/0",
    "gram_panchayats": "kgismaps2/rest/services/Boundaries/GP_Boundary/MapServer/0",
    "schools": "kgismaps/rest/services/Education/Education_New/MapServer/1",
    "puc_colleges": "kgismaps/rest/services/Education/Education_New/MapServer/3",
    "gp_water_supply": "kgismaps2/rest/services/GP_Utility/GP_Utility/MapServer/2",
    "gp_buildings": "kgismaps2/rest/services/GP_Utility/GP_Utility/MapServer/0",
    "polio_sites": "kgismaps2/rest/services/Health/Immunisation_Centers/MapServer/0",
    "govt_buildings": "kgismaps2/rest/services/GovtBuildings/GovtBuildings/MapServer/0",
}
con = duckdb.connect()
con.load_extension("spatial")
rows = con.sql(
    """SELECT name, ST_AsGeoJSON(ST_SimplifyPreserveTopology(ST_MakeValid(geom), 0.005))
                  FROM ST_Read('data/samples/candidate_districts.geojson') ORDER BY name"""
).fetchall()
out = {}
for name, gj in rows:
    g = json.loads(gj)
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    esri = json.dumps(
        {"rings": [ring for p in polys for ring in p], "spatialReference": {"wkid": 4326}}
    )
    out[name] = {}
    for key, path in LAYERS.items():
        data = {
            "where": "1=1",
            "geometry": esri,
            "geometryType": "esriGeometryPolygon",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "returnCountOnly": "true",
            "f": "json",
        }
        try:
            r = requests.post(f"{B}/{path}/query", data=data, headers=H, timeout=120).json()
            out[name][key] = r.get("count", r.get("error", {}).get("message"))
        except Exception as e:
            out[name][key] = f"ERR {type(e).__name__}"
    print(name, out[name], flush=True)
json.dump(out, open("data/samples/kgis_district_counts.json", "w"), indent=1)
