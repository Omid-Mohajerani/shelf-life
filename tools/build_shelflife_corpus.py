#!/usr/bin/env python3
"""Build the Shelf Life corpus: official docs + the channel where reality happens.

Two sources, deliberately in conflict:

  docs/     official product documentation - authoritative, versioned, dated,
            and in several places actively misleading
  channel/  the team channel - where the real answer lives, along with its age,
            its author, and sometimes an explicit "I am not sure about this"

The demo question is never "what does it say". It is "how much should I trust
what it says".

    python3 tools/build_shelflife_corpus.py [outdir]

Docs are extracted from a local Confluence export if present; otherwise the
paraphrased stubs below are used. Vendor documentation is never committed.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

DOCS_EXPORT = os.path.expanduser("~/docs-export")

# Real doc pages, by Confluence id. Used only when the export is present locally.
DOC_PAGES = {
    1001: "SFTP Connector: Data Collection",
    1002: "File Security in FTP Connectors",
    1003: "Callback Manager",
    1004: "Callbacks Overview",
    1005: "Different Types of Segments",
    1006: "Filtering & Segmentation",
    1007: "Outbound Voice Features with VoiceConnect Compatibility",
    1008: "API Connector: Data Collection",
}

# Fallback stubs - paraphrased, not vendor text. These carry the same *shape* as
# the real pages: authoritative tone, no mention of the failure modes that
# actually bite you.
DOC_STUBS = [
    ("SFTP Connector: Data Collection", "2025-11-04", 3, """
Configure an SFTP connector to import records on a schedule.

Required settings: host, port (default 22), username, authentication method,
and remote directory. Both password and RSA key authentication are supported.
Upload the private key in the Destination Specific Settings panel.

If the connector cannot reach the server, verify the connection details are
correct and that the host is reachable from Sprinklr's egress addresses.
Common causes are an incorrect username, an incorrect directory path, or a
firewall blocking the connection.
"""),
    ("Callback Manager", "2026-01-15", 4, """
Callback Manager provides a view of scheduled callbacks across campaigns.
Callbacks may be Agent-First or Customer-First. Use the Scheduled Callbacks
Report to review outcomes.

Callbacks are created against a campaign running a Callback dialer profile.
The Schedule Callback action returns a task identifier.
"""),
    ("Different Types of Segments", "2025-09-30", 2, """
A segment defines the set of records a campaign will dial. Segment states
include Active, Paused, and Data Exhausted.

Data Exhausted indicates the segment has dialed all callable records under its
current filter. Review the segment filter and the Estimated Reach if the
segment is not producing calls.
"""),
    ("Outbound Voice Features with VoiceConnect Compatibility", "2026-03-11", 5, """
VoiceConnect supports bring-your-own-carrier deployments. Inbound traffic is
authenticated using an IP Access Control List and, optionally, a Credential
List.

IP Address - public IPv4 address of your SBC or VoIP server.
Range - use 32 for a single IP address.
"""),
    ("API Connector: Data Collection", "2026-02-20", 3, """
API connectors let Sprinklr collect records from an external HTTP endpoint on a
schedule. Configure the endpoint, authentication, and a response mapping.

For outbound calls from a journey, register the destination under
All Settings -> APIs and Integrations.
"""),
]

# ---------------------------------------------------------------- channel ----
# The team channel. Where the answer actually is.
# (date, author, text, thread_key, flags)
#   flags: "unproven" - the author hedged, on the record
#          "supersedes:<key>" - this message overturns an earlier thread

PEOPLE = {
    "omid": ("Omid Mohajerani", "Senior Voice Engineer"),
    "jonas": ("Jonas Weber", "Integration Engineer"),
    "marek": ("Marek Nowak", "Platform Engineer"),
    "priya": ("Priya Raman", "Delivery Lead"),
    "sam": ("Sam Beck", "New joiner, Voice"),
}

CHANNEL = [
    # ---- 2025: an answer that is correct at the time and rots later ---------
    ("2025-06-12", "jonas", "Anyone got the OAuth flow for the platform APIs working? "
     "I want to script the token.", "oauth"),
    ("2025-06-12", "omid", "client_credentials works. Register the app, grab client id "
     "and secret, POST to /oauth/token with grant_type=client_credentials. Token lasts "
     "about a month.", "oauth"),
    ("2025-06-12", "jonas", "Perfect, that worked. Thanks.", "oauth"),

    # ---- 2025: the docs page everyone finds, and its problem ---------------
    ("2025-11-18", "priya", "Reminder that the official docs are the source of truth for "
     "customer-facing statements. If something in here contradicts them, raise it.", None),

    # ---- 2026-05: SFTP SHA-1. The docs actively mislead. -------------------
    ("2026-05-19", "jonas", "SFTP export connector won't connect on the acc server. "
     "Sprinklr just says there's an issue with the connection details. Host, port, user, "
     "directory and key are all correct - I've triple checked and I can sftp in myself "
     "from my laptop with the same key.", "sftp"),
    ("2026-05-19", "jonas", "Docs just say verify the connection details and check the "
     "firewall. Firewall is open, I can see the connection arrive.", "sftp"),
    ("2026-05-20", "omid", "This is not a credentials problem. Check /var/log/auth.log - "
     "I bet you see 'Disconnected ... [preauth]' mid-authentication.", "sftp"),
    ("2026-05-20", "jonas", "Yes! Exactly that. What is it?", "sftp"),
    ("2026-05-20", "omid", "Sprinklr's SFTP connector uses an old SSH client that signs "
     "RSA keys with the legacy ssh-rsa signature, which is SHA-1. OpenSSH 8.8 and later "
     "disabled SHA-1 RSA signatures by default and only accept rsa-sha2-256 or "
     "rsa-sha2-512. The server rejects the signature type and drops the connection. "
     "The UI surfaces that as a generic connection error, which is why it looks like bad "
     "credentials.", "sftp"),
    ("2026-05-20", "omid", "Quick fix for test, scoped to the sftp group only:\n"
     "Match Group sftpusers\n    PubkeyAcceptedAlgorithms +ssh-rsa\n"
     "then systemctl reload sshd. The rest of the box keeps modern defaults.", "sftp"),
    ("2026-05-20", "omid", "For production do it the other way round - use an ed25519 or "
     "ECDSA key for the destination and avoid SHA-1 entirely. Only re-enable ssh-rsa "
     "server-side, narrowly scoped, if you have no choice.", "sftp"),
    ("2026-05-20", "priya", "Can we get this into the docs? It cost Jonas two days.", "sftp"),
    ("2026-05-20", "omid", "Raised it. Not holding my breath.", "sftp"),

    # ---- 2026-06: the recipe that exists nowhere in the docs ---------------
    ("2026-06-24", "marek", "Is there a GET callback-status API? I need callback "
     "completion out to our system and I can't find an endpoint.", "callback"),
    ("2026-06-25", "omid", "There isn't one. Don't keep looking. It's a push, not a pull.",
     "callback"),
    ("2026-06-29", "omid", "Proven on prod-2 today. Campaign Post Call Workflow journey "
     "-> External REST API connector -> your authenticated webhook. Correlation works: "
     "Schedule Callback returns a taskId and it comes back on the call as "
     "VOICE_CONVERSATION.SCHEDULED_CALLBACK_TASK_ID, so the push can carry it and the "
     "receiver matches it up.", "callback"),
    ("2026-06-29", "omid", "Gotchas, each of which cost me real time:\n"
     "- Register an External REST API first (All Settings -> APIs and Integrations). "
     "The journey API node has no inline URL, only a connector dropdown.\n"
     "- Map values with the resource PICKER, not raw VOICE_CONVERSATION.x in custom code. "
     "In Post Call Workflow context only PROFILE is populated, so raw Groovy returns null.\n"
     "- The OpenAPI spec on a connector is read-only after creation. To rename a body "
     "field you recreate the connector.\n"
     "- Callbacks only exist on a Callback dialer profile. Preview dials have no callback "
     "task, so callbackTaskId comes back empty.", "callback"),
    ("2026-06-29", "marek", "This should be a docs page on its own.", "callback"),

    # ---- 2026-07-02: supersedes the 2025 OAuth answer ----------------------
    ("2026-07-02", "omid", "Heads up - client_credentials is not enabled any more, you "
     "get 'Default Admin User Not Setup'. Use the auth-code flow instead: browser, logged "
     "in, hit /oauth/authorize with client_id and redirect_uri, submit, pick the client, "
     "submit, then exchange the code at /oauth/token. Headers on calls are "
     "Authorization: Bearer <token> plus Key: <client_id>.", "oauth2",
     "supersedes:oauth"),
    ("2026-07-02", "jonas", "Ah - that's why my script broke last week. I assumed I'd "
     "broken it myself and rewrote the whole thing.", "oauth2"),

    # ---- 2026-07: the answer that is honestly flagged as unsure ------------
    ("2026-07-22", "marek", "Dialer isn't calling on the Northwind UAT tenant. Segment says "
     "Data Exhausted but Number of Callable Records is non-zero and Attempted Records is "
     "0.", "exhausted"),
    ("2026-07-23", "marek", "Best guess: Data Exhausted is sticky - updating the leads "
     "doesn't reopen a segment that already finished its pass. Probably need a fresh "
     "segment on the same filter rather than another upload.", "exhausted", "unproven"),
    ("2026-07-23", "marek", "Flagging that as a guess, not a finding. I haven't proven it.",
     "exhausted", "unproven"),
    ("2026-07-23", "omid", "Rechurn is not the lever either - its job is overriding "
     "attempt limits for leads that HAVE been attempted. With Attempted Records 0 there's "
     "no limit to override.", "exhausted"),
    ("2026-08-04", "marek", "Update on the Data Exhausted thing: it was not the segment. "
     "The segment went Active on its own and still scheduled zero calls, and brand new "
     "campaigns in the same tenant failed identically. It's an environment-level scheduler "
     "problem, escalated to Sprinklr support. So please don't go rebuilding segments on my "
     "earlier guess - treat Data Exhausted as a thing to clear, not as an explanation.",
     "exhausted2", "supersedes:exhausted"),

    # ---- 2026-07-31: silent failure the docs describe but nobody reads -----
    ("2026-07-31", "jonas", "The Meridian VoiceConnect trunk: outbound is fine, inbound "
     "never arrives. No error anywhere. Trunk looks half alive.", "acl"),
    ("2026-07-31", "omid", "What's in the IP Access Control List?", "acl"),
    ("2026-07-31", "jonas", "The AudioCodes hostname - "
     "qqjjgaaaqdcr.sip1-region1.audiocodes.io. It resolves to the right IP, I checked.",
     "acl"),
    ("2026-07-31", "omid", "That's it. The VC ACL does not resolve host names, it "
     "compares the literal value. A resolving implementation would have matched, so we "
     "know it doesn't. Put 198.51.100.15/32 in there.", "acl"),
    ("2026-07-31", "jonas", "Inbound working. That would have taken me another day.", "acl"),
    ("2026-07-31", "omid", "Whitelist the media address too - 198.51.100.49. Signalling and "
     "media are different hosts and people miss the second one.", "acl"),

    # ---- the new joiner, a year later, asking all of it again -------------
    ("2026-08-14", "sam", "New here - starting on the Meridian integration. Where do I even find "
     "how any of this works?", None),
]

# Questions this corpus is built to answer, and what a good answer looks like.
DEMO = [
    ("Our SFTP export connector won't connect but the credentials are correct.",
     "Docs say 'verify connection details' and are MISLEADING. The channel has the real "
     "cause (SHA-1 vs OpenSSH 8.8+) and two fixes. Answer must prefer the channel and "
     "say the docs are wrong here."),
    ("How do I get callback completion status out to an external system?",
     "Docs have NOTHING - there is no such endpoint. Only the channel has the recipe. "
     "Answer must say the docs do not cover this."),
    ("How do I authenticate to the platform API?",
     "Two answers on record. The 2025 one (client_credentials) is SUPERSEDED by the "
     "2026-07-02 one (auth-code). Answer must give the current one and say what changed."),
    ("The dialer isn't calling and the segment says Data Exhausted.",
     "The channel's first answer was flagged UNPROVEN by its own author and later "
     "contradicted. Answer must NOT present the guess as fact."),
]


def strip_html(s: str) -> str:
    s = re.sub(r"<ac:[^>]*>|</ac:[^>]*>|<ri:[^>]*>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", s)).strip()


def build_docs(out: str) -> list:
    d = os.path.join(out, "docs")
    os.makedirs(d, exist_ok=True)
    written = []

    idx_path = os.path.join(DOCS_EXPORT, "pages_index.json")
    # --stubs forces the paraphrased set even when the export is present. Used to
    # build the published corpus: vendor documentation is not ours to redistribute.
    if os.path.exists(idx_path) and "--stubs" not in sys.argv:
        idx = {int(p["id"]): p for p in json.load(open(idx_path))}
        for pid, title in DOC_PAGES.items():
            f = os.path.join(DOCS_EXPORT, "pages", f"{pid}.json")
            if not (pid in idx and os.path.exists(f)):
                continue
            page = json.load(open(f))
            body = strip_html(page.get("body_storage") or "")[:6000]
            meta = idx[pid]
            written.append({
                "source": "docs", "title": page["title"],
                "version": meta["version"], "updated": meta["versionAt"][:10],
                "created": meta["createdAt"][:10], "text": body,
            })
        if written:
            print(f"  docs: {len(written)} real pages from the local export "
                  f"(NOT committed - vendor content)")

    if not written:
        for title, updated, version, text in DOC_STUBS:
            written.append({"source": "docs", "title": title, "version": version,
                            "updated": updated, "created": updated,
                            "text": text.strip()})
        print(f"  docs: {len(written)} paraphrased stubs (no local export found)")

    for doc in written:
        slug = re.sub(r"[^a-z0-9]+", "-", doc["title"].lower()).strip("-")
        json.dump(doc, open(os.path.join(d, f"{slug}.json"), "w"), indent=2)
    return written


def build_channel(out: str) -> list:
    d = os.path.join(out, "channel")
    os.makedirs(d, exist_ok=True)
    msgs = []
    for row in CHANNEL:
        date, who, text, thread = row[0], row[1], row[2], row[3]
        flags = list(row[4:])
        name, title = PEOPLE[who]
        msgs.append({
            "source": "channel", "channel": "voice-eng", "date": date,
            "author": name, "author_title": title, "thread": thread,
            "unproven": "unproven" in flags,
            "supersedes": next((f.split(":", 1)[1] for f in flags
                                if f.startswith("supersedes:")), None),
            "text": text,
        })
    by_date = {}
    for m in msgs:
        by_date.setdefault(m["date"], []).append(m)
    for date, group in by_date.items():
        json.dump(group, open(os.path.join(d, f"{date}.json"), "w"), indent=2)
    return msgs


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "corpus2"
    os.makedirs(out, exist_ok=True)

    docs = build_docs(out)
    msgs = build_channel(out)

    json.dump({
        "people": {k: {"name": v[0], "title": v[1]} for k, v in PEOPLE.items()},
        "sources": ["docs", "channel"],
        "demo_questions": [{"question": q, "expected": e} for q, e in DEMO],
    }, open(os.path.join(out, "meta.json"), "w"), indent=2)

    print(f"  channel: {len(msgs)} messages, "
          f"{len({m['thread'] for m in msgs if m['thread']})} threads")
    print(f"  flagged unproven: {sum(m['unproven'] for m in msgs)}")
    print(f"  supersessions: {sum(1 for m in msgs if m['supersedes'])}")
    print(f"\n-> {out}/")
    for q, e in DEMO:
        print(f"\n  Q: {q}\n     {e}")


if __name__ == "__main__":
    main()
