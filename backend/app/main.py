"""Haseen HTTP API (FastAPI) and the web chat front end.

Run from the backend folder:  uvicorn app.main:app --reload
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from haseen import __version__, llm
from haseen.detector import analyze
from haseen.playbooks import get_playbook, list_playbooks
from haseen.report import build_report
from haseen.text import pick_language

Lang = Literal["ar", "en", "ur"]
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
RATE_LIMIT = int(os.getenv("HASEEN_RATE_LIMIT", "30"))  # requests per minute per client
MAX_TEXT = 5000

app = FastAPI(
    title="Haseen API",
    version=__version__,
    description="Scam checking, victim guidance and incident reports. Nothing users send is stored.",
)


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT, description="The message, link or offer to check")
    lang: Lang | None = Field(None, description="Reply language; detected from the text when omitted")


class ReportRequest(BaseModel):
    lang: Lang = "ar"
    incident_type: Literal["money_sent", "account_hacked", "extortion", "identity_shared", "suspicious_only"] = "suspicious_only"
    occurred_at: str | None = Field(None, max_length=100)
    description: str = Field("", max_length=MAX_TEXT)
    amount: str | None = Field(None, max_length=40)
    currency: str | None = Field("AED", max_length=10)
    payment_method: str | None = Field(None, max_length=200)
    scammer_identifiers: list[str] = Field(default_factory=list, max_length=30)
    evidence: list[str] = Field(default_factory=list, max_length=30)
    steps_taken: list[str] = Field(default_factory=list, max_length=30)
    reporter_name: str | None = Field(None, max_length=120)
    reporter_contact: str | None = Field(None, max_length=120)


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
def playbooks(lang: Lang | None = None):
    return list_playbooks(pick_language(lang))


@app.get("/api/playbooks/{playbook_id}")
def playbook(playbook_id: str, lang: Lang | None = None):
    result = get_playbook(playbook_id, pick_language(lang))
    if not result:
        raise HTTPException(status_code=404, detail="Unknown playbook")
    return result


@app.post("/api/report")
def report(body: ReportRequest):
    return build_report(body.model_dump(), body.lang)


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
