"""Post a message and watch the memory change its mind.

The point of the demo beat is that nothing is faked: the new message goes into
BOTH stores, exactly as the corpus did.

  Qdrant  - one more point, instantly. The trust verdict flips on the next ask.
  Cognee  - add_text then cognify, about 16 seconds. The distilled ANSWER
            changes, because the graph has re-read the thread.

That second half is the one that matters. A verdict flipping is a metadata
lookup; an answer changing means the memory actually revised what it knows.

`reset` puts it back: drop the Qdrant point, forget the channel dataset, re-add
the corpus, cognify. Slower (about a minute) because a knowledge graph has no
undo - which is itself worth knowing.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
AUTH = {"X-Api-Key": os.environ["COGNEE_CLOUD_API_KEY"],
        "Content-Type": "application/json"}
COLLECTION = "shelflife_messages"
DS_CHANNEL = "shelflife_channel"
INJECT_ID = 9001
CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus2", "channel")

_embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
                       timeout=60)

DEFAULT_TEXT = (
    "Update on the SFTP connector - today's platform release ships a modern SSH "
    "client, so it negotiates rsa-sha2-256 properly now. Don't go re-enabling "
    "ssh-rsa on any more servers; the workaround above is obsolete."
)


def _cognee(path: str, body: dict, timeout: int = 600):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 method="POST", headers=AUTH)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status


def _msg(text: str) -> dict:
    return {"source": "channel", "channel": "voice-eng", "date": "2026-08-14",
            "author": "Omid Mohajerani", "author_title": "Senior Voice Engineer",
            "thread": "sftp2", "unproven": False, "supersedes": "sftp",
            "text": text}


def _line(m: dict) -> str:
    return f"[{m['date']}] [#{m['channel']}] {m['author']} ({m['author_title']}): {m['text']}"


def inject(text: str | None = None) -> dict:
    """Write to both stores. Qdrant is instant; cognee has to re-read."""
    m = _msg((text or DEFAULT_TEXT).strip())
    t0 = time.perf_counter()

    vec = next(iter(_embedder.embed([_line(m)]))).tolist()
    _qdrant.upsert(COLLECTION,
                   points=[models.PointStruct(id=INJECT_ID, vector=vec, payload=m)])
    q_ms = int((time.perf_counter() - t0) * 1000)

    t1 = time.perf_counter()
    line = _line(m) + "\n   >> THIS SUPERSEDES THE EARLIER ANSWER IN THIS CHANNEL <<"
    _cognee("/api/v1/add_text",
            {"textData": [line], "datasetName": DS_CHANNEL, "nodeSet": ["channel"]})
    _cognee("/api/v1/cognify", {"datasets": [DS_CHANNEL], "runInBackground": False})
    c_ms = int((time.perf_counter() - t1) * 1000)

    return {"injected": True, "text": m["text"], "qdrant_ms": q_ms, "cognee_ms": c_ms}


def _corpus_threads() -> list[str]:
    msgs = []
    for fn in sorted(os.listdir(CORPUS)):
        msgs.extend(json.load(open(os.path.join(CORPUS, fn))))
    threads, loose = {}, []
    for m in msgs:
        line = _line(m)
        if m["unproven"]:
            line += "\n   >> THE AUTHOR EXPLICITLY FLAGGED THIS AS UNPROVEN <<"
        if m["supersedes"]:
            line += "\n   >> THIS SUPERSEDES THE EARLIER ANSWER IN THIS CHANNEL <<"
        (threads.setdefault(m["thread"], []) if m["thread"] else loose).append(line)
    out = ["[TEAM CHANNEL #voice-eng - practitioner experience, not official]\n\n"
           + "\n".join(v) for v in threads.values()]
    if loose:
        out.append("[TEAM CHANNEL #voice-eng]\n\n" + "\n".join(loose))
    return out


def reset() -> dict:
    """Put it back. A graph has no undo, so this rebuilds the channel dataset."""
    t0 = time.perf_counter()
    _qdrant.delete(COLLECTION,
                   points_selector=models.PointIdsList(points=[INJECT_ID]))
    _cognee("/api/v1/forget", {"dataset": DS_CHANNEL})
    _cognee("/api/v1/add_text",
            {"textData": _corpus_threads(), "datasetName": DS_CHANNEL,
             "nodeSet": ["channel"]})
    _cognee("/api/v1/cognify", {"datasets": [DS_CHANNEL], "runInBackground": False})
    return {"injected": False, "ms": int((time.perf_counter() - t0) * 1000)}


def state() -> dict:
    return {"injected": bool(_qdrant.retrieve(COLLECTION, ids=[INJECT_ID]))}
