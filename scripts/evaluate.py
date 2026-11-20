"""Measure Haris on the labelled sample messages.

    python scripts/evaluate.py          # rules engine only
    python scripts/evaluate.py --ai     # rules plus the AI (needs a key in .env); slower
    python scripts/evaluate.py --ai --hard   # new wording the rules were not written for

With --ai, the model never sees the message it is judging among its examples.

A scam counts as caught when Haris rates it medium or high. A legitimate
message counts as a false alarm when it is rated medium or high.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris.detector import analyze  # noqa: E402


DELAY = 1.0


def load_env() -> None:
    """Read KEY=value lines from .env, so the script uses the same keys as the server."""
    import os
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()


def main() -> int:
    global DELAY
    use_ai = "--ai" in sys.argv
    if use_ai:
        load_env()
        from haris import llm
        if not llm.enabled():
            print("No AI key found in .env (ANTHROPIC_API_KEY or GEMINI_API_KEY).")
            return 1
        import os
        DELAY = float(os.getenv("HARIS_EVAL_DELAY", "4.5" if llm.provider() == "gemini" else "0.5"))
        print(f"AI on: {llm.provider()} / {llm.model_name()} (one message every {DELAY:g} s)\n")
    name = "hard" if "--hard" in sys.argv else "messages"
    samples = json.loads((ROOT / "data" / "samples" / f"{name}.json").read_text(encoding="utf-8"))
    print(f"Set: data/samples/{name}.json ({len(samples)} messages)\n")
    count = {"rules": [0, 0], "final": [0, 0]}  # [scams caught, false alarms]
    ai_answered = 0
    print(f"{'id':<22} {'label':<6} {'rules':<7} {'final':<7} category")
    for s in samples:
        rules = analyze(s["text"], use_llm=False)
        r = analyze(s["text"], use_llm=True) if use_ai else rules
        ai_answered += r.get("engine") == "rules+ai"
        for key, res in (("rules", rules), ("final", r)):
            flagged = res["risk"] in ("medium", "high")
            count[key][0 if s["label"] == "scam" else 1] += flagged
        flagged = r["risk"] in ("medium", "high")
        mark = "" if flagged == (s["label"] == "scam") else "  <-- wrong"
        print(f"{s['id']:<22} {s['label']:<6} {rules['risk']:<7} {r['risk']:<7} {r['category']}{mark}")
        if use_ai:
            time.sleep(DELAY)  # stay inside the free tier's per-minute limit

    scams = sum(s["label"] == "scam" for s in samples)
    legit = len(samples) - scams
    print()
    print(f"Rules only:   scams caught {count['rules'][0]}/{scams}, false alarms {count['rules'][1]}/{legit}")
    if use_ai:
        print(f"Rules + AI:   scams caught {count['final'][0]}/{scams}, false alarms {count['final'][1]}/{legit}")
        print(f"AI answered:  {ai_answered}/{len(samples)} (the rest fell back to the rules)")
    caught, alarms = count["final"]
    return 0 if caught == scams and alarms == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
