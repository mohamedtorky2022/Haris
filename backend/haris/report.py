"""Build a structured incident report the victim can hand to the police.

Nothing is stored: the report is built in memory and returned to the browser,
which offers it for download. The report deliberately keeps the scammer's
numbers and links, because the police need them.
"""

from __future__ import annotations

import html
import secrets
from datetime import datetime, timezone

from .playbooks import PLAYBOOKS, contacts
from .redact import find_identifiers
from .text import normalize_digits
from .translations import table
from .urls import extract_urls

LABELS = table("report")

MAX_FIELD = 4000


def _clean(value, limit: int = MAX_FIELD) -> str:
    return normalize_digits(str(value or "")).strip()[:limit]


def _clean_list(values) -> list[str]:
    return [_clean(v, 300) for v in (values or []) if _clean(v, 300)][:30]


def build_report(data: dict, lang: str) -> dict:
    L = {k: v[lang] for k, v in LABELS.items()}
    now = datetime.now(timezone.utc)
    reference = f"HRS-{now:%Y%m%d}-{secrets.token_hex(3).upper()}"

    incident = data.get("incident_type", "suspicious_only")
    incident_title = PLAYBOOKS.get(incident, PLAYBOOKS["suspicious_only"])["title"][lang]
    description = _clean(data.get("description"))
    identifiers = _clean_list(data.get("scammer_identifiers"))

    found = find_identifiers(description)
    auto = sorted({*found.get("phones", []), *found.get("emails", []), *found.get("ibans", []), *extract_urls(description)})
    auto = [item for item in auto if item not in identifiers]

    amount = _clean(data.get("amount"), 40)
    currency = _clean(data.get("currency") or "AED", 10)
    money = f"{amount} {currency}" if amount else L["none"]

    sections: list[tuple[str, list[str] | str]] = [
        (L["type"], incident_title),
        (L["occurred"], _clean(data.get("occurred_at"), 100) or L["none"]),
        (L["description"], description or L["none"]),
        (L["money"], money),
        (L["payment_method"], _clean(data.get("payment_method"), 200) or L["none"]),
        (L["identifiers"], identifiers + [f"{item} ({L['found_in_text']})" for item in auto] or [L["none"]]),
        (L["evidence"], _clean_list(data.get("evidence")) or [L["none"]]),
        (L["steps_taken"], _clean_list(data.get("steps_taken")) or [L["none"]]),
    ]
    reporter = " · ".join(x for x in (_clean(data.get("reporter_name"), 120), _clean(data.get("reporter_contact"), 120)) if x)
    if reporter:
        sections.append((L["reporter"], reporter))
    sections.append((L["where"], [f"{c['label']}: {c['value']}" for c in contacts(lang)]))

    header = [(L["reference"], reference), (L["generated"], now.strftime("%Y-%m-%d %H:%M UTC"))]
    return {
        "reference": reference,
        "markdown": _markdown(L, header, sections),
        "html": _html(L, header, sections, lang),
        "identifiers_found": auto,
    }


def _markdown(L, header, sections) -> str:
    out = [f"# {L['title']}", ""]
    out += [f"**{k}:** {v}  " for k, v in header]
    for heading, body in sections:
        out += ["", f"## {heading}", ""]
        out += [f"- {item}" for item in body] if isinstance(body, list) else [body]
    out += ["", "---", f"_{L['disclaimer']}_", ""]
    return "\n".join(out)


def _html(L, header, sections, lang) -> str:
    e = html.escape
    direction = "rtl" if lang in ("ar", "ur") else "ltr"
    parts = [
        f'<!DOCTYPE html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8">',
        f"<title>{e(L['title'])}</title>",
        "<style>body{font-family:system-ui,'Segoe UI',Tahoma,sans-serif;max-width:760px;margin:32px auto;"
        "padding:0 20px;color:#1f2937;line-height:1.6}h1{color:#075e54;margin-bottom:4px}"
        "h2{font-size:1.05rem;margin:24px 0 6px;color:#075e54;border-bottom:1px solid #e5e7eb;padding-bottom:4px}"
        ".meta{color:#4b5563}footer{margin-top:32px;font-size:.85rem;color:#6b7280}"
        ".evidence img{max-width:100%;border:1px solid #e5e7eb;border-radius:8px;margin:8px 0;display:block}"
        "@media print{body{margin:0}}</style></head><body>",
        f"<h1>{e(L['title'])}</h1>",
    ]
    parts += [f'<div class="meta"><strong>{e(k)}:</strong> {e(v)}</div>' for k, v in header]
    for heading, body in sections:
        parts.append(f"<h2>{e(heading)}</h2>")
        if isinstance(body, list):
            parts.append("<ul>" + "".join(f"<li>{e(item)}</li>" for item in body) + "</ul>")
        else:
            parts.append("<p>" + e(body).replace("\n", "<br>") + "</p>")
    parts.append(f"<footer>{e(L['disclaimer'])}</footer></body></html>")
    return "".join(parts)
