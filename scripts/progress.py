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


report = os.path.join(ROOT, "docs/reports/S1_2_boundaries.md")
join_ok = False
if os.path.exists(report):
    import re

    m = re.search(r"\*\*Join rate\*\* \| \*\*([\d.]+)%", open(report).read())
    join_ok = bool(m) and float(m.group(1)) >= 90
tiles = sh("curl", "-sf", "localhost:3000/catalog")
pr = sh(
    "gh",
    "pr",
    "view",
    "--json",
    "state,statusCheckRollup",
    "-q",
    '.state + " " + ([.statusCheckRollup[].conclusion] | join(","))',
)

tasks = [
    ("Fetch KGIS village polygons by LGD code", exists("pipelines/connectors/boundaries.py")),
    (
        "Repair (make_valid) and merge multi-part villages",
        exists("pipelines/tests/test_boundaries.py"),
    ),
    (
        "District boundary loaded; pilot marked",
        exists("backend/apps/geo/management/commands/load_boundaries.py"),
    ),
    ("Join-rate report written", os.path.exists(report)),
    ("Join rate >= 90%", join_ok),
    ("Village tiles served by Martin", "geo_village" in tiles),
    ("Boundaries drawn on the map (screenshot checked)", exists("docs/reports/S1_2_map.png")),
    ("PR open with CI green", "SUCCESS,SUCCESS" in pr or "MERGED" in pr),
]

for done_step in [
    "S0.1 Source audit and pilot district selection",
    "S0.2 Repository, Docker and CI setup",
    "S0.3 Database schema and configuration files",
    "S1.1 LGD directory ingestion",
]:
    print(f"{done_step:<48} [done]")
print()
print("S1.2 Village boundaries")
print("  Overall   " + bar(sum(d for _, d in tasks), len(tasks)))
print()
for name, done in tasks:
    print(f"  {'[x]' if done else '[ ]'} {name}")
