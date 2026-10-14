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


report = os.path.join(ROOT, "docs/reports/S1_1_directory.md")
lgd_report = os.path.join(ROOT, "docs/reports/S1_1_lgd_comparison.md")
census_ok = False
if os.path.exists(report):
    import re

    m = re.search(r"With a Census 2011 code: \*\*[\d,]+\*\* \(([\d.]+)%\)", open(report).read())
    census_ok = bool(m) and float(m.group(1)) >= 95
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
    ("KGIS ArcGIS client (paging, retries, cache)", exists("pipelines/connectors/arcgis.py")),
    ("Directory builder: state, district, taluk, village", exists("pipelines/connectors/kgis.py")),
    ("Name normalization + transliteration variants", exists("pipelines/normalize/names.py")),
    ("LGD download parser + comparison", exists("pipelines/connectors/lgd.py")),
    ("Loader command run (Karnataka)", os.path.exists(report)),
    ("Pilot villages with Census code >= 95%", census_ok),
    (
        "LGD file downloaded (manual, captcha)",
        (
            any(
                f.endswith((".csv", ".xlsx"))
                for f in os.listdir(os.path.join(ROOT, "data/raw/lgd"))
            )
            if os.path.isdir(os.path.join(ROOT, "data/raw/lgd"))
            else False
        ),
    ),
    (
        "Pilot village count matches LGD",
        os.path.exists(lgd_report) and "**Match**" in open(lgd_report).read(),
    ),
    ("PR open with CI green", "SUCCESS,SUCCESS" in pr or "MERGED" in pr),
]

for done_step in [
    "S0.1 Source audit and pilot district selection",
    "S0.2 Repository, Docker and CI setup",
    "S0.3 Database schema and configuration files",
]:
    print(f"{done_step:<48} [done]")
print()
print("S1.1 LGD directory ingestion")
print("  Overall   " + bar(sum(d for _, d in tasks), len(tasks)))
print()
for name, done in tasks:
    print(f"  {'[x]' if done else '[ ]'} {name}")
