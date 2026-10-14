"""Parse a Local Government Directory (lgdirectory.gov.in) village download.

LGD download pages need a captcha, so the file is downloaded by hand once (PRD Section 5.2) and
saved under data/raw/lgd/. Column names vary between LGD reports, so columns are found by keyword.
"""

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

_COLUMNS = {
    "village_code": [r"^village\s*code$", r"^village\s*lgd\s*code$"],
    "village_name": [r"^village\s*name.*english", r"^village\s*name$"],
    "subdistrict_code": [r"^sub.?district\s*code$"],
    "subdistrict_name": [r"^sub.?district\s*name.*english", r"^sub.?district\s*name$"],
    "district_code": [r"^district\s*code$"],
    "census_2011": [r"census\s*2011"],
}


@dataclass(frozen=True)
class LgdVillage:
    village_code: str
    village_name: str
    subdistrict_code: str
    subdistrict_name: str
    district_code: str
    census_2011: str


class LgdFormatError(ValueError):
    pass


def _match(header: list[str]) -> dict[str, int]:
    found = {}
    for key, patterns in _COLUMNS.items():
        for i, h in enumerate(header):
            h = " ".join(h.replace("﻿", "").lower().split())
            if any(re.search(p, h) for p in patterns):
                found.setdefault(key, i)
    return found


def parse_villages(path: Path | str) -> list[LgdVillage]:
    """Read an LGD village CSV. The header may be preceded by title lines."""
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    header = next(
        (i for i, row in enumerate(rows) if {"village_code", "village_name"} <= set(_match(row))),
        None,
    )
    if header is None:
        raise LgdFormatError(f"{path}: no header row with 'Village Code' and 'Village Name'")
    cols = _match(rows[header])

    def cell(row, key):
        i = cols.get(key)
        return row[i].strip() if i is not None and i < len(row) else ""

    out = []
    for row in rows[header + 1 :]:
        get = lambda key, row=row: cell(row, key)  # noqa: E731
        code = get("village_code")
        if not code.isdigit():
            continue  # footer / blank lines
        census = get("census_2011")
        out.append(
            LgdVillage(
                code,
                get("village_name"),
                get("subdistrict_code"),
                get("subdistrict_name"),
                get("district_code"),
                census if census.strip("0") else "",
            )
        )
    return out


def compare(lgd: list[LgdVillage], ours: dict[str, str]) -> dict:
    """Compare LGD village codes with ours ({lgd_code: name}). Returns counts and examples."""
    lgd_codes = {v.village_code: v for v in lgd}
    missing = sorted(set(lgd_codes) - set(ours))
    extra = sorted(set(ours) - set(lgd_codes))
    return {
        "lgd_villages": len(lgd_codes),
        "our_villages": len(ours),
        "in_both": len(set(lgd_codes) & set(ours)),
        "missing_from_ours": len(missing),
        "not_in_lgd": len(extra),
        "missing_examples": [f"{c} {lgd_codes[c].village_name}" for c in missing[:10]],
        "extra_examples": [f"{c} {ours[c]}" for c in extra[:10]],
        "count_matches": len(lgd_codes) == len(ours) and not missing,
    }
