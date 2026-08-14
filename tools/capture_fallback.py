#!/usr/bin/env python3
"""Capture live answers to disk so the demo survives losing the network.

Run it while everything works. If cognee or the venue wifi dies at 21:15, the UI
falls back to these and renders identically - same code path, same markup, just
a cached payload.

    python3 tools/capture_fallback.py [base_url]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(__file__), "..", "app", "fallback.json")

QUESTIONS = [
    "Our SFTP export connector won't connect but the credentials are correct. What is wrong?",
    "How do I get callback completion status out to an external system?",
    "How do I authenticate to the platform API?",
    "The dialer isn't calling and the segment says Data Exhausted. What do I do?",
]


def main() -> None:
    cache = {}
    for q in QUESTIONS:
        req = urllib.request.Request(
            f"{BASE}/ask", data=json.dumps({"question": q}).encode(),
            method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        lvl = d["trust"]["level"]
        cache[q] = d
        print(f"  [{lvl:11}] {q[:64]}")

    json.dump(cache, open(OUT, "w"), indent=1)
    print(f"\n{len(cache)} answers -> {OUT}")


if __name__ == "__main__":
    main()
