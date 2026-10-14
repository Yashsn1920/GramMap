"""Minimal ArcGIS REST client: paged layer queries with retries and an on-disk cache.

Used for KGIS (Karnataka). Pure Python, no Django.
"""

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path

import requests

USER_AGENT = "GramMap/0.1 (college project; public data only)"


class ArcGISError(RuntimeError):
    pass


def _get(session, url, params, retries, backoff):
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise ArcGISError(f"{url}: {data['error']}")
            return data
        except (requests.RequestException, ValueError) as exc:
            if attempt == retries - 1:
                raise ArcGISError(f"{url} failed after {retries} attempts: {exc}") from exc
            time.sleep(backoff * 2**attempt)
    raise AssertionError("unreachable")


def query_layer(
    layer_url: str,
    where: str = "1=1",
    out_fields: str = "*",
    geometry: bool = False,
    page_size: int = 1000,
    cache_dir: Path | None = None,
    min_interval_s: float = 0.5,
    retries: int = 4,
    backoff: float = 2.0,
    progress: Callable[[int, int], None] | None = None,
    session: requests.Session | None = None,
    geojson: bool = False,
) -> list[dict]:
    """Return every feature of a layer.

    Esri JSON features are {"attributes": ..., "geometry": ...}; with geojson=True they are
    GeoJSON features {"properties": ..., "geometry": ...} in EPSG:4326.
    Pages are cached in cache_dir by a hash of the request, so a re-run reads from disk.
    """
    session = session or requests.Session()
    session.headers.setdefault("User-Agent", USER_AGENT)
    query_url = layer_url.rstrip("/") + "/query"
    base = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": str(geometry).lower(),
        "outSR": 4326,
        "f": "json",
    }

    total = _get(session, query_url, {**base, "returnCountOnly": "true"}, retries, backoff)["count"]
    features: list[dict] = []
    offset = 0
    while offset < total:
        params = {
            **base,
            "orderByFields": "OBJECTID",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        if geojson:
            params.update(f="geojson", geometryPrecision=6)
        page = _cached(cache_dir, query_url, params)
        if page is None:
            page = _get(session, query_url, params, retries, backoff)
            _store(cache_dir, query_url, params, page)
            time.sleep(min_interval_s)
        batch = page.get("features", [])
        if not batch:
            break
        features.extend(batch)
        offset += len(batch)
        if progress:
            progress(len(features), total)
    return features


def _key(url, params):
    raw = json.dumps([url, sorted(params.items())], default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _cached(cache_dir, url, params):
    if cache_dir is None:
        return None
    path = Path(cache_dir) / f"{_key(url, params)}.json"
    return json.loads(path.read_text()) if path.exists() else None


def _store(cache_dir, url, params, data):
    if cache_dir is None:
        return
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    (Path(cache_dir) / f"{_key(url, params)}.json").write_text(json.dumps(data))
