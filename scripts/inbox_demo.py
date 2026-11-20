"""Fill the report inbox with fictional reports for a demo of the authority dashboard.

    python3 scripts/inbox_demo.py          # add 6 fictional reports
    python3 scripts/inbox_demo.py --clear  # empty the inbox first

Every name, number and link below is made up.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from haris import inbox  # noqa: E402

REPORTS = [
    ("ar", "dubai", True, {
        "incident_type": "money_sent", "occurred_at": "اليوم، قبل 40 دقيقة",
        "description": "وصلتني رسالة أن طرداً متوقفاً ويجب دفع 12.5 درهم. أدخلت بيانات البطاقة فخُصم 3,400 درهم.",
        "amount": "3400", "payment_method": "بطاقة بنكية", "evidence": ["1", "2"],
        "scammer_identifiers": ["https://parcel-uae-fee.top", "+971 50 000 0101"],
        "steps_taken": ["اتصلت بالبنك وأوقفت البطاقة"], "reporter_name": "مُبلّغ تجريبي 1"}),
    ("en", "abu_dhabi", True, {
        "incident_type": "extortion", "occurred_at": "Yesterday evening",
        "description": "Someone on Instagram is threatening my son (15) to post his photos unless he pays.",
        "scammer_identifiers": ["@fake_account_demo"], "evidence": ["1"], "reporter_name": "Demo reporter 2"}),
    ("ur", "sharjah", False, {
        "incident_type": "account_hacked", "occurred_at": "آج صبح",
        "description": "میرا واٹس ایپ ہیک ہو گیا اور میرے دوستوں سے پیسے مانگے جا رہے ہیں۔",
        "scammer_identifiers": ["+971 55 000 0202"], "reporter_name": "ڈیمو رپورٹر 3"}),
    ("hi", "ajman", True, {
        "incident_type": "money_sent", "occurred_at": "पिछले हफ्ते",
        "description": "नौकरी के नाम पर वीज़ा फीस के 1,800 दिरहम लिए और फिर नंबर बंद कर दिया।",
        "amount": "1800", "payment_method": "बैंक ट्रांसफर", "scammer_identifiers": ["+971 52 000 0303"],
        "reporter_name": "डेमो रिपोर्टर 4"}),
    ("ar", "ras_al_khaimah", True, {
        "incident_type": "impersonation", "occurred_at": "منذ يومين",
        "description": "حساب ينتحل اسم شركتي ويطلب من العملاء الدفع لحساب آخر.",
        "scammer_identifiers": ["https://my-company-offers.shop"], "reporter_name": "مُبلّغ تجريبي 5"}),
    ("ar", "fujairah", False, {
        "incident_type": "suspicious_only", "occurred_at": "اليوم",
        "description": "رسالة تقول إن حسابي في البنك سيُجمّد، لم أضغط على الرابط.",
        "scammer_identifiers": ["https://bank-secure-update.top"]}),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clear", action="store_true", help="empty the inbox first")
    args = ap.parse_args()
    if args.clear:
        db = inbox._settings()["db"]
        if db.exists():
            db.unlink()
    for lang, emirate, verified, data in REPORTS:
        r = inbox.submit(data, lang, emirate, verified)
        print(f"{r['reference']}  {r['priority']:<10} {emirate:<15} {data['incident_type']}")
    hacked = next(i["reference"] for i in inbox.queue()["items"] if i["incident_type"] == "account_hacked")
    inbox.act(hacked, "receive")
    print(f"\n{len(REPORTS)} fictional reports in {os.path.relpath(inbox._settings()['db'], ROOT)}")


if __name__ == "__main__":
    main()
