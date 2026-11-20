"""WhatsApp channel: turns WhatsApp Cloud API webhooks into Haris replies.

Meta sends every incoming message to our webhook. We check its signature,
run the same engine as the web chat, and reply through the Graph API.
Only the standard library is used.

Privacy: message text is never logged or written to disk. When a risky
message is checked, its text is kept in memory for 30 minutes only, so the
"Report to protect others" button can send it to the campaign radar if the
user taps it. Nothing else about the conversation is kept.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from collections import OrderedDict, defaultdict, deque

from . import radar
from .detector import analyze
from .playbooks import contacts, get_playbook, list_playbooks
from .text import SUPPORTED_LANGS, detect_language, normalize
from .translations import section

log = logging.getLogger("haris.whatsapp")

GRAPH_URL = "https://graph.facebook.com"
DEFAULT_VERSION = "v26.0"
MAX_TEXT = 5000
BODY_LIMIT = 1024          # WhatsApp limit for the body of a message with buttons
REPORT_TTL = 30 * 60       # seconds a checked message can still be reported
PER_SENDER_LIMIT = 20      # messages per minute per WhatsApp user
RISK_ICON = {"high": "🔴", "medium": "🟠", "low": "⚪"}

TEXT = {lang: section(lang, "whatsapp") for lang in SUPPORTED_LANGS}

# Short greetings that open the welcome menu instead of a scam check.
GREETINGS = {
    "مرحبا", "مرحبا بك", "اهلا", "اهلا وسهلا", "هلا", "هاي", "السلام عليكم", "السلام عليكم ورحمه الله",
    "السلام عليكم ورحمه الله وبركاته", "صباح الخير", "مساء الخير", "القائمه", "ابدا", "سلام",
    "hi", "hello", "hey", "salam", "salaam", "start", "menu", "help",
    "السلام علیکم", "ہیلو", "سلام علیکم",
    "नमस्ते", "हेलो", "हाय",
}
_NAME = re.compile(r"\b(?:haris|حارس|हारिस)\b", re.IGNORECASE)
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def settings() -> dict:
    return {
        "token": os.getenv("WHATSAPP_TOKEN", ""),
        "phone_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
        "verify_token": os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
        "app_secret": os.getenv("WHATSAPP_APP_SECRET", ""),
        "version": os.getenv("WHATSAPP_API_VERSION", DEFAULT_VERSION),
    }


def enabled() -> bool:
    s = settings()
    return all(s[k] for k in ("token", "phone_id", "verify_token", "app_secret"))


# --- Webhook security -------------------------------------------------------

def verify_subscription(mode: str | None, token: str | None, challenge: str | None) -> str | None:
    """Answer Meta's set-up check: return the challenge only if our verify token matches."""
    expected = settings()["verify_token"]
    if mode == "subscribe" and expected and token and challenge and hmac.compare_digest(token, expected):
        return challenge
    return None


def valid_signature(body: bytes, header: str | None) -> bool:
    """Meta signs each webhook with the app secret (X-Hub-Signature-256). Unsigned calls are refused."""
    secret = settings()["app_secret"]
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


# --- Short-lived memory -----------------------------------------------------

class _Expiring:
    """A small dict whose entries disappear after `ttl` seconds."""

    def __init__(self, ttl: float, size: int):
        self.ttl, self.size, self.items = ttl, size, OrderedDict()

    def _trim(self) -> None:
        now = time.monotonic()
        while self.items and (len(self.items) > self.size or next(iter(self.items.values()))[0] < now):
            self.items.popitem(last=False)

    def put(self, key, value=True) -> None:
        self.items[key] = (time.monotonic() + self.ttl, value)
        self._trim()

    def pop(self, key):
        self._trim()
        entry = self.items.pop(key, None)
        return entry[1] if entry else None

    def __contains__(self, key) -> bool:
        self._trim()
        return key in self.items


_seen = _Expiring(ttl=24 * 3600, size=5000)       # message ids, because Meta retries deliveries
_pending = _Expiring(ttl=REPORT_TTL, size=2000)   # report token -> (text, lang)
_hits: dict[str, deque] = defaultdict(deque)


def _over_limit(sender: str) -> bool | None:
    """True when the sender just went over the limit, None when already over, False otherwise."""
    now = time.monotonic()
    window = _hits[sender]
    while window and now - window[0] > 60:
        window.popleft()
    window.append(now)
    if len(window) == PER_SENDER_LIMIT + 1:
        return True
    return None if len(window) > PER_SENDER_LIMIT else False


def reset() -> None:
    """Forget everything kept in memory (used by tests)."""
    _seen.items.clear()
    _pending.items.clear()
    _hits.clear()


# --- Incoming messages ------------------------------------------------------

def incoming(payload: dict) -> list[dict]:
    """Pull the user messages out of a webhook payload; status updates are ignored."""
    found = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for m in value.get("messages") or []:
                msg = {"id": m.get("id", ""), "from": m.get("from", ""), "type": m.get("type", ""),
                       "text": "", "reply_id": ""}
                if msg["type"] == "text":
                    msg["text"] = ((m.get("text") or {}).get("body") or "")[:MAX_TEXT]
                elif msg["type"] == "interactive":
                    inter = m.get("interactive") or {}
                    reply = inter.get("button_reply") or inter.get("list_reply") or {}
                    msg["reply_id"] = reply.get("id", "")
                elif msg["type"] == "button":
                    msg["reply_id"] = (m.get("button") or {}).get("payload", "")
                if msg["from"]:
                    found.append(msg)
    return found


def _clean(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", _NAME.sub(" ", normalize(text))).split())


_GREETINGS = {_clean(g) for g in GREETINGS}


def is_greeting(text: str) -> bool:
    cleaned = _clean(text)
    return cleaned == "" or cleaned in _GREETINGS


# --- Building replies -------------------------------------------------------

def _button(action: str, lang: str, arg: str = "") -> dict:
    rid = f"{action}:{lang}" + (f":{arg}" if arg else "")
    return {"type": "reply", "reply": {"id": rid, "title": TEXT[lang]["buttons"][action]}}


def _with_buttons(body: str, buttons: list[dict], lang: str) -> list[dict]:
    """One message with buttons; if the text is too long for that, the text first and the buttons after."""
    interactive = lambda text: {"type": "interactive", "interactive": {  # noqa: E731
        "type": "button", "body": {"text": text}, "footer": {"text": TEXT[lang]["footer"]},
        "action": {"buttons": buttons[:3]}}}
    if len(body) <= BODY_LIMIT:
        return [interactive(body)]
    return [{"type": "text", "text": {"body": body[:4096], "preview_url": False}}, interactive(TEXT[lang]["next"])]


def welcome(lang: str) -> list[dict]:
    t = TEXT[lang]
    return _with_buttons(t["welcome"], [_button("check", lang), _button("scammed", lang), _button("guide", lang)], lang)


def format_result(result: dict, lang: str, max_items: int = 3) -> str:
    t = TEXT[lang]
    risk = result["risk"]
    head = f"{RISK_ICON.get(risk, '')} *{result['risk_label']}*"
    if risk != "low" and result.get("category") not in (None, "unknown"):
        head += f" · {result['category_label']}"
    parts = [head, result["summary"]]
    info = result.get("radar") or {}
    if info.get("broadcast"):
        parts.append(f"📢 *{info['broadcast']['title']}*\n{info['broadcast']['body']}")
    elif info.get("message"):
        parts.append(f"👥 {info['message']}")
    if result.get("reasons"):
        parts.append(f"*{t['reasons_heading']}*\n" + "\n".join(f"• {r}" for r in result["reasons"][:max_items]))
    if result.get("advice"):
        parts.append(f"*{t['advice_heading']}*\n" + "\n".join(f"• {a}" for a in result["advice"][:max_items]))
    return "\n\n".join(parts)


def check(text: str, lang: str) -> list[dict]:
    result = radar.annotate(analyze(text, lang), text, lang)
    body = format_result(result, lang)
    for n in (2, 1):  # keep the reply in one message with buttons when we can
        if len(body) <= BODY_LIMIT:
            break
        body = format_result(result, lang, max_items=n)
    if result["risk"] in ("medium", "high"):
        token = secrets.token_urlsafe(9)
        _pending.put(token, (text, lang))
        buttons = [_button("report", lang, token), _button("scammed", lang), _button("again", lang)]
    else:
        buttons = [_button("again", lang), _button("scammed", lang), _button("guide", lang)]
    return _with_buttons(body, buttons, lang)


def scammed_menu(lang: str) -> list[dict]:
    t = TEXT[lang]
    rows = [{"id": f"pb:{lang}:{p['id']}", "title": t["playbooks"].get(p["id"], p["title"])[:24],
             "description": p["title"][:72]} for p in list_playbooks(lang)][:10]
    return [{"type": "interactive", "interactive": {
        "type": "list", "body": {"text": t["scammed_intro"]}, "footer": {"text": t["footer"]},
        "action": {"button": t["list_button"], "sections": [{"title": t["list_section"], "rows": rows}]}}}]


def playbook(playbook_id: str, lang: str) -> list[dict]:
    pb = get_playbook(playbook_id, lang)
    if not pb:
        return welcome(lang)
    t = TEXT[lang]
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(pb["steps"], 1))
    people = "\n".join(f"• {c['label']}: {c['value']}" for c in contacts(lang))
    body = f"*{pb['title']}*\n\n*{t['steps_heading']}*\n{steps}\n\n*{t['contacts_heading']}*\n{people}\n\n{t['report_app']}"
    return _with_buttons(body, [_button("check", lang), _button("guide", lang)], lang)


def report(token: str, sender: str, lang: str) -> list[dict]:
    t = TEXT[lang]
    kept = _pending.pop(token)
    if not kept:
        return _with_buttons(t["report_expired"], [_button("check", lang)], lang)
    text, msg_lang = kept
    found = radar.report(text, "wa-" + hashlib.sha256(sender.encode()).hexdigest()[:32], msg_lang)
    body = t["reported"]
    campaign = found.get("campaign") or {}
    if campaign.get("people", 0) > 1:
        hours = radar._settings()["window"] // 3600
        body += "\n\n👥 " + radar.TEXT["reported"][lang].format(n=campaign["people"], h=hours)
    return _with_buttons(body, [_button("again", lang), _button("guide", lang)], lang)


def handle(msg: dict) -> list[dict]:
    """Decide the reply to one incoming message. Returns the messages to send, without the recipient."""
    if msg["type"] == "text":
        text = msg["text"].strip()
        lang = detect_language(text) if text else "ar"
        if is_greeting(text):
            return welcome(lang)
        return check(text, lang)
    if msg["reply_id"]:
        action, _, rest = msg["reply_id"].partition(":")
        lang, _, arg = rest.partition(":")
        if lang not in SUPPORTED_LANGS:
            lang = "ar"
        if action == "check" or action == "again":
            return [{"type": "text", "text": {"body": TEXT[lang]["ask_check"]}}]
        if action == "scammed":
            return scammed_menu(lang)
        if action == "guide":
            return _with_buttons(TEXT[lang]["guide"], [_button("check", lang), _button("scammed", lang)], lang)
        if action == "pb":
            return playbook(arg, lang)
        if action == "report":
            return report(arg, msg["from"], lang)
        return welcome(lang)
    if msg["type"] in ("image", "audio", "video", "document", "sticker", "location", "contacts"):
        return _with_buttons(TEXT["ar"]["unsupported"] + "\n\n" + TEXT["en"]["unsupported"],
                             [_button("check", "ar"), _button("scammed", "ar")], "ar")
    return []


# --- Sending ----------------------------------------------------------------

def send(to: str, message: dict) -> bool:
    s = settings()
    url = f"{GRAPH_URL}/{s['version']}/{s['phone_id']}/messages"
    body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to, **message}
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {s['token']}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as err:
        detail = err.read(400).decode("utf-8", "replace")
        log.warning("WhatsApp send failed: HTTP %s %s", err.code, detail)
    except OSError as err:  # URLError and socket.timeout (not a TimeoutError on Python 3.9)
        log.warning("WhatsApp send failed: %s", err)
    return False


def process(payload: dict) -> int:
    """Handle every new message in a webhook payload. Returns how many messages were sent."""
    sent = 0
    for msg in incoming(payload):
        if msg["id"] and msg["id"] in _seen:
            continue
        if msg["id"]:
            _seen.put(msg["id"])
        over = _over_limit(msg["from"])
        if over is None:
            continue
        lang = detect_language(msg["text"]) if msg["text"] else "ar"
        replies = [{"type": "text", "text": {"body": TEXT[lang]["too_many"]}}] if over else handle(msg)
        for reply in replies:
            sent += send(msg["from"], reply)
    return sent
