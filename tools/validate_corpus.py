#!/usr/bin/env python3
"""Ingest the generated corpus into Cognee Cloud and check the demo actually works.

Two configurations, the same four questions:

  naive  - one shared dataset, node_set per channel, scoped with nodeName.
           This is the "before". It is expected to LEAK.
  safe   - one dataset per channel, asker sees only their datasets.
           This is the boundary Clearance builds on.

A corpus that does not reproduce the leak is worthless, so this is a gate, not a demo.

    python3 tools/validate_corpus.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ENVF = os.path.expanduser(os.environ.get("SHELFLIFE_ENV_FILE", "~/.shelflife.env"))
env = dict(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", open(ENVF).read(), re.M))
BASE = env["COGNEE_CLOUD_URL"].rstrip("/")
KEY = env["COGNEE_CLOUD_API_KEY"]

EXPORT = "corpus/export"
SUF = time.strftime("%H%M%S")

# words that must never reach an unauthorised asker
SECRETS = ["meridian", "12m", "eur 12", "acquisition", "diligence",
           "do not convert", "don't convert", "after the meridian close"]


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"X-Api-Key": KEY, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
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
        out[name] = {"members": c["members"], "lines": lines}
    return users, out


GROUNDED = (
    "You are answering questions about a company's Slack workspace using ONLY the "
    "provided context. Never use outside or general knowledge. If the context does "
    "not contain the answer, say plainly that you have nothing on record about it. "
    "Quote the specific messages you relied on, with their channel and date."
)


def ask(label, query, datasets, node_name=None, forbidden=True):
    body = {"searchType": "GRAPH_COMPLETION", "query": query,
            "datasets": datasets, "includeReferences": True, "topK": 20,
            "systemPrompt": GROUNDED}
    if node_name:
        body["nodeName"] = node_name
    st, res = call("POST", "/api/v1/search", body)
    blob = json.dumps(res).lower() if not isinstance(res, str) else res.lower()
    hits = sorted({s for s in SECRETS if s in blob})
    if forbidden:
        verdict = f"*** LEAKED: {', '.join(hits)} ***" if hits else "CLEAN"
    else:
        verdict = f"reasoned (found {', '.join(hits)})" if hits else "!! TOO THIN - no private context"
    try:
        answer = res[0]["search_result"][0]
    except Exception:
        answer = str(res)[:400]
    prose = answer.split("Evidence:")[0]
    prose_hits = sorted({s for s in SECRETS if s in prose.lower()})
    if prose_hits:
        verdict += f"  [IN PROSE: {', '.join(prose_hits)}]"
    print(f"\n--- {label}\n  Q: {query}\n  {verdict}\n  A: {prose[:520]}", flush=True)
    return not hits, prose


def fanout(label, query, channels, ds, forbidden=True):
    """Clearance's actual read path: one query per PERMITTED channel, never a
    multi-dataset query. You cannot leak a channel you never asked.

    Also sidesteps cognee's weak multi-dataset retrieval - measured, see
    findings/SPIKE-RESULTS.md.
    """
    print(f"\n--- {label}\n  Q: {query}\n  querying: {', '.join('#' + c for c in channels)}", flush=True)
    cards, blob = [], ""
    for ch in channels:
        st, res = call("POST", "/api/v1/search",
                       {"searchType": "GRAPH_COMPLETION", "query": query,
                        "datasets": [ds[ch]], "topK": 20, "systemPrompt": GROUNDED,
                        "includeReferences": True})
        try:
            prose = res[0]["search_result"][0].split("Evidence:")[0].strip()
        except Exception:
            prose = f"<{st}>"
        cards.append((ch, prose))
        blob += " " + prose.lower()
        print(f"    #{ch}: {prose[:200].replace(chr(10), ' ')}", flush=True)
    hits = sorted({s for s in SECRETS if s in blob})
    if forbidden:
        print(f"  => {'*** LEAKED: ' + ', '.join(hits) + ' ***' if hits else 'CLEAN'}", flush=True)
    else:
        print(f"  => {'reasoned: ' + ', '.join(hits) if hits else '!! TOO THIN'}", flush=True)
    return cards, blob


def main():
    users, corpus = load_corpus()
    total = sum(len(c["lines"]) for c in corpus.values())
    print(f"corpus: {total} messages across {len(corpus)} channels\n", flush=True)

    # Re-ingesting costs ~2 minutes. Set CL_SUFFIX to reuse an earlier run's
    # datasets and iterate on the questions in seconds instead.
    reuse = os.environ.get("CL_SUFFIX")
    if reuse:
        globals()["SUF"] = reuse
        naive = f"cl_naive_{reuse}"
        ds = {n: f"cl_{n.replace('-', '_')}_{reuse}" for n in corpus}
        print(f"reusing datasets from run {reuse}\n", flush=True)
        return run_checks(corpus, naive, ds)

    # ---- naive: one dataset, node_set per channel ----------------------
    naive = f"cl_naive_{SUF}"
    for name, c in corpus.items():
        st, _ = call("POST", "/api/v1/add_text",
                     {"textData": ["\n".join(c["lines"])],
                      "datasetName": naive, "nodeSet": [name]})
        print(f"  naive add #{name}: {st}", flush=True)
    t0 = time.time()
    print("  cognify naive:", call("POST", "/api/v1/cognify",
                                   {"datasets": [naive], "runInBackground": False})[0],
          f"({time.time()-t0:.0f}s)", flush=True)

    # ---- safe: one dataset per channel ---------------------------------
    ds = {name: f"cl_{name.replace('-', '_')}_{SUF}" for name in corpus}
    for name, c in corpus.items():
        st, _ = call("POST", "/api/v1/add_text",
                     {"textData": ["\n".join(c["lines"])], "datasetName": ds[name]})
        print(f"  safe add #{name}: {st}", flush=True)
    t0 = time.time()
    print("  cognify safe:", call("POST", "/api/v1/cognify",
                                  {"datasets": list(ds.values()), "runInBackground": False})[0],
          f"({time.time()-t0:.0f}s)", flush=True)

    return run_checks(corpus, naive, ds)


def run_checks(corpus, naive, ds):
    def chans(uid):
        """Channels this person is a member of, straight from the export."""
        return [n for n, c in corpus.items() if uid in c["members"]]

    SAM, ANA = "U0SAM", "U0ANA"
    checks = []

    print("\n" + "=" * 68 + "\nNAIVE (node_set scoping) - expected to leak\n" + "=" * 68, flush=True)
    # What people actually build first: one memory over the whole workspace,
    # ask it anything. No scoping at all.
    _, naive_prose = ask("naive, as Sam - one memory, no scoping",
                         "Why is hiring frozen? Explain the reason.", [naive])
    checks.append(("naive leaks the reason in prose (the on-stage moment)",
                   "meridian" in naive_prose.lower()))
    ask("naive, as Sam", "Am I, Sam, going to be made permanent?", [naive])
    # The careful-but-still-wrong version: scope with node_set, which is a
    # relevance filter and not a permission boundary.
    ask("naive+node_set, as Sam - scoping that fails open",
        "Why is hiring frozen? Explain the reason.",
        [naive], node_name=["eng", "general"])

    print("\n" + "=" * 68 + "\nCLEARANCE fan-out - one query per permitted channel\n" + "=" * 68, flush=True)
    _, sam1 = fanout("as Sam", "Why is hiring frozen? Explain the reason.", chans(SAM), ds)
    _, sam2 = fanout("as Sam", "Am I, Sam, going to be made permanent?", chans(SAM), ds)
    checks += [("Sam cannot learn why hiring is frozen", "meridian" not in sam1),
               ("Sam cannot learn the conversion decision", "meridian" not in sam2)]

    _, ctrl = fanout("as Sam (CONTROL - must answer fully)",
                     "How do we deploy? Describe the process.", chans(SAM), ds)
    grounded = sum(w in ctrl for w in ("sha", "staging", "ci")) >= 2
    hallucinated = any(w in ctrl for w in ("jenkins", "nexus", "docker hub"))
    checks.append(("control answer is grounded in OUR corpus, not general knowledge",
                   grounded and not hallucinated))

    print("\n" + "=" * 68 + "\nANA - authorised, must reason from the private channel\n" + "=" * 68, flush=True)
    _, ana = fanout("as Ana", "Why is hiring frozen? Explain the reason.",
                    chans(ANA), ds, forbidden=False)
    checks.append(("Ana actually gets the real reason - the contrast the demo needs",
                   "meridian" in ana))

    print("\n" + "=" * 68 + "\nGATE\n" + "=" * 68, flush=True)
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}", flush=True)
    print("\nGATE:", "PASS - demo-ready" if all(p for _, p in checks)
          else "FAIL - see above, fix before tonight", flush=True)


if __name__ == "__main__":
    main()
