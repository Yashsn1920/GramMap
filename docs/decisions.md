# Decisions log

Dated entries for choices that change the PRD (PRD Section 12.2). Each one also has a Change Log row.

## 2026-10-14 — S0.2 stack versions

- Django **5.2 LTS** (not 6.x): the PRD names Django 5, and 5.2 has support until April 2028.
- Images: `pgrouting/pgrouting:16-3.5-3.8` (PostgreSQL 16, PostGIS 3.5, pgRouting 3.8), `ghcr.io/maplibre/martin:1.16.1`, `redis:7-alpine`, `python:3.12-slim-bookworm`, `node:22-alpine`.
- Frontend: React 19, Vite 8, MapLibre GL 5, TypeScript 6, ESLint 10.

## 2026-10-14 — S0.3 data model and config (PRD v1.2)

- **`village.gp_lgd_code` added.** KGIS village polygons carry the LGD Gram Panchayat code (S0.1), and GP is the unit for GP water supply and GP buildings. Storing it avoids a later migration.
- **`water_body.geom` is MULTIPOLYGON**, not POLYGON: OSM water relations often have several parts.
- **Codes are stored as text** (state, district, block, village, census), so Census codes keep leading zeros.
- **Uniqueness constraints** that the PRD implies but does not list: `bronze_record (source, content_hash)` for idempotent re-runs (S2.1), `source_record (source, source_id)`, `asset_source_link (asset, source_record)`, `match_review (record_a, record_b)`, `settlement_access (settlement, category, mode)`, `expected_amenity (village, category, source)`.
- **`gap_flag.kind`** values: `missing`, `unlisted`, `count_mismatch` (Section 7.7) and `unmapped_road` (Section 7.8).
- **Custom user model** (`accounts.User`, with `role`) is in place from the first migration, because swapping it later is painful in Django.
- **`config/pipeline.yaml` added** to the six files in Section 12.1. It holds the numeric parameters of Sections 7.1, 7.4 to 7.8, 7.13 and 7.14 (buffers, conflation weights and thresholds, confidence factors, DBSCAN settings, road-gap thresholds, completeness weights), so none of them are hard-coded.
- **Category is stored as its 3-letter code, without database choices.** The list lives in `config/categories.yaml`, so adding a category needs no migration.
- **Source weights** (Section 7.5) are in `sources.yaml`: `weight` for each source, plus `geocoded_weight` (0.40) for government sources whose records are placed by the geocoding fallback.
- **Config loader** is in `pipelines/config.py` (pydantic, no Django) so pipelines and backend share it. It rejects unknown keys, checks weights sum to 1, keeps thresholds in order, and cross-checks references between files. `Config.hash` is stored as `pipeline_run.config_hash`.

## 2026-10-14 — S1.1 administrative directory

- **Source is KGIS, not an LGD bulk download.** LGD download pages need a captcha; KGIS `Admin_Dynamic` (state, district, taluk, hobli) and `Village_Dynamic` layers carry the LGD district, sub-district and village codes, Census 2011 codes and LGD GP codes (PRD 7.1 already says this for Karnataka). A hand-downloaded LGD list is used only to verify counts (`manage.py compare_lgd`).
- **Block = taluk (LGD sub-district).** Karnataka's LGD hierarchy below district is the taluk; KGIS gives its `LGD_TalukCode`. Villages are linked to taluks through their hobli.
- **District names are KGIS names.** The pilot is stored as "Bengaluru (Rural)" (LGD 526); the 2025 name is Bengaluru North.
- **Census code** = last 6 digits of KGIS `CensusVillageCode` (state 2 + district 3 + sub-district 5 + village 6). `000000` and the placeholder `999999` count as missing.
- **Shared Census codes are kept.** 172 pilot villages share a Census code with another village, usually because an LGD village was split or renumbered after 2011. S2.6 joins Census tables by code, so these will be handled there (for example by splitting counts or joining by name).
- **Multi-polygon villages are merged by LGD code** (2,229 extra rows statewide); 219 statewide (1 pilot) have the same code with a different name or taluk and are logged.
- **is_pilot is set in S1.1** from the district, so S1.2 only has to attach polygons.
- **Village name variants** for search: cleaned name, name without spaces, and a phonetic key (`pipelines/normalize/names.py`) that maps romanization variants such as Doddaballapura / Dodballapur to one form. Kannada-script names are not in KGIS; they can come from OSM `name:kn` in S2.2.
- **LGD wins for pilot membership** (`compare_lgd --apply`, after the official LGD list for district 526 was downloaded on 2026-10-14). LGD lists 1,171 villages against 1,139 from KGIS: 29 post-2011 villages (codes 910xxx and above, no Census 2011 code) and 3 older ones are missing from KGIS and were added without boundaries; 3 that KGIS places in Bengaluru South were moved to Nelamangala; 3 KGIS villages with codes LGD does not list for this district (same names, other codes) are kept with is_pilot = false. After this the pilot matches LGD exactly. Re-running `load_directory` undoes the moves, so always run `compare_lgd --apply` after it.

## 2026-10-14 — S1.2 village boundaries

- **Join by LGD code, not Census code.** Every KGIS polygon carries `LGD_VillageCode`, which is our primary key, so the PRD's "join by Census code" step is not needed for Karnataka. The Census code on each polygon is checked instead: it agrees for 1,137 of the 1,139 joined villages.
- **Join rate 97.3%** (1,139 of 1,171). The 32 without a polygon are LGD-only villages (29 created after 2011, plus 3 older ones KGIS lacks). They get approximate boundaries from building clusters in a later step (PRD 7.1, `boundary_precision = approximate`).
- **Geometry handling uses Shapely 2 in `pipelines/`** (make_valid, keep polygonal parts, union multi-part villages), so it is testable without a database. 75 multi-part villages were merged and 1 invalid polygon was repaired.
- **The 3 villages LGD moves into Nelamangala keep their KGIS polygons**, which lie in Bengaluru South. They show as 3 polygons outside the district outline. That is a disagreement between the two government sources, and we keep both facts.
- **Map layers** are Martin vector tiles of `geo_village` and `geo_district`, requested from `/tiles/<table>/{z}/{x}/{y}` through the Vite proxy. `lgd_code` is promoted to the feature id for hover state.
