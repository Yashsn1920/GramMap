"""Village and district boundaries (PRD step S1.2).

For Karnataka the polygons come from KGIS and already carry the LGD village code, so they are
joined by LGD code; the Census code on the polygon is used as a cross-check.
repair_and_merge() is pure (Shapely); fetching uses the ArcGIS client.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

from pipelines.connectors.arcgis import query_layer
from pipelines.connectors.kgis import ADMIN, VILLAGES, census_village_code

CODES_PER_REQUEST = 100


def fetch_village_polygons(lgd_codes, cache_dir: Path | None = None, progress=None) -> list[dict]:
    """GeoJSON features for the given LGD village codes (several features per code possible)."""
    codes = sorted({int(c) for c in lgd_codes})
    features = []
    for i in range(0, len(codes), CODES_PER_REQUEST):
        chunk = codes[i : i + CODES_PER_REQUEST]
        features += query_layer(
            VILLAGES,
            where=f"LGD_VillageCode IN ({','.join(map(str, chunk))})",
            out_fields="KGISVillageID,KGISVillageName,LGD_VillageCode,CensusVillageCode",
            geometry=True,
            geojson=True,
            page_size=200,
            cache_dir=cache_dir,
        )
        if progress:
            progress(min(i + CODES_PER_REQUEST, len(codes)), len(codes))
    return features


def fetch_district_polygon(lgd_district_code: str, cache_dir: Path | None = None) -> list[dict]:
    return query_layer(
        f"{ADMIN}/1",
        where=f"LGD_DistrictCode = {int(lgd_district_code)}",
        out_fields="KGISDistrictCode,KGISDistrictName,LGD_DistrictCode",
        geometry=True,
        geojson=True,
        cache_dir=cache_dir,
    )


def to_multipolygon(geom) -> MultiPolygon | None:
    """Repair a geometry (make_valid) and keep only its polygonal parts."""
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        geom = make_valid(geom)
    parts = []
    stack = [geom]
    while stack:
        g = stack.pop()
        if isinstance(g, Polygon):
            if g.area > 0:
                parts.append(g)
        elif hasattr(g, "geoms"):
            stack.extend(g.geoms)
    if not parts:
        return None
    merged = unary_union(parts)
    return merged if isinstance(merged, MultiPolygon) else MultiPolygon([merged])


@dataclass
class BoundaryResult:
    polygons: dict[str, MultiPolygon]  # lgd_code -> boundary
    census_codes: dict[str, set[str]]  # lgd_code -> census codes seen on its polygons
    stats: Counter = field(default_factory=Counter)
    examples: dict = field(default_factory=lambda: defaultdict(list))

    def note(self, kind, example):
        self.stats[kind] += 1
        if len(self.examples[kind]) < 5:
            self.examples[kind].append(example)


def repair_and_merge(features: list[dict]) -> BoundaryResult:
    """Group polygon features by LGD code, repair invalid ones and union the parts."""
    parts = defaultdict(list)
    census = defaultdict(set)
    result = BoundaryResult(polygons={}, census_codes=census)
    for f in features:
        props = f.get("properties") or {}
        code = props.get("LGD_VillageCode")
        if not code or not f.get("geometry"):
            result.note("feature_without_code_or_geometry", props.get("KGISVillageID"))
            continue
        code = str(code)
        geom = shape(f["geometry"])
        if not geom.is_valid:
            result.note("invalid_geometry_repaired", f"{code} {props.get('KGISVillageName')}")
        mp = to_multipolygon(geom)
        if mp is None:
            result.note("empty_after_repair", code)
            continue
        parts[code].append(mp)
        if c := census_village_code(props.get("CensusVillageCode")):
            census[code].add(c)
    for code, polys in parts.items():
        if len(polys) > 1:
            result.stats["multi_part_villages_merged"] += 1
        result.polygons[code] = to_multipolygon(unary_union(polys))
    result.stats["features"] = len(features)
    return result
