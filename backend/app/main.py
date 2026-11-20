"""Haris HTTP API (FastAPI) and the web chat front end.

Run from the backend folder:  uvicorn app.main:app --reload
"""

from __future__ import annotations

import hmac
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, List, Literal, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from haris import __version__, alerts, inbox, llm, radar, whatsapp
from haris.detector import analyze
from haris.intake import MAX_IMAGES, extract
from haris.playbooks import get_playbook, list_playbooks
from haris.polish import polish
from haris.report import build_report
from haris.text import pick_language

Lang = Literal["ar", "en", "ur", "hi"]
Incident = Literal["money_sent", "account_hacked", "extortion", "harassment", "impersonation", "privacy_violation",
                   "device_hacked", "identity_shared", "business_fraud", "suspicious_only"]
ImageDataUrl = Annotated[str, Field(max_length=6_000_000)]  # a 4 MB image as a base64 data: URL
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
RATE_LIMIT = int(os.getenv("HARIS_RATE_LIMIT", "30"))  # requests per minute per client
MAX_TEXT = 5000

app = FastAPI(
    title="Haris API",
    version=__version__,
    description="Scam checking, victim guidance and incident reports. Nothing users send is stored.",
)


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT, description="The message, link or offer to check")
    lang: Optional[Lang] = Field(None, description="Reply language; detected from the text when omitted")


class ExtractRequest(BaseModel):
    lang: Optional[Lang] = None
    text: str = Field("", max_length=MAX_TEXT, description="The victim's story, typed or dictated")
    images: List[ImageDataUrl] = Field(default_factory=list, max_length=MAX_IMAGES, description="Screenshots as data: URLs")
    incident_type: Optional[Incident] = None


class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT, description="Dictated text to fix")
    lang: Lang = "ar"
    dialect: Optional[str] = Field(None, pattern=r"^[a-z]{2}-[A-Z]{2}$", description="Dictation locale, e.g. ar-EG")


class RadarReport(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT, description="The suspicious message")
    lang: Lang = "ar"
    reporter_id: str = Field(..., min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$",
                             description="A random id the browser made; stored only as a keyed hash")


class Decision(BaseModel):
    status: Literal["confirmed", "dismissed"]


Emirate = Literal["abu_dhabi", "dubai", "sharjah", "ajman", "umm_al_quwain", "ras_al_khaimah", "fujairah"]


class ReportRequest(BaseModel):
    lang: Lang = "ar"
    incident_type: Incident = "suspicious_only"
    occurred_at: Optional[str] = Field(None, max_length=100)
    description: str = Field("", max_length=MAX_TEXT)
    amount: Optional[str] = Field(None, max_length=40)
    currency: Optional[str] = Field("AED", max_length=10)
    payment_method: Optional[str] = Field(None, max_length=200)
    scammer_identifiers: list[str] = Field(default_factory=list, max_length=30)
    evidence: list[str] = Field(default_factory=list, max_length=30)
    steps_taken: list[str] = Field(default_factory=list, max_length=30)
    reporter_name: Optional[str] = Field(None, max_length=120)
    reporter_contact: Optional[str] = Field(None, max_length=120)


# --- Middleware -----------------------------------------------------------

_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def protect(request: Request, call_next):
    if request.url.path.startswith("/api/") and RATE_LIMIT > 0:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _hits[client]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= RATE_LIMIT:
            return JSONResponse({"detail": "Too many requests. Please wait a minute."}, status_code=429)
        window.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    else:  # pages and scripts: the browser checks for a newer copy each time, so an update is never half-loaded
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


# --- Routes ---------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "ai_enabled": llm.enabled(), "ai_provider": llm.provider(), "ai_model": llm.model_name(), "whatsapp_enabled": whatsapp.enabled(), "inbox_retention_days": inbox.retention_days()}


@app.post("/api/check")
def check(body: CheckRequest):
    result = analyze(body.text, body.lang)
    return radar.annotate(result, body.text, result["language"])


# --- Campaign radar ---------------------------------------------------------

@app.post("/api/radar/report")
def radar_report(body: RadarReport):
    """Report a suspicious message. Only the sender's details and the redacted text are kept."""
    return radar.report(body.text, body.reporter_id, body.lang)


@app.get("/api/radar/broadcasts")
def radar_broadcasts(lang: Lang = "ar"):
    """Official warnings the authority approved. Shown to every Haris user."""
    return radar.broadcasts(lang)


def require_authority(request: Request) -> None:
    """With HARIS_AUTHORITY_TOKEN set, the dashboard needs that token; without it, only this computer."""
    token = os.getenv("HARIS_AUTHORITY_TOKEN")
    if token:
        given = request.headers.get("x-authority-token", "")
        if not hmac.compare_digest(given.encode(), token.encode()):
            raise HTTPException(status_code=401, detail="Authority token required")
    # "testclient" is the address FastAPI's test client reports; a real network peer can't have it.
    elif not request.client or request.client.host not in ("127.0.0.1", "::1", "localhost", "testclient"):
        raise HTTPException(status_code=403, detail="Set HARIS_AUTHORITY_TOKEN to open the dashboard remotely")
    # A tunnel or reverse proxy (Cloudflare, ngrok, a load balancer) also connects from this computer,
    # but the visitor is elsewhere: it adds these headers, so the token is required then too.
    elif any(h in request.headers for h in ("x-forwarded-for", "cf-connecting-ip", "forwarded", "x-real-ip")):
        raise HTTPException(status_code=403, detail="Set HARIS_AUTHORITY_TOKEN to open the dashboard through a tunnel")


@app.get("/api/authority/campaigns")
def authority_campaigns(request: Request):
    require_authority(request)
    return radar.campaigns("ar")


@app.post("/api/authority/campaigns/{campaign_id}")
def authority_decide(campaign_id: str, body: Decision, request: Request, background: BackgroundTasks):
    require_authority(request)
    result = radar.decide(campaign_id, body.status)
    if not result:
        raise HTTPException(status_code=404, detail="Unknown campaign")
    if result.get("broadcast_id"):
        # The official warning goes to every WhatsApp subscriber, after this answer is sent.
        background.add_task(alerts.deliver, result["broadcast_id"])
        result["whatsapp_alert"] = {**alerts.counts(), "mode": alerts.mode()}
    return result


@app.get("/api/authority/alerts")
def authority_alerts(request: Request):
    """WhatsApp alert subscribers and the last deliveries, for the radar dashboard."""
    require_authority(request)
    return {"subscribers": alerts.counts(), "mode": alerts.mode(), "sends": alerts.history()}


@app.get("/api/playbooks")
def playbooks(lang: Optional[Lang] = None):
    return list_playbooks(pick_language(lang))


@app.get("/api/playbooks/{playbook_id}")
def playbook(playbook_id: str, lang: Optional[Lang] = None):
    result = get_playbook(playbook_id, pick_language(lang))
    if not result:
        raise HTTPException(status_code=404, detail="Unknown playbook")
    return result


@app.post("/api/extract")
def extract_fields(body: ExtractRequest):
    """Pull report fields out of a story and screenshots. Nothing is stored."""
    return extract(body.text, body.images, body.lang, body.incident_type)


@app.post("/api/polish")
def polish_text(body: PolishRequest):
    """Fix misheard words in dictated text. Numbers are never changed; nothing is stored."""
    return polish(body.text, body.lang, body.dialect)


@app.post("/api/report")
def report(body: ReportRequest):
    return build_report(body.model_dump(), body.lang)


# --- Report inbox (demo): the victim sends a report to the authority --------

class SubmitRequest(ReportRequest):
    emirate: Emirate
    consent: bool = False
    identity_confirmed: bool = False  # demo stand-in for UAE PASS
    reference: str = Field("", max_length=24)  # the number on the victim's report file


class ReplyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class CaseAction(BaseModel):
    action: Literal["receive", "request_info", "close"]
    note: str = Field("", max_length=1000)


@app.post("/api/reports")
def submit_report(body: SubmitRequest):
    """Kept only because the victim pressed send after seeing the whole report; deleted after the retention period."""
    if not body.consent:
        raise HTTPException(400, "The victim must agree before the report is sent")
    data = body.model_dump(exclude={"emirate", "consent", "identity_confirmed", "reference"})
    return inbox.submit(data, body.lang, body.emirate, body.identity_confirmed, body.reference)


def _report_token(request: Request) -> str:
    return request.headers.get("x-report-token", "")


@app.get("/api/reports/{ref}")
def report_status(ref: str, request: Request):
    found = inbox.status(ref, _report_token(request))
    if not found:
        raise HTTPException(404, "Report not found")
    return found


@app.post("/api/reports/{ref}/reply")
def report_reply(ref: str, body: ReplyRequest, request: Request):
    try:
        found = inbox.reply(ref, _report_token(request), body.text)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    if not found:
        raise HTTPException(404, "Report not found or closed")
    return found


@app.get("/api/authority/reports")
def authority_reports(request: Request):
    require_authority(request)
    return inbox.queue()


@app.get("/api/authority/reports/{ref}")
def authority_report(ref: str, request: Request):
    require_authority(request)
    found = inbox.detail(ref)
    if not found:
        raise HTTPException(404, "Report not found")
    return found


@app.post("/api/authority/reports/{ref}")
def authority_report_action(ref: str, body: CaseAction, request: Request):
    require_authority(request)
    try:
        found = inbox.act(ref, body.action, body.note)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    if not found:
        raise HTTPException(404, "Report not found or closed")
    return found



# --- WhatsApp channel (Cloud API webhook) ------------------------------------

@app.get("/webhook/whatsapp")
def whatsapp_verify(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Meta calls this once when the webhook is set up, to check our verify token."""
    answer = whatsapp.verify_subscription(mode, token, challenge)
    if answer is None:
        raise HTTPException(403, "Verification failed")
    return PlainTextResponse(answer)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background: BackgroundTasks):
    """Incoming WhatsApp messages. Signed by Meta; we answer at once and reply in the background."""
    body = await request.body()
    if len(body) > 1_000_000:
        raise HTTPException(413, "Payload too large")
    if not whatsapp.valid_signature(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(401, "Invalid signature")
    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(400, "Invalid JSON") from None
    if whatsapp.enabled() and isinstance(payload, dict):
        background.add_task(whatsapp.process, payload)
    return {"received": True}

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
