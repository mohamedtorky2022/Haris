"""Scam signals in Arabic, English and Urdu.

Each signal is a set of phrase groups. A signal fires when every group has a
match and no `unless` phrase is present (so "never share this code" does not
count as a request for the code). Phrases are written naturally and
normalised with the same function as the incoming text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .text import normalize


@dataclass(frozen=True)
class Signal:
    code: str
    weight: int
    groups: tuple[tuple[str, ...], ...]
    category: str | None = None
    unless: tuple[str, ...] = ()


SIGNALS: tuple[Signal, ...] = (
    Signal(
        "otp_request", 35, category="otp_theft",
        groups=(
            ("رمز", "الرمز", "كود", "otp", "verification code", "code", "pin", "کوڈ", "او ٹی پی"),
            ("ارسل", "أرسل", "ابعث", "شارك", "اعطني", "أعطني", "زودنا", "قل لي", "اخبرني", "send", "share",
             "tell me", "give", "provide", "reply with", "بھیجیں", "بتائیں", "دیں"),
        ),
        unless=("لا تشارك", "لا تعط", "لا تخبر", "لا تفصح", "do not share", "don't share", "never share",
                "never ask", "will never", "شیئر نہ", "نہ بتائیں", "کسی کو نہ"),
    ),
    Signal("card_details", 25, groups=((
        "رقم البطاقة", "بيانات البطاقة", "معلومات البطاقة", "cvv", "card number", "card details", "expiry date",
        "تاريخ الانتهاء", "کارڈ نمبر", "کارڈ کی تفصیل"),)),
    Signal(
        "account_suspended", 20, category="bank_impersonation",
        groups=(
            ("حسابك", "بطاقتك", "حسابكم", "your account", "your card", "آپ کا اکاؤنٹ", "آپ کا کارڈ"),
            ("إيقاف", "موقوف", "تعليق", "معلق", "محظور", "حظر", "تجميد", "إغلاق", "blocked", "suspended",
             "locked", "frozen", "deactivated", "معطل", "بند"),
        ),
    ),
    Signal("bank_mention", 10, category="bank_impersonation", groups=((
        "بنك", "مصرف", "bank", "بینک", "emirates nbd", "adcb", "mashreq", "الإمارات دبي الوطني",
        "أبوظبي التجاري", "أبوظبي الأول"),)),
    Signal("delivery", 15, category="delivery_scam", groups=((
        "شحنة", "شحنتك", "طرد", "التوصيل", "عنوان غير مكتمل", "رسوم الشحن", "parcel", "package", "shipment",
        "delivery", "courier", "redelivery", "emirates post", "aramex", "dhl", "fedex", "البريد", "پارسل",
        "ڈیلیوری"),)),
    Signal("gov_impersonation", 15, category="gov_impersonation", groups=((
        "الشرطة", "شرطة دبي", "شرطة أبوظبي", "وزارة الداخلية", "الهوية والجنسية", "الجمارك", "النيابة",
        "المحكمة", "مخالفة", "غرامة", "police", "ministry of interior", "icp", "customs", "court", "fine",
        "violation", "پولیس", "جرمانہ", "عدالت"),)),
    Signal("payment_request", 15, groups=((
        "ادفع", "سدد", "سداد", "دفع", "تحويل", "حول المبلغ", "رسوم", "pay", "payment", "fee", "transfer", "settle",
        "ادائیگی", "ادا کریں", "فیس", "رقم بھیجیں"),)),
    Signal("urgency", 15, groups=((
        "فورا", "فوراً", "حالا", "عاجل", "خلال 24 ساعة", "خلال ساعة", "خلال ساعتين", "اليوم فقط", "آخر فرصة",
        "آخر تحذير", "قبل فوات", "urgent", "immediately", "within 24 hours", "within 2 hours", "final notice",
        "last chance", "act now", "today only", "asap", "فوری", "ابھی", "آخری موقع", "24 گھنٹے"),)),
    Signal("prize", 25, category="prize_scam", groups=((
        "مبروك", "فزت", "ربحت", "جائزة", "الفائز", "congratulations", "you won", "you have won", "winner",
        "prize", "lucky draw", "مبارک ہو", "انعام", "جیت"),)),
    Signal("job_offer", 15, category="job_scam", groups=((
        "وظيفة", "فرصة عمل", "عمل من المنزل", "دوام جزئي", "راتب", "دخل يومي", "تقييم المنتجات", "job",
        "work from home", "part-time", "part time", "salary", "daily income", "earn", "hiring", "like videos",
        "rate products", "نوکری", "ملازمت", "تنخواہ", "گھر سے کام"),)),
    Signal("upfront_fee", 20, category="job_scam", groups=((
        "رسوم التأشيرة", "رسوم التسجيل", "رسوم المعاملة", "مبلغ تأمين", "دفعة مقدمة", "رسوم مقدمة", "عربون",
        "visa fee", "registration fee", "processing fee", "security deposit", "pay a deposit", "upfront fee",
        "ویزا فیس", "رجسٹریشن فیس"),)),
    Signal("investment", 20, category="investment_scam", groups=((
        "استثمار", "أرباح", "عائد", "تداول", "فوركس", "عملات رقمية", "investment", "invest", "profit",
        "returns", "trading", "forex", "crypto", "سرمایہ کاری", "منافع"),)),
    Signal("guaranteed", 15, category="investment_scam", groups=((
        "مضمون", "مضمونة", "بدون مخاطرة", "ضاعف", "guaranteed", "risk-free", "risk free", "double your",
        "گارنٹی", "یقینی منافع"),)),
    Signal(
        "extortion_threat", 45, category="extortion",
        groups=(
            ("صورك", "صورتك", "صور", "فيديو", "فيديوهات", "مقطع", "محادثاتك", "photos", "pictures", "video",
             "videos", "recording", "chats", "تصاویر", "ویڈیو"),
            ("سأنشر", "سانشر", "سأرسلها", "سأرسل", "أفضحك", "افضحك", "فضيحة", "عائلتك", "أهلك", "publish",
             "leak", "expose", "your family", "your friends", "your contacts", "go viral", "بدنام", "گھر والوں"),
        ),
    ),
    Signal("secrecy", 10, groups=((
        "لا تخبر أحد", "لا تخبر احدا", "بيننا فقط", "don't tell anyone", "do not tell anyone",
        "keep this secret", "کسی کو مت بتائیں"),)),
    Signal("remote_access", 25, category="tech_support", groups=((
        "anydesk", "teamviewer", "any desk", "rustdesk", "quicksupport", "remote access", "screen share",
        "مشاركة الشاشة", "حمل التطبيق", "install the app", "download this app", "ایپ ڈاؤن لوڈ"),)),
    Signal("gift_cards", 25, groups=((
        "بطاقات هدايا", "بطاقة هدايا", "بطاقات ايتونز", "gift card", "itunes card", "google play card",
        "steam card", "گفٹ کارڈ"),)),
    Signal("crypto_payment", 15, groups=((
        "usdt", "بيتكوين", "bitcoin", "btc", "wallet address", "crypto wallet", "binance", "عنوان المحفظة"),)),
    Signal(
        "personal_info_request", 20,
        groups=(
            ("رقم الهوية", "صورة الهوية", "جواز السفر", "بيانات شخصية", "emirates id", "passport", "id copy",
             "personal details", "date of birth", "شناختی کارڈ", "پاسپورٹ"),
            ("أرسل", "ارسل", "زودنا", "حدث", "تحديث", "send", "provide", "update", "verify", "confirm",
             "بھیجیں", "تصدیق"),
        ),
    ),
    # Romance scams: affection plus a request for money, often from someone never met in person.
    Signal(
        "romance_money", 20, category="romance_scam",
        groups=(
            ("حبيبتي", "حبيبي", "عزيزتي", "أحبك", "احبك", "يا عمري", "my love", "darling", "sweetheart", "i love you",
             "honey", "babe", "میری جان", "پیار", "محبت"),
            ("أرسل لي", "ارسل لي", "حول لي", "حولي لي", "أحتاج مبلغ", "احتاج مبلغ", "أحتاج مال", "تذكرة", "تذاكر الطيران",
             "المستشفى", "رسوم الجمارك", "send me", "wire me", "transfer me", "lend me", "plane ticket", "flight ticket",
             "hospital", "customs fee", "need money", "مجھے پیسے", "ٹکٹ", "ہسپتال"),
        ),
    ),
    Signal("romance_profile", 15, category="romance_scam", groups=((
        "لم نلتق", "لم نلتقي", "تعارفنا عبر", "تعرفنا على الانترنت", "موقع زواج", "تطبيق تعارف", "سنلتقي قريبا",
        "dating app", "we met online", "never met in person", "oil rig", "deployed overseas", "peacekeeping mission",
        "un doctor", "ڈیٹنگ ایپ", "آن لائن ملے"),)),
    # Recovery scams target people who were already scammed.
    Signal("recovery_offer", 30, category="recovery_scam", groups=((
        "استرداد أموالك", "استرجاع أموالك", "نسترجع أموالك", "نسترد أموالك", "استعادة أموالك", "استرداد المبلغ المسروق",
        "recover your money", "recover your funds", "recover lost funds", "fund recovery", "funds recovery",
        "get your money back", "asset recovery", "recovery agent", "رقم واپس دلا", "پیسے واپس دلا"),)),
    Signal("link_click", 5, groups=((
        "اضغط", "انقر", "افتح الرابط", "الرابط", "click", "tap", "visit", "follow the link", "link below",
        "لنک", "کلک"),)),
)

SMALL_AMOUNT = re.compile(
    r"(?<![\d.,])\d{1,2}(?:[.,]\d{1,2})?\s?(?:درهم|دراهم|درہم|aed|dhs|dh)\b"
    r"|\b(?:aed|dhs)\s?\d{1,2}(?:[.,]\d{1,2})?(?!\d|[.,]\d)",
    re.IGNORECASE,
)
SMALL_AMOUNT_WEIGHT = 10

# Combinations that are much more telling together than apart.
COMBOS: tuple[tuple[tuple[str, ...], int], ...] = (
    (("prize", "payment_request"), 20),
    (("job_offer", "upfront_fee"), 10),
    (("extortion_threat", "payment_request"), 10),
    (("romance_money", "romance_profile"), 20),
    (("recovery_offer", "payment_request"), 15),
    (("recovery_offer", "gov_impersonation"), 10),
)


def _alt_to_regex(phrase: str) -> str:
    norm = re.escape(normalize(phrase))
    start = r"\b" if phrase[:1].isascii() and phrase[:1].isalnum() else ""
    end = r"\b" if phrase[-1:].isascii() and phrase[-1:].isalnum() else ""
    return f"{start}{norm}{end}"


def _compile(phrases: tuple[str, ...]) -> re.Pattern:
    return re.compile("|".join(_alt_to_regex(p) for p in phrases))


_COMPILED = [
    (signal, [_compile(g) for g in signal.groups], _compile(signal.unless) if signal.unless else None)
    for signal in SIGNALS
]


def match_signals(normalized_text: str) -> list[Signal]:
    hits = []
    for signal, groups, unless in _COMPILED:
        if unless and unless.search(normalized_text):
            continue
        if all(g.search(normalized_text) for g in groups):
            hits.append(signal)
    return hits
