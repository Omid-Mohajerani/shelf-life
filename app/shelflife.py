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
               prompt: str) -> str:
    try:
        r = await client.post(f"{BASE}/api/v1/search", json={
            "searchType": "GRAPH_COMPLETION", "query": question,
            "datasets": [dataset], "topK": 20, "systemPrompt": prompt,
            "includeReferences": False,
        }, timeout=120)
        if r.status_code != 200:
            return f"(unavailable: HTTP {r.status_code})"
        return r.json()[0]["search_result"][0].split("Evidence:")[0].strip()
    except Exception as e:
        return f"(unavailable: {type(e).__name__})"


def _evidence(question: str, limit: int = 6) -> list[dict]:
    """The messages behind the answer. Their metadata is what we judge."""
    qv = next(iter(_embedder.query_embed(question))).tolist()
    hits = _qdrant.query_points(COLLECTION, query=qv, limit=limit).points
    return [{**h.payload, "score": h.score} for h in hits]


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
    newest = max(evidence, key=lambda e: e["date"])
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

    return {
        "level": level, "headline": headline, "signals": signals,
        "newest": newest["date"], "age_days": age,
        "ask": sorted(contributors.values(), key=lambda c: (-c["n"], c["latest"]))[:2],
        "evidence": [{"date": e["date"], "author": e["author"], "text": e["text"][:400],
                      "unproven": e.get("unproven", False),
                      "supersedes": e.get("supersedes")} for e in evidence[:4]],
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


async def answer(question: str) -> dict:
    """Both sources, in parallel, then a verdict computed from the evidence."""
    async with httpx.AsyncClient(headers=AUTH) as client:
        docs, channel = await asyncio.gather(
            _ask(client, question, DS_DOCS, DOCS_PROMPT),
            _ask(client, question, DS_CHANNEL, CHANNEL_PROMPT),
        )
    evidence = _evidence(question)
    trust = assess(question, evidence)

    docs_silent = _admits_nothing(docs)
    return {
        "question": question,
        "docs": {"answer": docs, "silent": docs_silent},
        "channel": {"answer": channel},
        "trust": trust,
    }
