from shapely.geometry import MultiPolygon, Polygon, mapping

from pipelines.connectors.boundaries import repair_and_merge, to_multipolygon

SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
NEXT = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
BOWTIE = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])  # self-intersecting


def feature(code, geom, census="2958305603625278", vid=1):
    return {
        "type": "Feature",
        "properties": {
            "LGD_VillageCode": code,
            "CensusVillageCode": census,
            "KGISVillageID": vid,
            "KGISVillageName": "X",
        },
        "geometry": mapping(geom),
    }


def test_to_multipolygon_repairs_bowtie():
    assert not BOWTIE.is_valid
    mp = to_multipolygon(BOWTIE)
    assert isinstance(mp, MultiPolygon) and mp.is_valid
    assert abs(mp.area - 2.0) < 1e-9


def test_parts_with_same_code_are_merged():
    r = repair_and_merge([feature(625278, SQUARE), feature(625278, NEXT, vid=2)])
    poly = r.polygons["625278"]
    assert poly.is_valid and abs(poly.area - 2.0) < 1e-9
    assert len(poly.geoms) == 1  # touching squares dissolve into one polygon
    assert r.stats["multi_part_villages_merged"] == 1
    assert r.census_codes["625278"] == {"625278"}


def test_invalid_and_missing_are_counted():
    r = repair_and_merge(
        [feature(1, BOWTIE), {"properties": {"LGD_VillageCode": None}, "geometry": None}]
    )
    assert r.stats["invalid_geometry_repaired"] == 1
    assert r.stats["feature_without_code_or_geometry"] == 1
    assert r.polygons["1"].is_valid
