"""Check our village directory against a hand-downloaded LGD village list (S1.1 acceptance).

    python manage.py compare_lgd data/raw/lgd/villages_526.csv --district 526 \\
        --report docs/reports/S1_1_lgd_comparison.md

Villages without a Census 2011 code are filled from the LGD file when it has one.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.geo.models import Village
from pipelines.connectors.lgd import compare, parse_villages


class Command(BaseCommand):
    help = "Compare the village directory for one district with an LGD download"

    def add_arguments(self, parser):
        parser.add_argument("path", help="LGD village CSV")
        parser.add_argument("--district", required=True, help="LGD district code")
        parser.add_argument("--report", help="write a Markdown report to this path")

    def handle(self, *args, path, district, report=None, **opts):
        lgd = parse_villages(path)
        qs = Village.objects.filter(block__district_id=district)
        ours = dict(qs.values_list("lgd_code", "name"))
        result = compare(lgd, ours)

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


def render(r, path, district):
    verdict = "**Match**" if r["count_matches"] else "**Mismatch** (see below)"
    lines = [
        f"# S1.1 LGD comparison, district {district}",
        "",
        f"- LGD file: `{path}`",
        f"- Result: {verdict}",
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
    return "\n".join(lines) + "\n"
