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


APPS = ["geo", "sources", "assets", "analytics", "accounts"]
CONFIGS = [
    "categories",
    "sources",
    "field_priority",
    "abbreviations",
    "norms",
    "speeds",
    "pipeline",
]

running_svcs = sh("docker", "compose", "ps", "--status", "running", "--services").split()
applied = sh(
    "docker", "compose", "exec", "-T", "backend", "python", "manage.py", "showmigrations", "--plan"
)
tests = sh("docker", "compose", "exec", "-T", "-w", "/app", "backend", "pytest", "-q")
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
    (
        "Models for geo, sources, assets, analytics, accounts",
        all(exists(f"backend/apps/{a}/models.py") for a in APPS),
    ),
    (
        "Migrations created",
        all(
            exists(
                f"backend/apps/{a}/migrations/0001_"
                + ("extensions.py" if a == "geo" else "initial.py")
            )
            for a in APPS
        ),
    ),
    ("GiST + trigram indexes", text_has("backend/apps/geo/models.py", "gin_trgm_ops")),
    ("config/*.yaml with Section 7 values", all(exists(f"config/{c}.yaml") for c in CONFIGS)),
    (
        "Config loader (pydantic) + tests",
        exists("pipelines/config.py") and exists("pipelines/tests/test_config.py"),
    ),
    ("Models registered in admin", all(exists(f"backend/apps/{a}/admin.py") for a in APPS)),
    ("Migrations apply on empty database", "[ ]" not in applied and "analytics.0001" in applied),
    ("All tests pass", " passed" in tests and "failed" not in tests),
    (
        "Decisions log + PRD v1.2",
        exists("docs/decisions.md") and exists("docs/GramMap_PRD_v1.2.docx"),
    ),
    ("PR open with CI green", "SUCCESS,SUCCESS" in pr or "MERGED" in pr),
]

print("S0.1 Source audit and pilot district selection  [done]")
print("S0.2 Repository, Docker and CI setup             [done]")
print()
print("S0.3 Database schema and configuration files")
print("  Overall   " + bar(sum(d for _, d in tasks), len(tasks)))
print()
for name, done in tasks:
    print(f"  {'[x]' if done else '[ ]'} {name}")
