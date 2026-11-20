"""Teach Haris a new example: the next check of a similar message learns from it.

    python scripts/teach.py scam  "نص الرسالة الاحتيالية"  --category bank_impersonation --why "يطلب رمز التحقق"
    python scripts/teach.py legit "رسالة حقيقية من البنك"  --why "لا يطلب أي بيانات ولا رابط"
    python scripts/teach.py --list

Personal data in the text (cards, IDs, phone numbers, IBANs, e-mails) is removed before saving.
Examples are saved in data/training/examples.jsonl and are used only when the AI is on.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris import examples  # noqa: E402
from haris.llm import CATEGORIES  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("label", nargs="?", choices=examples.LABELS)
    ap.add_argument("text", nargs="?")
    ap.add_argument("--category", choices=CATEGORIES)
    ap.add_argument("--why", help="one short line: why this is (or is not) a scam")
    ap.add_argument("--list", action="store_true", help="show the examples you added")
    args = ap.parse_args()
    if args.list:
        import json
        lines = examples.TRAINING.read_text(encoding="utf-8").splitlines() if examples.TRAINING.exists() else []
        added = [json.loads(line) for line in lines if line.strip()]
        for e in added:
            print(f"[{e['label']}] {e['text'][:100]}")
        print(f"\n{len(added)} examples added, {len(examples.load())} in total")
        return 0
    if not (args.label and args.text):
        ap.error("give a label (scam or legit) and the message text")
    entry = examples.add(args.text, args.label, args.category, args.why)
    print("Saved:", entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
