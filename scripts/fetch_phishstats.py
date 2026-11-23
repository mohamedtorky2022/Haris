"""Download recent phishing sites from PhishStats, for evaluate_sites.py, keeping only fresh ones.

    python3 scripts/fetch_phishstats.py                 # up to 60 sites from the last 3 days
    python3 scripts/fetch_phishstats.py --days 7 --limit 100

PhishStats (phishstats.info) offers a free JSON API, 50 requests a day without an account (150 with a
free key in .env as PHISHSTATS_API_KEY), and its terms allow use "for lawful security research,
threat intelligence, and related purposes"; its raw data may not be redistributed, so the list file
is kept out of Git (.gitignore lists phishing*.txt) and the links are not printed.

Only entries reported in the last --days days are kept, because phishing sites die within days and an
old list would mostly test dead or re-used domains. If none are fresh, the script says so and writes
nothing. Uses one to three requests. Never open the links in your own browser.

Then:
    python3 scripts/evaluate_sites.py phishing-today.txt --label phishing --server https://haris-uae.onrender.com
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.phishstats.info/api/phishing?_where=(score,gt,5)&_sort=-date&_size=100&_p={page}"


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def parse_date(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def fresh(entries: list[dict], since: datetime, limit: int, seen: set[str]) -> list[str]:
    """Links reported after `since`, one per host, newest first."""
    rows = [(parse_date(e.get("date")), e.get("url") or "") for e in entries]
    rows = [(d, u) for d, u in rows if d and d >= since and u.lower().startswith(("http://", "https://"))]
    rows.sort(key=lambda r: r[0], reverse=True)
    picked = []
    for _, url in rows:
        host = (urlsplit(url).hostname or "").lower()
        if host and host not in seen:
            seen.add(host)
            picked.append(url)
            if len(picked) >= limit:
                break
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description="Download recent phishing sites from PhishStats.")
    ap.add_argument("--days", type=int, default=3, help="keep entries from the last N days (default 3)")
    ap.add_argument("--limit", type=int, default=60, help="how many links (default 60)")
    ap.add_argument("--out", default="phishing-today.txt", help="output file (default phishing-today.txt)")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="earlier list files whose domains must not appear again, for a fresh test set")
    args = ap.parse_args()
    load_env()

    headers = {"User-Agent": "haris-hackathon-benchmark", "Accept": "application/json"}
    if os.getenv("PHISHSTATS_API_KEY"):
        headers["X-API-Key"] = os.environ["PHISHSTATS_API_KEY"]
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    seen: set[str] = set()
    for path in args.exclude:  # a held-out list: no domain that was already measured, or tuned on
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip().lower().startswith(("http://", "https://")):
                seen.add((urlsplit(line.strip()).hostname or "").lower())
    excluded = len(seen)
    picked: list[str] = []
    newest_seen: datetime | None = None
    for page in range(1, 7):
        req = urllib.request.Request(API.format(page=page), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                entries = json.load(resp)
        except urllib.error.HTTPError as exc:
            print(f"PhishStats answered HTTP {exc.code}" + (" (daily limit reached; try tomorrow)." if exc.code == 429 else "."))
            break
        except (OSError, ValueError) as exc:
            print(f"Could not read PhishStats: {type(exc).__name__}")
            break
        if not isinstance(entries, list) or not entries:
            break
        dates = [d for d in (parse_date(e.get("date")) for e in entries) if d]
        if dates:
            newest_seen = max([newest_seen] + dates) if newest_seen else max(dates)
        picked += fresh(entries, since, args.limit - len(picked), seen)
        if len(picked) >= args.limit or (dates and min(dates) < since):
            break  # enough, or this page already reaches back past the window

    if not picked:
        when = f"the newest entry PhishStats returned is from {newest_seen:%Y-%m-%d}" if newest_seen else "it returned nothing"
        print(f"No phishing sites from the last {args.days} days: {when}. Nothing written. "
              "Use a same-day list from the organisers instead.")
        return 1
    out = Path(args.out)
    out.write_text(f"# Phishing sites reported to PhishStats since {since:%Y-%m-%d}. Do not open them.\n"
                   + "\n".join(picked) + "\n", encoding="utf-8")
    print(f"Wrote {len(picked)} phishing sites from the last {args.days} days (one per domain) to {out}"
          + (f", none of them among the {excluded} domains in {', '.join(args.exclude)}." if args.exclude else "."))
    print(f"Next: python3 scripts/evaluate_sites.py {out} --label phishing --server https://haris-uae.onrender.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
