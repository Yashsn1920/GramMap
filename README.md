# GramMap

Village asset mapping for Indian villages, built only from public online data
(OpenStreetMap, Overture, LGD, Census, UDISE+, KGIS, PMGSY and others).
The full specification is in [`docs/GramMap_PRD_v1.2.docx`](docs/GramMap_PRD_v1.2.docx).

## Quick start

Requirements: Docker with Compose v2.

```bash
git clone https://github.com/Yashsn1920/GramMap.git
cd GramMap
cp .env.example .env    # optional; the defaults work without it
docker compose up --build
```

| What | URL |
|---|---|
| Map (frontend) | http://localhost:5173 |
| API health check | http://localhost:8000/api/health |
| Django admin | http://localhost:8000/admin/ |
| Vector tiles (Martin) | http://localhost:3000/catalog |

The first start pulls images and builds the backend and frontend, which takes a few minutes.
Database migrations run automatically when the backend starts.

## Services

| Service | Image / build | Purpose |
|---|---|---|
| `db` | `pgrouting/pgrouting` (PostgreSQL 16, PostGIS 3.5, pgRouting) | Main database; `postgis`, `pgrouting`, `pg_trgm` enabled |
| `redis` | `redis:7-alpine` | Celery broker and result store |
| `backend` | `backend/Dockerfile` | Django + GeoDjango + DRF |
| `worker` | same image as backend | Celery worker |
| `tiles` | `ghcr.io/maplibre/martin` | Vector tiles straight from PostGIS |
| `frontend` | `frontend/Dockerfile` | React + Vite + MapLibre dev server |

Useful commands:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend pytest -q        # backend + pipeline tests
docker compose logs -f worker
docker compose down -v                       # stop and delete the database volume
```

## Development without Docker for the app

Run only the database and Redis in Docker, and the app on your machine:

```bash
docker compose up -d db redis
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements-dev.txt   # needs GDAL installed on the system
cd backend && python manage.py migrate && python manage.py runserver
cd frontend && npm install && npm run dev
```

## Checks (same as CI)

```bash
ruff check . && black --check . && pytest -q
cd frontend && npm run lint && npm run build
```

## Repository layout

```
config/      YAML configuration (categories, sources, norms, ...)
pipelines/   pure Python data pipelines (no Django imports)
backend/     Django project (grammap/) and apps (apps/)
frontend/    React + TypeScript + Vite + MapLibre
docker/      container init files
scripts/     one-off and audit scripts
docs/        PRD, source audit, decisions log
data/        downloads and cache (git-ignored)
notebooks/   exploration only
```

## Loading data

```bash
# S1.1 administrative directory (KGIS), then reconcile the pilot with the official LGD list
docker compose exec backend python manage.py load_directory --pilot-district 526 \
    --report /app/docs/reports/S1_1_directory.md
docker compose exec backend python manage.py compare_lgd /app/data/raw/lgd/villages_526.xlsx \
    --district 526 --apply --report /app/docs/reports/S1_1_lgd_comparison.md
```

The LGD file is a one-time manual download (captcha) from lgdirectory.gov.in: Download Directory,
villages of a specific district, Xls Report.

## Configuration

All thresholds, weights, mappings and norms are in `config/*.yaml`. They are loaded and validated by
`pipelines/config.py`:

```python
from pipelines.config import load_config
cfg = load_config()                  # raises ConfigError naming the file and field on any problem
cfg.categories["SCH"].match.meters   # 150
cfg.hash                             # stored on every pipeline run
```

Set `GRAMMAP_CONFIG_DIR` to load a different directory.

## Conventions

- Work on `feature/S<step>-<short-name>` branches and merge to `main` by pull request.
- Commit messages start with the PRD step ID, e.g. `S4.2: add pair scoring`.
- Thresholds, weights and mappings live in `config/*.yaml`, never in code.

Map data © OpenStreetMap contributors.
