#!/usr/bin/env python3
"""Wipe and rebuild everything. Use between rehearsals, or after editing the corpus.

Cognee datasets ACCUMULATE. Re-adding to a dataset that already has data leaves
the old entities in the graph - which is how a renamed person came back as
"Omid Mohajerani (also Nadia Farsi)" in a distilled answer. Always forget before
you re-add.

    python3 tools/rebuild.py [corpusdir]

Takes about two minutes, most of it cognify. For the fast reset between demo
runs - just removing the injected message - use POST /reset instead.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
KEY = os.environ["COGNEE_CLOUD_API_KEY"]
DATASETS = ["shelflife_docs", "shelflife_channel"]


def forget(dataset: str) -> str:
    req = urllib.request.Request(
        f"{BASE}/api/v1/forget", data=json.dumps({"dataset": dataset}).encode(),
        method="POST", headers={"X-Api-Key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode()).get("status", "?")
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"


def main() -> None:
    corpus = sys.argv[1] if len(sys.argv) > 1 else "corpus2"

    print("forgetting:")
    for ds in DATASETS:
        print(f"  {ds}: {forget(ds)}")

    print("\nre-ingesting:")
    here = os.path.dirname(__file__)
    subprocess.run([sys.executable, os.path.join(here, "ingest_shelflife.py"), corpus],
                   check=True)

    # A rebuild invalidates the offline cache - it was captured from the old graph.
    print("\nrefreshing the offline fallback:")
    subprocess.run([sys.executable, os.path.join(here, "capture_fallback.py")],
                   check=False)


if __name__ == "__main__":
    main()
