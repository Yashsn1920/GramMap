"""S0.1: check that each candidate source's site or file endpoint responds."""

import concurrent.futures as cf

import requests

H = {"User-Agent": "Mozilla/5.0 (GramMap college project source audit)"}
SOURCES = {
    "LGD": "https://lgdirectory.gov.in/",
    "Overture S3 listing": "https://overturemaps-us-west-2.s3.amazonaws.com/?list-type=2&prefix=release/&delimiter=/",
    "Google Open Buildings tiles index": "https://openbuildings-public-dot-gweb-research.uw.r.appspot.com/public/tiles.geojson",
    "MS RoadDetections repo": "https://github.com/microsoft/RoadDetections",
    "MS GlobalMLBuildingFootprints links": "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv",
    "WorldPop data": "https://data.worldpop.org/GIS/Population/",
    "data.gov.in API": "https://api.data.gov.in/",
    "UDISE+": "https://udiseplus.gov.in/",
    "School GIS (NIC)": "https://schoolgis.nic.in/",
    "NHFR (ABDM)": "https://facility.abdm.gov.in/",
    "PMGSY GeoSadak": "https://geosadak-pmgsy.nic.in/",
    "PMGSY OMMAS": "https://omms.nic.in/",
    "Mission Antyodaya": "https://missionantyodaya.nic.in/",
    "JJM dashboard": "https://ejalshakti.gov.in/jjmreport/JJMIndia.aspx",
    "SHRUG": "https://www.devdatalab.org/shrug_download/",
    "Bhuvan": "https://bhuvan.nrsc.gov.in/",
    "DataMeet village boundaries": "https://github.com/datameet/indian_village_boundaries",
    "Census of India": "https://censusindia.gov.in/",
    "Karnataka KGIS": "https://kgis.ksrsac.in/",
    "Wikidata SPARQL": "https://query.wikidata.org/sparql?query=ASK%7B%7D&format=json",
    "JRC Global Surface Water": "https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence_70E_20Nv1_4_2021.tif",
    "Copernicus DEM (AWS)": "https://copernicus-dem-30m.s3.amazonaws.com/readme.html",
    "ESA WorldCover (AWS)": "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif",
}


def check(item):
    name, url = item
    try:
        r = requests.get(url, headers=H, timeout=30, stream=True, allow_redirects=True)
        size = r.headers.get("content-length", "?")
        r.close()
        return name, r.status_code, size, r.url[:90]
    except Exception as e:
        return name, "ERR", "", type(e).__name__ + ": " + str(e)[:80]


with cf.ThreadPoolExecutor(8) as ex:
    for res in ex.map(check, SOURCES.items()):
        print(" | ".join(map(str, res)))
