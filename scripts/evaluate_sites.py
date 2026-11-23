"""Measure the live website check on a list of real addresses.

    python scripts/evaluate_sites.py data/samples/sites.json
    python scripts/evaluate_sites.py data/samples/sites.json --ai     # also let the model read each page

The file is a list of {"url": ..., "label": "phishing" | "legitimate", "note": ...}. Every address
is visited the way a victim's phone would reach it, and the result is compared with the label:

    caught        a phishing site rated 25 points or more
    false alarm   a legitimate site rated 25 points or more
    missed        a phishing site that scored below that
    unreachable   the site did not answer (taken down, or blocked); reported separately, since
                  a dead phishing link is not a failure of the check

Phishing addresses are live and dangerous. Run this on a machine you are willing to expose, never
open the addresses in your own browser, and keep the file out of the repository if it holds
addresses a partner shared in confidence.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris import sitecheck  # noqa: E402

THRESHOLD = 25
DELAY = 0.5


def load_env() -> None:
    import os
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_ai = "--ai" in sys.argv
    if not args:
        print(__doc__)
        return 2
    load_env()
    cases = json.loads(Path(args[0]).read_text(encoding="utf-8"))

    caught = missed = false_alarms = clean = unreachable = 0
    rows = []
    for case in cases:
        report = sitecheck.inspect(case["url"], case.get("lang", "en"), use_llm=use_ai)
        score, phishing = report["score"], case["label"] == "phishing"
        if not report["reachable"]:
            unreachable += 1
            verdict = "unreachable"
        elif phishing and score >= THRESHOLD:
            caught += 1
            verdict = "caught"
        elif phishing:
            missed += 1
            verdict = "MISSED"
        elif score >= THRESHOLD:
            false_alarms += 1
            verdict = "FALSE ALARM"
        else:
            clean += 1
            verdict = "clean"
        rows.append((verdict, score, report["final_domain"], ", ".join(report["flags"]) or "-"))
        print(f"{verdict:<12} {score:>3}  {report['final_domain'][:40]:<40} {rows[-1][3][:60]}")
        time.sleep(DELAY)

    live_phishing = caught + missed
    live_legit = clean + false_alarms
    print("\n--- Summary ---")
    print(f"Phishing sites reached : {live_phishing}   caught {caught}"
          f"  ({caught / live_phishing:.0%})" if live_phishing else "Phishing sites reached : 0")
    print(f"Legitimate sites       : {live_legit}   false alarms {false_alarms}"
          f"  ({false_alarms / live_legit:.0%})" if live_legit else "Legitimate sites       : 0")
    print(f"Did not answer         : {unreachable}")
    print(f"AI page reading        : {'on' if use_ai else 'off'}")
    return 1 if missed or false_alarms else 0


if __name__ == "__main__":
    raise SystemExit(main())
