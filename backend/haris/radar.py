"""Campaign radar: turn many small reports into one early warning.

A person who received a suspicious message and did not respond can report
it. Only what belongs to the sender is kept: their phone numbers, e-mails,
IBANs, link domains, and the message text with the reporter's own personal
data removed. Nothing about the reporter is stored except a keyed hash of a
random id their browser made, so one device counts once.

Reports that share a number, a link domain or the same message text are
grouped into one campaign, and a campaign moves up these steps:

    collecting  fewer than WARN people reported it
    warning     WARN or more people within the window: Haris shows
                "reported by N people" to anyone who checks it
    escalated   ESCALATE or more people, or WARN or more with a link that
                imitates an official brand: the authority is alerted
    confirmed   the authority approved a public warning: every Haris user
                sees it, and a block request goes to the telecom providers
    dismissed   the authority decided it is not a scam

Only the authority can confirm. Reports alone never block a number, because
people can report an innocent number on purpose and scammers spoof real
numbers. This is a demo store in SQLite; a real launch needs a data-sharing
agreement, hosting in the UAE and verified reporters (for example UAE PASS).
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

from .detector import analyze
from .i18n import CATEGORY_LABELS, RISK_LABELS, RISK_SUMMARY, t
from .redact import EMAIL, IBAN, PHONE, redact
from .text import SUPPORTED_LANGS, normalize, normalize_digits
from .translations import section
from .urls import analyze_url, extract_urls

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "radar.db"
DAY = 24 * 3600

AUTHORITY_NAME = {lang: section(lang, "radar")["authority"] for lang in SUPPORTED_LANGS}
TEXT = {key: {lang: section(lang, "radar")[key] for lang in SUPPORTED_LANGS}
        for key in section("ar", "radar") if key not in ("authority", "kind")}
TEXT["kind"] = {kind: {lang: section(lang, "radar")["kind"][kind] for lang in SUPPORTED_LANGS}
                for kind in section("ar", "radar")["kind"]}


def _settings() -> dict:
    return {
        "db": Path(os.getenv("HARIS_RADAR_DB", str(DEFAULT_DB))),
        "warn": int(os.getenv("HARIS_RADAR_WARN", "3")),
        "escalate": int(os.getenv("HARIS_RADAR_ESCALATE", "10")),
        "window": int(os.getenv("HARIS_RADAR_WINDOW_HOURS", "24")) * 3600,
        "retention": int(os.getenv("HARIS_RADAR_RETENTION_DAYS", "30")) * DAY,
    }


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=5)
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY, created_at REAL, reporter TEXT, text TEXT, category TEXT, lang TEXT,
            lookalike INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS report_keys (report_id INTEGER, kind TEXT, value TEXT);
        CREATE INDEX IF NOT EXISTS report_keys_value ON report_keys (kind, value);
        CREATE TABLE IF NOT EXISTS decisions (kind TEXT, value TEXT, status TEXT, decided_at REAL,
            PRIMARY KEY (kind, value));
        CREATE TABLE IF NOT EXISTS broadcasts (id INTEGER PRIMARY KEY, created_at REAL, category TEXT,
            keys TEXT, active INTEGER DEFAULT 1);
        """
    )
    return con


def _secret(con: sqlite3.Connection) -> bytes:
    row = con.execute("SELECT value FROM meta WHERE key = 'secret'").fetchone()
    if row:
        return bytes.fromhex(row["value"])
    value = secrets.token_bytes(32)
    con.execute("INSERT INTO meta (key, value) VALUES ('secret', ?)", (value.hex(),))
    return value


# --- What identifies a campaign ---------------------------------------------

def _phone_key(raw: str) -> str:
    digits = re.sub(r"\D", "", normalize_digits(raw))
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) in (9, 10):
        digits = "971" + digits[1:]  # 050 123 4567 -> 971501234567
    return digits


def template_of(text: str) -> str | None:
    """The message with numbers, links and names of amounts stripped, so one campaign sent
    from many numbers still groups together."""
    body = normalize(redact(text).text)
    body = re.sub(r"https?://\S+|www\.\S+|\S+\.(?:com|ae|net|org|top|click|xyz|online|info|site)\S*", " ", body)
    body = re.sub(r"\[[a-z_]+\]|\d+(?:[.,]\d+)?", " ", body)
    body = re.sub(r"[^\w؀-ۿ]+", " ", body).strip()
    if len(body) < 25:
        return None
    return hashlib.sha256(body[:300].encode()).hexdigest()[:16]


def keys_of(text: str) -> list[tuple[str, str]]:
    plain = normalize_digits(text)
    keys = [("phone", _phone_key(m.group(0))) for m in PHONE.finditer(plain)]
    keys += [("email", m.group(0).lower()) for m in EMAIL.finditer(plain)]
    keys += [("iban", re.sub(r"\s", "", m.group(0))) for m in IBAN.finditer(plain)]
    for url in extract_urls(text):
        link = analyze_url(url)
        if link.domain and not link.official:
            keys.append(("domain", link.domain))
    template = template_of(text)
    if template:
        keys.append(("template", template))
    return list(dict.fromkeys(k for k in keys if k[1]))


# --- Writing ----------------------------------------------------------------

def report(text: str, reporter_id: str, lang: str) -> dict:
    """Store one report and return the campaign it belongs to now."""
    cfg = _settings()
    result = analyze(text, lang, use_llm=False)
    keys = keys_of(text)
    lookalike = any("brand_lookalike" in link["flags"] for link in result["links"])
    now = time.time()
    with closing(_connect(cfg["db"])) as con, con:
        reporter = hmac.new(_secret(con), reporter_id.encode(), hashlib.sha256).hexdigest()[:20]
        con.execute("DELETE FROM report_keys WHERE report_id IN (SELECT id FROM reports WHERE created_at < ?)",
                    (now - cfg["retention"],))
        con.execute("DELETE FROM reports WHERE created_at < ?", (now - cfg["retention"],))
        cur = con.execute(
            "INSERT INTO reports (created_at, reporter, text, category, lang, lookalike) VALUES (?, ?, ?, ?, ?, ?)",
            (now, reporter, redact(text).text[:2000], result["category"], lang, int(lookalike)),
        )
        con.executemany("INSERT INTO report_keys (report_id, kind, value) VALUES (?, ?, ?)",
                        [(cur.lastrowid, kind, value) for kind, value in keys])
    found = campaign_for(keys, lang)
    return {"received": True, "keys": len(keys), "campaign": found}


# --- Grouping ---------------------------------------------------------------

def _load(con: sqlite3.Connection, since: float):
    reports = {r["id"]: dict(r) for r in con.execute("SELECT * FROM reports WHERE created_at >= ?", (since,))}
    links = con.execute(
        "SELECT report_id, kind, value FROM report_keys WHERE report_id IN (SELECT id FROM reports WHERE created_at >= ?)",
        (since,),
    ).fetchall()
    decisions = {(d["kind"], d["value"]): d["status"] for d in con.execute("SELECT * FROM decisions")}
    return reports, links, decisions


def campaigns(lang: str = "ar") -> list[dict]:
    """Group recent reports into campaigns: reports sharing any key end up together."""
    cfg = _settings()
    with closing(_connect(cfg["db"])) as con, con:
        reports, links, decisions = _load(con, time.time() - cfg["window"])

    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for row in links:
        parent[find(("r", row["report_id"]))] = find((row["kind"], row["value"]))
    groups: dict = {}
    for row in links:
        groups.setdefault(find(("r", row["report_id"])), set()).add(row["report_id"])

    out = []
    for root, ids in groups.items():
        members = [reports[i] for i in ids if i in reports]
        if not members:
            continue
        keys = sorted({(r["kind"], r["value"]) for r in links if r["report_id"] in ids})
        people = len({m["reporter"] for m in members})
        lookalike = any(m["lookalike"] for m in members)
        statuses = {decisions.get(k) for k in keys}
        if "confirmed" in statuses:
            status = "confirmed"
        elif "dismissed" in statuses:
            status = "dismissed"
        elif people >= cfg["escalate"] or (lookalike and people >= cfg["warn"]):
            status = "escalated"
        elif people >= cfg["warn"]:
            status = "warning"
        else:
            status = "collecting"
        categories = [m["category"] for m in members if m["category"] != "unknown"]
        category = max(set(categories), key=categories.count) if categories else "unknown"
        latest = max(members, key=lambda m: m["created_at"])
        out.append({
            "id": hashlib.sha256(json.dumps(keys[0]).encode()).hexdigest()[:12],
            "status": status,
            "people": people,
            "reports": len(members),
            "first_seen": min(m["created_at"] for m in members),
            "last_seen": latest["created_at"],
            "category": category,
            "category_label": t(CATEGORY_LABELS, category, lang),
            "lookalike_link": lookalike,
            "identifiers": [{"kind": k, "value": v} for k, v in keys if k != "template"],
            "keys": [{"kind": k, "value": v} for k, v in keys],
            "sample": latest["text"],
        })
    order = {"escalated": 0, "warning": 1, "confirmed": 2, "collecting": 3, "dismissed": 4}
    return sorted(out, key=lambda c: (order[c["status"]], -c["people"], -c["last_seen"]))


def campaign_for(keys: list[tuple[str, str]], lang: str = "ar") -> dict | None:
    wanted = set(keys)
    for c in campaigns(lang):
        if wanted & {(k["kind"], k["value"]) for k in c["keys"]}:
            return c
    return None


# --- The authority's decisions ----------------------------------------------

def decide(campaign_id: str, status: str) -> dict | None:
    if status not in ("confirmed", "dismissed"):
        raise ValueError("status must be confirmed or dismissed")
    found = next((c for c in campaigns() if c["id"] == campaign_id), None)
    if not found:
        return None
    cfg = _settings()
    now = time.time()
    keys = [(k["kind"], k["value"]) for k in found["keys"]]
    broadcast_id = None
    with closing(_connect(cfg["db"])) as con, con:
        con.executemany("INSERT OR REPLACE INTO decisions (kind, value, status, decided_at) VALUES (?, ?, ?, ?)",
                        [(k, v, status, now) for k, v in keys])
        if status == "confirmed":
            broadcast_id = con.execute("INSERT INTO broadcasts (created_at, category, keys) VALUES (?, ?, ?)",
                                       (now, found["category"], json.dumps(keys))).lastrowid
    blocks = [i for i in found["identifiers"] if i["kind"] in ("phone", "domain")] if status == "confirmed" else []
    return {"campaign": campaign_id, "status": status, "block_requests": blocks, "simulated": True,
            "broadcast_id": broadcast_id}


def _describe(keys: list, lang: str) -> str:
    shown = [f"{TEXT['kind'][k][lang]} ⁦{v if k != 'phone' else '+' + v}⁩" for k, v in keys if k != "template"]
    return "، ".join(shown) if lang in ("ar", "ur") else ", ".join(shown)


def _broadcast_view(row, lang: str) -> dict:
    keys = [tuple(k) for k in json.loads(row["keys"])]
    category = t(CATEGORY_LABELS, row["category"], lang)
    if lang == "en":
        category = category.lower()
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "title": TEXT["broadcast_title"][lang].format(category=category),
        "body": TEXT["broadcast_body"][lang].format(authority=AUTHORITY_NAME[lang], ids=_describe(keys, lang) or "—"),
        "demo": TEXT["demo"][lang],
        "keys": keys,
    }


def broadcast_view(broadcast_id: int, lang: str = "ar") -> dict | None:
    with closing(_connect(_settings()["db"])) as con:
        row = con.execute("SELECT * FROM broadcasts WHERE id = ?", (broadcast_id,)).fetchone()
    return _broadcast_view(row, lang) if row else None


def broadcasts(lang: str = "ar") -> list[dict]:
    cfg = _settings()
    with closing(_connect(cfg["db"])) as con, con:
        rows = con.execute("SELECT * FROM broadcasts WHERE active = 1 ORDER BY created_at DESC LIMIT 5").fetchall()
    return [_broadcast_view(r, lang) for r in rows]


# --- What a person checking a message sees -----------------------------------

def annotate(result: dict, text: str, lang: str) -> dict:
    """Add radar information to a /api/check result. A confirmed campaign raises the risk."""
    keys = set(keys_of(text))
    info = {"people": 0, "status": None, "message": None, "broadcast": None}
    found = campaign_for(list(keys), lang) if keys else None
    if found and found["status"] != "dismissed":
        hours = _settings()["window"] // 3600
        info.update(people=found["people"], status=found["status"])
        if found["status"] in ("warning", "escalated", "confirmed"):
            info["message"] = TEXT["reported"][lang].format(n=found["people"], h=hours)
    for b in broadcasts(lang):
        if keys & set(b["keys"]):
            info["broadcast"] = {k: b[k] for k in ("title", "body", "demo")}
            result["risk"] = "high"
            result["risk_label"] = t(RISK_LABELS, "high", lang)
            result["summary"] = t(RISK_SUMMARY, "high", lang)
            result["score"] = max(result.get("score", 0), 90)
            result["reasons"] = [TEXT["confirmed_reason"][lang]] + result["reasons"]
            break
    result["radar"] = info
    return result
