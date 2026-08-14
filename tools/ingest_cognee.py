#!/usr/bin/env python3
"""Ingest the Slack corpus into Cognee Cloud with stable dataset names.

One dataset per channel - the dataset is cognee's real permission boundary, so
it is also ours. Plus one shared dataset holding everything, which is the naive
baseline the demo opens with.

    python3 tools/ingest_cognee.py            # ingest + cognify everything
    python3 tools/ingest_cognee.py --status   # just report what exists
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
KEY = os.environ["COGNEE_CLOUD_API_KEY"]
EXPORT = os.path.join(os.path.dirname(__file__), "..", "corpus", "export")

SHARED = "clearance_all"                      # naive baseline: everything, one memory
def ds_for(channel: str) -> str:              # per-channel, the real boundary
    return "clearance_" + channel.replace("-", "_")


def call(method, path, body=None, timeout=900):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"X-Api-Key": KEY, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def load_corpus():
    users = {u["id"]: u["real_name"] for u in json.load(open(f"{EXPORT}/users.json"))}
    chans = json.load(open(f"{EXPORT}/channels.json")) + json.load(open(f"{EXPORT}/groups.json"))
    out = {}
    for c in chans:
        name = c["name"]
        lines = []
        d = os.path.join(EXPORT, name)
        for fn in sorted(os.listdir(d)):
            date = fn[:-5]
            for m in json.load(open(os.path.join(d, fn))):
                lines.append(f"[{date}] [#{name}] {users[m['user']]}: {m['text']}")
        out[name] = {"members": c["members"], "lines": lines,
                     "is_private": c in json.load(open(f"{EXPORT}/groups.json"))}
    return out


def main():
    corpus = load_corpus()

    if "--status" in sys.argv:
        st, ds = call("GET", "/api/v1/datasets/")
        for d in ds if isinstance(ds, list) else []:
            if d["name"].startswith("clearance"):
                print(f"  {d['name']:34} {d.get('id','')}")
        return

    print(f"corpus: {sum(len(c['lines']) for c in corpus.values())} messages\n", flush=True)

    # per-channel datasets
    for name, c in corpus.items():
        st, _ = call("POST", "/api/v1/add_text",
                     {"textData": ["\n".join(c["lines"])],
                      "datasetName": ds_for(name), "nodeSet": [name]})
        print(f"  add {ds_for(name):34} {st}", flush=True)

    # shared dataset for the naive baseline
    for name, c in corpus.items():
        st, _ = call("POST", "/api/v1/add_text",
                     {"textData": ["\n".join(c["lines"])],
                      "datasetName": SHARED, "nodeSet": [name]})
        print(f"  add {SHARED + ' (' + name + ')':34} {st}", flush=True)

    targets = [ds_for(n) for n in corpus] + [SHARED]
    t0 = time.time()
    st, _ = call("POST", "/api/v1/cognify", {"datasets": targets, "runInBackground": False})
    print(f"\n  cognify {targets} -> {st} ({time.time()-t0:.0f}s)", flush=True)
    print("\nready.")


if __name__ == "__main__":
    main()
