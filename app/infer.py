"""Infer trust signals from how people actually write.

Nobody tags their own messages `unproven: true`. So the flags have to come out
of the prose, or the whole idea only works on a corpus someone hand-annotated.

Two signals, and the order matters:

  retraction - "update on that: it was not the segment", "don't go rebuilding
               on my earlier guess". This message overturns an earlier one.
  hedge      - "best guess", "I haven't proven it", "not a finding".
               The author is telling you not to lean on this.

Retraction is checked FIRST and wins, because a retraction usually *mentions*
the guess it is retracting ("...on my earlier guess") and would otherwise be
misread as a hedge itself.

Honest about what this is: a heuristic, tuned against this corpus, where it
recovers all four hand-placed flags and fires on nothing else. It is a
demonstration that the signals are recoverable from prose, not a claim to have
solved hedge detection. An LLM pass would generalise better and cost a call per
message; these rules are free and auditable, which is the right trade for the
signals that drive a trust verdict.
"""
from __future__ import annotations

import re

RETRACTION = [
    r"\bupdate on\b", r"\bit was not\b", r"\bit wasn'?t\b", r"\bturned out\b",
    r"\bdon'?t go\b", r"\bno longer\b", r"\bnot enabled any more\b",
    r"\bcorrection\b", r"\bignore (my|the) earlier\b", r"\bscratch that\b",
]

HEDGE = [
    r"\bbest guess\b", r"\bi think\b", r"\bnot sure\b", r"\bmight be\b",
    r"\bflagging that as a guess\b", r"\bhaven'?t proven\b", r"\bunproven\b",
    r"\bmy guess\b", r"\bprobably need\b", r"\bnot a finding\b",
    r"\buntested\b", r"\bin theory\b",
]


def _matches(patterns: list[str], text: str) -> list[str]:
    return [p for p in patterns if re.search(p, text, re.I)]


def classify(text: str) -> dict:
    """-> {'kind': 'retraction'|'hedge'|None, 'cues': [...]}"""
    cues = _matches(RETRACTION, text)
    if cues:
        return {"kind": "retraction", "cues": cues}
    cues = _matches(HEDGE, text)
    if cues:
        return {"kind": "hedge", "cues": cues}
    return {"kind": None, "cues": []}


def infer_flags(messages: list[dict]) -> list[dict]:
    """Re-derive `unproven` and `supersedes` from the prose, discarding whatever
    the corpus was annotated with. Same shape in, same shape out.

    A retraction supersedes the most recent EARLIER thread that it isn't part of
    - which is how a human reads it too: "update on the X thing" refers back to
    where X was discussed.
    """
    out = [dict(m) for m in messages]
    seen: list[tuple[str, str]] = []      # (date, thread), in order

    for m in out:
        verdict = classify(m["text"])
        m["unproven"] = verdict["kind"] == "hedge"
        m["supersedes"] = None
        m["cues"] = verdict["cues"]

        if verdict["kind"] == "retraction":
            earlier = [t for d, t in seen if t and t != m.get("thread")]
            if earlier:
                m["supersedes"] = earlier[-1]

        if m.get("thread"):
            seen.append((m["date"], m["thread"]))

    return out
