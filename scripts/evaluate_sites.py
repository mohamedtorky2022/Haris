"""Measure the live website check on real addresses, and write the result for the slides.

Run it against the deployed server, so the visits come from the server and not from your computer:

    python3 scripts/evaluate_sites.py phishing.txt --label phishing --server https://haris-uae.onrender.com
    python3 scripts/evaluate_sites.py data/samples/sites.json --server https://haris-uae.onrender.com
    python3 scripts/evaluate_sites.py phishing.txt legit.txt --label phishing,legitimate --server https://...

Or locally, visiting from this machine (needs the backend's code, nothing to install):

    python3 scripts/evaluate_sites.py data/samples/sites.json

Inputs: a .txt file with one address per line (lines starting with # are skipped), labelled with
--label; a .csv with two columns (address, then phishing or legitimate; a header line is fine); or a
.json list of {"url", "label": "phishing"|"legitimate", "note"}. --limit N takes the first N
addresses of each file. Only the Python standard library is used.

--offline judges each address from the link alone, as Haris does inside a message, without visiting
it: instant, and it works on phishing links that are already dead, which a hidden set usually holds.

    python3 scripts/evaluate_sites.py my_urls.csv --offline

Outcomes, for a site that answered:
    caught        a phishing site rated 25 points or more
    missed        a phishing site rated below 25
    false alarm   a legitimate site rated 25 points or more
    clean         a legitimate site rated below 25
A site that did not answer (taken down, or blocked) is counted apart: a dead phishing link is not a
failure of the check, and most phishing links die within a day, so use a list from the same day.

The result is printed, and saved next to the first input as <name>-results.md and -results.json.
Phishing addresses are live and dangerous: never open them in your own browser.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import metrics  # noqa: E402

THRESHOLD = 25
# 5.5 s between sites keeps each visit's AI reading under the free Gemini tier's limit; at 2.2 s the AI
# paused and read only 25 of 42 pages (23 November 2026).
SERVER_DELAY = float(__import__("os").getenv("HARIS_BENCH_DELAY", "5.5"))
LOCAL_DELAY = 0.3


def load_env() -> None:
    import os
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def read_cases(paths: list[str], labels: list[str], limit: int | None) -> list[dict]:
    cases: list[dict] = []
    for i, path in enumerate(paths):
        p = Path(path)
        if not p.exists():
            raise SystemExit(f"{path} does not exist. Was the list written? (the fetch script says so if not)")
        if p.suffix in (".json", ".csv", ".jsonl"):
            items = [{**c, "label": "phishing" if c["positive"] else "legitimate"}
                     for c in metrics.read_labelled(path, "url")]
        else:
            label = labels[i] if i < len(labels) else (labels[-1] if labels else None)
            if label not in ("phishing", "legitimate"):
                raise SystemExit(f"{path}: give --label phishing or legitimate for a .txt file")
            items = [{"url": line.strip(), "label": label} for line in p.read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
        seen = {c["url"] for c in cases}
        items = [c for c in items if c["url"] not in seen]
        cases += items[:limit] if limit else items
    return cases


def check_on_server(server: str, url: str) -> dict:
    req = urllib.request.Request(f"{server.rstrip('/')}/api/site", data=json.dumps({"url": url, "lang": "en"}).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                return {"reachable": False, "score": 0, "flags": [], "final_domain": "", "error": "refused"}
            if exc.code == 429 and attempt < 2:
                time.sleep(30)
                continue
            return {"reachable": False, "score": 0, "flags": [], "final_domain": "", "error": f"HTTP {exc.code}"}
        except OSError as exc:
            if attempt < 2:
                time.sleep(5)
                continue
            return {"reachable": False, "score": 0, "flags": [], "final_domain": "", "error": type(exc).__name__}
    return {"reachable": False, "score": 0, "flags": [], "final_domain": "", "error": "gave up"}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Measure the live website check.", epilog="See the top of this file.")
    ap.add_argument("files", nargs="+", help=".txt (one address per line) or .json files")
    ap.add_argument("--label", default="", help="phishing or legitimate, one per .txt file, comma-separated")
    ap.add_argument("--server", help="run the checks on this deployed Haris, e.g. https://haris-uae.onrender.com")
    ap.add_argument("--limit", type=int, help="take only the first N addresses of each file")
    ap.add_argument("--no-ai", action="store_true", help="locally: skip the AI reading of each page")
    ap.add_argument("--offline", action="store_true",
                    help="judge each address from the link alone, without visiting it (works on dead links)")
    args = ap.parse_args()
    labels = [x.strip() for x in args.label.split(",") if x.strip()]
    paths, server = args.files, args.server
    cases = read_cases(paths, labels, args.limit)

    if args.offline:
        sys.path.insert(0, str(ROOT / "backend"))
        from haris.detector import MEDIUM_THRESHOLD
        from haris.urls import analyze_url

        def run(url: str) -> dict:
            # The link's own points, as they enter a message's score: medium or more counts as flagged.
            link = analyze_url(url)
            flagged = not link.official and link.score >= MEDIUM_THRESHOLD
            return {"reachable": True, "score": THRESHOLD if flagged else 0, "final_domain": link.domain,
                    "flags": link.flags}
        delay = 0.0
    elif server:
        run = lambda url: check_on_server(server, url)  # noqa: E731
        delay = SERVER_DELAY
    else:
        sys.path.insert(0, str(ROOT / "backend"))
        load_env()
        from haris import sitecheck
        run = lambda url: sitecheck.inspect(url, "en", use_llm=not args.no_ai)  # noqa: E731
        delay = LOCAL_DELAY

    sys.path.insert(0, str(ROOT / "backend"))
    from haris.detector import MEDIUM_THRESHOLD as _MEDIUM
    from haris.urls import analyze_url as _link

    counts = {"caught": 0, "missed": 0, "false alarm": 0, "clean": 0, "unreachable": 0}
    # Every link, as Haris judges it inside a message: the visit when the page answers, and the link itself
    # always, so a dead phishing link is still judged rather than left out. [tp, fp, fn, tn]
    whole = [0, 0, 0, 0]
    rows = []
    started = datetime.now(timezone.utc)
    print(f"Checking {len(cases)} addresses {'on ' + server if server else 'from this machine'}…\n")
    for n, case in enumerate(cases, 1):
        r = run(case["url"])
        phishing = case["label"] == "phishing"
        if not r.get("reachable"):
            verdict = "unreachable"
        elif phishing:
            verdict = "caught" if r["score"] >= THRESHOLD else "missed"
        else:
            verdict = "false alarm" if r["score"] >= THRESHOLD else "clean"
        counts[verdict] += 1
        link = _link(case["url"])
        # As detector.py does: what the visit found counts even when the page is down (a domain registered
        # three days ago, a certificate issued yesterday), and the link's own points always count.
        hit = r.get("score", 0) >= THRESHOLD or (not link.official and link.score >= _MEDIUM)
        whole[(0 if hit else 2) if phishing else (1 if hit else 3)] += 1
        rows.append({"url": case["url"], "label": case["label"], "verdict": verdict, "score": r.get("score", 0),
                     "final_domain": r.get("final_domain", ""), "flags": r.get("flags", []),
                     "ai": (r.get("ai") or {}).get("risk"), "error": r.get("error")})
        print(f"{n:>3}/{len(cases)} {verdict:<12} {r.get('score', 0):>3}  {(r.get('final_domain') or '')[:38]:<38} "
              f"{', '.join(r.get('flags', []))[:55]}")
        if delay:
            time.sleep(delay)

    live_phish = counts["caught"] + counts["missed"]
    live_legit = counts["clean"] + counts["false alarm"]
    pct = lambda a, b: f"{a / b:.0%}" if b else "n/a"  # noqa: E731
    flag_counts: dict[str, int] = {}
    for row in rows:
        if row["verdict"] == "caught":
            for f in row["flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
    top = sorted(flag_counts.items(), key=lambda kv: -kv[1])[:8]

    summary = [
        "# Live website check — results",
        "",
        f"Run {started:%Y-%m-%d %H:%M} UTC, "
        + ("offline: from the link alone, without visiting it (flagged = the link's own points reach medium risk)." if args.offline
           else f"{'on ' + server if server else 'locally'}, threshold {THRESHOLD} points."),
        "",
        "| | Count | Rate |",
        "|---|---:|---:|",
        f"| Phishing sites that answered | {live_phish} | |",
        f"| … caught | {counts['caught']} | **{pct(counts['caught'], live_phish)}** |",
        f"| … missed | {counts['missed']} | {pct(counts['missed'], live_phish)} |",
        f"| Legitimate sites that answered | {live_legit} | |",
        f"| … false alarms | {counts['false alarm']} | **{pct(counts['false alarm'], live_legit)}** |",
        f"| Did not answer (excluded) | {counts['unreachable']} | |",
        "",
    ] + metrics.table(metrics.scores(counts["caught"], counts["false alarm"], counts["missed"], counts["clean"]),
                      positive="phishing") + ([] if args.offline else [
        "",
        "**Every link, dead ones included**, as Haris judges a link inside a message: what the visit found (domain "
        "age and certificate count even when the page is down) and the link itself:",
        "",
    ] + metrics.table(metrics.scores(*whole), positive="phishing")) + [
        "",
    ] + ([] if args.offline else [
        f"The AI read {sum(1 for r in rows if r['ai'])} of the {sum(1 for r in rows if r['verdict'] != 'unreachable')} "
        "pages that answered (the free tier pauses when it gets too many requests a minute; the rules answer meanwhile).",
        ""]) + [
        "Signals behind the catches: " + (", ".join(f"`{k}` {v}" for k, v in top) or "none"),
        "",
        "Missed and false alarms:",
        "",
    ] + [f"- {r['verdict']}: `{r['final_domain'] or r['url'][:60]}` score {r['score']} ({', '.join(r['flags']) or 'no flags'})"
         for r in rows if r["verdict"] in ("missed", "false alarm")] + [""]
    text = "\n".join(summary)
    print("\n" + text)

    base = Path(paths[0])
    out = base.with_name(base.stem + "-results")
    out.with_suffix(".md").write_text(text, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"counts": counts, "rows": rows}, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    print(f"Saved {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
