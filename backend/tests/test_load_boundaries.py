import json
from pathlib import Path

import pytest
from django.core.management import call_command
from shapely.geometry import box, mapping

from apps.geo.models import District, Village

FIXTURE = Path(__file__).resolve().parents[2] / "pipelines/tests/fixtures/kgis_directory.json"
CMD = "apps.geo.management.commands.load_boundaries"


@pytest.fixture
def directory(monkeypatch):
    raw = json.loads(FIXTURE.read_text())
    monkeypatch.setattr(
        "apps.geo.management.commands.load_directory.fetch_directory", lambda **kw: raw
    )
    call_command("load_directory", "--pilot-district", "526")


def feat(code, geom, census=""):
    return {
        "type": "Feature",
        "properties": {
            "LGD_VillageCode": code,
            "CensusVillageCode": census,
            "KGISVillageID": 1,
            "KGISVillageName": "x",
        },
        "geometry": mapping(geom),
    }


@pytest.mark.django_db
def test_load_boundaries(directory, monkeypatch, tmp_path):
    codes = sorted(Village.objects.filter(is_pilot=True).values_list("lgd_code", flat=True))
    with_poly = codes[:-1]  # last village gets no polygon
    features = [
        feat(int(c), box(77 + i * 0.01, 13, 77.01 + i * 0.01, 13.01))
        for i, c in enumerate(with_poly)
    ]
    features.append(feat(int(with_poly[0]), box(77, 13.01, 77.01, 13.02)))  # second part
    monkeypatch.setattr(f"{CMD}.fetch_village_polygons", lambda codes, **kw: features)
    monkeypatch.setattr(
        f"{CMD}.fetch_district_polygon", lambda code, **kw: [feat(1, box(76.9, 12.9, 78, 14))]
    )
    report = tmp_path / "b.md"
    call_command("load_boundaries", "--district", "526", "--report", str(report))

    assert District.objects.get(code="526").boundary is not None
    assert Village.objects.filter(is_pilot=True, boundary__isnull=False).count() == len(with_poly)
    first = Village.objects.get(lgd_code=with_poly[0])
    assert first.boundary_precision == "exact"
    assert abs(first.boundary.area - 0.0002) < 1e-9  # both parts, merged
    text = report.read_text()
    assert "Join rate" in text and codes[-1] in text
