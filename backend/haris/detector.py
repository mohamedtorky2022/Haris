"""Scam detection: rules + link analysis, with an optional AI second opinion."""

from __future__ import annotations

from . import llm, sitecheck
from .i18n import ADVICE, CATEGORY_LABELS, REASONS, RISK_LABELS, RISK_SUMMARY, SITE_FLAGS, URL_FLAGS, t
from .redact import redact
from .rules import COMBOS, SMALL_AMOUNT, SMALL_AMOUNT_WEIGHT, match_signals
from .text import normalize, pick_language
from .urls import analyze_url, extract_urls

HIGH_THRESHOLD = 55
MEDIUM_THRESHOLD = 25
MAX_LINK_POINTS = 50
MAX_SITE_POINTS = 60
MAX_SITES = 2  # sites visited per message, to keep the reply quick
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
LLM_SCORE = {"low": 15, "medium": 45, "high": 80}

# Signals that become more dangerous when the message also carries a non-official link.
_LINK_SENSITIVE = {"payment_request", "card_details", "otp_request", "personal_info_request"}
_IMPERSONATION = {"bank_mention", "gov_impersonation", "delivery", "account_suspended"}


def risk_level(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def analyze(text: str, lang: str | None = None, use_llm: bool = True, inspect_sites: bool = True) -> dict:
    lang = pick_language(lang, text)
    normalized = normalize(text)

    signals = match_signals(normalized)
    codes = [s.code for s in signals]
    score = sum(s.weight for s in signals)

    if SMALL_AMOUNT.search(normalized):
        codes.append("small_amount")
        score += SMALL_AMOUNT_WEIGHT

    for combo, bonus in COMBOS:
        if all(c in codes for c in combo):
            score += bonus

    links = [analyze_url(u) for u in extract_urls(text)]
    risky_links = [link for link in links if not link.official and link.score > 0]
    if risky_links:
        score += min(MAX_LINK_POINTS, sum(link.score for link in risky_links))
        codes.append("suspicious_link")
        if _LINK_SENSITIVE & set(codes):
            score += 15
        if _IMPERSONATION & set(codes):
            score += 10
    elif links and all(link.official for link in links) and not {"otp_request", "card_details"} & set(codes):
        codes.append("official_link")
        score = max(0, score - 15)

    # Visit the sites themselves: a brand-new phishing domain can look clean in the link alone.
    sites: dict[str, dict] = {}
    if inspect_sites and sitecheck.enabled():
        for link in [link for link in links if not link.official][:MAX_SITES]:
            sites[link.url] = sitecheck.inspect(link.url, lang, use_llm)
    site_points = max((s["score"] for s in sites.values()), default=0)
    if site_points >= 20:
        score += min(MAX_SITE_POINTS, site_points)
        codes.append("risky_website")

    score = min(100, score)
    risk = risk_level(score)

    category = "unknown"
    categorized = sorted((s for s in signals if s.category), key=lambda s: s.weight, reverse=True)
    if categorized:
        category = categorized[0].category
    elif any("brand_lookalike" in link.flags for link in risky_links):
        category = "phishing_link"
    elif "risky_website" in codes:
        category = "phishing_link"
    if any((s.get("ai") or {}).get("risk") == "high" for s in sites.values()) and risk != "high":
        risk, score = "high", max(score, HIGH_THRESHOLD)  # the AI read the page itself and calls it a scam
    if risk == "low":
        category = "unknown"  # don't label a message with a scam type we are not warning about

    redaction = redact(text)
    engine = "rules"
    reasons = [t(REASONS, c, lang) for c in codes]
    for site in sites.values():
        reasons += [r for r in (site.get("ai") or {}).get("reasons", []) if r not in reasons]
    advice = list(ADVICE.get(category, {}).get(lang, [])) + list(t(ADVICE, "general", lang))

    if use_llm and llm.enabled():
        opinion = llm.assess(redaction.text, codes, [link.safe_for_model() for link in links], lang)
        if opinion:
            engine = "rules+ai"
            # Conservative merge: the more cautious of the two verdicts wins.
            if RISK_ORDER[opinion["risk"]] > RISK_ORDER[risk]:
                risk = opinion["risk"]
                score = max(score, LLM_SCORE[risk])
            if category == "unknown" and risk != "low":
                category = opinion["category"]  # a scam type is named only when we warn
            reasons += [r for r in opinion["reasons"] if r not in reasons]
            advice = opinion["advice"] + [a for a in advice if a not in opinion["advice"]]

    return {
        "risk": risk,
        "risk_label": t(RISK_LABELS, risk, lang),
        "summary": t(RISK_SUMMARY, risk, lang),
        "score": score,
        "category": category,
        "category_label": t(CATEGORY_LABELS, category, lang),
        "reasons": reasons,
        "advice": advice[:5],
        "links": [
            {
                "url": link.url,
                "domain": link.domain,
                "official": link.official,
                "flags": link.flags,
                "flag_labels": [t(URL_FLAGS, f, lang) for f in link.flags],
                "site": _site_view(sites[link.url], lang) if link.url in sites else None,
            }
            for link in links
        ],
        "signals": codes,
        "redacted": redaction.counts,
        "engine": engine,
        "language": lang,
    }


def _site_view(site: dict, lang: str) -> dict:
    """What the live visit found, with each finding in the reader's language."""
    view = {k: site[k] for k in ("final_domain", "reachable", "status", "redirects", "title", "domain_age_days",
                                 "cert_age_days", "flags", "score", "ai", "error")}
    view["flag_labels"] = [t(SITE_FLAGS, f, lang) for f in site["flags"]]
    if not site["reachable"]:
        view["flag_labels"].append(t(SITE_FLAGS, "unreachable", lang))
    return view
