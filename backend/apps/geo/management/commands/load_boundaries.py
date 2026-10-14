"""Attach KGIS boundaries to the pilot villages and the district (PRD step S1.2).

python manage.py load_boundaries --district 526 --report docs/reports/S1_2_boundaries.md
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from apps.geo.models import District, Precision, Village
from apps.sources.models import PipelineRun
from pipelines.config import load_config
from pipelines.connectors.boundaries import (
    fetch_district_polygon,
    fetch_village_polygons,
    repair_and_merge,
)


def geos(mp):
    return GEOSGeometry(memoryview(mp.wkb), srid=4326)


class Command(BaseCommand):
    help = "Load village and district boundaries from KGIS for the pilot villages"

    def add_arguments(self, parser):
        parser.add_argument("--district", required=True, help="LGD district code")
        parser.add_argument("--report", help="write a Markdown report to this path")

    def handle(self, *args, district, report=None, **opts):
        run = PipelineRun.objects.create(
            kind=PipelineRun.Kind.BATCH,
            scope={"step": "S1.2", "source": "kgis_villages", "district": district},
            status=PipelineRun.Status.RUNNING,
            config_hash=load_config().hash,
        )
        cache = settings.DATA_DIR / "cache" / "kgis"
        villages = {v.lgd_code: v for v in Village.objects.filter(is_pilot=True)}

        def progress(n, total):
            self.stdout.write(f"\r  village codes {n}/{total} ({100 * n / total:.0f}%)", ending="")
            self.stdout.flush()

        try:
            features = fetch_village_polygons(villages, cache_dir=cache, progress=progress)
            self.stdout.write("")
            result = repair_and_merge(features)
            district_result = repair_and_merge(
                [
                    {**f, "properties": {"LGD_VillageCode": district}}
                    for f in fetch_district_polygon(district, cache_dir=cache)
                ]
            )
            with transaction.atomic():
                d = District.objects.get(code=district)
                d.boundary = geos(district_result.polygons[district])
                d.save(update_fields=["boundary"])
                for code, mp in result.polygons.items():
                    if code in villages:
                        v = villages[code]
                        v.boundary = geos(mp)
                        v.boundary_precision = Precision.EXACT
                        v.save(update_fields=["boundary", "boundary_precision"])
        except Exception as exc:
            run.status = PipelineRun.Status.FAILED
            run.errors = [repr(exc)]
            run.save()
            raise

        stats = summarize(district, villages, result)
        run.status = PipelineRun.Status.SUCCEEDED
        run.stats = stats
        run.finished_at = timezone.now()
        run.save()
        self.stdout.write(json.dumps(stats, indent=2, ensure_ascii=False))
        if report:
            Path(report).parent.mkdir(parents=True, exist_ok=True)
            Path(report).write_text(render(stats, result, run))
            self.stdout.write(f"report written to {report}")


def summarize(district, villages, result):
    total = len(villages)
    joined = [c for c in villages if c in result.polygons]
    census_agree = sum(
        1
        for c in joined
        if villages[c].census_code and villages[c].census_code in result.census_codes.get(c, set())
    )
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT
              count(*) FILTER (WHERE NOT ST_Within(ST_PointOnSurface(v.boundary), d.boundary)),
              percentile_cont(0.5) WITHIN GROUP (ORDER BY ST_Area(v.boundary::geography)) / 1e6,
              min(ST_Area(v.boundary::geography)) / 1e6,
              max(ST_Area(v.boundary::geography)) / 1e6,
              sum(ST_Area(v.boundary::geography)) / 1e6,
              ST_Area(d.boundary::geography) / 1e6,
              count(*) FILTER (WHERE NOT ST_IsValid(v.boundary))
            FROM geo_village v JOIN geo_district d ON d.code = %s
            WHERE v.is_pilot AND v.boundary IS NOT NULL
            GROUP BY d.boundary
            """,
            [district],
        )
        outside, median, smallest, largest, village_area, district_area, invalid = cur.fetchone()
    missing = sorted(set(villages) - set(result.polygons))
    return {
        "pilot_villages": total,
        "with_boundary": len(joined),
        "join_rate": round(len(joined) / total, 4) if total else None,
        "census_code_agrees_on_polygon": census_agree,
        "without_boundary": [f"{c} {villages[c].name}" for c in missing],
        "invalid_after_load": invalid,
        "outside_district": outside,
        "area_km2": {
            "median": round(median, 3),
            "min": round(smallest, 4),
            "max": round(largest, 2),
            "villages_total": round(village_area, 1),
            "district": round(district_area, 1),
        },
        "kgis": dict(result.stats),
    }


def render(s, result, run):
    a = s["area_km2"]
    lines = [
        "# S1.2 Village boundaries",
        "",
        f"- **Run:** PipelineRun {run.pk}, finished {run.finished_at:%Y-%m-%d %H:%M %Z}",
        "- **Source:** KGIS Village_Dynamic and Admin_Dynamic (district) layers, EPSG:4326",
        "- **Join key:** LGD village code (present on every KGIS polygon); Census code checked",
        "",
        "## Join rate",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Pilot villages (LGD list) | {s['pilot_villages']:,} |",
        f"| With a boundary | {s['with_boundary']:,} |",
        f"| **Join rate** | **{100 * s['join_rate']:.1f}%** (target 90%) |",
        f"| Polygon Census code agrees with village Census code | "
        f"{s['census_code_agrees_on_polygon']:,} |",
        f"| KGIS features fetched | {s['kgis'].get('features', 0):,} |",
        f"| Multi-part villages merged | {s['kgis'].get('multi_part_villages_merged', 0):,} |",
        f"| Invalid polygons repaired (make_valid) | "
        f"{s['kgis'].get('invalid_geometry_repaired', 0):,} |",
        f"| Invalid after load | {s['invalid_after_load']:,} |",
        f"| Village polygons whose interior point is outside the district | "
        f"{s['outside_district']:,} |",
        "",
        "## Areas (km²)",
        "",
        f"Median village {a['median']}, smallest {a['min']}, largest {a['max']}. "
        f"All village polygons {a['villages_total']:,} km² against a district area of "
        f"{a['district']:,} km².",
        "",
        f"## Villages without a boundary ({len(s['without_boundary'])})",
        "",
        "These are in LGD but have no KGIS polygon (mostly villages created after 2011). "
        "They get an approximate boundary from building clusters later (PRD Section 7.1).",
        "",
        "; ".join(s["without_boundary"]) or "None",
    ]
    for kind, ex in result.examples.items():
        lines += ["", f"Examples of {kind}: " + "; ".join(map(str, ex))]
    return "\n".join(lines) + "\n"
