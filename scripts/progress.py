"""Show progress of the current step's tasks and running jobs.

Usage:  python3 scripts/progress.py          (from the project folder)
        watch -n 10 python3 scripts/progress.py   (live refresh)
"""

import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bar(done, total, width=20):
    pct = 100 * done / total if total else 100
    filled = round(width * pct / 100)
    return f"[{'#' * filled}{'.' * (width - filled)}] {pct:5.1f}%  ({done}/{total})"


def running(pattern):
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return any(line.startswith(".venv/bin/python " + pattern) for line in out.splitlines())


# ---- S0.1 checklist: (task, done?) ----
def exists(p):
    return os.path.exists(os.path.join(ROOT, p))


def text_has(p, s):
    try:
        return s in open(os.path.join(ROOT, p)).read()
    except OSError:
        return False


def sh(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=20)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


IMAGES = [
    "pgrouting/pgrouting:16-3.5-3.8",
    "ghcr.io/maplibre/martin:v1.16.1",
    "redis:7-alpine",
    "python:3.12-slim-bookworm",
    "node:22-alpine",
]
SERVICES = ["db", "redis", "backend", "worker", "tiles", "frontend"]

have_images = sh("docker", "images", "--format", "{{.Repository}}:{{.Tag}}").split()
running_svcs = sh("docker", "compose", "ps", "--status", "running", "--services").split()
ci = sh("gh", "run", "list", "--limit", "1", "--json", "conclusion", "-q", ".[0].conclusion")

tasks = [
    (
        "Repository layout (Section 12.1)",
        all(
            exists(p) for p in ["config", "pipelines", "backend/apps", "frontend/src", "notebooks"]
        ),
    ),
    (
        "docker-compose.yml with 6 services",
        all(text_has("docker-compose.yml", f"  {s}:") for s in SERVICES),
    ),
    (
        "Extensions postgis, pgrouting, pg_trgm",
        exists("backend/apps/geo/migrations/0001_extensions.py"),
    ),
    ("Django + GeoDjango + DRF + /api/health", exists("backend/grammap/health.py")),
    (
        "React + Vite + MapLibre with OSM basemap",
        exists("frontend/src/map/BaseMap.tsx") and exists("frontend/package-lock.json"),
    ),
    ("GitHub Actions workflow", exists(".github/workflows/ci.yml")),
    (".env.example and README", exists(".env.example") and text_has("README.md", "Quick start")),
    ("Base images pulled", all(i in have_images for i in IMAGES)),
    ("Stack running (docker compose up)", all(s in running_svcs for s in SERVICES)),
    ("/api/health returns OK", '"ok"' in sh("curl", "-sf", "localhost:8000/api/health")),
    ("Map served at localhost:5173", "GramMap" in sh("curl", "-sf", "localhost:5173")),
    ("Pushed to GitHub", bool(sh("git", "ls-remote", "--heads", "origin"))),
    ("CI green", ci.strip() == "success"),
]

print("S0.1 Source audit and pilot district selection  [done]")
print()
print("S0.2 Repository, Docker and CI setup")
print("  Overall   " + bar(sum(d for _, d in tasks), len(tasks)))
print()
for name, done in tasks:
    print(f"  {'[x]' if done else '[ ]'} {name}")
print()
print("  Images    " + bar(sum(i in have_images for i in IMAGES), len(IMAGES)))
