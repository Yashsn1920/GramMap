import json
from pathlib import Path

import pytest

from pipelines.connectors.kgis import build_directory, census_village_code

FIXTURE = Path(__file__).parent / "fixtures" / "kgis_directory.json"


@pytest.fixture(scope="module")
def raw():
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def directory(raw):
    return build_directory(raw)


def test_census_village_code():
    assert census_village_code("2958305603625278") == "625278"
    assert census_village_code("2958305603000000") == ""
    assert census_village_code(None) == ""
    assert census_village_code("625278") == ""


def test_hierarchy(directory):
    assert [s.code for s in directory.states] == ["29"]
    districts = {r.code: r.name for r in directory.districts}
    assert districts["526"] == "Bengaluru (Rural)"
    assert {b.parent for b in directory.blocks} == {"526"}
    assert {b.name for b in directory.blocks} == {
        "Nelamangala",
        "Doddaballapura",
        "Devanahalli",
        "Hoskote",
    }


def test_villages_have_codes_and_names(directory, raw):
    block_codes = {b.code for b in directory.blocks}
    assert directory.villages
    for v in directory.villages:
        assert v.lgd_code.isdigit()
        assert v.block_code in block_codes
        assert v.norm_name == v.norm_name.lower()
        assert v.name_variants[0] == v.norm_name


def test_duplicate_code_rows_are_merged(directory, raw):
    first = raw["village"][0]
    merged = [v for v in directory.villages if v.lgd_code == str(first["LGD_VillageCode"])]
    assert len(merged) == 1
    assert merged[0].kgis_ids[0] == first["KGISVillageID"]
    assert merged[0].kgis_ids[-1] == 999999
    loadable = [a for a in raw["village"] if a["LGD_VillageCode"] and a["KGISHobliID"] != -5]
    assert directory.issues["extra_polygons_merged"] == len(loadable) - len(directory.villages)


def test_bad_rows_are_counted_not_loaded(directory):
    assert directory.issues["village_without_lgd_code"] == 1
    assert directory.issues["village_without_taluk"] == 1
    assert "1" not in {v.lgd_code for v in directory.villages}


def test_placeholder_census_code_is_missing():
    assert census_village_code("2958305603999999") == ""
