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
