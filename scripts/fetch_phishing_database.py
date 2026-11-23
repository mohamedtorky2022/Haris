"""Download a sample of live phishing links from Phishing.Database, for evaluate_sites.py.

    python3 scripts/fetch_phishing_database.py              # 60 links, one per domain, into phishing-today.txt
    python3 scripts/fetch_phishing_database.py --limit 100 --out my-list.txt

Phishing.Database (github.com/Phishing-Database/Phishing.Database, MIT licence, no account needed)
publishes the phishing links its automated tests still find active. The list is large, so a random
sample is taken, one link per domain so that a single campaign does not fill it. The sample changes
every day and is the same within a day, so a run can be repeated.

Many links on any phishing list are dead by the time they are tested; evaluate_sites.py counts those
apart. The list file is kept out of Git (.gitignore lists phishing*.txt) and the links are not
printed. Never open them in your own browser.

Then:
    python3 scripts/evaluate_sites.py phishing-today.txt --label phishing --server https://haris-uae.onrender.com
"""

from __future__ import annotations

import argparse
import random
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

SOURCE = "https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt"


def sample(lines: list[str], limit: int, seed: str) -> list[str]:
    """Up to `limit` http(s) links, one per host, picked at random with a fixed seed."""
    links = [ln.strip() for ln in lines if ln.strip().lower().startswith(("http://", "https://"))]
    rng = random.Random(seed)
    rng.shuffle(links)
    seen, picked = set(), []
    for link in links:
        host = (urlsplit(link).hostname or "").lower()
        if host and host not in seen:
            seen.add(host)
            picked.append(link)
            if len(picked) >= limit:
                break
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description="Download a sample of live phishing links from Phishing.Database.")
    ap.add_argument("--limit", type=int, default=60, help="how many links (default 60)")
    ap.add_argument("--out", default="phishing-today.txt", help="output file (default phishing-today.txt)")
    args = ap.parse_args()

    req = urllib.request.Request(SOURCE, headers={"User-Agent": "haris-hackathon-benchmark"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        print(f"GitHub answered HTTP {exc.code} for the Phishing.Database list.")
        return 1
    except OSError as exc:
        print(f"Could not reach GitHub: {type(exc).__name__}")
        return 1

    lines = text.splitlines()
    picked = sample(lines, args.limit, seed=date.today().isoformat())
    if not picked:
        print(f"The Phishing.Database active list is empty right now ({len(lines)} line). The project seems to "
              "have stopped updating; try scripts/fetch_phishstats.py, or a same-day list from the organisers.")
        return 1
    out = Path(args.out)
    out.write_text("# Phishing links from Phishing.Database (MIT licence), sampled "
                   f"{date.today().isoformat()}. Do not open them.\n" + "\n".join(picked) + "\n", encoding="utf-8")
    print(f"{len(lines)} links on the active list; wrote a sample of {len(picked)} (one per domain) to {out}.")
    print(f"Next: python3 scripts/evaluate_sites.py {out} --label phishing --server https://haris-uae.onrender.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
