# Shelf Life — submission

**Cognee × Qdrant Hack Night, Berlin, 2026-08-14**
**Author:** Omid Mohajerani (solo)
**Live:** https://shelflife.ringamo.dev · **Repo:** https://github.com/Omid-Mohajerani/shelf-life

---

## The idea

**Every answer in a company has a shelf life. Nothing tells you when it expired.**

I work on Sprinklr voice integrations. The knowledge I need is not in the product
documentation — it's in a Teams channel, in a thread, four replies down, written a year ago
by someone who has since moved teams. I don't read those channels. Nobody does. And when I
finally search for something, I find *an* answer with no way to tell whether it's still true.

That is not a retrieval problem. Retrieval works. It's a **trust** problem:

- The official docs are **confidently wrong** about the specific case that's biting you.
- The real answer is spread across a thread — a symptom, a wrong guess, the diagnosis, the
  fix, and then a better fix.
- Someone answered it in 2025 and someone else **overturned it** in 2026.
- The author **said themselves they weren't sure** — and was later proved wrong.

A similarity search returns all four, ranked by cosine distance, with no way to tell them apart.

## What it does

Ask a question and you get four things instead of one:

| | |
|---|---|
| **What the docs say** | Authoritative, versioned, dated — and sometimes wrong |
| **What the team found** | The *conclusion* of the thread, not the first reply |
| **How much to trust it** | `current` · `stale` · `unproven` · `superseded` |
| **Who to ask** | The person who actually worked it out, and when |

### The verdict is computed, not guessed

Three things can undermine an answer, and they are **not** the same thing:

- **`superseded`** — someone explicitly overturned it later
- **`unproven`** — the author hedged, on the record
- **`stale`** — nobody has touched it in months

Asking an LLM "is this trustworthy?" produces a vibe. Shelf Life reads `date`, `author`,
`unproven` and `supersedes` off the actual messages behind the answer, so the verdict is
deterministic — and it can always point at the message that caused it.

## Why both Cognee and Qdrant

Each does something the other cannot.

**Cognee** reads a whole *thread* and distils the conclusion. The real answer to "why won't
my SFTP connector authenticate" exists in **no single message** — it's assembled from five.
That's graph distillation, not chunk retrieval. Cognee is also asked the **docs** and the
**channel as two separate datasets**, so their disagreement stays visible instead of being
blended into one confident paragraph.

**Qdrant** holds every message with its trust metadata in the payload, and finds *which
messages* back the answer. That's the evidence the verdict is computed from.

> Cognee gives you the answer. Qdrant gives you what you need to judge it.

## What's built

- `tools/build_shelflife_corpus.py` — two sources, deliberately in conflict
- `tools/ingest_shelflife.py` — two cognee datasets (docs, channel) + a Qdrant collection
  carrying `date` / `author` / `thread` / `unproven` / `supersedes`
- `app/shelflife.py` — parallel fan-out over both sources, evidence retrieval, verdict
- `app/main.py` — the UI, single file, no external assets (venue wifi is not a dependency
  a demo can afford)

## Demo — four questions, four different failure modes

| Question | Docs | Channel | Verdict |
|---|---|---|---|
| SFTP connector won't connect, credentials are correct | **Confidently wrong** — blames a feature flag and module permissions | It's SHA-1: the connector signs RSA keys with legacy `ssh-rsa`, rejected by OpenSSH 8.8+ | `current` |
| How do I push callback completion status out? | **Silent** — no such endpoint exists | Post Call Workflow → External REST API connector, + six gotchas | `current` |
| How do I authenticate to the platform API? | Silent | 2025 said `client_credentials` — **overturned 2026-07-02**, now auth-code | **`superseded`** |
| Dialer isn't calling, segment says Data Exhausted | Silent | First answer **flagged unproven by its own author**, then contradicted — it was an environment scheduler bug | **`superseded` + `unproven`** |

**The last row is the whole project.** A vector search hands you a colleague's guess as
though it were fact. Shelf Life says *"treat as a guess — the author said so themselves"*,
shows the message where he retracted it, and gives you the corrected answer instead.

## Ready on Monday

It runs now, on a public HTTPS URL, with the corpus loaded. To point it at a real workspace
you swap the ingest adapter — the trust layer doesn't care where messages came from. The
format is Slack-shaped; my own problem is Microsoft Teams, which is the same shape and worse,
because nobody has ever built anything for those channels.

## Honest limitations

- The corpus is **synthetic**. Every gotcha in it is real and cost somebody a real day, but
  the messages were written for this demo rather than exported from a live workspace.
- `unproven` and `supersedes` are **explicit metadata** here. In the wild you'd infer them —
  from hedging language ("I think", "not sure", "guessing") and from later messages that
  contradict earlier ones. That inference is the obvious next step, and I'd rather ship the
  mechanism working on clean signals than a shaky classifier on messy ones.
- **Staleness is age-based**, not change-based. Knowing an answer expired *because the product
  shipped a release that touched it* needs the changelog as a third source. The doc pages
  already carry `version` and `versionAt`, so the hook is there.
- Doc pages ship as **paraphrased stubs** — vendor documentation is not mine to redistribute.
  The live demo runs against a local export.
