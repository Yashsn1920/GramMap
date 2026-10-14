import json
from pathlib import Path

import pytest
from django.core.management import call_command

from apps.geo.models import Block, District, Village
from apps.sources.models import PipelineRun

FIXTURE = Path(__file__).resolve().parents[2] / "pipelines/tests/fixtures/kgis_directory.json"


@pytest.fixture
def offline(monkeypatch):
    raw = json.loads(FIXTURE.read_text())
    monkeypatch.setattr(
        "apps.geo.management.commands.load_directory.fetch_directory",
        lambda **kw: raw,
    )


@pytest.mark.django_db
def test_load_directory_is_idempotent(offline, tmp_path):
    report = tmp_path / "report.md"
    call_command("load_directory", "--pilot-district", "526", "--report", str(report))
    first = Village.objects.count()
    call_command("load_directory", "--pilot-district", "526")

    assert Village.objects.count() == first > 0
    assert District.objects.filter(code="526").exists()
    assert Block.objects.filter(district_id="526").count() == 4
    assert Village.objects.filter(is_pilot=True).count() == first
    v = Village.objects.exclude(census_code="").first()
    assert v.name_variants and v.norm_name

    run = PipelineRun.objects.latest("started_at")
    assert run.status == "succeeded" and run.config_hash
    assert run.stats["pilot"]["villages"] == first
    assert "Pilot district: Bengaluru (Rural)" in report.read_text()


@pytest.mark.django_db
def test_compare_lgd(offline, tmp_path):
    call_command("load_directory", "--pilot-district", "526")
    code, name = Village.objects.values_list("lgd_code", "name").first()
    csv = tmp_path / "lgd.csv"
    csv.write_text(
        '"District Code","Sub-District Code","Village Code","Village Name (In English)",'
        '"Census 2011 Code"\n'
        f'"526","5602","{code}","{name}","{code}"\n"526","5602","1234567","Not Ours","000000"\n'
    )
    report = tmp_path / "cmp.md"
    call_command("compare_lgd", str(csv), "--district", "526", "--report", str(report))
    text = report.read_text()
    assert "Mismatch" in text
    assert "1234567 Not Ours" in text


@pytest.mark.django_db
def test_compare_lgd_apply_reconciles_pilot(offline, tmp_path):
    call_command("load_directory", "--pilot-district", "526")
    kept = list(Village.objects.values_list("lgd_code", "name")[:2])
    dropped = Village.objects.exclude(lgd_code__in=[c for c, _ in kept]).first()
    rows = "".join(f'"526","5602","{c}","{n}","{c}"\n' for c, n in kept)
    csv = tmp_path / "lgd.csv"
    csv.write_text(
        '"District Code","Sub-District Code","Village Code","Village Name (In English)",'
        '"Census 2011 Code"\n' + rows + '"526","5602","910080","Mopurahalli (D)","0"\n'
    )
    report = tmp_path / "cmp.md"
    call_command("compare_lgd", str(csv), "--district", "526", "--apply", "--report", str(report))
    pilot = set(Village.objects.filter(is_pilot=True).values_list("lgd_code", flat=True))
    assert pilot == {kept[0][0], kept[1][0], "910080"}
    new = Village.objects.get(lgd_code="910080")
    assert new.block_id == "5602" and new.census_code == "" and new.boundary is None
    assert Village.objects.get(lgd_code=dropped.lgd_code).is_pilot is False
    assert "After reconciling" in report.read_text()
