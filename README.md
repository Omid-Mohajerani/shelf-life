# Clearance

**Your Slack has a memory now, and it knows what you're cleared to know.**

Built for *Give Your Slack a Memory* — the Cognee × Qdrant Hack Night, Berlin, 2026-08-14.

---

## The problem

Point an AI at your Slack and it answers beautifully — and it answers *everyone* from
*everything*, including the private channels they cannot see.

The leak is not a copied message. **The model works the secret out.** Nobody has to be shown
a private document for the secret to escape, which is exactly why document-level permissions
do not catch it.

## The demo

The workspace has a hiring freeze. `#eng` has the **fact**: *"freezing new hires until Q4."*
Only `#leadership-private` has the **reason** — an acquisition closing, and leadership wanting
headcount flat for diligence. Ana even writes: *"announce it as a freeze until Q4. Do not give
a reason."*

**Sam is a contractor** in `#eng` and `#general`. He is not in `#leadership-private`.

Ask as Sam, with one memory and no scoping — the thing everyone builds first:

> **"Am I going to be made permanent?"**
> *"Leadership has already decided to extend Sam as a contractor through Q4 and only revisit a
> permanent conversion after the Meridian deal closes (`#leadership-private`, 2026-06-02)."*

A contractor asked about his own future and was shown the room he was not in.

Ask the same question through Clearance:

> `#general` — *"I have no record that says Sam will be made a permanent employee."*
> `#eng` — *"The only relevant exchange is Sam asking Tom, and Tom saying nothing he can commit to."*

Then ask **"How do we deploy?"** and Sam gets the complete process, quoted from `#eng` — proof
this scopes rather than stonewalls. Then ask as **Ana**, and `#leadership-private` gives her the
real reason, because she is allowed it.

## How it works

Cognee's permission boundary is the **dataset**, and it works. The problem is what it costs:

| | Unauthorised asker | Authorised asker |
|---|---|---|
| Everything in one memory | **Leaks** | Great answers |
| One dataset per channel | Correctly refuses | **Answers fall apart too** |

*Useful or safe, pick one.* Clearance is the third option:

> **Work out who is asking → query only the channels they are cleared for, one at a time →
> return one answer card per channel.**

**You cannot leak a channel you never queried.** Permission stops being a filter applied to
results and becomes a property of which questions get asked at all. Answers also get *better*,
because each query is focused rather than spread across datasets.

### Two things we measured rather than assumed

- **`node_set` scoping fails open.** A search scoped to `#eng` returned the private message
  verbatim in its evidence. It is a relevance filter, never documented as a security boundary —
  but it is what you reach for, and it fails open rather than closed.
- **Derived facts carry no channel.** Cognee builds summary nodes from what it reads. One read
  *"a private leadership chat where Tom advises delaying hiring until the Meridian deal closes"*
  — tagged `[tom, hiring, deal]`, **with no channel marker at all.** Raw messages carry
  `[#channel]` so a text filter catches them. That one it cannot catch.

### Identity

Two front doors, one memory. The web UI has an "asking as" switch. The voice line uses
**caller ID as the identity** — no login. An unknown number is an outsider by construction and
gets nothing, which is what makes it safe to hand a stranger the number.

## Stack

- **Cognee Cloud** — the graph, the reasoning, the per-channel datasets that form the boundary
- **Qdrant** — all messages in one collection with `channel` in the payload. The naive baseline
  queries it unfiltered; the scoped path adds a single `Filter`. Same collection, same query,
  same embedding, one line apart. Embeddings run locally via FastEmbed.
- **FastAPI** — fan-out, cards, and the voice webhook

## Run it

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
export COGNEE_CLOUD_URL=... COGNEE_CLOUD_API_KEY=... QDRANT_URL=http://127.0.0.1:6333

python3 tools/build_corpus.py corpus/export   # regenerate the Slack export
python3 tools/ingest_cognee.py                # per-channel datasets + shared baseline
python3 tools/load_qdrant.py                  # load Qdrant, then show the one-line leak demo

cd app && uvicorn main:app --host 0.0.0.0 --port 8000
```

## The corpus

Synthetic, in the real Slack export layout (`users.json`, `channels.json`, **`groups.json`** for
private channels, `<channel>/YYYY-MM-DD.json`). Generated rather than exported: no real workspace
data, a demo that is identical every run, and the chains the story needs are planted rather than
hoped for. Ingesting it is genuinely ingesting a Slack export — the format is the interface.

`tools/validate_corpus.py` is a gate, not a demo: it asserts that the naive path leaks, that the
scoped path does not, that the control question is answered from the corpus rather than general
knowledge, and that **the authorised user still gets the real answer**.
