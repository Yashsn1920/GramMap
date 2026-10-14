"""Check our village directory against a hand-downloaded LGD village list (S1.1 acceptance).

    python manage.py compare_lgd data/raw/lgd/villages_526.csv --district 526 \\
        --report docs/reports/S1_1_lgd_comparison.md

Villages without a Census 2011 code are filled from the LGD file when it has one.

With --apply, LGD is treated as the official list for the pilot district:
- LGD villages missing from the district are added (or moved here from another district),
  with LGD's name, sub-district and Census code; they have no boundary until S1.2;
- villages in the district that LGD does not list are kept but marked is_pilot = False.
Then the comparison is repeated on the pilot villages.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.geo.models import Block, Village
from pipelines.connectors.lgd import compare, parse_villages
from pipelines.normalize.names import basic_clean, village_variants


class Command(BaseCommand):
    help = "Compare the village directory for one district with an LGD download"

    def add_arguments(self, parser):
        parser.add_argument("path", help="LGD village CSV")
        parser.add_argument("--district", required=True, help="LGD district code")
        parser.add_argument("--report", help="write a Markdown report to this path")
        parser.add_argument(
            "--apply", action="store_true", help="reconcile the pilot district with LGD"
        )

    def handle(self, *args, path, district, report=None, apply=False, **opts):
        lgd = parse_villages(path)
        qs = Village.objects.filter(block__district_id=district)
        ours = dict(qs.values_list("lgd_code", "name"))
        result = compare(lgd, ours)
        if apply:
            result["applied"] = reconcile(lgd, district)
            pilot = dict(Village.objects.filter(is_pilot=True).values_list("lgd_code", "name"))
            result["after"] = compare(lgd, pilot)

        filled = 0
        census = {v.village_code: v.census_2011 for v in lgd if v.census_2011}
        for v in qs.filter(census_code="", lgd_code__in=list(census)):
            v.census_code = census[v.lgd_code]
            v.save(update_fields=["census_code"])
            filled += 1
        result["census_codes_filled_from_lgd"] = filled
        total = qs.count()
        with_census = qs.exclude(census_code="").count()
        result["census_share_after"] = round(with_census / total, 4) if total else None

        self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
        if report:
            Path(report).parent.mkdir(parents=True, exist_ok=True)
            Path(report).write_text(render(result, path, district))
            self.stdout.write(f"report written to {report}")


@transaction.atomic
def reconcile(lgd, district):
    blocks = set(Block.objects.filter(district_id=district).values_list("code", flat=True))
    lgd_codes = {v.village_code for v in lgd}
    existing = {v.lgd_code: v for v in Village.objects.filter(lgd_code__in=lgd_codes)}
    added, moved = [], []
    for v in lgd:
        if v.subdistrict_code not in blocks:
            continue
        if v.village_code in existing:
            ours = existing[v.village_code]
            if ours.block_id != v.subdistrict_code or not ours.is_pilot:
                if ours.block_id != v.subdistrict_code:
                    moved.append(f"{v.village_code} {v.village_name} (from block {ours.block_id})")
                ours.block_id = v.subdistrict_code
                ours.is_pilot = True
                ours.save(update_fields=["block", "is_pilot"])
            continue
        Village.objects.create(
            lgd_code=v.village_code,
            census_code=v.census_2011,
            block_id=v.subdistrict_code,
            name=v.village_name,
            norm_name=basic_clean(v.village_name),
            name_variants=village_variants(v.village_name),
            is_pilot=True,
        )
        added.append(f"{v.village_code} {v.village_name}")
    not_listed = Village.objects.filter(block__district_id=district, is_pilot=True).exclude(
        lgd_code__in=lgd_codes
    )
    unmarked = [f"{v.lgd_code} {v.name}" for v in not_listed]
    not_listed.update(is_pilot=False)
    return {"added": added, "moved": moved, "unmarked_not_in_lgd": unmarked}


def render(r, path, district):
    verdict = "**Match**" if r["count_matches"] else "**Mismatch** (see below)"
    lines = [
        f"# S1.1 LGD comparison, district {district}",
        "",
        f"- LGD file: `{path}`",
        f"- Before reconciling: {verdict}",
        "",
        "| Measure | Count |",
        "|---|---|",
        f"| Villages in LGD | {r['lgd_villages']:,} |",
        f"| Villages in our directory (KGIS) | {r['our_villages']:,} |",
        f"| In both | {r['in_both']:,} |",
        f"| In LGD but not ours | {r['missing_from_ours']:,} |",
        f"| Ours but not in LGD | {r['not_in_lgd']:,} |",
        f"| Census codes filled from LGD | {r['census_codes_filled_from_lgd']:,} |",
        f"| Census code coverage after | {100 * r['census_share_after']:.1f}% |",
    ]
    for title, key in [
        ("In LGD but not ours", "missing_examples"),
        ("Ours but not in LGD", "extra_examples"),
    ]:
        if r[key]:
            lines += ["", f"**{title} (first 10):** " + "; ".join(r[key])]
    if "applied" in r:
        a, after = r["applied"], r["after"]
        verdict = "**Match**" if after["count_matches"] else "**Mismatch**"
        lines += [
            "",
            "## After reconciling with LGD (--apply)",
            "",
            f"- Pilot villages: **{after['our_villages']:,}**, LGD villages: "
            f"**{after['lgd_villages']:,}**, result: {verdict}",
            f"- Added from LGD (no boundary yet): {len(a['added'])}",
            f"- Moved into this district (KGIS had them elsewhere): {len(a['moved'])}",
            f"- In KGIS for this district but not in LGD, marked is_pilot = false: "
            f"{len(a['unmarked_not_in_lgd'])}",
        ]
        for title, key in [
            ("Added", "added"),
            ("Moved", "moved"),
            ("Not in LGD", "unmarked_not_in_lgd"),
        ]:
            if a[key]:
                lines += ["", f"**{title}:** " + "; ".join(a[key])]
    return "\n".join(lines) + "\n"
