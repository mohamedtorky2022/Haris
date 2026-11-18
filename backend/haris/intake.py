"""Turn a victim's free story (text, dictated voice, screenshots) into report fields.

The victim tells what happened in one go. Rules pull out what they can
(amounts, phone numbers, links, IBANs, payment method, time words, steps
already taken); when the AI is on, Claude reads the story and screenshots too
and fills what the rules missed. The result lists the fields still missing, so
the chat asks only about those.
"""

from __future__ import annotations

import base64
import re

from . import llm
from .redact import find_identifiers, redact
from .text import normalize, normalize_digits, pick_language
from .urls import extract_urls

MAX_IMAGES = 3
MAX_IMAGE_BYTES = 4 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DATA_URL = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$")

# Which fields the police need first, per incident type.
REQUIRED = {
    "money_sent": ("occurred_at", "amount", "payment_method", "steps_taken"),
    "account_hacked": ("occurred_at", "steps_taken"),
    "extortion": ("occurred_at",),
    "identity_shared": ("occurred_at",),
    "harassment": ("occurred_at",),
    "impersonation": ("occurred_at",),
    "privacy_violation": ("occurred_at",),
    "device_hacked": ("occurred_at", "steps_taken"),
    "business_fraud": ("occurred_at", "amount", "payment_method", "steps_taken"),
    "suspicious_only": (),
}

INCIDENT_HINTS = {
    "impersonation": ("حساب مزيف باسمي", "حساب وهمي باسمي", "حسابا مزيفا باسمي", "حسابا وهميا باسمي", "ينتحل شخصيتي",
                      "انتحل شخصيتي", "يستخدم اسمي", "يستخدم صوري", "fake account in my name", "fake account with my",
                      "fake profile", "impersonating me", "pretending to be me", "using my photos", "using my name",
                      "میرے نام سے جعلی", "میرے نام کا جعلی", "میری تصویر استعمال"),
    "privacy_violation": ("صورني دون", "صورني بدون", "صوروني دون", "صوروني بدون", "صورني من غير", "نشر صوري دون", "نشر صوري بدون", "نشر صورتي دون",
                          "نشر صورتي بدون", "نشر عنواني", "نشر بياناتي", "نشر رقمي", "دون اذني", "بدون اذني", "بدون علمي",
                          "filmed me", "recorded me without", "posted my photo", "posted my address", "shared my photos without",
                          "without my permission", "without my consent", "اجازت کے بغیر", "میری ویڈیو بنائی"),
    "device_hacked": ("فدية", "ملفاتي مشفرة", "الملفات مشفرة", "فيروس", "برنامج خبيث", "هاتفي مخترق", "جهازي مخترق",
                      "اللابتوب مخترق", "فقدت الشبكة فجأة", "نقلوا شريحتي", "ransomware", "ransom", "files are encrypted",
                      "files encrypted", "virus", "malware", "my phone is hacked", "my laptop is hacked", "computer is hacked",
                      "sim swap", "lost signal", "وائرس", "تاوان", "فون ہیک"),
    "extortion": ("ابتزاز", "يبتزني", "يهددني", "سينشر", "صوري", "فضيحة", "blackmail", "extort", "threaten",
                  "my photos", "my video", "بلیک میل", "دھمکی"),
    "account_hacked": ("اختراق", "اخترق", "سرق حسابي", "سرقة حسابي", "لا أستطيع الدخول", "hacked", "lost access",
                       "account was stolen", "ہیک"),
    "harassment": ("يتنمر", "تنمر", "يتحرش", "تحرش", "يسبني", "سبني", "يشتمني", "شتمني", "يسيء لي", "إساءة", "تشهير",
                   "يشهر بي", "bully", "bullied", "harass", "insult", "abusive messages", "defam", "troll",
                   "ہراساں", "گالی", "تنگ کر"),
    "business_fraud": ("فاتورة", "المورد", "الحساب البنكي الجديد", "تغيير الحساب البنكي", "invoice", "supplier",
                       "vendor", "ceo asked", "the boss asked", "my manager asked", "new bank details",
                       "changed their bank", "انوائس", "سپلائر"),
    "identity_shared": ("صورة الهوية", "جواز السفر", "أرسلت هويتي", "passport", "emirates id", "my id",
                        "شناختی کارڈ", "پاسپورٹ"),
    "money_sent": ("دفعت", "حولت", "تحويل", "خصم", "سحب", "بيانات بطاقتي", "رقم البطاقة", "الرمز", "paid", "transferred",
                   "debited", "charged", "card details", "otp", "رقم دی", "پیسے بھیجے", "ادائیگی کی", "کٹ گئے",
                   "ٹرانسفر کیے", "بھیج دیے", "ادا کیے"),
}

EXTORTION_THREATS = ("ابتزاز", "يبتزني", "يهددني بنشر", "يهدد بنشر", "سينشر", "blackmail", "extort", "threatening to post",
                     "threatening to share", "threatening to publish", "بلیک میل")

PAYMENT_HINTS = {
    "gift_cards": ("بطاقات هدايا", "بطاقة هدايا", "gift card", "itunes", "google play", "گفٹ کارڈ"),
    "crypto": ("usdt", "بيتكوين", "bitcoin", "عملات رقمية", "crypto", "binance", "محفظة", "wallet", "کرپٹو"),
    "transfer": ("تحويل", "حولت", "حوالة", "آيبان", "iban", "transfer", "wire", "ٹرانسفر"),
    "card": ("بطاقة", "بطاقتي", "فيزا", "ماستركارد", "card", "visa", "mastercard", "cvv", "کارڈ"),
    "cash": ("نقداً", "نقدا", "كاش", "cash", "نقد"),
}

PAYMENT_LABELS = {
    "card": {"ar": "بطاقة بنكية", "en": "Bank card", "ur": "بینک کارڈ"},
    "transfer": {"ar": "تحويل بنكي", "en": "Bank transfer", "ur": "بینک ٹرانسفر"},
    "crypto": {"ar": "عملات رقمية", "en": "Crypto", "ur": "کرپٹو"},
    "gift_cards": {"ar": "بطاقات هدايا", "en": "Gift cards", "ur": "گفٹ کارڈ"},
    "cash": {"ar": "نقداً", "en": "Cash", "ur": "نقد"},
    "other": {"ar": "طريقة أخرى", "en": "Other", "ur": "دیگر"},
}

STEP_HINTS = {
    "bank": (("اتصلت بالبنك", "كلمت البنك", "أبلغت البنك", "called the bank", "called my bank", "told the bank",
              "بینک کو فون"),
             {"ar": "اتصلت بالبنك", "en": "Called the bank", "ur": "بینک کو فون کیا"}),
    "card": (("أوقفت البطاقة", "اوقفت البطاقة", "جمدت البطاقة", "blocked the card", "blocked my card", "froze my card",
              "کارڈ بند"),
             {"ar": "أوقفت البطاقة", "en": "Blocked the card", "ur": "کارڈ بند کروایا"}),
    "password": (("غيرت كلمة المرور", "غيرت الباسورد", "changed my password", "changed the password",
                  "پاس ورڈ بدل"),
                 {"ar": "غيّرت كلمة المرور", "en": "Changed the password", "ur": "پاس ورڈ بدلا"}),
    "offline": (("فصلت الانترنت", "فصلت الجهاز", "اطفأت الواي فاي", "disconnected", "turned off wi-fi", "turned off the wifi",
                 "انٹرنیٹ بند"),
                {"ar": "فصلت الجهاز عن الإنترنت", "en": "Took the device offline", "ur": "ڈیوائس انٹرنیٹ سے الگ کی"}),
    "blocked": (("حظرت الرقم", "حظرته", "blocked the number", "blocked him", "blocked them", "نمبر بلاک"),
                {"ar": "حظرت رقم المحتال", "en": "Blocked the scammer", "ur": "نمبر بلاک کیا"}),
}

AMOUNT = re.compile(
    r"(\d[\d,]*(?:\.\d{1,2})?)\s?(درهم|دراهم|درہم|aed|dhs|dh|usdt|usd|\$|دولار|ريال|sar)"
    r"|(aed|dhs|usdt|usd|\$)\s?(\d[\d,]*(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
CURRENCY = {"درهم": "AED", "دراهم": "AED", "درہم": "AED", "aed": "AED", "dhs": "AED", "dh": "AED", "usd": "USD",
            "$": "USD", "دولار": "USD", "usdt": "USDT", "ريال": "SAR", "sar": "SAR"}
DAY_WORDS = re.compile(r"(اليوم|امس|أمس|البارحة|قبل ساعة|قبل ساعتين|قبل قليل|today|yesterday|this morning|tonight|"
                       r"an hour ago|آج|کل|ابھی)", re.IGNORECASE)
CLOCK = re.compile(r"(?:الساعة\s?)?\b\d{1,2}(?::\d{2})?\s?(?:صباحاً|صباحا|مساءً|مساء|ظهراً|عصراً|am|pm|بجے)?",
                   re.IGNORECASE)


def _has(text: str, phrases) -> bool:
    return any(normalize(p) in text for p in phrases)


def decode_images(data_urls: list[str]) -> list[tuple[str, str]]:
    """Validate data: URLs and return (media_type, base64) pairs. Invalid ones are dropped."""
    images = []
    for url in data_urls[:MAX_IMAGES]:
        match = DATA_URL.match(url or "")
        if not match or match.group(1) not in IMAGE_TYPES:
            continue
        try:
            raw = base64.b64decode(match.group(2), validate=True)
        except ValueError:
            continue
        if 0 < len(raw) <= MAX_IMAGE_BYTES:
            images.append((match.group(1), match.group(2)))
    return images


def rules_extract(story: str, lang: str) -> dict:
    norm = normalize(story)
    out: dict = {}

    # A threat to publish is extortion even when the story also says "without my permission".
    if _has(norm, EXTORTION_THREATS):
        out["incident_type"] = "extortion"
    else:
        for incident, phrases in INCIDENT_HINTS.items():  # ordered: most specific first
            if _has(norm, phrases):
                out["incident_type"] = incident
                break

    money = AMOUNT.search(normalize_digits(story))
    if money:
        number = (money.group(1) or money.group(4) or "").replace(",", "")
        cur = (money.group(2) or money.group(3) or "").lower()
        if number:
            out["amount"] = number
            out["currency"] = CURRENCY.get(cur, "AED")

    for method, phrases in PAYMENT_HINTS.items():
        if _has(norm, phrases):
            out["payment_method"] = method
            break

    when = [m.group(0).strip() for m in DAY_WORDS.finditer(story)]
    clock = [m.group(0).strip() for m in CLOCK.finditer(normalize_digits(story))
             if re.search(r"الساعة|:|صباح|مساء|ظهر|عصر|am|pm|بجے", m.group(0), re.IGNORECASE)]
    if when or clock:
        out["occurred_at"] = " ".join(dict.fromkeys(when + clock))

    steps = [labels[lang] for phrases, labels in STEP_HINTS.values() if _has(norm, phrases)]
    if steps:
        out["steps_taken"] = steps

    found = find_identifiers(story)
    ids = [*found.get("phones", []), *found.get("emails", []), *found.get("ibans", []), *extract_urls(story)]
    if ids:
        out["scammer_identifiers"] = list(dict.fromkeys(ids))
    return out


def extract(story: str, image_urls: list[str], lang: str | None, incident_type: str | None = None) -> dict:
    lang = pick_language(lang, story)
    story = (story or "").strip()
    images = decode_images(image_urls or [])
    fields = rules_extract(story, lang) if story else {}
    if incident_type in REQUIRED:
        fields["incident_type"] = incident_type

    engine = "rules"
    ai = llm.extract(redact(story).text if story else "", images, lang)
    if ai:
        engine = "rules+ai"
        for key in ("incident_type", "occurred_at", "amount", "currency", "payment_method"):
            if ai.get(key) and not fields.get(key):
                fields[key] = ai[key]
        ids = fields.get("scammer_identifiers", []) + [i for i in ai["scammer_identifiers"]
                                                       if i not in fields.get("scammer_identifiers", [])]
        if ids:
            fields["scammer_identifiers"] = ids
        if ai.get("summary"):
            fields["summary"] = ai["summary"]

    if not fields.get("incident_type") and fields.get("amount") and fields.get("payment_method"):
        fields["incident_type"] = "money_sent"  # an amount paid by a named method means money was lost
    fields.setdefault("incident_type", "suspicious_only")
    if story:
        fields["description"] = story
    elif fields.get("summary"):
        fields["description"] = fields["summary"]
    if fields.get("payment_method"):
        fields["payment_method_label"] = PAYMENT_LABELS[fields["payment_method"]][lang]

    missing = [f for f in REQUIRED[fields["incident_type"]] if not fields.get(f)]
    if not fields.get("description"):
        missing.insert(0, "description")
    return {
        "fields": fields,
        "missing": missing,
        "images_received": len(images),
        "images_read": bool(ai) and bool(images),
        "engine": engine,
        "language": lang,
    }
