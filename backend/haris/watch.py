"""Early warning: new domains that look like UAE brands, caught before anyone reports them.

Two sources, so one being down does not blind the watch:

* Certificate Transparency. A scam site needs a certificate before it can show the padlock, and every
  certificate is written to the public logs within minutes. Haris asks the logs (through crt.sh) for
  certificates issued in the last two weeks to names containing a protected brand.
* A DNS sweep of the look-alike names scammers use most: the brand with a bait word and a cheap ending
  (dewa-pay.com, uaepass-verify.top, tamm-fines.online). Names that resolve right now are kept.

Every name is first read by the offline link check, so only look-alikes of a protected brand stay. The
newest are then visited once with the safe website check (no AI, so the free quota is kept for people):
a name that only forwards to the brand's own site is dropped, a parked name stays quiet, and a live
page asking for card details or a password rises to the top of the authority's radar page, with a link
to the takedown evidence file. When someone later checks a message carrying one of these domains,
Haris says it was already on the watch list.

Nothing is blocked or reported on the watch's word alone: the list says "needs review", an officer decides.
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from . import radar, sitecheck, urls

# Brand names to watch, as they appear inside domain names. Short or common words (rta, icp, moi,
# dhl, noon, amazon) would bring thousands of unrelated certificates, so they are left out here;
# the link check still catches them in messages.
TERMS: dict[str, str] = {
    "uaepass": "UAE PASS",
    "tamm": "TAMM",
    "adcb": "ADCB",
    "emiratesnbd": "Emirates NBD",
    "bankfab": "FAB",
    "mashreq": "Mashreq",
    "dewa": "DEWA",
    "salik": "Salik",
    "etisalat": "e& (Etisalat)",
    "emiratespost": "Emirates Post",
    "aramex": "Aramex",
    "dubaipolice": "Dubai Police",
    "adpolice": "Abu Dhabi Police",
}

CRT_URL = "https://crt.sh/?q={q}&output=json&exclude=expired&deduplicate=Y"
DAY = 86400
_lock = threading.Lock()
_state = {"running": False, "last_run": None, "last_error": None}


def _settings() -> dict:
    return {
        "days": int(os.getenv("HARIS_WATCH_DAYS", "14")),        # how recent a certificate must be
        "every": int(os.getenv("HARIS_WATCH_HOURS", "6")) * 3600,
        "visit": int(os.getenv("HARIS_WATCH_VISITS", "30")),     # live checks per run
        "keep": int(os.getenv("HARIS_WATCH_KEEP_DAYS", "30")) * DAY,
    }


def _connect() -> sqlite3.Connection:
    con = radar._connect(radar._settings()["db"])
    con.execute("""CREATE TABLE IF NOT EXISTS watch (
        domain TEXT PRIMARY KEY, brand TEXT, source TEXT, issued_at REAL, found_at REAL, last_seen REAL,
        score INTEGER, flags TEXT, live TEXT)""")
    return con


def _parse_time(raw: str | None) -> float | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return time.mktime(time.strptime(raw[:26], fmt)) - time.timezone
        except ValueError:
            continue
    return None


def fetch_ct(term: str, timeout: int = 45) -> list[dict]:
    """Certificates from the public logs whose names contain the term."""
    url = CRT_URL.format(q=urllib.parse.quote(f"%{term}%"))
    req = urllib.request.Request(url, headers={"User-Agent": "Haris/1.0 (early warning; hackathon demo)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read(8_000_000) or b"[]")  # capped: the free host has 512 MB


def candidates(term: str, entries: list[dict], since: float) -> list[dict]:
    """New look-alike names for one brand, from crt.sh entries. Pure: no network."""
    found: dict[str, dict] = {}
    for e in entries:
        issued = _parse_time(e.get("not_before")) or _parse_time(e.get("entry_timestamp"))
        if issued is None or issued < since:
            continue
        for name in str(e.get("name_value", "")).lower().split("\n"):
            name = name.strip().lstrip("*.").rstrip(".")
            if not name or term not in name.replace("-", "").replace(".", "") or " " in name:
                continue
            report = urls.analyze_url(f"https://{name}")
            if report.official or "brand_lookalike" not in report.flags:
                continue
            # The brand's own sites in other countries (aramex.jo, emiratesnbd.com.sa) are not look-alikes.
            first = sitecheck.registrable(name).split(".")[0]
            if first == term and "risky_tld" not in report.flags:
                continue
            if name not in found or issued < found[name]["issued_at"]:
                found[name] = {"domain": name, "brand": TERMS.get(term, term), "source": "ct",
                               "issued_at": issued, "score": report.score, "flags": report.flags}
    return list(found.values())


# The look-alike names scammers register most: the brand with a bait word, on a cheap or generic ending.
BAIT = ("pay", "fines", "fine", "verify", "update", "login", "secure", "online", "portal", "services",
        "app", "uae", "ae", "gov")
ENDINGS = ("com", "net", "org", "info", "xyz", "top", "online", "site", "live", "app", "co", "me", "cc",
           "icu", "shop", "vip")


def permutations(term: str) -> set[str]:
    names = {f"{term}.{t}" for t in ENDINGS if t not in ("app", "co", "me")}
    for w in BAIT:
        for t in ENDINGS:
            names |= {f"{term}-{w}.{t}", f"{term}{w}.{t}", f"{w}-{term}.{t}", f"{w}{term}.{t}"}
    return {n for n in names if not urls.analyze_url(f"https://{n}").official}


def _resolves(name: str) -> bool:
    try:
        return bool(socket.getaddrinfo(name, 443, type=socket.SOCK_STREAM))
    except (OSError, UnicodeError):
        return False


def sweep_dns(terms: list[str], workers: int = 32) -> list[dict]:
    """Look-alike names that resolve right now."""
    names = sorted({(n, t) for t in terms for n in permutations(t)})
    with ThreadPoolExecutor(workers) as ex:
        live = [nt for nt, ok in zip(names, ex.map(lambda nt: _resolves(nt[0]), names)) if ok]
    out = []
    for name, term in live:
        report = urls.analyze_url(f"https://{name}")
        if "brand_lookalike" in report.flags:
            out.append({"domain": name, "brand": TERMS.get(term, term), "source": "dns", "issued_at": None,
                        "score": report.score, "flags": report.flags})
    return out


def save(items: list[dict]) -> int:
    """Keep new names and mark known ones as seen again; return how many were new."""
    now = time.time()
    new = 0
    with _connect() as con:
        for it in items:
            cur = con.execute(
                "INSERT OR IGNORE INTO watch (domain, brand, source, issued_at, found_at, last_seen, score, flags)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (it["domain"], it["brand"], it["source"], it["issued_at"], now, now, it["score"], json.dumps(it["flags"])))
            if cur.rowcount:
                new += 1
            else:
                con.execute("UPDATE watch SET last_seen = ?, issued_at = COALESCE(issued_at, ?) WHERE domain = ?",
                            (now, it["issued_at"], it["domain"]))
        con.execute("DELETE FROM watch WHERE last_seen < ?", (now - _settings()["keep"],))
    return new


def _visit(domain: str) -> dict:
    try:
        r = sitecheck.inspect(f"https://{domain}", "ar", use_llm=False)
        final = (r.get("final_domain") or domain).lower()
        return {"reachable": bool(r.get("reachable")), "score": r.get("score", 0), "title": r.get("title") or "",
                "uae": bool(r.get("uae")),
                "flags": r.get("flags", []), "age_days": r.get("domain_age_days"), "final_domain": final,
                "official": bool(final and (sitecheck._is_official(final) or sitecheck._global_official(final))),
                "checked_at": time.time()}
    except Exception as exc:  # a dead or hostile name must not stop the run
        return {"reachable": False, "score": 0, "error": type(exc).__name__, "checked_at": time.time()}


def visit_newest(limit: int, workers: int = 6) -> int:
    """Visit unvisited names once with the safe website check, without AI: certificate finds first."""
    with _connect() as con:
        rows = con.execute("SELECT domain FROM watch WHERE live IS NULL ORDER BY source = 'ct' DESC,"
                           " issued_at DESC, found_at DESC LIMIT ?", (limit,)).fetchall()
    domains = [r[0] for r in rows]
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(_visit, domains))
    with _connect() as con:
        for domain, live in zip(domains, results):
            con.execute("UPDATE watch SET live = ? WHERE domain = ?", (json.dumps(live), domain))
    return len(domains)


def run(terms: list[str] | None = None) -> dict:
    """One pass over both sources. Safe to call from a thread; a second call while running is skipped."""
    if not _lock.acquire(blocking=False):
        return {"skipped": True}
    _state.update(running=True, last_error=None)
    s = _settings()
    terms = terms or list(TERMS)
    since = time.time() - s["days"] * DAY
    new, errors, visited = 0, [], 0
    try:
        for term in terms:
            try:
                new += save(candidates(term, fetch_ct(term), since))
            except Exception as exc:  # crt.sh is often slow or down; the DNS sweep still runs
                errors.append(f"crt.sh {term}: {type(exc).__name__}")
        try:
            new += save(sweep_dns(terms))
        except Exception as exc:
            errors.append(f"dns: {type(exc).__name__}")
        visited = visit_newest(s["visit"])
    finally:
        _state.update(running=False, last_run=time.time(), last_error="; ".join(errors[:4]) or None)
        _lock.release()
    return {"new": new, "visited": visited, "errors": errors}


def start_background() -> None:
    """Run the watch a minute after start, then every few hours (on a hosted server only)."""
    if os.getenv("HARIS_WATCH", "1") == "0":
        return

    def loop() -> None:
        time.sleep(60)
        while True:
            try:
                run()
            except Exception:
                pass
            time.sleep(_settings()["every"])

    threading.Thread(target=loop, name="haris-watch", daemon=True).start()


def run_soon() -> bool:
    """Start a pass now in the background; False if one is already running."""
    if _state["running"]:
        return False
    threading.Thread(target=run, name="haris-watch-now", daemon=True).start()
    return True


def _row(r) -> dict:
    live = json.loads(r["live"]) if r["live"] else None
    registered = time.time() - live["age_days"] * DAY if live and live.get("age_days") is not None else None
    return {"domain": r["domain"], "brand": r["brand"], "source": r["source"], "issued_at": r["issued_at"],
            "registered_at": registered, "found_at": r["found_at"], "score": r["score"],
            "flags": json.loads(r["flags"] or "[]"), "live": live}


# What makes a live look-alike page urgent: it asks for details, or a threat list already has it.
ASKS = {"brand_with_form", "card_form", "otp_form", "password_form", "threat_list"}
NEW = {"new_domain", "new_certificate"}


def risky(item: dict) -> bool:
    """Urgent for an officer: live, and either asking for details or new and aimed at the UAE.

    A look-alike name alone is weak: "dewa" is also an everyday Indonesian word, "tamm" a surname.
    """
    live = item.get("live") or {}
    flags = set(live.get("flags") or [])
    return bool(live.get("reachable") and (flags & ASKS or (live.get("uae") and flags & NEW)))


def tier(item: dict) -> str:
    """urgent, review (worth an officer's look) or low."""
    if risky(item):
        return "urgent"
    live = item.get("live") or {}
    flags = set(live.get("flags") or [])
    if live.get("reachable") and ("new_domain" in flags or (live.get("uae") and "brand_on_page" in flags)):
        return "review"
    return "low"


def _rank(item: dict) -> tuple:
    live = item["live"] or {}
    newest = item["issued_at"] or item["registered_at"] or 0
    return (["urgent", "review", "low"].index(item["tier"]), not (live.get("reachable") and live.get("uae")),
            not live.get("reachable"), item["live"] is None, -(live.get("score") or 0), -newest)


def listing(limit: int = 60) -> dict:
    """Names to review, most dangerous first; names that only forward to the brand's own site are left out."""
    with _connect() as con:
        rows = [_row(r) for r in con.execute("SELECT * FROM watch").fetchall()]
    rows = [i for i in rows if not (i["live"] or {}).get("official")]
    for i in rows:
        i["tier"] = tier(i)
    rows.sort(key=_rank)
    counts = {"total": len(rows),
              "live": sum(1 for i in rows if (i["live"] or {}).get("reachable")),
              "risky": sum(1 for i in rows if i["tier"] == "urgent"),
              "review": sum(1 for i in rows if i["tier"] == "review"),
              "unvisited": sum(1 for i in rows if i["live"] is None),
              "new": sum(1 for i in rows if (i["issued_at"] or i["registered_at"] or 0) > time.time() - 30 * DAY)}
    return {"items": rows[:limit], **counts, "terms": list(TERMS.values()), **_state}


SPOTTED = {
    "ar": "رصده «حارس» مبكراً: نطاق يشبه {brand}، على قائمة المراقبة منذ {age}، قبل أن يبلّغ عنه أحد.",
    "en": "Haris spotted this early: a domain that looks like {brand}, on the watch list for {age}, before anyone reported it.",
    "ur": "«حارس» نے اسے پہلے ہی پکڑ لیا: {brand} جیسا ڈومین، {age} سے نگرانی کی فہرست میں، کسی کی رپورٹ سے پہلے۔",
    "hi": "Haris ने इसे पहले ही पकड़ लिया: {brand} जैसा डोमेन, {age} से निगरानी सूची में, किसी की रिपोर्ट से पहले।",
    "ru": "Haris заметил это заранее: домен, похожий на {brand}, в списке наблюдения уже {age}, ещё до жалоб.",
}
AGE = {"ar": ("{n} ساعة", "{n} يوم"), "en": ("{n} h", "{n} days"), "ur": ("{n} گھنٹے", "{n} دن"),
       "hi": ("{n} घंटे", "{n} दिन"), "ru": ("{n} ч", "{n} дн.")}


def annotate(result: dict, text: str, lang: str) -> dict:
    """If a link in the message is on the watch list, say so first among the reasons."""
    for link in urls.extract_urls(text):
        domain = urls.analyze_url(link).domain
        hit = spotted(domain) if domain else None
        if hit:
            hours = max(1, int((time.time() - hit["since"]) // 3600))
            short, long_ = AGE.get(lang, AGE["en"])
            age = short.format(n=hours) if hours < 48 else long_.format(n=hours // 24)
            result.setdefault("reasons", []).insert(0, SPOTTED.get(lang, SPOTTED["en"]).format(brand=hit["brand"], age=age))
            result.setdefault("radar", {})["spotted"] = {"domain": domain, **hit}
            break
    return result


def spotted(domain: str) -> dict | None:
    """The watch entry for a domain (or its registrable parent), if Haris spotted it early."""
    domain = domain.lower().strip(".")
    names = {domain, sitecheck.registrable(domain)}
    with _connect() as con:
        for name in names:
            row = con.execute("SELECT brand, issued_at, found_at, live FROM watch WHERE domain = ?", (name,)).fetchone()
            if row and not json.loads(row["live"] or "{}").get("official"):
                return {"brand": row["brand"], "since": min(t for t in (row["issued_at"], row["found_at"]) if t)}
    return None
