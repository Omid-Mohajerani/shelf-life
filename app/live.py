"""The live flip: post one message and watch a verdict age.

The whole claim of this project is that the trust verdict is *computed from
evidence*, not decided by a model. The cheapest way to prove that on a stage is
to change the evidence and re-ask the same question.

`/inject` writes one new message into the same Qdrant collection the verdict is
computed from. Nothing else changes - same question, same prompts, same code
path. The banner goes from `current` to `superseded` because a retraction now
exists, and that is the entire argument.

`/reset` removes it again, so the demo can be rehearsed as many times as needed.
"""
from __future__ import annotations

import os

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

COLLECTION = "shelflife_messages"
INJECT_ID = 9001                # well clear of the corpus ids

_embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
                       timeout=60)

# Written in advance, deliberately: this is a scripted demo beat, not a claim
# that the system authored it. It retracts the SFTP workaround thread.
NEW_MESSAGE = {
    "source": "channel", "channel": "voice-eng", "date": "2026-08-14",
    "author": "Omid Mohajerani", "author_title": "Senior Voice Engineer",
    "thread": "sftp2", "unproven": False, "supersedes": "sftp",
    "text": ("Update on the SFTP connector - today's platform release ships a "
             "modern SSH client, so it negotiates rsa-sha2-256 properly now. "
             "Don't go re-enabling ssh-rsa on any more servers; the workaround "
             "above is obsolete and we should undo it where we applied it."),
}


def inject() -> dict:
    vec = next(iter(_embedder.embed([
        f"[{NEW_MESSAGE['date']}] {NEW_MESSAGE['author']}: {NEW_MESSAGE['text']}"
    ]))).tolist()
    _qdrant.upsert(COLLECTION, points=[
        models.PointStruct(id=INJECT_ID, vector=vec, payload=NEW_MESSAGE)
    ])
    return {"injected": True, "date": NEW_MESSAGE["date"],
            "author": NEW_MESSAGE["author"], "text": NEW_MESSAGE["text"]}


def reset() -> dict:
    _qdrant.delete(COLLECTION, points_selector=models.PointIdsList(
        points=[INJECT_ID]))
    return {"injected": False}


def state() -> dict:
    got = _qdrant.retrieve(COLLECTION, ids=[INJECT_ID])
    return {"injected": bool(got)}
