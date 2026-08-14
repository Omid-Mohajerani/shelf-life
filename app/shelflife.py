"""Shelf Life - every answer in a company has one.

Ask a question and you get four things instead of one:

  what the docs say        - authoritative, versioned, sometimes wrong
  what the team found      - the real answer, usually spread across a thread
  how much to trust it     - age, supersession, and whether the author hedged
  who to ask               - the person who actually worked it out

Cognee distils each source. Qdrant finds the messages behind the answer so we
can judge them - the trust verdict is computed from evidence, not guessed by a
model.
"""
from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import date, datetime

import httpx
from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
AUTH = {"X-Api-Key": os.environ["COGNEE_CLOUD_API_KEY"],
        "Content-Type": "application/json"}
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")

DS_DOCS = "shelflife_docs"
DS_CHANNEL = "shelflife_channel"
COLLECTION = "shelflife_messages"
TODAY = date(2026, 8, 14)
STALE_DAYS = 270          # past this, an unrefreshed answer gets a warning

_embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_qdrant = QdrantClient(url=QDRANT_URL, timeout=60)

DOCS_PROMPT = (
    "You are quoting OFFICIAL PRODUCT DOCUMENTATION. Answer using ONLY the provided "
    "context. If the documentation does not cover the question, say exactly that - do "
    "not guess and do not fill the gap from general knowledge. Three sentences at most. "
    "Name the page you used."
)
CHANNEL_PROMPT = (
    "You are summarising what a team actually discovered, from their chat channel. "
    "Use ONLY the provided context. The real answer is usually spread across a thread: "
    "a symptom, a wrong guess, then the diagnosis and the fix - report the CONCLUSION, "
    "not the first thing said. If a message is marked UNPROVEN or says it supersedes an "
    "earlier answer, respect that. If there is nothing on record, say so. Four sentences "
    "at most. Name who worked it out and when."
)


async def _ask(client: httpx.AsyncClient, question: str, dataset: str,
               prompt: str) -> tuple[str, int]:
    t0 = time.perf_counter()

    def ms() -> int:
        return int((time.perf_counter() - t0) * 1000)

    try:
        r = await client.post(f"{BASE}/api/v1/search", json={
            "searchType": "GRAPH_COMPLETION", "query": question,
            "datasets": [dataset], "topK": 20, "systemPrompt": prompt,
            "includeReferences": False,
        }, timeout=120)
        if r.status_code != 200:
            return f"(unavailable: HTTP {r.status_code})", ms()
        return r.json()[0]["search_result"][0].split("Evidence:")[0].strip(), ms()
    except Exception as e:
        return f"(unavailable: {type(e).__name__})", ms()


def _evidence(question: str, limit: int = 6) -> tuple[list[dict], int, int]:
    """The messages behind the answer. Their metadata is what we judge."""
    t0 = time.perf_counter()
    qv = next(iter(_embedder.query_embed(question))).tolist()
    hits = _qdrant.query_points(COLLECTION, query=qv, limit=limit).points
    total = _qdrant.get_collection(COLLECTION).points_count
    return ([{**h.payload, "score": h.score} for h in hits],
            int((time.perf_counter() - t0) * 1000), total)


def _age_days(d: str) -> int:
    return (TODAY - datetime.strptime(d, "%Y-%m-%d").date()).days


def assess(question: str, evidence: list[dict]) -> dict:
    """Compute the trust verdict from evidence, not from a model's opinion.

    Three things can undermine an answer, and they are not the same:
      superseded - somebody explicitly overturned it later
      unproven   - the author said themselves they were not sure
      stale      - nobody has touched it in a long time
    """
    if not evidence:
        return {"level": "none", "headline": "Nothing on record.", "signals": []}

    threads = {e["thread"] for e in evidence if e.get("thread")}
    # A later message that supersedes a thread our evidence sits in.
    overturned = [e for e in evidence if e.get("supersedes") in threads]
    # The author of the evidence hedged, on the record.
    hedged = [e for e in evidence if e.get("unproven")]
    # Age the answer by the newest message that is part of a THREAD. Loose
    # chatter ("new here, where do I start?") is retrieved by similarity but
    # says nothing about whether the answer is still current, and letting it
    # set the age makes every answer look freshly confirmed.
    substantive = [e for e in evidence if e.get("thread")] or evidence
    newest = max(substantive, key=lambda e: e["date"])
    age = _age_days(newest["date"])

    signals, level = [], "good"
    if overturned:
        o = overturned[0]
        level = "superseded"
        signals.append(f"Overturned on {o['date']} by {o['author']}.")
    if hedged:
        h = hedged[0]
        level = "superseded" if level == "superseded" else "unproven"
        signals.append(
            f"{h['author']} flagged their own answer as unproven on {h['date']}.")
    if age > STALE_DAYS and level == "good":
        level = "stale"
        signals.append(f"Nothing new on this for {age // 30} months.")

    headline = {
        "good": f"Current. Last confirmed {age} days ago.",
        "stale": f"Possibly stale - {age // 30} months old and untouched since.",
        "unproven": "Treat as a guess - the author said so themselves.",
        "superseded": "Do not act on the older answer - it was overturned.",
    }[level]

    contributors = {}
    for e in evidence:
        contributors.setdefault(e["author"], {"name": e["author"],
                                              "title": e.get("author_title", ""),
                                              "n": 0, "latest": e["date"]})
        contributors[e["author"]]["n"] += 1
        contributors[e["author"]]["latest"] = max(
            contributors[e["author"]]["latest"], e["date"])

    trace = [f"newest evidence {age}d old", f"{len(evidence)} messages considered"]
    if overturned:
        trace.insert(0, f"{overturned[0]['date']} retracts thread '{overturned[0]['supersedes']}'")
    if hedged:
        trace.insert(0, f"{hedged[0]['date']} author-flagged unproven")
    if not overturned and not hedged:
        trace.insert(0, "no retraction, no hedge")

    return {
        "level": level, "headline": headline, "signals": signals,
        "trace": f"{level} \u2190 " + " \u00b7 ".join(trace),
        "newest": newest["date"], "age_days": age,
        "ask": sorted(contributors.values(), key=lambda c: (-c["n"], c["latest"]))[:2],
        "evidence": [{"date": e["date"], "author": e["author"], "text": e["text"][:400],
                      "unproven": e.get("unproven", False),
                      "supersedes": e.get("supersedes")}
                     for e in sorted(evidence[:4], key=lambda x: x["date"])],
    }


def _admits_nothing(text: str) -> bool:
    """Did this source say, in its own words, that it has nothing?

    Matched as negation + coverage-verb rather than a list of exact phrases -
    the model phrases it a different way nearly every time ("does not cover",
    "does not provide any guidance", "contains no information about").
    """
    t = text.lower()
    negation = ("does not", "doesn't", "do not", "no ", "not ", "nothing", "lacks")
    coverage = ("cover", "provide", "mention", "include", "contain", "address",
                "document", "guidance", "information", "reference", "detail",
                "on record", "specify", "describe")
    for sentence in re.split(r"[.\n]", t)[:4]:
        if any(n in sentence for n in negation) and any(c in sentence for c in coverage):
            return True
    return False


def verdict_only(question: str) -> dict:
    """The trust verdict, from Qdrant alone. ~150ms.

    This is the point of computing trust from metadata instead of asking a model:
    the verdict, the evidence and who to ask do not need an LLM at all. The two
    graph-distilled answers take fifteen seconds and arrive afterwards.
    """
    evidence, q_ms, q_total = _evidence(question)
    return {"question": question, "trust": assess(question, evidence),
            "timing": {"qdrant_ms": q_ms, "qdrant_points": q_total}}


async def answer(question: str) -> dict:
    """Both sources, in parallel, then a verdict computed from the evidence."""
    async with httpx.AsyncClient(headers=AUTH) as client:
        docs, channel = await asyncio.gather(
            _ask(client, question, DS_DOCS, DOCS_PROMPT),
            _ask(client, question, DS_CHANNEL, CHANNEL_PROMPT),
        )
    (docs, docs_ms), (channel, chan_ms) = docs, channel
    evidence, q_ms, q_total = _evidence(question)
    trust = assess(question, evidence)

    return {
        "question": question,
        "docs": {"answer": docs, "silent": _admits_nothing(docs), "ms": docs_ms},
        "channel": {"answer": channel, "ms": chan_ms},
        "trust": trust,
        "timing": {"cognee_docs_ms": docs_ms, "cognee_channel_ms": chan_ms,
                   "qdrant_ms": q_ms, "qdrant_points": q_total},
    }
