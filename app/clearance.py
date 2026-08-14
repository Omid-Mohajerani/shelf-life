"""Clearance - a workspace memory that knows what you are cleared to know.

The read path, in one sentence: work out who is asking, then ask only the
channels they are cleared for, one at a time.

Permission is not a filter applied to results. It decides which questions get
asked at all - you cannot leak a channel you never queried.
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field

import httpx

BASE = os.environ["COGNEE_CLOUD_URL"].rstrip("/")
KEY = os.environ["COGNEE_CLOUD_API_KEY"]
EXPORT = os.path.join(os.path.dirname(__file__), "..", "corpus", "export")

SHARED_DATASET = "clearance_all"          # naive baseline: everything in one memory
ANSWER_TIMEOUT = 120
AUTH = {"X-Api-Key": KEY, "Content-Type": "application/json"}

GROUNDED = (
    "You are answering questions about a company's Slack workspace using ONLY the "
    "provided context. Never use outside or general knowledge. If the context does "
    "not contain the answer, say plainly that you have nothing on record about it. "
    "Be brief - three sentences at most. Quote the message you relied on with its "
    "channel and date."
)


def dataset_for(channel: str) -> str:
    return "clearance_" + channel.replace("-", "_")


@dataclass
class Workspace:
    """Who exists, which channels they are in. Read from the Slack export itself,
    so there is no second source of truth to drift."""
    people: dict = field(default_factory=dict)      # user_id -> {name, title}
    channels: dict = field(default_factory=dict)    # name -> {members, is_private}
    by_phone: dict = field(default_factory=dict)    # E.164 -> user_id

    @classmethod
    def load(cls) -> "Workspace":
        users = json.load(open(f"{EXPORT}/users.json"))
        public = json.load(open(f"{EXPORT}/channels.json"))
        private = json.load(open(f"{EXPORT}/groups.json"))
        ws = cls()
        for u in users:
            ws.people[u["id"]] = {
                "name": u["real_name"],
                "handle": u["name"],
                "title": u["profile"].get("title", ""),
            }
        for c in public:
            ws.channels[c["name"]] = {"members": c["members"], "is_private": False}
        for c in private:
            ws.channels[c["name"]] = {"members": c["members"], "is_private": True}
        vis = os.path.join(os.path.dirname(EXPORT), "visibility.json")
        if os.path.exists(vis):
            ws.by_phone = {k: v for k, v in
                           json.load(open(vis))["identities"]["phone"].items() if v}
        return ws

    def channels_for(self, user_id: str | None) -> list[str]:
        """The whole access-control model. An unknown caller is an outsider and
        gets nothing - least privilege by default, which is what makes it safe to
        hand the phone number to a stranger."""
        if user_id not in self.people:
            return []
        return [n for n, c in self.channels.items() if user_id in c["members"]]

    def resolve_phone(self, number: str | None) -> str | None:
        return self.by_phone.get((number or "").strip())


async def _ask_one(client: httpx.AsyncClient, question: str, datasets: list[str],
                   node_name: list[str] | None = None) -> str:
    body = {
        "searchType": "GRAPH_COMPLETION", "query": question,
        "datasets": datasets, "topK": 20, "systemPrompt": GROUNDED,
        "includeReferences": True,
    }
    if node_name:
        body["nodeName"] = node_name
    try:
        r = await client.post(f"{BASE}/api/v1/search", json=body, timeout=ANSWER_TIMEOUT)
        if r.status_code != 200:
            return f"(unavailable: HTTP {r.status_code} {r.text[:300]})"
        return r.json()[0]["search_result"][0]
    except Exception as e:                       # a dead channel must not kill the answer
        return f"(unavailable: {type(e).__name__}: {e})"


def _split(answer: str) -> tuple[str, list[str]]:
    prose, _, ev = answer.partition("Evidence:")
    sources = [ln.strip(" -") for ln in ev.strip().splitlines() if ln.strip()]
    return prose.strip(), sources[:4]


async def ask_clearance(ws: Workspace, question: str, user_id: str | None) -> dict:
    """The real read path. One query per permitted channel, in parallel."""
    channels = ws.channels_for(user_id)
    if not channels:
        return {"mode": "clearance", "channels": [], "cards": [], "outsider": True}

    async with httpx.AsyncClient(headers=AUTH) as client:
        answers = await asyncio.gather(*[
            _ask_one(client, question, [dataset_for(c)]) for c in channels
        ])

    cards = []
    for channel, answer in zip(channels, answers):
        prose, sources = _split(answer)
        cards.append({
            "channel": channel,
            "is_private": ws.channels[channel]["is_private"],
            "answer": prose,
            "sources": sources,
        })
    return {"mode": "clearance", "channels": channels, "cards": cards, "outsider": False}


async def ask_naive(question: str) -> dict:
    """What everyone builds first: one memory over the whole workspace, no scoping.
    Kept in the product on purpose - it is the 'before' the demo opens with."""
    async with httpx.AsyncClient(headers=AUTH) as client:
        answer = await _ask_one(client, question, [SHARED_DATASET])
    prose, sources = _split(answer)
    return {"mode": "naive", "cards": [{"channel": "entire workspace",
                                        "is_private": False,
                                        "answer": prose, "sources": sources}]}
