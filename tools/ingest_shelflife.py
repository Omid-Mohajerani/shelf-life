#!/usr/bin/env python3
"""Ingest the Shelf Life corpus.

Cognee gets two datasets - the docs and the channel - kept separate so we can
ask each one what it thinks and compare. Qdrant gets every channel message with
its trust metadata in the payload, which is how we work out *which* threads back
an answer and therefore how much to trust it.

    python3 tools/ingest_shelflife.py [corpusdir]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
KEY = os.environ["COGNEE_CLOUD_API_KEY"]
QDRANT = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")

DS_DOCS = "shelflife_docs"
DS_CHANNEL = "shelflife_channel"
COLLECTION = "shelflife_messages"
MODEL = "BAAI/bge-small-en-v1.5"


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


def load(corpus):
    docs = [json.load(open(os.path.join(corpus, "docs", f)))
            for f in sorted(os.listdir(os.path.join(corpus, "docs")))]
    msgs = []
    cdir = os.path.join(corpus, "channel")
    for f in sorted(os.listdir(cdir)):
        msgs.extend(json.load(open(os.path.join(cdir, f))))
    return docs, msgs


def main():
    corpus = sys.argv[1] if len(sys.argv) > 1 else "corpus2"
    docs, msgs = load(corpus)
    print(f"corpus: {len(docs)} doc pages, {len(msgs)} channel messages\n", flush=True)

    # ---- cognee: docs ----------------------------------------------------
    doc_texts = [
        f"[OFFICIAL DOCUMENTATION] [{d['title']}] "
        f"[version {d['version']}, last updated {d['updated']}]\n\n{d['text']}"
        for d in docs
    ]
    st, _ = call("POST", "/api/v1/add_text",
                 {"textData": doc_texts, "datasetName": DS_DOCS, "nodeSet": ["docs"]})
    print(f"  add {DS_DOCS}: {st}", flush=True)

    # ---- cognee: channel, one document per thread -------------------------
    # A thread is the unit of meaning here - the answer is rarely in one message,
    # and the correction is usually three messages later.
    threads, loose = {}, []
    for m in msgs:
        line = f"[{m['date']}] [#{m['channel']}] {m['author']} ({m['author_title']}): {m['text']}"
        if m["unproven"]:
            line += "\n   >> THE AUTHOR EXPLICITLY FLAGGED THIS AS UNPROVEN <<"
        if m["supersedes"]:
            line += "\n   >> THIS SUPERSEDES THE EARLIER ANSWER IN THIS CHANNEL <<"
        if m["thread"]:
            threads.setdefault(m["thread"], []).append(line)
        else:
            loose.append(line)
    chan_texts = ["[TEAM CHANNEL #voice-eng - practitioner experience, not official]\n\n"
                  + "\n".join(v) for v in threads.values()]
    if loose:
        chan_texts.append("[TEAM CHANNEL #voice-eng]\n\n" + "\n".join(loose))
    st, _ = call("POST", "/api/v1/add_text",
                 {"textData": chan_texts, "datasetName": DS_CHANNEL,
                  "nodeSet": ["channel"]})
    print(f"  add {DS_CHANNEL}: {st} ({len(chan_texts)} threads)", flush=True)

    t0 = time.time()
    st, _ = call("POST", "/api/v1/cognify",
                 {"datasets": [DS_DOCS, DS_CHANNEL], "runInBackground": False})
    print(f"  cognify: {st} ({time.time()-t0:.0f}s)", flush=True)

    # ---- qdrant: every message with its trust metadata --------------------
    embedder = TextEmbedding(model_name=MODEL)
    client = QdrantClient(url=QDRANT, timeout=120)
    texts = [f"[{m['date']}] {m['author']}: {m['text']}" for m in msgs]
    vectors = [v.tolist() for v in embedder.embed(texts)]
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(COLLECTION, vectors_config=models.VectorParams(
        size=len(vectors[0]), distance=models.Distance.COSINE))
    client.upsert(COLLECTION, points=[
        models.PointStruct(id=i, vector=v, payload=m)
        for i, (v, m) in enumerate(zip(vectors, msgs))
    ])
    print(f"  qdrant {COLLECTION}: {len(msgs)} points", flush=True)
    print("\nready.")


if __name__ == "__main__":
    main()
