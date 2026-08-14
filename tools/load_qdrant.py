#!/usr/bin/env python3
"""Load the Slack corpus into Qdrant, then show the one line that separates a
leaking system from a safe one.

Every message becomes a point whose payload carries its channel. The naive
search queries the collection; the scoped search queries the same collection
with a channel filter. Same data, same index, one filter apart.

    python3 tools/load_qdrant.py          # load + demo
    python3 tools/load_qdrant.py --demo   # demo only, skip loading

Embeddings run locally through FastEmbed - no API key anywhere in this path.
"""
from __future__ import annotations

import json
import os
import sys

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

# qdrant-client 1.19 dropped the .add()/.query() FastEmbed wrappers, so we
# embed explicitly. Local model, no API key on this path.
MODEL = "BAAI/bge-small-en-v1.5"

URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
API_KEY = os.environ.get("QDRANT_API_KEY") or None
COLLECTION = "clearance_messages"
EXPORT = os.path.join(os.path.dirname(__file__), "..", "corpus", "export")


def load_messages():
    users = {u["id"]: u["real_name"] for u in json.load(open(f"{EXPORT}/users.json"))}
    public = json.load(open(f"{EXPORT}/channels.json"))
    private = json.load(open(f"{EXPORT}/groups.json"))
    docs, payloads, ids = [], [], []
    n = 0
    for c in public + private:
        name, is_private = c["name"], c in private
        d = os.path.join(EXPORT, name)
        for fn in sorted(os.listdir(d)):
            date = fn[:-5]
            for m in json.load(open(os.path.join(d, fn))):
                who = users[m["user"]]
                docs.append(f"[{date}] [#{name}] {who}: {m['text']}")
                payloads.append({
                    "channel": name, "is_private": is_private, "date": date,
                    "user": m["user"], "real_name": who, "ts": m["ts"],
                    "text": m["text"], "members": c["members"],
                })
                ids.append(n)
                n += 1
    return docs, payloads, ids


def show(title, hits):
    print(f"\n  {title}")
    for h in hits:
        p = h.payload
        flag = "PRIVATE" if p.get("is_private") else "public "
        print(f"    [{flag}] #{p['channel']:19} {p['real_name']:12} {p['text'][:78]}")


def main():
    client = QdrantClient(url=URL, api_key=API_KEY, timeout=120)
    embedder = TextEmbedding(model_name=MODEL)

    if "--demo" not in sys.argv:
        docs, payloads, ids = load_messages()
        vectors = [v.tolist() for v in embedder.embed(docs)]
        if client.collection_exists(COLLECTION):
            client.delete_collection(COLLECTION)
        client.create_collection(
            COLLECTION,
            vectors_config=models.VectorParams(size=len(vectors[0]),
                                               distance=models.Distance.COSINE),
        )
        client.upsert(COLLECTION, points=[
            models.PointStruct(id=i, vector=v, payload=p)
            for i, v, p in zip(ids, vectors, payloads)
        ])
        print(f"loaded {len(docs)} messages into {COLLECTION!r} at {URL}")

    info = client.get_collection(COLLECTION)
    print(f"collection points: {info.points_count}")

    # Sam is a contractor: #eng and #general only. Straight from the export.
    sam_channels = ["eng", "general"]
    q = "Why is hiring frozen? What is the reason?"
    qv = next(iter(embedder.query_embed(q))).tolist()

    print("\n" + "=" * 72)
    print("NAIVE - query the collection. This is what you write first.")
    print("=" * 72)
    naive = client.query_points(COLLECTION, query=qv, limit=5).points
    show("query_points(collection, query=qv)", naive)
    leaked = [h for h in naive if h.payload["is_private"]]
    print(f"\n  => {len(leaked)} of {len(naive)} results are from a channel Sam cannot see.")

    print("\n" + "=" * 72)
    print("SCOPED - same collection, same query, one filter.")
    print("=" * 72)
    scoped = client.query_points(
        COLLECTION, query=qv, limit=5,
        query_filter=models.Filter(must=[models.FieldCondition(
            key="channel", match=models.MatchAny(any=sam_channels))]),
    ).points
    show("query_filter=Filter(channel IN sam_channels)", scoped)
    bad = [h for h in scoped if h.payload["is_private"]]
    print(f"\n  => {len(bad)} of {len(scoped)} results are private. Expected 0.")

    print("\nGATE:", "PASS" if leaked and not bad
          else "FAIL - baseline did not leak" if not leaked else "FAIL - scoped query leaked")


if __name__ == "__main__":
    main()
