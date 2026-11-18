"""Haris HTTP API (FastAPI) and the web chat front end.

Run from the backend folder:  uvicorn app.main:app --reload
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Annotated, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from haris import __version__, llm
from haris.detector import analyze
from haris.intake import MAX_IMAGES, extract
from haris.playbooks import get_playbook, list_playbooks
from haris.polish import polish
from haris.report import build_report
from haris.text import pick_language

Lang = Literal["ar", "en", "ur"]
Incident = Literal["money_sent", "account_hacked", "extortion", "identity_shared", "suspicious_only"]
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
    return response


# --- Routes ---------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "ai_enabled": llm.enabled()}


@app.post("/api/check")
def check(body: CheckRequest):
    return analyze(body.text, body.lang)


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


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
