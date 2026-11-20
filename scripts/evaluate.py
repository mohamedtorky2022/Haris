"""Measure Haris on the labelled sample messages.

    python scripts/evaluate.py          # rules engine only
    python scripts/evaluate.py --ai     # rules plus the AI (needs a key in .env); slower

With --ai, the model never sees the message it is judging among its examples.

A scam counts as caught when Haris rates it medium or high. A legitimate
message counts as a false alarm when it is rated medium or high.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris.detector import analyze  # noqa: E402


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
    use_ai = "--ai" in sys.argv
    if use_ai:
        load_env()
        from haris import llm
        if not llm.enabled():
            print("No AI key found in .env (ANTHROPIC_API_KEY or GEMINI_API_KEY).")
            return 1
        print(f"AI on: {llm.provider()} / {llm.model_name()}\n")
    samples = json.loads((ROOT / "data" / "samples" / "messages.json").read_text(encoding="utf-8"))
    caught = missed = false_alarms = clean = 0
    print(f"{'id':<20} {'label':<6} {'risk':<7} score  category")
    for s in samples:
        r = analyze(s["text"], use_llm=use_ai)
        flagged = r["risk"] in ("medium", "high")
        if s["label"] == "scam":
            caught += flagged
            missed += not flagged
        else:
            false_alarms += flagged
            clean += not flagged
        mark = "" if flagged == (s["label"] == "scam") else "  <-- wrong"
        print(f"{s['id']:<20} {s['label']:<6} {r['risk']:<7} {r['score']:>5}  {r['category']}{mark}")

    scams, legit = caught + missed, false_alarms + clean
    print()
    print(f"Scams caught:  {caught}/{scams} ({caught / scams:.0%})")
    print(f"False alarms:  {false_alarms}/{legit} ({false_alarms / legit:.0%})")
    return 0 if missed == 0 and false_alarms == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
