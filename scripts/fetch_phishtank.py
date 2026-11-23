"""Download today's verified, online phishing sites from PhishTank, for evaluate_sites.py.

    python3 scripts/fetch_phishtank.py                 # the 60 newest, into phishing-today.txt
    python3 scripts/fetch_phishtank.py --limit 100 --out my-list.txt

PhishTank (run by Cisco Talos) is free for commercial and non-commercial use. Its list holds only
phishing sites that people verified and that were online at the last check, updated hourly. It
needs a free account at https://phishtank.org/register.php: the key shown on its API page goes in
.env as PHISHTANK_APP_KEY, and your PhishTank user name as PHISHTANK_USER (it asks for a user agent
that names you). Without a key PhishTank allows only a few downloads a day.

The newest entries are taken, because phishing sites are usually taken down within a day. The list
file is kept out of Git (.gitignore lists phishing*.txt), and the addresses are not printed. Never
open them in your own browser.

Then:
    python3 scripts/evaluate_sites.py phishing-today.txt --label phishing --server https://haris-uae.onrender.com
"""

from __future__ import annotations

import argparse
import bz2
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def newest(entries: list[dict], limit: int) -> list[str]:
    """The newest verified, online entries, one per domain so a single campaign does not fill the list."""
    from urllib.parse import urlsplit

    entries = [e for e in entries if str(e.get("verified", "")).lower() in ("yes", "true")
               and str(e.get("online", "")).lower() in ("yes", "true") and e.get("url")]
    entries.sort(key=lambda e: e.get("submission_time") or "", reverse=True)
    seen, picked = set(), []
    for e in entries:
        host = (urlsplit(e["url"]).hostname or "").lower()
        if host and host not in seen:
            seen.add(host)
            picked.append(e["url"])
        if len(picked) >= limit:
            break
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description="Download today's verified phishing sites from PhishTank.")
    ap.add_argument("--limit", type=int, default=60, help="how many addresses (default 60)")
    ap.add_argument("--out", default="phishing-today.txt", help="output file (default phishing-today.txt)")
    args = ap.parse_args()
    load_env()

    key = os.getenv("PHISHTANK_APP_KEY", "").strip()
    user = os.getenv("PHISHTANK_USER", "").strip() or "haris-hackathon"
    url = (f"https://data.phishtank.com/data/{key}/online-valid.json.bz2" if key
           else "https://data.phishtank.com/data/online-valid.json.bz2")
    if not key:
        print("No PHISHTANK_APP_KEY in .env: trying without one (PhishTank allows only a few a day).")
    req = urllib.request.Request(url, headers={"User-Agent": f"phishtank/{user}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        print(f"PhishTank answered HTTP {exc.code}. "
              + ("Check PHISHTANK_APP_KEY in .env." if key else "Register for a free key and put it in .env."))
        return 1
    except OSError as exc:
        print(f"Could not reach PhishTank: {type(exc).__name__}")
        return 1

    entries = json.loads(bz2.decompress(raw) if raw[:3] == b"BZh" else raw)
    picked = newest(entries, args.limit)
    out = Path(args.out)
    out.write_text("# Verified, online phishing sites from PhishTank (phishtank.org). Do not open them.\n"
                   + "\n".join(picked) + "\n", encoding="utf-8")
    print(f"{len(entries)} verified sites online on PhishTank; wrote the {len(picked)} newest "
          f"(one per domain) to {out}.")
    print(f"Next: python3 scripts/evaluate_sites.py {out} --label phishing --server https://haris-uae.onrender.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
