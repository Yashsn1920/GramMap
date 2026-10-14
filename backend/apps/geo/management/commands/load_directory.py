"""Load the administrative directory (state, districts, blocks, villages) for Karnataka from KGIS.

    python manage.py load_directory                     # whole state
    python manage.py load_directory --pilot-district 526 --report docs/reports/S1_1_directory.md

Safe to re-run: rows are upserted by their LGD code.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.geo.models import Block, District, State, Village
from apps.sources.models import PipelineRun
from pipelines.config import load_config
from pipelines.connectors.kgis import build_directory, fetch_directory


class Command(BaseCommand):
    help = "Load state, districts, blocks (taluks) and villages from KGIS"

    def add_arguments(self, parser):
        parser.add_argument("--pilot-district", help="LGD district code to mark is_pilot")
        parser.add_argument("--report", help="write a Markdown report to this path")

    def handle(self, *args, pilot_district=None, report=None, **opts):
        cfg = load_config()
        run = PipelineRun.objects.create(
            kind=PipelineRun.Kind.BATCH,
            scope={"step": "S1.1", "source": "kgis_villages", "pilot_district": pilot_district},
            status=PipelineRun.Status.RUNNING,
            config_hash=cfg.hash,
        )

        def progress(n, total):
            self.stdout.write(f"\r  villages {n}/{total} ({100 * n / total:.0f}%)", ending="")
            self.stdout.flush()

        try:
            raw = fetch_directory(cache_dir=settings.DATA_DIR / "cache" / "kgis", progress=progress)
            self.stdout.write("")
            directory = build_directory(raw)
            with transaction.atomic():
                counts = self.save(directory, pilot_district)
        except Exception as exc:
            run.status = PipelineRun.Status.FAILED
            run.errors = [repr(exc)]
            run.save()
            raise

        stats = {**counts, "issues": dict(directory.issues)}
        if pilot_district:
            stats["pilot"] = pilot_stats(pilot_district)
            pilot_codes = set(
                Village.objects.filter(block__district_id=pilot_district).values_list(
                    "lgd_code", flat=True
                )
            )
            stats["pilot"]["issues"] = {
                kind: len(codes & pilot_codes)
                for kind, codes in sorted(directory.village_issues.items())
            }
        run.status = PipelineRun.Status.SUCCEEDED
        run.stats = stats
        run.finished_at = timezone.now()
        run.save()

        self.stdout.write(json.dumps(stats, indent=2))
        if report:
            Path(report).parent.mkdir(parents=True, exist_ok=True)
            Path(report).write_text(render_report(stats, directory, pilot_district, run))
            self.stdout.write(f"report written to {report}")

    def save(self, d, pilot_district):
        State.objects.bulk_create(
            [State(code=r.code, name=r.name) for r in d.states],
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=["name"],
        )
        District.objects.bulk_create(
            [District(code=r.code, name=r.name, state_id=r.parent) for r in d.districts],
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=["name", "state"],
        )
        Block.objects.bulk_create(
            [Block(code=r.code, name=r.name, district_id=r.parent) for r in d.blocks],
            update_conflicts=True,
            unique_fields=["code"],
            update_fields=["name", "district"],
        )
        pilot_blocks = {r.code for r in d.blocks if r.parent == pilot_district}
        Village.objects.bulk_create(
            [
                Village(
                    lgd_code=v.lgd_code,
                    census_code=v.census_code,
                    gp_lgd_code=v.gp_lgd_code,
                    block_id=v.block_code,
                    name=v.name,
                    norm_name=v.norm_name,
                    name_variants=v.name_variants,
                    is_pilot=v.block_code in pilot_blocks,
                )
                for v in d.villages
            ],
            update_conflicts=True,
            unique_fields=["lgd_code"],
            update_fields=[
                "census_code",
                "gp_lgd_code",
                "block",
                "name",
                "norm_name",
                "name_variants",
                "is_pilot",
            ],
            batch_size=2000,
        )
        return {
            "states": State.objects.count(),
            "districts": District.objects.count(),
            "blocks": Block.objects.count(),
            "villages": Village.objects.count(),
        }


def pilot_stats(district_code):
    qs = Village.objects.filter(block__district_id=district_code)
    total = qs.count()
    with_census = qs.exclude(census_code="").count()
    return {
        "district": District.objects.get(code=district_code).name,
        "villages": total,
        "with_census_code": with_census,
        "census_share": round(with_census / total, 4) if total else None,
        "by_block": {
            b.name: b.villages.count()
            for b in Block.objects.filter(district_id=district_code).order_by("name")
        },
    }


def render_report(stats, d, pilot_district, run):
    lines = [
        "# S1.1 Administrative directory load",
        "",
        f"- **Run:** PipelineRun {run.pk}, finished {run.finished_at:%Y-%m-%d %H:%M %Z}",
        "- **Source:** KGIS (KSRSAC) Admin_Dynamic and Village_Dynamic layers (attributes only)",
        f"- **Config hash:** `{run.config_hash[:12]}`",
        "",
        "## Totals (Karnataka)",
        "",
        "| Level | Rows |",
        "|---|---|",
    ]
    lines += [f"| {k} | {stats[k]:,} |" for k in ("states", "districts", "blocks", "villages")]
    if pilot_district:
        p = stats["pilot"]
        lines += [
            "",
            f"## Pilot district: {p['district']} (LGD {pilot_district})",
            "",
            f"- Villages: **{p['villages']:,}**",
            f"- With a Census 2011 code: **{p['with_census_code']:,}** "
            f"({100 * p['census_share']:.1f}%)",
            "",
            "| Taluk (block) | Villages |",
            "|---|---|",
        ]
        lines += [f"| {name} | {n:,} |" for name, n in p["by_block"].items()]
        lines += [
            "",
            "Pilot villages affected by each data issue:",
            "",
            "| Issue | Villages |",
            "|---|---|",
        ]
        lines += [f"| {k} | {n:,} |" for k, n in p["issues"].items()]
    lines += [
        "",
        "## Data issues (whole state)",
        "",
        "| Issue | Count | Examples |",
        "|---|---|---|",
    ]
    for kind, n in sorted(d.issues.items()):
        ex = "; ".join(d.examples.get(kind, []))
        lines.append(f"| {kind} | {n:,} | {ex} |")
    return "\n".join(lines) + "\n"
