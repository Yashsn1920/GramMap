"""Small Overpass helper used by the S0.1 source audit."""

import json
import sys
import time

import requests

URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "GramMap-college-project/0.1 (source audit)"}


def query(q, timeout=300):
    last = None
    for url in URLS:
        for attempt in range(3):
            try:
                r = requests.post(url, data={"data": q}, headers=HEADERS, timeout=timeout)
                if r.status_code == 200:
                    return r.json()
                last = f"{url} HTTP {r.status_code}: {r.text[:200]}"
            except requests.RequestException as e:
                last = f"{url} {e}"
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(last)


if __name__ == "__main__":
    print(json.dumps(query(sys.stdin.read()), indent=1)[:5000])
