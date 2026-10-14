from pathlib import Path

import pytest

from pipelines.connectors.lgd import LgdFormatError, compare, parse_villages

SAMPLE = Path(__file__).parent / "fixtures" / "lgd_villages_sample.csv"


def test_parse_skips_title_and_footer():
    villages = parse_villages(SAMPLE)
    assert [v.village_code for v in villages] == ["625278", "625279", "625280"]
    first = villages[0]
    assert first.village_name == "Alurududdanahalli"
    assert first.subdistrict_code == "5602"
    assert first.district_code == "526"
    assert first.census_2011 == "625278"
    assert villages[1].census_2011 == ""  # 000000 means no code


def test_parse_rejects_wrong_file(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b,c\n1,2,3\n")
    with pytest.raises(LgdFormatError, match="Village Code"):
        parse_villages(bad)


def test_compare():
    result = compare(parse_villages(SAMPLE), {"625278": "Alurududdanahalli", "999": "Extra"})
    assert result["in_both"] == 1
    assert result["missing_from_ours"] == 2
    assert result["not_in_lgd"] == 1
    assert result["count_matches"] is False
    assert result["extra_examples"] == ["999 Extra"]


def test_parse_xlsx_report():
    villages = parse_villages(SAMPLE.with_suffix(".xlsx"))
    assert [v.village_code for v in villages] == ["625373", "625438"]
    assert villages[0].subdistrict_code == "5603"
    assert villages[0].census_2011 == "625373"
    assert villages[1].census_2011 == ""
