"""KGIS (Karnataka GIS, KSRSAC) administrative directory: state, districts, taluks, villages.

For Karnataka KGIS replaces the LGD download (PRD Section 7.1, docs/source_audit.md): its layers
carry the LGD district, sub-district (taluk) and village codes, Census 2011 codes and LGD Gram
Panchayat codes. Block in the data model = taluk (LGD sub-district) here.

fetch_directory() downloads the raw layers; build_directory() is pure and turns them into rows.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from pipelines.connectors.arcgis import query_layer
from pipelines.normalize.names import basic_clean, village_variants

ADMIN = "https://kgis.ksrsac.in/kgismaps2/rest/services/Boundaries/Admin_Dynamic/MapServer"
VILLAGES = "https://kgis.ksrsac.in/kgismaps2/rest/services/Boundaries/Village_Dynamic/MapServer/0"
VILLAGE_FIELDS = (
    "OBJECTID,KGISVillageID,KGISVillageName,KGISHobliID,CensusVillageCode,"
    "LGDGPCode,LGD_VillageCode"
)


@dataclass
class Row:
    code: str
    name: str
    parent: str = ""


@dataclass
class VillageRow:
    lgd_code: str
    name: str
    norm_name: str
    name_variants: list[str]
    block_code: str
    census_code: str
    gp_lgd_code: str
    kgis_ids: list[int]


@dataclass
class Directory:
    states: list[Row]
    districts: list[Row]
    blocks: list[Row]
    villages: list[VillageRow]
    issues: Counter = field(default_factory=Counter)
    examples: dict = field(default_factory=lambda: defaultdict(list))
    village_issues: dict = field(default_factory=lambda: defaultdict(set))  # kind -> lgd codes

    def note(self, kind, example, lgd_code=None):
        self.issues[kind] += 1
        if len(self.examples[kind]) < 5:
            self.examples[kind].append(example)
        if lgd_code:
            self.village_issues[kind].add(lgd_code)


def fetch_directory(cache_dir: Path | None = None, progress=None) -> dict[str, list[dict]]:
    """Download the raw KGIS layers (attributes only). Cached pages make re-runs instant."""
    layers = {
        "state": f"{ADMIN}/0",
        "district": f"{ADMIN}/1",
        "taluk": f"{ADMIN}/2",
        "hobli": f"{ADMIN}/3",
    }
    raw = {
        k: [f["attributes"] for f in query_layer(u, cache_dir=cache_dir)] for k, u in layers.items()
    }
    raw["village"] = [
        f["attributes"]
        for f in query_layer(
            VILLAGES, out_fields=VILLAGE_FIELDS, cache_dir=cache_dir, progress=progress
        )
    ]
    return raw


def clean_display(name: str | None) -> str:
    return " ".join((name or "").split())


def census_village_code(composite: str | None) -> str:
    """KGIS stores state(2)+district(3)+sub-district(5)+village(6); return the 6-digit village
    code, or "" when absent, zero or the placeholder 999999."""
    digits = (composite or "").strip()
    if len(digits) == 16 and digits.isdigit() and digits[-6:] not in ("000000", "999999"):
        return digits[-6:]
    return ""


def build_directory(raw: dict[str, list[dict]]) -> Directory:
    state = raw["state"][0]
    state_code = str(state["KGISStateCode"])
    states = [Row(state_code, clean_display(state["KGISStateName"]))]
    d = Directory(states=states, districts=[], blocks=[], villages=[])

    district_lgd = {}
    for a in raw["district"]:
        if not a.get("LGD_DistrictCode"):
            d.note("district_without_lgd_code", a["KGISDistrictName"])
            continue
        district_lgd[a["KGISDistrictCode"]] = str(a["LGD_DistrictCode"])
        d.districts.append(
            Row(str(a["LGD_DistrictCode"]), clean_display(a["KGISDistrictName"]), state_code)
        )

    taluk_lgd = {}
    for a in raw["taluk"]:
        parent = district_lgd.get(a["KGISDistrictCode"])
        if not a.get("LGD_TalukCode") or not parent:
            d.note("taluk_without_lgd_code_or_district", a["KGISTalukName"])
            continue
        taluk_lgd[a["KGISTalukCode"]] = str(a["LGD_TalukCode"])
        d.blocks.append(Row(str(a["LGD_TalukCode"]), clean_display(a["KGISTalukName"]), parent))

    hobli_taluk = {a["KGISHobliID"]: taluk_lgd.get(a["KGISTalukCode"]) for a in raw["hobli"]}

    merged: dict[str, VillageRow] = {}
    for a in raw["village"]:
        name = clean_display(a.get("KGISVillageName"))
        if not a.get("LGD_VillageCode"):
            d.note("village_without_lgd_code", f"KGIS {a['KGISVillageID']} {name}")
            continue
        code = str(a["LGD_VillageCode"])
        block = hobli_taluk.get(a.get("KGISHobliID"))
        if not block:
            d.note("village_without_taluk", f"{code} {name}")
            continue
        census = census_village_code(a.get("CensusVillageCode"))
        if code in merged:  # village split into several polygons: merge by code (PRD 7.1)
            v = merged[code]
            v.kgis_ids.append(a["KGISVillageID"])
            d.issues["extra_polygons_merged"] += 1
            if basic_clean(name) != v.norm_name or block != v.block_code:
                d.note("same_code_different_name_or_taluk", f"{code}: {v.name} / {name}", code)
            if not v.census_code and census:
                v.census_code = census
            continue
        merged[code] = VillageRow(
            lgd_code=code,
            name=name,
            norm_name=basic_clean(name),
            name_variants=village_variants(name),
            block_code=block,
            census_code=census,
            gp_lgd_code=str(a.get("LGDGPCode") or "").strip(),
            kgis_ids=[a["KGISVillageID"]],
        )
        if census and census != code.zfill(6):
            d.note("census_code_differs_from_lgd_code", f"{code} {name}: census {census}", code)

    d.villages = list(merged.values())
    census_counts = Counter(v.census_code for v in d.villages if v.census_code)
    for v in d.villages:
        if not v.census_code:
            d.note("village_without_census_code", f"{v.lgd_code} {v.name}", v.lgd_code)
        elif census_counts[v.census_code] > 1:
            d.note("census_code_shared", f"{v.census_code}: {v.lgd_code} {v.name}", v.lgd_code)
    return d
