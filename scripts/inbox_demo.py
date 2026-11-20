"""Fill the report inbox with fictional reports for a demo of the authority dashboard.

    python3 scripts/inbox_demo.py --clear             # empty the inbox, then add 30 fictional reports
    python3 scripts/inbox_demo.py --clear --count 6   # just the 6 hand-written ones

Beyond the first 6, reports are drawn from the templates below with a fixed random seed, so every run
gives the same mix: different situations, languages, emirates, ages over the past 5 days, and statuses
(received, waiting for information, closed), so the dashboard can be worked like a real queue.

Every name, number and link below is made up.
"""

import argparse
import json
import os
import random
import time
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def _load_env(path: Path) -> None:
    """Read KEY=value lines from .env, as the server does with --env-file, without overriding the shell."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key and not key.startswith("#") and value and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


_load_env(ROOT / ".env")  # the AI key, so the demo reports are translated like real ones

from haris import inbox, llm  # noqa: E402
from haris.report import UAE_TIME  # noqa: E402

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


EXTRA = [
    ("ar", "money_sent", "قبل ساعتين", "اتصل بي شخص قال إنه من البنك وطلب رمز التحقق لتحديث البطاقة، فأعطيته الرمز وخُصم {amount} درهم.", "بطاقة بنكية", ["+971 50 000 1{n:03d}"]),
    ("ar", "money_sent", "أمس", "اشتريت هاتفاً من إعلان على إنستغرام وحوّلت {amount} درهم، ثم حظرني البائع.", "تحويل بنكي", ["@phone_deals_demo{n}"]),
    ("en", "money_sent", "this morning", "A 'Salik' text said I had an unpaid fine. I paid on the link and {amount} AED left my card.", "card", ["https://salik-fine-pay{n}.top"]),
    ("ur", "money_sent", "آج", "نوکری کے لیے ویزا فیس کے نام پر {amount} درہم لیے، اب نمبر بند ہے۔", "بینک ٹرانسفر", ["+971 52 000 2{n:03d}"]),
    ("hi", "money_sent", "आज सुबह", "निवेश ऐप में मुनाफ़ा दिखाया, निकालने के लिए {amount} दिरहम फीस माँगी और ले ली।", "क्रिप्टो (USDT)", ["https://uae-invest-pro{n}.app"]),
    ("ar", "business_fraud", "اليوم", "وصلنا بريد من «المورّد» بتغيير رقم الحساب، فدفعت الشركة فاتورة بقيمة {amount} درهم للحساب الجديد.", "تحويل بنكي", ["accounts@supp1ier-demo{n}.com"]),
    ("en", "business_fraud", "last week", "Our accountant got a WhatsApp from the 'CEO' asking for gift cards worth {amount} AED, and bought them.", "gift cards", ["+971 55 000 3{n:03d}"]),
    ("ar", "extortion", "منذ ثلاثة أيام", "شخص تعرفت عليه على تطبيق تعارف يهدد بنشر محادثاتنا إن لم أدفع.", "", ["@lonely_heart_demo{n}"]),
    ("en", "extortion", "yesterday", "Someone is threatening my daughter (14) on Snapchat to share her photos unless she sends more.", "", ["snap: shadow_demo{n}"]),
    ("ar", "harassment", "هذا الأسبوع", "حساب مجهول يرسل لي رسائل سب وتهديد يومياً ويقول سأقتلك إن خرجتِ.", "", ["@anon_demo{n}"]),
    ("ur", "harassment", "اس ہفتے", "کوئی مجھے روز گالیاں اور دھمکی بھرے پیغام بھیج رہا ہے۔", "", ["+971 56 000 4{n:03d}"]),
    ("ar", "account_hacked", "اليوم", "اخترقوا حسابي في إنستغرام وغيّروا البريد ويطلبون مالاً من متابعيّ.", "", ["@my_hacked_demo{n}"]),
    ("en", "account_hacked", "two hours ago", "My email was taken over after a fake login page; they are sending invoices to my clients.", "", ["https://outlook-verify{n}.site"]),
    ("hi", "device_hacked", "कल", "मेरे लैपटॉप की फ़ाइलें लॉक हो गईं और फिरौती माँग रहे हैं।", "", ["decrypt-help{n}@proton.demo"]),
    ("ar", "privacy_violation", "قبل يومين", "نشر أحدهم صوري ورقم هاتفي في مجموعة على تيليجرام دون إذني.", "", ["t.me/group_demo{n}"]),
    ("ar", "identity_shared", "اليوم", "أرسلت صورة الهوية والجواز لشركة توظيف على واتساب ثم اختفت.", "", ["+971 54 000 5{n:03d}"]),
    ("en", "impersonation", "this week", "A fake account with my name and photos is asking my friends for money.", "", ["@my_name_fake{n}"]),
    ("ar", "suspicious_only", "اليوم", "رسالة تقول إن حسابي في «الإقامة» سيُوقف وفيها رابط، لم أضغط عليه.", "", ["https://icp-update-demo{n}.top"]),
    ("en", "suspicious_only", "today", "A text about a parcel at the post office with a link. I didn't open it.", "", ["https://emirates-post-demo{n}.top"]),
    ("ru", "money_sent", "сегодня утром", "Пришло сообщение, что бронь отеля отменят, если не оплатить {amount} дирхамов по ссылке. Я оплатил картой своего банка.", "банковская карта", ["https://booking-confirm-dxb{n}.top"]),
    ("ru", "account_hacked", "вчера", "Взломали мой Telegram и от моего имени просят деньги у друзей.", "", ["@ru_hacked_demo{n}"]),
    ("ru", "suspicious_only", "сегодня", "Пришло сообщение о штрафе за парковку со ссылкой, я не переходил.", "", ["https://dubai-fine-pay{n}.top"]),
]
# The officer writes in Arabic; Haris translates for a victim who wrote in another language.
NOTES = {
    "request_info": ["أرسل اسم البنك وآخر 4 أرقام من البطاقة ووقت الخصم.", "أرسل لقطة شاشة للمحادثة يظهر فيها الرقم كاملاً.",
                     "أرسل رابط الحساب المنتحِل كما يظهر في المتصفح.", "متى وصلتك آخر رسالة تهديد؟ اذكر التاريخ والوقت."],
    "close": ["أُبلغ البنك وجُمّد جزء من المبلغ. أُغلق البلاغ.", "حذفت المنصة الحساب المنتحِل، وأُغلق البلاغ.",
              "حُوّل البلاغ إلى قسم الجرائم الإلكترونية في الإمارة المختصة."],
}
REPLIES = {
    "ar": ["بنك تجريبي، البطاقة المنتهية بـ 0000، الساعة 8:12 م", "الرابط هو الموجود في البلاغ نفسه."],
    "en": ["Demo Bank, card ending 0000, at 8:12 pm.", "The last message came yesterday at 11 pm."],
    "ur": ["ڈیمو بینک، کارڈ کے آخری نمبر 0000، رات 8:12 بجے۔", "آخری پیغام کل رات 11 بجے آیا۔"],
    "hi": ["डेमो बैंक, कार्ड के आख़िरी अंक 0000, रात 8:12 बजे।", "आख़िरी मैसेज कल रात 11 बजे आया।"],
    "ru": ["Демо-банк, карта заканчивается на 0000, в 20:12.", "Последнее сообщение пришло вчера в 23:00."],
}
PACE = float(os.getenv("HARIS_DEMO_PACE", "4.5"))  # seconds per AI call: Gemini's free tier allows about 15 a minute


def wait(calls: int) -> None:
    if llm.enabled() and PACE > 0:
        time.sleep(PACE * calls)


VISITOR_LANGS = {"en": ["British", "German", "American", "Australian"], "ru": ["Russian", "Kazakh", "Ukrainian"]}


def _generated(count: int) -> list:
    random.seed(7)  # the officer's pace in _backdate
    rng = random.Random(42)
    out = []
    for n in range(count):
        lang, incident, when, text, method, ids = EXTRA[n % len(EXTRA)]
        amount = rng.choice([250, 480, 950, 1200, 2750, 4300, 8900, 15000, 38000])
        data = {"incident_type": incident, "occurred_at": when, "description": text.format(amount=f"{amount:,}", n=n),
                "scammer_identifiers": [i.format(n=n) for i in ids], "evidence": ["1"] * rng.randint(0, 3)}
        if method:
            data.update(amount=str(amount), payment_method=method)
        visitor = None
        if lang in VISITOR_LANGS and rng.random() < 0.6:  # tourists: no Emirates ID, a flight home
            visitor = {"nationality": rng.choice(VISITOR_LANGS[lang]), "departure": rng.choice(
                ["within_3_days", "within_3_days", "within_week", "later", "unknown"]),
                "contact_abroad": f"visitor{n}@example.com", "identity": rng.choice(["uae_pass_visitor", "passport"])}
        emirate = rng.choice(["dubai", "dubai", "abu_dhabi", "ras_al_khaimah"]) if visitor else rng.choice(inbox.EMIRATES)
        out.append((lang, emirate, rng.random() < 0.8, data, rng, visitor))
    return out


def _backdate(ref: str, hours: float) -> str:
    """Spread the demo over the past days, so the queue shows "2 hours ago", "3 days ago".

    The reference carries the day the report was made, so it moves back with it."""
    with closing(inbox._connect()) as con, con:
        row = con.execute("SELECT created_at, events FROM reports WHERE ref = ?", (ref,)).fetchone()
        shift = hours * 3600
        day = datetime.fromtimestamp(row["created_at"] - shift, UAE_TIME)
        new_ref = f"HRS-{day:%Y%m%d}-{ref.rsplit('-', 1)[1]}"
        # Each later step comes some minutes after the one before, as an officer would work it.
        events, gap = json.loads(row["events"]), 0.0
        for k, e in enumerate(events):
            if k:
                gap = min(gap + random.uniform(6, 75) * 60, shift * 0.9)
            e["ts"] = e["ts"] - shift + gap
        con.execute("UPDATE reports SET ref = ?, created_at = created_at - ?, updated_at = ?, events = ? WHERE ref = ?",
                    (new_ref, shift, events[-1]["ts"], json.dumps(events, ensure_ascii=False), ref))
    return new_ref


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clear", action="store_true", help="empty the inbox first")
    ap.add_argument("--count", type=int, default=30, help="how many reports in all (default 30)")
    args = ap.parse_args()
    if args.clear:
        db = inbox._settings()["db"]
        if db.exists():
            db.unlink()
    made = 0
    if llm.enabled():
        print(f"Translating the reports that are not in Arabic with {llm.model_name()}, "
              f"{PACE:g} s per call (HARIS_DEMO_PACE=0 to go faster and risk the free-tier limit)...\n")
    for lang, emirate, verified, data in REPORTS[: args.count]:
        r = inbox.submit(data, lang, emirate, verified)
        if lang != "ar":
            wait(2)
        made += 1
        print(f"{r['reference']}  {r['priority']:<10} {emirate:<15} {data['incident_type']}")
    hacked = next((i["reference"] for i in inbox.queue()["items"] if i["incident_type"] == "account_hacked"), None)
    if hacked:
        inbox.act(hacked, "receive")
    for lang, emirate, verified, data, rng, visitor in _generated(max(0, args.count - len(REPORTS))):
        r = inbox.submit(data, lang, emirate, verified, visitor=visitor)
        other = lang != "ar"
        wait(2 if other else 0)
        ref, roll = r["reference"], rng.random()
        if roll < 0.25:
            inbox.act(ref, "receive")
        elif roll < 0.42:
            inbox.act(ref, "receive")
            inbox.act(ref, "request_info", rng.choice(NOTES["request_info"]))
            wait(1 if other else 0)
            if rng.random() < 0.5:
                inbox.reply(ref, r["token"], rng.choice(REPLIES[lang]))
                wait(1 if other else 0)
        elif roll < 0.55:
            inbox.act(ref, "receive")
            inbox.act(ref, "close", rng.choice(NOTES["close"]))
            wait(1 if other else 0)
        # Money lost "today" stays within the last hours; the rest spreads over 5 days.
        recent = r["priority"] in ("critical", "financial")
        ref = _backdate(ref, rng.uniform(0.2, 5) if recent else rng.uniform(1, 5 * 24))
        made += 1
        print(f"{ref}  {r['priority']:<10} {emirate:<15} {data['incident_type']}")
    s = inbox.queue()["stats"]
    print(f"\n{made} fictional reports in {os.path.relpath(inbox._settings()['db'], ROOT)}: "
          f"{s['new']} new, {s['in_progress']} in progress, {s['closed']} closed, {s['urgent']} urgent or critical open")
    print(f"Open cases by language: {s['by_lang']}; needing a translator: {s['needs_translator']}; "
          f"visitors: {s['visitors']} ({s['leaving_soon']} leaving within 3 days)")


if __name__ == "__main__":
    main()
