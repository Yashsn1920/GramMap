# S0.1 Source Audit and Pilot District Selection

- **Step:** S0.1 (PRD Section 15)
- **Date:** 2026-10-14
- **Region considered:** Bengaluru and neighbouring districts, Karnataka
- **Status:** Done. Pilot district chosen (Section 4).

Scripts used are in `scripts/audit/`. Raw outputs are in `data/samples/`. Downloaded data is in `data/raw/`; it is git-ignored and can be re-downloaded.

---

## 1. Summary

| Result | Detail |
|---|---|
| Biggest find | **KGIS** (Karnataka Geographic Information System, KSRSAC) publishes queryable ArcGIS REST services for the whole state. They include **official village boundaries already carrying LGD, Census 2011 and Gram Panchayat codes**, plus schools (with UDISE codes), GP water supply points, GP buildings, polio immunisation sites and government buildings. |
| Second biggest | **PMGSY GeoSadak** (via the DataMeet GitHub mirror, GODL licence): 64,555 Karnataka habitations with population and 61,042 geotagged rural facilities. |
| Global sources | Overture, ESA WorldCover, JRC Surface Water and Copernicus DEM all download fine. OpenStreetMap works through Overpass, but bulk downloads are very slow on our network (see Section 5). |
| Not usable | KGIS health layers (hidden), NHFR (needs login), Mission Antyodaya, the Census of India site and PMGSY's own portal (unreachable). LGD needs a captcha, but KGIS already provides LGD codes. |
| Effect on the PRD | The PRD's riskiest join, LGD to Census to boundary (Risk table, row 5), is **solved by KGIS**. Health facilities shift to PMGSY, OSM and Overture. |

---

## 2. Source-by-source results

Status meanings: **Usable** = tested with real data. **Partial** = works with limitations. **Blocked** = not accessible now. **Not needed** = covered by another source.

### 2.1 Karnataka state sources

| Source | Status | Access method | What we confirmed | Licence / notes |
|---|---|---|---|---|
| **KGIS village boundaries** | **Usable** | ArcGIS REST: `kgis.ksrsac.in/kgismaps2/rest/services/Boundaries/Village_Dynamic/MapServer/0` (Query enabled, max 1,000 records per request, so results must be paged) | Village polygons with `LGD_VillageCode`, `CensusVillageCode`, `LGDGPCode`, `KGISVillageID`, `KGISVillageName`, `BhoomiVillageCode` | Government portal. Terms not stated on the service; attribute KSRSAC/KGIS. Confirm terms before any public release. |
| KGIS Gram Panchayat boundaries | Usable | `.../Boundaries/GP_Boundary/MapServer/0` | GP polygons | Same as above |
| **KGIS schools** | **Usable** | `kgismaps/rest/services/Education/Education_New/MapServer/1` (max 100,000 records) | `SCHName`, `Category` (Primary / Upper Primary and Secondary...), `DepartmentCode` = 11-digit **UDISE code**, `KGISVillageID` | Also layers for PU colleges, degree and engineering colleges, polytechnics |
| **KGIS GP water supply** | **Usable** | `kgismaps2/.../GP_Utility/GP_Utility/MapServer/2` | Water supply points linked to `KGISVillageId`; names are mostly empty | Main source for water assets |
| KGIS GP buildings | Usable | `.../GP_Utility/MapServer/0` | Panchayat offices; name values are inconsistent ("GP office", "1") | Needs cleaning |
| KGIS polio immunisation sites | Usable | `kgismaps2/.../Health/Immunisation_Centers/MapServer/0` | Points; a proxy for health outreach locations (often anganwadis or sub-centres) | Routine immunisation layer is empty |
| KGIS government buildings | Usable | `.../GovtBuildings/GovtBuildings/MapServer/0` | Points | Small counts |
| KGIS GramaOne / CSC | Usable | `.../GramaOne/GramaOne/MapServer/0,1` | Citizen service centres | Optional category |
| KGIS PWD bridges | Usable | `.../PWD/PWD/MapServer/1` | Bridges | Useful for what-if "block a bridge" |
| KGIS health facilities | **Blocked** | `kgismaps/.../Health/Health/MapServer` | The service is listed, but all 26 health sub-layers are hidden (sub-layer id −1) | Use PMGSY / OSM / Overture instead |
| KGIS Village_Ward_Census | Blocked | `.../Village_Ward_Census/MapServer` | No layers exposed | — |
| KGIS DWCD (anganwadis), AssetRegistry | Blocked | Folders exist but are empty | — | Anganwadis: try OSM names and data.gov.in later (S2.x) |

### 2.2 National government sources

| Source | Status | Access method | What we confirmed | Licence / notes |
|---|---|---|---|---|
| **PMGSY GeoSadak** | **Usable** | DataMeet mirror: `github.com/datameet/pmgsy-geosadak` (`data/Habitation/Karnataka.zip`, `data/Facilities/Karnataka.zip`, `data/Road_DRRP/Karnataka-split.*` about 114 MB) | Habitations: `HAB_ID`, `HAB_NAME`, `TOT_POPULA` (64,555 in Karnataka). Facilities: `FAC_DESC` (free text), `FAC_CATEGO` (Education / Medical / Agro / Transport/Admin), 61,042 points | GODL-India. Mirror last updated **July 2022**, so the data is a 2022 snapshot. PMGSY district IDs are internal, so join spatially. The official portal `geosadak-pmgsy.nic.in` does not resolve from our network. |
| UDISE+ School GIS | Partial | React app at `schoolgis.udiseplus.gov.in`; data comes from `geoportal.nic.in/nicgis/rest/services/SCHOOLGIS/Schooldata/MapServer/0` | `geoportal.nic.in` resets TLS connections from our network | **Not needed** for the pilot: KGIS schools already carry UDISE codes. Retry later for school attributes. |
| UDISE+ public API | Partial | `api.udiseplus.gov.in/public-api/v1.1/district-school-count/public` | Found in the School GIS code; not yet tested | Good for checking district school counts |
| LGD | Partial | `lgdirectory.gov.in` download pages work but need a captcha | — | **Not needed now**: KGIS provides LGD village and GP codes. A one-time manual download is optional for official names and hierarchy. |
| NHFR (health facility registry) | Blocked | `facility.abdm.gov.in` redirects to the professionals registry (login) | — | Health comes from other sources |
| Mission Antyodaya | Blocked | `missionantyodaya.nic.in` does not resolve | 2020 survey data is reported on data.gov.in and AIKosh | Revisit in S2.6 (expected amenities) |
| Census of India site | Blocked | `censusindia.gov.in` TLS certificate error | — | Census village amenities: try data.gov.in or SHRUG in S2.6 |
| data.gov.in API | Partial | `api.data.gov.in` responds; needs a free API key | — | Register a key before S2.6 |
| JJM dashboard | Usable (site) | `ejalshakti.gov.in/jjmreport/JJMIndia.aspx` | Site responds | Village-level tap coverage: optional, later |
| Bhuvan | Usable (site) | `bhuvan.nrsc.gov.in` | Site responds | Not needed: KGIS covers boundaries |
| SHRUG | Usable (site) | `devdatalab.org/shrug_download` | Site responds | Option for Census 2011 village tables in S2.6 (check licence) |
| DataMeet village boundaries | Not needed | GitHub | Karnataka layer is from Census 1991 and has ±500 m registration error | KGIS is better |

### 2.3 Global sources

| Source | Status | Access method | What we confirmed | Licence |
|---|---|---|---|---|
| **Overture Maps** | **Usable** | DuckDB over `s3://overturemaps-us-west-2/release/2026-09-23.1/` (about 420 KB/s from our network) | District boundaries for all 5 candidates (`divisions`, subtype `county`); places extracted for the region (Section 3) | Mixed by theme (CDLA-Permissive / ODbL) |
| **OpenStreetMap (Overpass)** | Usable (slow) | `overpass-api.de` and `overpass.kumi.systems` | District relations carry `ref:LGD:district` | ODbL |
| OSM bulk extracts | Partial | Geofabrik `southern-zone` (558 MB), openstreetmap.fr `karnataka` (129 MB) | Both download at only about 5 KB/s on our network | Download on another network, or use Overpass per area |
| Google Open Buildings | Usable | Tiles index responds | Also included inside Overture buildings | CC BY 4.0 / ODbL |
| Microsoft building footprints | Usable | `dataset-links.csv` responds (large) | Also included inside Overture buildings | ODbL |
| Microsoft Road Detections | Usable (repo) | GitHub repo responds | Not yet downloaded | ODbL |
| WorldPop | Partial | `data.worldpop.org` very slow (under 1 KB/s) | — | CC BY 4.0. Alternative: PMGSY habitation populations. |
| JRC Global Surface Water | Usable | Google Cloud Storage, about 260 KB/s | Tile for 70E 20N responds (49 MB) | Free, attribution |
| ESA WorldCover | Usable | AWS, about 1.8 MB/s | Tile N12E075 responds (128 MB) | CC BY 4.0 |
| Copernicus DEM | Usable | AWS bucket | Responds | Free, attribution |
| Wikidata | Usable | SPARQL endpoint | Responds | CC0 |

---

## 3. Candidate district comparison

The five districts around Bengaluru (2025 names; **Bengaluru North was Bengaluru Rural** and **Bengaluru South was Ramanagara**). Tumakuru was excluded as too large (about 10,600 km²).

KGIS counts include features crossing the district boundary, so totals are slightly high. Population is the sum of PMGSY habitation populations (rural only).

| Measure | Bengaluru North | Bengaluru South | Bengaluru Urban | Chikkaballapura | Kolar |
|---|---|---|---|---|---|
| Area (km², Overture) | 2,302 | 3,515 | 2,192 | 4,243 | 3,979 |
| **KGIS villages** | 1,379 | 1,012 | 1,174 | 1,757 | 2,038 |
| KGIS Gram Panchayats | 264 | 256 | 165 | 278 | 265 |
| KGIS schools | 1,529 | 1,737 | 6,153 | 2,055 | 2,494 |
| KGIS PU colleges | 71 | 88 | 705 | 111 | 122 |
| KGIS GP water supply points | 1,827 | 2,814 | 2,293 | 4,270 | 2,533 |
| KGIS GP buildings | 130 | 87 | 152 | 113 | 128 |
| KGIS polio immunisation sites | 462 | 592 | 3,857 | 357 | 753 |
| PMGSY habitations | 1,364 | 1,921 | 1,172 | 1,869 | 2,013 |
| PMGSY rural population | 800,151 | 832,392 | 836,705 | 1,318,449 | 1,150,521 |
| PMGSY facilities: Education | 248 | 256 | 400 | 166 | 263 |
| PMGSY facilities: Medical | 205 | 242 | 113 | 158 | 268 |
| PMGSY facilities: Transport/Admin | 290 | 289 | 481 | 339 | 469 |
| PMGSY facilities: Agro | 606 | 844 | 495 | 898 | 1,164 |
| OSM schools | 77 | – | – | – | 26 |
| OSM colleges | 27 | – | – | – | 20 |
| OSM health (hospital/clinic/doctors) | 65 | – | – | – | 101 |
| OSM anganwadis (by name) | 2 | – | – | – | 0 |
| OSM water towers / tanks | 88 | – | – | – | 6 |
| OSM wells / pumps | 84 | – | – | – | – |
| OSM drinking water points | 5 | – | – | – | – |
| OSM water bodies | 9,286 | – | – | – | – |
| OSM government offices | 8 | – | – | – | – |
| OSM post offices | 3 | – | – | – | – |
| OSM banks / ATMs | 30 | – | – | – | – |
| OSM village / hamlet place nodes | 784 | – | – | – | – |
| Overture schools | 113 | 45 | 3,086 | 44 | 54 |
| Overture colleges | 78 | 66 | 1,996 | 46 | 72 |
| Overture health | 103 | 71 | 7,201 | 48 | 106 |
| Overture banks / ATMs | 266 | 205 | 6,509 | 165 | 189 |
| Overture government offices | 71 | 45 | 1,665 | 32 | 54 |

"–" = not counted. OSM was counted only for the two finalists because every Overpass server was overloaded during the audit. Kolar has 5 of 12 categories; the rest timed out. This doesn't affect the decision, since Kolar is the backup. Where both were counted, Bengaluru North has about 3× the OSM schools and 15× the water towers.

**Key observation:** in the rural districts, OSM and Overture each list only about 25 to 115 schools, against 1,500 to 2,500 in KGIS. Open global sources alone would miss over 90% of rural schools. This is the main justification for the multi-source design and will be the headline chart in the 'value added by each source' evaluation (PRD Section 13.2).

---

## 4. Pilot district decision

**Pilot district: Bengaluru North (formerly Bengaluru Rural).** Backup: Kolar.

**Why Bengaluru North**

1. **Rural, but not too big.** About 1,380 villages and 264 Gram Panchayats on 2,302 km². That's large enough for meaningful district analytics and small enough to process quickly on a laptop. Kolar and Chikkaballapura have 50% more villages.
2. **Strong official coverage.** KGIS has 1,529 schools, 1,827 GP water supply points, 130 GP buildings and 462 immunisation sites, plus village and GP boundaries with LGD codes. PMGSY adds 1,364 habitations (800,151 rural people) and 743 rural education, medical and admin facilities.
3. **Best OSM and Overture coverage of the rural candidates** (Section 3), which helps conflation and the source-value evaluation.
4. **Interesting for analysis.** Its four taluks (Devanahalli, Doddaballapura, Hosakote, Nelamangala) range from fast-growing peri-urban areas near the airport and highways to fully rural interiors, so access and gap scores will vary.
5. **Close to the team**, which helps when checking results against imagery and local knowledge.

**Why not the others**

- **Bengaluru Urban:** mostly city wards, not villages. The project is about villages.
- **Bengaluru South:** a good candidate, but larger (3,515 km²) and its KGIS boundaries cover fewer villages (1,012) relative to habitations (1,921), so village linking would be harder.
- **Chikkaballapura and Kolar:** more rural, but larger, and weaker in OSM and Overture. Kolar is the backup because it has the most villages and good PMGSY medical coverage.

**Test village for development:** villages around **Doddaballapura** (the KGIS test box `77.45,13.25,77.60,13.35`; 123 villages, saved in `data/samples/kgis_villages_testbox.geojson`). Steps S1 to S4 are built and tested on this box first, then run on the whole district.

---

## 5. Problems found and how we handle them

| Problem | Impact | Handling |
|---|---|---|
| OSM mirrors download at about 5 KB/s on our network | Cannot fetch bulk OSM extracts now | Use Overpass per district or per village (works). Download the 129 MB Karnataka extract once on a faster network (college Wi-Fi) for S2.2. |
| Overpass servers are often overloaded | Slow or failed queries | The connector (S2.1) must retry, back off and switch mirrors; cache all results. |
| KGIS returns at most 1,000 records per request (100,000 for schools) | Large layers need several requests | Page with `resultOffset` / `resultRecordCount`, or split by Gram Panchayat. |
| KGIS hides health layers | No official health locations | Health from PMGSY Medical + OSM + Overture, with conflation. |
| PMGSY facility descriptions are free text ("phc", "primary health center", "primary health centre") | Category mapping is harder | Keyword rules plus the name normalization in S3.2. These are good test cases. |
| PMGSY mirror is a 2022 snapshot | Some data is older | Recency weight in the confidence score (PRD 7.5) handles this. |
| Some national portals unreachable (`*.nic.in` DNS and TLS failures) | Fewer sources | Not essential now; retry during S2.x. Record in this file. |
| Mixed CRS labels in DuckDB (EPSG:4326 vs OGC:CRS84) | Spatial joins fail | Normalise every source to EPSG:4326 in the silver layer (PRD FR-3.2). |

---

## 6. Changes to make in the PRD (Change Log v1.1)

1. Section 5.2: add **KGIS** as a Must source for Karnataka (village boundaries with codes, schools, GP water supply, GP buildings, immunisation sites, bridges).
2. Section 5.2: PMGSY access is through the **DataMeet GitHub mirror** (2022 snapshot); the official portal is unreachable.
3. Section 5.2: NHFR, Mission Antyodaya and the Census site are **blocked for now**; LGD is optional because KGIS provides LGD codes.
4. Section 7.1: the village master list for Karnataka comes from **KGIS** (LGD and Census codes on each polygon), not a separate LGD + boundary join.
5. Section 14 (Risks): the LGD-to-boundary join risk is resolved for Karnataka. Add a new risk: slow OSM bulk downloads on the home network.
6. Title page: pilot district fixed (Section 4 above).

---

## 7. Sample files

| File | Contents |
|---|---|
| `data/samples/candidate_districts.geojson` | Boundaries of the 5 candidate districts (Overture divisions) |
| `data/samples/kgis_probe.txt` | KGIS layer list and test-box counts |
| `data/samples/kgis_district_counts.json` | KGIS counts per district |
| `data/samples/osm_coverage.json` | OSM counts per district |
| `data/raw/pmgsy/Habitation_Karnataka.zip`, `Facilities_Karnataka.zip` | PMGSY Karnataka layers |
| `data/raw/overture/places_2026-09-23.1_blr_region.parquet` | Overture places for the region |
