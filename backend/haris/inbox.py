"""The report inbox (demo): reports a victim chooses to send to the authority.

Until now Haris kept nothing: the report file was built in memory and handed to
the victim. Sending a report straight to the authority means it has to wait
somewhere until a person opens it, so this inbox keeps a report only when:
  1. the victim has seen the whole report and pressed "send" (consent), and
  2. for as long as the retention period (HARIS_INBOX_RETENTION_DAYS, 7 days),
     after which it is deleted automatically, whatever its status.
Screenshots are not stored: they stay in the victim's own report file.

Each report gets a priority (critical, financial, medium, indicator) and the
emirate it belongs to, so the most urgent case is at the top of the queue.
The victim follows the status with the reference number and a private token;
the token is stored only as a hash.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .playbooks import PLAYBOOKS
from .report import _clean, _clean_list, new_reference
from .text import SUPPORTED_LANGS, detect_language, normalize
from .translate import translate, translate_lines
from .translations import section

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "inbox.db"
DAY = 24 * 3600
STATUSES = ("new", "received", "info_requested", "closed")
PRIORITIES = ("critical", "financial", "medium", "indicator")
EMIRATES = ("abu_dhabi", "dubai", "sharjah", "ajman", "umm_al_quwain", "ras_al_khaimah", "fujairah")
ACTIONS = {"receive": "received", "request_info": "info_requested", "close": "closed"}
# Visitors have no Emirates ID: they confirm identity with a UAE PASS visitor account (passport) or the passport itself.
DEPARTURES = ("within_3_days", "within_week", "later", "unknown")
VISITOR_IDENTITY = ("uae_pass_visitor", "passport")
TEXT = {lang: section(lang, "inbox") for lang in SUPPORTED_LANGS}


def _pattern(words: str) -> re.Pattern:
    return re.compile("|".join(re.escape(normalize(w)) for w in words.split("|")))


# Signs that a life is at risk or that a child is involved: these go to the top of the queue.
VIOLENCE = _pattern("اقتلك|سأقتل|قتل|أذبح|سأؤذي|أؤذيك|انتحار|ينتحر|أنتحر|kill you|i will kill|hurt you|suicide|shoot"
                    "|मार डालूँगा|मार दूँगा|आत्महत्या|جان سے مار|خودکشی")
MINOR = _pattern("طفل|أطفال|قاصر|ابني|بنتي|ولدي|طالب|طالبة|عمره 1|عمرها 1|child|minor|my son|my daughter|kid|teen"
                 "|बच्चा|बच्चे|बेटा|बेटी|نابالغ|بچہ|بچے|بیٹا|بیٹی")
# Money lost more than a day ago: still serious, but the chance to freeze it has passed.
OLD = _pattern("أقدم|قديم|أسبوع|اسبوع|شهر|older|last week|weeks ago|a week|month|पुराना|हफ्ते|महीने|پرانا|ہفتے|مہینے")


def _settings() -> dict:
    return {
        "db": Path(os.getenv("HARIS_INBOX_DB", str(DEFAULT_DB))),
        "retention": int(os.getenv("HARIS_INBOX_RETENTION_DAYS", "7")) * DAY,
    }


def retention_days() -> int:
    return _settings()["retention"] // DAY


def _connect() -> sqlite3.Connection:
    cfg = _settings()
    path = cfg["db"]
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists()
    con = sqlite3.connect(path, timeout=5)
    if fresh:
        os.chmod(path, 0o600)  # readable by this server's user only
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS reports (
            ref TEXT PRIMARY KEY, created_at REAL, updated_at REAL, status TEXT, priority TEXT,
            emirate TEXT, incident TEXT, lang TEXT, verified INTEGER, token_hash TEXT,
            fields TEXT, events TEXT);
        CREATE INDEX IF NOT EXISTS reports_created ON reports (created_at);
        """
    )
    con.execute("DELETE FROM reports WHERE created_at < ?", (time.time() - cfg["retention"],))
    return con


def triage(fields: dict) -> str:
    """The queue priority, from the same table as the blueprint."""
    incident = fields.get("incident_type", "suspicious_only")
    tr = fields.get("translation") or {}
    # The victim's words and, when there is one, their Arabic translation: a threat is caught in either.
    text = normalize(" ".join([fields.get("description", ""), *fields.get("steps_taken", []),
                               tr.get("description", ""), *tr.get("steps_taken", [])]))
    if VIOLENCE.search(text) or (incident in ("extortion", "harassment", "privacy_violation") and MINOR.search(text)):
        return "critical"
    if incident in ("money_sent", "business_fraud"):
        return "medium" if OLD.search(normalize(fields.get("occurred_at", ""))) else "financial"
    if incident == "suspicious_only":
        return "indicator"
    return "medium"


def _fields(data: dict) -> dict:
    incident = data.get("incident_type") if data.get("incident_type") in PLAYBOOKS else "suspicious_only"
    return {
        "incident_type": incident,
        "occurred_at": _clean(data.get("occurred_at"), 100),
        "description": _clean(data.get("description")),
        "amount": _clean(data.get("amount"), 40),
        "currency": _clean(data.get("currency") or "AED", 10),
        "payment_method": _clean(data.get("payment_method"), 200),
        "scammer_identifiers": _clean_list(data.get("scammer_identifiers")),
        "steps_taken": _clean_list(data.get("steps_taken")),
        "evidence_count": len(data.get("evidence") or []),
        "reporter_name": _clean(data.get("reporter_name"), 120),
        "reporter_contact": _clean(data.get("reporter_contact"), 120),
    }


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


REFERENCE = re.compile(r"HRS-\d{8}-[0-9A-F]{6}")


def to_arabic(fields: dict, lang: str) -> dict | None:
    """The officer reads Arabic: translate what the victim wrote in their own words. Labels Haris wrote are already Arabic."""
    if lang == "ar":
        return None
    story = translate(fields["description"], lang, "ar")
    short = [("occurred_at", fields["occurred_at"]), ("payment_method", fields["payment_method"])]
    short += [("steps_taken", s) for s in fields["steps_taken"]]
    short += [("nationality", (fields.get("visitor") or {}).get("nationality", ""))]
    short = [(k, v) for k, v in short if v]
    lines = translate_lines([v for _, v in short], lang, "ar") if short else {"lines": [], "ok": True}
    got = lines["lines"] if lines["ok"] else []
    out = {"from": lang, "ok": story["ok"], "engine": story["engine"] or lines.get("engine"),
           "description": story["text"], "steps_taken": []}
    if len(got) == len(short):  # one line out for each line in; otherwise keep only the originals
        for (key, _), value in zip(short, got):
            if key == "steps_taken":
                out["steps_taken"].append(value.strip())
            else:
                out[key] = value.strip()
    return out


def _visitor(info: dict | None) -> dict | None:
    """A tourist or other visitor: where they are from, when they leave, and how to reach them after."""
    if not info:
        return None
    departure = info.get("departure") if info.get("departure") in DEPARTURES else "unknown"
    identity = info.get("identity") if info.get("identity") in VISITOR_IDENTITY else None
    return {"nationality": _clean(info.get("nationality"), 60), "departure": departure,
            "contact_abroad": _clean(info.get("contact_abroad"), 120), "identity": identity}


def leaving_soon(fields: dict) -> bool:
    return (fields.get("visitor") or {}).get("departure") == "within_3_days"


def submit(data: dict, lang: str, emirate: str, verified: bool, reference: str = "",
           visitor: dict | None = None) -> dict:
    """Save a report the victim agreed to send. Returns the reference and the private status token.

    The reference of the report file the victim already has is kept, so one case has one number.
    """
    if emirate not in EMIRATES:
        raise ValueError("unknown emirate")
    fields = _fields(data)
    if _visitor(visitor):
        fields["visitor"] = _visitor(visitor)
    translated = to_arabic(fields, lang)
    if translated:
        fields["translation"] = translated
    now = time.time()
    ref = reference if REFERENCE.fullmatch(reference or "") else ""
    token = secrets.token_urlsafe(18)
    priority = triage(fields)
    events = [{"ts": now, "kind": "submitted"}]
    with closing(_connect()) as con, con:
        if not ref or _row(con, ref):  # missing, malformed or already sent: a fresh number
            ref = new_reference()
        con.execute("INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (ref, now, now, "new", priority, emirate, fields["incident_type"], lang, int(verified),
                     _hash(token), json.dumps(fields, ensure_ascii=False), json.dumps(events)))
    return {"reference": ref, "token": token, "status": "new", "priority": priority,
            "status_label": TEXT[lang]["status"]["new"], "retention_days": retention_days()}


def _row(con, ref: str):
    return con.execute("SELECT * FROM reports WHERE ref = ?", (ref,)).fetchone()


def _check(row, token: str) -> bool:
    return bool(row) and bool(token) and hmac.compare_digest(row["token_hash"], _hash(token))


def status(ref: str, token: str) -> dict | None:
    """What the victim sees: the status and the messages from the authority."""
    with closing(_connect()) as con:
        row = _row(con, ref)
        if not _check(row, token):
            return None
        return _public(row)


def _public(row) -> dict:
    T = TEXT[row["lang"]]
    events = json.loads(row["events"])
    return {
        "reference": row["ref"], "status": row["status"], "status_label": T["status"][row["status"]],
        "updated_at": row["updated_at"],
        # An officer's note is shown in the victim's language, with the Arabic original beside it.
        "events": [{"ts": e["ts"], "kind": e["kind"], "label": T["events"][e["kind"]],
                    "note": e.get("note_victim") or e.get("note", ""),
                    "original": e.get("note", "") if e.get("note_victim") else ""}
                   for e in events],
    }


def reply(ref: str, token: str, text: str) -> dict | None:
    """The victim adds information, usually after the authority asked for it."""
    text = _clean(text, 2000)
    if not text:
        raise ValueError("empty reply")
    with closing(_connect()) as con:
        row = _row(con, ref)
    if not _check(row, token) or row["status"] == "closed":
        return None
    event = {"ts": time.time(), "kind": "reply", "note": text}
    if row["lang"] != "ar":  # translated outside the database lock: the model can take seconds
        tr = translate(text, row["lang"], "ar")
        event.update(note_ar=tr["text"]) if tr["ok"] else event.update(needs_translator=True)
    with closing(_connect()) as con, con:
        row = _row(con, ref)
        if not row or row["status"] == "closed":
            return None
        events = json.loads(row["events"]) + [event]
        new_status = "received" if row["status"] == "info_requested" else row["status"]
        con.execute("UPDATE reports SET events = ?, status = ?, updated_at = ? WHERE ref = ?",
                    (json.dumps(events, ensure_ascii=False), new_status, time.time(), ref))
        return _public(_row(con, ref))


# --- The authority's side ----------------------------------------------------

def _summary(row) -> dict:
    f = json.loads(row["fields"])
    events = json.loads(row["events"])
    received = next((e["ts"] for e in events if e["kind"] == "received"), None)
    return {
        "reference": row["ref"], "status": row["status"], "priority": row["priority"], "emirate": row["emirate"],
        "incident_type": row["incident"], "incident_title": PLAYBOOKS[row["incident"]]["title"]["ar"],
        "lang": row["lang"], "verified": bool(row["verified"]), "created_at": row["created_at"],
        "updated_at": row["updated_at"], "received_at": received,
        "amount": f["amount"], "currency": f["currency"], "has_reply": any(e["kind"] == "reply" for e in events),
        "needs_translator": row["lang"] != "ar" and not (f.get("translation") or {}).get("ok"),
        "visitor": bool(f.get("visitor")), "leaving_soon": leaving_soon(f),
    }


def queue() -> dict:
    """Every report, most urgent first; closed ones at the bottom. Plus the counters for the dashboard."""
    with closing(_connect()) as con:
        rows = con.execute("SELECT * FROM reports").fetchall()
    items = [_summary(r) for r in rows]
    rank = {p: i for i, p in enumerate(PRIORITIES)}
    # A visitor who leaves within 3 days moves up one step: after they fly, a statement or a refund is much harder.
    def place(i):
        r = rank[i["priority"]]
        return (i["status"] == "closed", r - 1 if i["leaving_soon"] and r > 1 else r, not i["leaving_soon"], i["created_at"])

    items.sort(key=place)
    open_items = [i for i in items if i["status"] != "closed"]
    waits = [i["received_at"] - i["created_at"] for i in items if i["received_at"]]
    return {
        "items": items,
        "stats": {
            "new": sum(i["status"] == "new" for i in items),
            "urgent": sum(i["priority"] in ("critical", "financial") for i in open_items),
            "in_progress": sum(i["status"] in ("received", "info_requested") for i in items),
            "closed": sum(i["status"] == "closed" for i in items),
            "avg_minutes_to_receive": round(sum(waits) / len(waits) / 60, 1) if waits else None,
            "retention_days": retention_days(),
            # Open cases by the reporter's language, so a supervisor can hand them to officers who speak it.
            "by_lang": {lang: sum(i["lang"] == lang for i in open_items) for lang in SUPPORTED_LANGS},
            "needs_translator": sum(i["needs_translator"] for i in open_items),
            "visitors": sum(i["visitor"] for i in open_items),
            "leaving_soon": sum(i["leaving_soon"] for i in open_items),
        },
    }


def detail(ref: str) -> dict | None:
    with closing(_connect()) as con:
        row = _row(con, ref)
    if not row:
        return None
    return {**_summary(row), "fields": json.loads(row["fields"]), "events": json.loads(row["events"])}


def act(ref: str, action: str, note: str = "") -> dict | None:
    """Receive, ask for more information, or close a report. A note is sent to the victim."""
    if action not in ACTIONS:
        raise ValueError("unknown action")
    note = _clean(note, 1000)
    if action == "request_info" and not note:
        raise ValueError("say what information is needed")
    with closing(_connect()) as con:
        row = _row(con, ref)
    if not row or row["status"] == "closed":
        return None
    event = {"ts": time.time(), "kind": ACTIONS[action], **({"note": note} if note else {})}
    if note and row["lang"] != "ar":  # the victim reads it in their own language
        tr = translate(note, detect_language(note), row["lang"])
        event.update(note_victim=tr["text"]) if tr["ok"] else event.update(untranslated=True)
    with closing(_connect()) as con, con:
        row = _row(con, ref)
        if not row or row["status"] == "closed":
            return None
        new_status = ACTIONS[action]
        events = json.loads(row["events"]) + [event]
        con.execute("UPDATE reports SET status = ?, events = ?, updated_at = ? WHERE ref = ?",
                    (new_status, json.dumps(events, ensure_ascii=False), time.time(), ref))
    return detail(ref)
