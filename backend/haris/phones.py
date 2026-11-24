"""Fake helplines: a message names a UAE bank or authority and gives a number to call that is not theirs.

A common scam needs no link at all: "DEWA: your supply will be cut today, call 055 xxx xxxx", or a
fake "customer service" number found through a search engine or an ad. Haris keeps the numbers each
entity publishes on its own website, and flags a number offered for that entity that is not one of
them. A mobile number or a number from abroad offered as a bank's or an authority's helpline weighs
more: these entities answer on their published landline, 600 or 800 numbers.

Each list was read from the entity's own website on 24 November 2026 (the source is kept beside it).
An entity without a verified list is never judged on its number. Only a number next to a word like
"call", "contact" or "WhatsApp", and shaped like a phone number, is read: a one-time code, an
amount or a date is not a phone number.
"""

from __future__ import annotations

import re

from .sitecheck import BRAND_NAMES

# entity -> (names in Arabic and English, published numbers as written on the site, source page)
OFFICIAL: dict[str, dict] = {
    "dewa": {"ar": "هيئة كهرباء ومياه دبي (ديوا)", "en": "DEWA", "numbers": ("04 601 9999", "991"),
             "source": "https://www.dewa.gov.ae/en/about-us/support-and-points-of-interest/contact-us"},
    "tamm": {"ar": "«تم» (حكومة أبوظبي)", "en": "TAMM (Abu Dhabi Government)", "numbers": ("800 555", "02 815 8888"),
             "source": "https://added.gov.ae/en/contact-us/ded"},
    "uaepass": {"ar": "الهوية الرقمية UAE PASS", "en": "UAE PASS", "numbers": ("600 56 1111",),
                "source": "https://icp.gov.ae/en/uae-pass/"},
    "icp": {"ar": "الهيئة الاتحادية للهوية والجنسية", "en": "ICP", "numbers": ("600 522222",),
            "source": "https://icp.gov.ae/en/contact-us/"},
    "adcb": {"ar": "بنك أبوظبي التجاري", "en": "ADCB",
             "numbers": ("600 50 2030", "600 50 2322", "600 555 000", "600 50 2004", "600 50 8008", "600 56 2626",
                         "600 57 6363", "600 50 3325", "+971 2 621 0090"),
             "source": "https://www.adcb.com/en/ways-to-bank/phone-banking"},
    "emiratesnbd": {"ar": "بنك الإمارات دبي الوطني", "en": "Emirates NBD", "numbers": ("600 54 0000", "600 54 0009", "800 456"),
                    "source": "https://www.emiratesnbd.com/ar/customer-care/complaints"},
    "bankfab": {"ar": "بنك أبوظبي الأول", "en": "First Abu Dhabi Bank",
                "numbers": ("600 52 5500", "+971 2 681 1511", "800 2200", "600 52 2235", "600 560137", "600 500201"),
                "source": "https://www.bankfab.com/en-ae/contact-us"},
    "mashreq": {"ar": "بنك المشرق", "en": "Mashreq",
                "numbers": ("04 424 4444", "800 7748283", "800 44653", "04 424 4653", "800 2278", "04 424 6620",
                            "04 424 4763", "04 424 4550", "04 424 4466"),
                "source": "https://www.mashreq.com/en/uae/customer-care/know-your-rights/"},
    "salik": {"ar": "سالك", "en": "Salik", "numbers": ("800 72545",),
              "source": "https://www.rta.ae/ (Salik top-up announcement, 800-SALIK)"},
    "rta": {"ar": "هيئة الطرق والمواصلات", "en": "RTA", "numbers": ("800 9090", "+971 4 605 1414", "+971 4 284 4444"),
            "source": "https://rta.ae/wps/portal/rta/ae/home/about-rta/contactus"},
    "emiratespost": {"ar": "بريد الإمارات", "en": "Emirates Post", "numbers": ("600 599999",),
                     "source": "https://www.emiratespost.ae/all-services/international-offering"},
    "etisalat": {"ar": "اتصالات e&", "en": "e& (Etisalat)", "numbers": ("101", "800 101", "800 5800", "+971 4 00444101"),
                 "source": "https://www.etisalat.ae/en/system/wst/assets/docs/consumer/general/customer-service-charter-en.pdf"},
    "dubaipolice": {"ar": "شرطة دبي", "en": "Dubai Police", "numbers": ("901", "999", "800 4888"),
                    "source": "https://u.ae/en/information-and-services/justice-safety-and-the-law/handling-emergencies"},
    "adpolice": {"ar": "شرطة أبوظبي", "en": "Abu Dhabi Police", "numbers": ("999", "800 2626"),
                 "source": "https://srv.adpolice.gov.ae/en/aman/Pages/contactus.aspx"},
}

# More ways a message names these entities than the names a web page uses.
EXTRA_NAMES = {"dewa": ("ديوا", "هيئة كهرباء ومياه"), "uaepass": ("الهوية الرقمية", "uae-pass"),
               "icp": ("emirates id", "الهوية الإماراتية", "بطاقة الهوية"), "bankfab": ("بنك ابوظبي الاول",),
               "adcb": ("بنك ابوظبي التجاري",), "emiratesnbd": ("enbd",), "etisalat": ("e&",)}

CALL_WORDS = re.compile(
    r"call|phone|contact|hotline|helpline|customer (?:service|care|support)|whats ?app|dial|\btel\b|number|"
    r"اتصل|اتصال|رقم|هاتف|تواصل|واتس|الخط الساخن|خدمة العملاء|"
    r"کال|فون|رابطہ|नंबर|कॉल|फोन|संपर्क|звон|номер|телефон", re.I)
NUMBER = re.compile(r"(?<![\w+])(\+?\d[\d \-().]{1,18}\d)(?!\d)")
DATE = re.compile(r"^\d{4}[-./]\d{1,2}[-./]\d{1,2}$|^\d{1,2}[-./]\d{1,2}[-./]\d{2,4}$")


def canonical(raw: str) -> str:
    """The number as dialled inside the UAE, without the leading 0 or the country code."""
    digits = re.sub(r"\D", "", raw)
    international = raw.strip().startswith("+") or digits.startswith("00")
    digits = digits[2:] if digits.startswith("00") else digits
    if digits.startswith("971") and (international or len(digits) >= 11):
        digits = digits[3:]
    return digits.lstrip("0")


def kind(raw: str) -> str | None:
    """mobile, landline, service (600/800), short, foreign; None if this is not a phone number."""
    text = raw.strip()
    if DATE.match(text):
        return None
    digits = re.sub(r"\D", "", text)
    international = text.startswith("+") or digits.startswith("00")
    if international and not re.sub(r"^00", "", digits).startswith("971"):
        return "foreign" if len(digits) >= 8 else None
    n = canonical(text)
    if re.fullmatch(r"5\d{8}", n):
        return "mobile"
    if re.fullmatch(r"(?:600\d{6}|800\d{2,8})", n):
        return "service"
    if re.fullmatch(r"[2-79]\d{7}", n) and (text.startswith(("0", "+", "(")) or international):
        return "landline"
    if re.fullmatch(r"\d{3}", n):
        return "short"
    return None


OFFICIAL_CANON = {k: {canonical(n) for n in v["numbers"]} for k, v in OFFICIAL.items()}


def entities(text: str) -> list[str]:
    low = text.lower()
    return [k for k in OFFICIAL if any(n in low for n in BRAND_NAMES.get(k, ()) + EXTRA_NAMES.get(k, ()))]


def check(text: str) -> dict | None:
    """The first number offered for a named entity that is not one of its published numbers."""
    named = entities(text)
    if not named:
        return None
    for m in NUMBER.finditer(text):
        raw = m.group(1)
        around = text[max(0, m.start() - 45):m.start()] + " " + text[m.end():m.end() + 30]
        if not CALL_WORDS.search(around):
            continue
        k = kind(raw)
        if k is None or k == "short":
            continue
        n = canonical(raw)
        if any(n in OFFICIAL_CANON[e] for e in named):
            continue  # the entity's own number
        entity = named[0]
        weight = 30 if k in ("mobile", "foreign") else 20
        return {"entity": entity, "number": raw.strip(), "kind": k, "weight": weight,
                "official": OFFICIAL[entity]["numbers"][0], "source": OFFICIAL[entity]["source"]}
    return None


def label(entity: str, lang: str) -> str:
    return OFFICIAL[entity]["ar" if lang == "ar" else "en"]
