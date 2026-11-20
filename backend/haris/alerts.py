"""Official warnings on WhatsApp: when the authority approves a campaign, every subscriber is told.

WhatsApp allows a business to message only people who agreed to hear from it, so nobody is
added without asking: a user sends «تنبيهات» (or presses the alerts button) to subscribe, and
«إيقاف» (STOP) to leave at any time. Their WhatsApp number is the one thing kept, because it is
needed to send; it is deleted as soon as they leave.

When a campaign is approved (radar.decide), `deliver` sends the warning in each subscriber's
language. Outside the 24-hour window after a user's last message, WhatsApp accepts only a
template approved by Meta: set WHATSAPP_ALERT_TEMPLATE to its name, with two body variables
(the title and the text). Without WhatsApp settings the delivery is simulated and only counted.

Demo subscribers (scripts/alerts_demo.py) have ids that are not phone numbers and are never sent
anything, even when WhatsApp is switched on.
"""

from __future__ import annotations

import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .text import SUPPORTED_LANGS, normalize
from .translations import section

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "alerts.db"
TEXT = {lang: section(lang, "whatsapp")["alerts"] for lang in SUPPORTED_LANGS}

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def _clean(text: str) -> str:
    # The same cleaning on both sides: it also drops Devanagari vowel signs, so a Hindi word still matches.
    return " ".join(normalize(_PUNCT.sub(" ", text or "")).split())


# Whole-message commands. Anything longer is checked as a message, so a scam that contains "stop" is still checked.
SUBSCRIBE = {_clean(w) for w in ("تنبيهات", "التنبيهات", "اشتراك", "اشترك", "alerts", "alert", "subscribe",
                                  "الرٹس", "الرٹ", "اطلاعات", "अलर्ट", "सब्सक्राइब")}
STOP = {_clean(w) for w in ("إيقاف", "ايقاف", "أوقف", "الغاء", "إلغاء الاشتراك", "stop", "unsubscribe",
                             "بند", "بند کریں", "रोकें", "बंद")}


def _settings() -> dict:
    return {"db": Path(os.getenv("HARIS_ALERTS_DB", str(DEFAULT_DB))),
            "template": os.getenv("WHATSAPP_ALERT_TEMPLATE", ""),
            "template_langs": os.getenv("WHATSAPP_ALERT_TEMPLATE_LANGS", "ar,en")}


def _connect() -> sqlite3.Connection:
    path = _settings()["db"]
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists()
    con = sqlite3.connect(path, timeout=5)
    if fresh:
        os.chmod(path, 0o600)  # WhatsApp numbers: readable by this server's user only
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS subscribers (wa_id TEXT PRIMARY KEY, lang TEXT, joined_at REAL, demo INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sends (id INTEGER PRIMARY KEY, broadcast_id INTEGER, created_at REAL, mode TEXT,
            title TEXT, total INTEGER, sent INTEGER DEFAULT 0, simulated INTEGER DEFAULT 0, failed INTEGER DEFAULT 0,
            done INTEGER DEFAULT 0);
        """
    )
    return con


def command(text: str) -> str | None:
    """'subscribe', 'stop', or None when the message is not one of the two commands."""
    cleaned = _clean(text)
    if cleaned in SUBSCRIBE:
        return "subscribe"
    if cleaned in STOP:
        return "stop"
    return None


def subscribe(wa_id: str, lang: str) -> bool:
    """Returns False if they were already subscribed (their language is updated)."""
    with closing(_connect()) as con, con:
        known = con.execute("SELECT 1 FROM subscribers WHERE wa_id = ?", (wa_id,)).fetchone()
        con.execute("INSERT INTO subscribers (wa_id, lang, joined_at) VALUES (?, ?, ?) "
                    "ON CONFLICT(wa_id) DO UPDATE SET lang = excluded.lang", (wa_id, lang, time.time()))
    return not known


def unsubscribe(wa_id: str) -> bool:
    with closing(_connect()) as con, con:
        return con.execute("DELETE FROM subscribers WHERE wa_id = ?", (wa_id,)).rowcount > 0


def is_subscribed(wa_id: str) -> bool:
    with closing(_connect()) as con:
        return con.execute("SELECT 1 FROM subscribers WHERE wa_id = ?", (wa_id,)).fetchone() is not None


def counts() -> dict:
    with closing(_connect()) as con:
        rows = con.execute("SELECT lang, demo, COUNT(*) AS n FROM subscribers GROUP BY lang, demo").fetchall()
    by_lang = {lang: 0 for lang in SUPPORTED_LANGS}
    real = demo = 0
    for r in rows:
        by_lang[r["lang"]] = by_lang.get(r["lang"], 0) + r["n"]
        if r["demo"]:
            demo += r["n"]
        else:
            real += r["n"]
    return {"total": real + demo, "real": real, "demo": demo, "by_lang": by_lang}


def message_text(view: dict, lang: str) -> str:
    t = TEXT[lang]
    return f"🚨 *{view['title']}*\n\n{view['body']}\n\n{t['stop_line']}\n_{view['demo']}_"


def _live() -> bool:
    from . import whatsapp
    return whatsapp.enabled()


def mode() -> str:
    """How a delivery would go now: 'template' or 'text' on WhatsApp, or 'simulated'."""
    if not _live():
        return "simulated"
    return "template" if _settings()["template"] else "text"


def _template_message(view: dict, lang: str) -> dict:
    cfg = _settings()
    langs = [x.strip() for x in cfg["template_langs"].split(",") if x.strip()]
    code = lang if lang in langs else (langs[0] if langs else "en")
    params = [{"type": "text", "text": view["title"][:1000]}, {"type": "text", "text": view["body"][:1000]}]
    return {"type": "template", "template": {"name": cfg["template"], "language": {"code": code},
                                             "components": [{"type": "body", "parameters": params}]}}


def deliver(broadcast_id: int, pace: float = 0.05) -> dict:
    """Send one approved warning to every subscriber. Runs in the background after the approval."""
    from . import radar, whatsapp

    views = {lang: radar.broadcast_view(broadcast_id, lang) for lang in SUPPORTED_LANGS}
    if not views["ar"]:
        return {}
    how = mode()
    with closing(_connect()) as con, con:
        subs = con.execute("SELECT wa_id, lang, demo FROM subscribers").fetchall()
        send_id = con.execute("INSERT INTO sends (broadcast_id, created_at, mode, title, total) VALUES (?, ?, ?, ?, ?)",
                              (broadcast_id, time.time(), how, views["ar"]["title"], len(subs))).lastrowid
    sent = simulated = failed = 0
    for i, sub in enumerate(subs):
        lang = sub["lang"] if sub["lang"] in SUPPORTED_LANGS else "ar"
        if sub["demo"] or how == "simulated":
            simulated += 1
        else:
            message = (_template_message(views[lang], lang) if how == "template"
                       else {"type": "text", "text": {"body": message_text(views[lang], lang), "preview_url": False}})
            if whatsapp.send(sub["wa_id"], message):
                sent += 1
            else:
                failed += 1
            time.sleep(pace)  # stay well under WhatsApp's throughput limits
        if i % 200 == 199:
            _progress(send_id, sent, simulated, failed)
    _progress(send_id, sent, simulated, failed, done=True)
    return {"id": send_id, "total": len(subs), "sent": sent, "simulated": simulated, "failed": failed, "mode": how}


def _progress(send_id: int, sent: int, simulated: int, failed: int, done: bool = False) -> None:
    with closing(_connect()) as con, con:
        con.execute("UPDATE sends SET sent = ?, simulated = ?, failed = ?, done = ? WHERE id = ?",
                    (sent, simulated, failed, int(done), send_id))


def history(limit: int = 10) -> list[dict]:
    with closing(_connect()) as con:
        rows = con.execute("SELECT * FROM sends ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def add_demo_subscribers(n: int, langs: dict | None = None) -> int:
    """Fictional subscribers for a demo. Their ids are not phone numbers, so nothing is ever sent to them."""
    share = langs or {"ar": 0.45, "en": 0.25, "hi": 0.17, "ur": 0.13}
    now = time.time()
    rows, k = [], 0
    sizes = {lang: int(n * part) for lang, part in share.items()}
    sizes[next(iter(sizes))] += n - sum(sizes.values())  # the rounding left-over goes to the first language
    for lang, size in sizes.items():
        for _ in range(size):
            rows.append((f"demo-{k:06d}", lang, now - k * 37, 1))
            k += 1
    with closing(_connect()) as con, con:
        con.execute("DELETE FROM subscribers WHERE demo = 1")
        con.executemany("INSERT OR REPLACE INTO subscribers VALUES (?, ?, ?, ?)", rows)
    return len(rows)
