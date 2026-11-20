"""Add fictional WhatsApp alert subscribers, so approving a campaign shows a delivery to thousands.

    python3 scripts/alerts_demo.py                     # 2,400 fictional subscribers in 4 languages
    python3 scripts/alerts_demo.py --subscribers 500
    python3 scripts/alerts_demo.py --clear             # remove the fictional ones (real subscribers stay)

Their ids are "demo-000123", not phone numbers, so nothing is ever sent to them, even with WhatsApp
switched on: they are only counted as a simulated delivery. A real phone that sends «تنبيهات» to the
Haris WhatsApp number joins the same list and does receive the warning.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris import alerts  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--subscribers", type=int, default=2400)
    ap.add_argument("--clear", action="store_true", help="remove the fictional subscribers only")
    args = ap.parse_args()
    made = alerts.add_demo_subscribers(0 if args.clear else args.subscribers)
    c = alerts.counts()
    print(f"{made} fictional subscribers. In all: {c['total']} ({c['real']} real), by language: {c['by_lang']}")
    print(f"Delivery mode now: {alerts.mode()}")


if __name__ == "__main__":
    main()
