"""Scam signals in Arabic, English, Urdu, Hindi and Russian.

Each signal is a set of phrase groups. A signal fires when every group has a
match and no `unless` phrase is present (so "never share this code" does not
count as a request for the code). Phrases are written naturally and
normalised with the same function as the incoming text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

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
        "مخالفات مرورية", "مخالفة مرورية", "سداد المخالفات", "traffic fine", "traffic fines", "unpaid fine",
        "تطبيق تم", "منصة تم", "tamm", "uae pass", "uaepass", "الهوية الرقمية", "salik",
        "violation", "پولیس", "جرمانہ", "عدالت"),)),
    Signal("payment_request", 15, groups=((
        "ادفع", "سدد", "سداد", "دفع", "تحويل", "حول المبلغ", "رسوم", "pay", "payment", "fee", "transfer", "settle",
        "ادائیگی", "ادا کریں", "فیس", "رقم بھیجیں"),),
        # Paying in cash when the parcel arrives, or at the camp on arrival, is the safe way to pay, not a red flag.
        unless=("cash on delivery", "pay on delivery", "الدفع عند الاستلام", "دفع عند الاستلام", "ڈیلیوری پر ادائیگی",
                "الدفع عند الوصول", "ادفع عند الوصول", "الدفع في الموقع", "pay on arrival", "payment on arrival",
                "pay at the venue", "payment is at the venue", "payment at the venue", "pay at the camp",
                "عند نقل الملكية", "عند التنازل", "in the rta", "at the transfer of ownership", "when ownership is transferred")),
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
        "رسوم التأشيرة", "رسوم التسجيل", "رسوم المعاملة", "مبلغ تأمين", "دفعة مقدمة", "رسوم مقدمة",
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
    # Fake ads, for renting or selling. Abu Dhabi Police warned on 22 November 2026 about fake ads for renting
    # motorbikes, rest houses, farms and desert camps, with a booking link and payment in advance; the same trick
    # sells cars far below the market price and asks a deposit "to hold the car" before anyone sees it.
    # An offer mentioned alone is not a warning (a genuine booking or listing says the same words); it adds up
    # with money asked in advance, a price below the market, transfer-only payment or a link.
    Signal("rental_ad", 15, groups=(
        ("تأجير", "للتأجير", "للإيجار", "ايجار", "إيجار", "استئجار", "حجز", "احجز", "للحجز", "rent", "rental", "for hire",
         "hire", "booking", "book now", "book your", "reserve", "کرایہ", "کرائے", "بکنگ"),
        ("دراجة نارية", "دراجات نارية", "دراجات", "دباب", "دبابات", "بقي", "باجي", "قاري", "استراحة", "استراحات",
         "عزبة", "عزب", "مزرعة", "مخيم", "مخيمات", "كشتة", "كشته", "خيمة", "خيام", "شاليه", "شاليهات", "كرفان",
         "سيارة", "سيارات", "سياره", "motorbike", "motorcycle", "quad bike", "atv", "dune buggy", "buggy", "rest house",
         "resthouse", "desert camp", "campsite", "camping", "camp", "chalet", "farm stay", "farmhouse", "caravan",
         "car", "cars", "suv", "موٹر سائیکل", "کیمپ", "فارم ہاؤس", "گاڑی"),
    )),
    Signal("sale_ad", 10, groups=(
        ("للبيع", "بيع", "أبيع", "ابيع", "معروضة", "معروض", "بسعر", "سعرها", "سعره", "for sale", "selling", "sell",
         "asking price", "price", "برائے فروخت", "فروخت"),
        ("سيارة", "سيارات", "سياره", "موديل", "بورش", "مرسيدس", "بي ام", "لكزس", "رنج روفر", "رينج روفر",
         "لاندكروزر", "لاند كروزر", "باترول", "جي كلاس", "كامري", "تويوتا", "نيسان", "دراجة نارية", "دباب",
         "car", "suv", "model", "mileage", "porsche", "mercedes", "bmw", "lexus", "range rover", "land cruiser", "patrol",
         "g class", "g-class", "camry", "toyota", "nissan", "audi", "ferrari", "lamborghini", "motorbike", "motorcycle",
         "گاڑی", "موٹر سائیکل"),
    )),
    # Weak alone (schools, salons and real agents take deposits too); strong next to an ad (combos below).
    Signal("advance_booking", 5, groups=((
        "عربون", "دفعة مقدمة", "دفعه مقدمه", "الدفع مقدما", "ادفع مقدما", "دفع مقدم", "مبلغ الحجز", "رسوم الحجز",
        "لتأكيد الحجز", "لتاكيد الحجز", "تأكيد الحجز بالدفع", "حجز مقدم", "deposit", "advance payment",
        "pay in advance", "pay upfront", "upfront payment", "booking fee", "reservation fee", "to confirm your booking",
        "to confirm the booking", "secure your booking", "hold the car", "token amount", "ایڈوانس", "بکنگ فیس", "بکنگ کنفرم",
        "بیعانہ"),),
        unless=("الدفع عند الوصول", "ادفع عند الوصول", "الدفع في الموقع", "عند توقيع العقد", "عند التوقيع",
                "في المكتب", "في مكتب", "عند الاستلام", "pay on arrival", "pay at the venue", "pay at the camp",
                "at signing", "when you sign", "in person", "at our office", "at the office", "no deposit",
                "بدون عربون", "تم تأكيد حجزك", "your booking is confirmed", "booking confirmed", "refunded")),
    # Shopping and rental scams: a deposit before seeing the item or flat, transfer-only payment, unreal prices.
    Signal("deposit_to_reserve", 25, category="shopping_scam", groups=((
        "عربون لحجز", "عربون للحجز", "عربون قبل المعاينة", "قبل المعاينة", "بدون معاينة", "دون معاينة",
        "احجز الشقة", "لحجز الشقة", "deposit to reserve", "deposit to hold", "before viewing",
        "without viewing", "send the deposit", "token money",
        "دیکھے بغیر", "بکنگ کے لیے ایڈوانس"),)),
    Signal("owner_abroad", 15, category="shopping_scam", groups=((
        "المالك مسافر", "المالك خارج الدولة", "انا مسافر حاليا", "owner is abroad", "landlord is abroad", "i am abroad",
        "i'm abroad", "currently overseas", "مالک ملک سے باہر"),)),
    Signal("transfer_only", 20, category="shopping_scam", groups=((
        "تحويل فقط", "تحويل بنكي فقط", "لا يوجد دفع عند الاستلام", "لا يوجد استلام نقدي", "الدفع مقدما فقط",
        "bank transfer only", "transfer only", "no cash on delivery", "no cod", "pay in advance only", "advance payment only",
        "صرف ایڈوانس", "صرف ٹرانسفر"),)),
    Signal("too_good_deal", 15, category="shopping_scam", groups=((
        "خصم 90", "خصم 80", "تصفية كاملة", "نصف السعر", "ارخص من السوق", "أرخص من السوق", "أقل من سعر السوق",
        "اقل من سعر السوق", "تحت سعر السوق", "سعر حرق", "بسعر حرق", "للبيع السريع", "بيع سريع", "مستعجل على البيع",
        "بداعي السفر", "لداعي السفر", "90% off", "80% off", "clearance sale", "half price", "below market price",
        "below market", "under market price", "urgent sale", "quick sale", "must sell", "too good to miss", "آدھی قیمت",
        "مارکیٹ سے کم"),)),
    # Fake charity appeals: donations to a personal account or an unofficial link.
    Signal(
        "charity_appeal", 20, category="charity_scam",
        groups=(
            ("تبرع", "تبرعك", "صدقة", "زكاة", "كفالة يتيم", "ساهم في علاج", "donate", "donation", "charity",
             "help the victims", "orphans", "zakat", "sadaqah", "عطیہ", "خیرات", "زکوٰۃ"),
            ("رقم الحساب", "حساب شخصي", "حول", "تحويل", "ارسل", "الرابط", "send", "transfer", "link", "account number",
             "bank account", "iban", "بھیجیں", "اکاؤنٹ نمبر"),
        ),
    ),
    Signal("personal_account", 15, groups=((
        "حساب شخصي", "حسابي الشخصي", "باسمي الشخصي", "personal account", "my own account", "ذاتی اکاؤنٹ"),)),
    # Visa and residency scams: guaranteed visas for a fee, often aimed at workers.
    Signal(
        "visa_offer", 25, category="visa_scam",
        groups=(
            ("تأشيرة", "تاشيرة", "فيزا عمل", "فيزا زيارة", "إقامة", "اقامة", "الاقامة الذهبية", "golden visa",
             "work visa", "visit visa", "residency", "work permit", "ویزا", "اقامہ", "ورک پرمٹ"),
            ("مضمونة", "مضمون", "بدون شروط", "بدون كفيل", "خلال 24 ساعة", "خلال 48 ساعة", "خلال اسبوع", "guaranteed",
             "no requirements", "without a job", "without sponsor", "in 24 hours", "in 48 hours", "100%", "گارنٹی",
             "یقینی", "بغیر شرط"),
        ),
    ),
    Signal("link_click", 5, groups=((
        "اضغط", "انقر", "افتح الرابط", "الرابط", "click", "tap", "visit", "follow the link", "link below",
        "لنک", "کلک"),)),
)

# Hindi phrases, kept together so a native speaker can review them in one place.
# Each entry adds phrases to the signal's groups in order; HINDI_UNLESS adds exceptions.
HINDI: dict[str, tuple[tuple[str, ...], ...]] = {
    "otp_request": (("ओटीपी", "कोड", "पिन"), ("भेजें", "भेजो", "बताएं", "बताएँ", "बताओ", "शेयर करें", "दे दें")),
    "card_details": (("कार्ड नंबर", "कार्ड की जानकारी", "कार्ड की डिटेल", "सीवीवी", "एक्सपायरी"),),
    "account_suspended": (("आपका खाता", "आपका अकाउंट", "आपका कार्ड"), ("बंद", "ब्लॉक", "निलंबित", "फ्रीज", "फ़्रीज़")),
    "bank_mention": (("बैंक",),),
    "delivery": (("पार्सल", "डिलीवरी", "शिपमेंट", "कूरियर", "पैकेज"),),
    "gov_impersonation": (("पुलिस", "जुर्माना", "चालान", "कस्टम", "अदालत", "मंत्रालय"),),
    "payment_request": (("भुगतान", "पैसे भेजें", "पैसे भेजो", "शुल्क", "फीस", "फ़ीस", "ट्रांसफर", "ट्रांसफ़र"),),
    "urgency": (("तुरंत", "फौरन", "24 घंटे", "आखिरी मौका", "आख़िरी मौका", "जल्दी करें", "आज ही"),),
    "prize": (("बधाई हो", "आपने जीता", "आप जीत गए", "इनाम", "लकी ड्रा", "विजेता"),),
    "job_offer": (("नौकरी", "घर से काम", "पार्ट टाइम", "वेतन", "रोज़ाना कमाई", "रोजाना कमाई", "रोज की कमाई"),),
    "upfront_fee": (("वीज़ा फ़ीस", "वीजा फीस", "रजिस्ट्रेशन फीस", "रजिस्ट्रेशन फ़ीस", "प्रोसेसिंग फीस", "सिक्योरिटी डिपॉजिट"),),
    "investment": (("निवेश", "मुनाफ़ा", "मुनाफा", "ट्रेडिंग", "रिटर्न"),),
    "guaranteed": (("गारंटी", "पक्का मुनाफ़ा", "पक्का मुनाफा", "बिना जोखिम", "पैसा दोगुना"),),
    "extortion_threat": (("तस्वीरें", "फोटो", "फ़ोटो", "वीडियो", "चैट"),
                         ("वायरल", "परिवार को", "घरवालों को", "सबको भेज", "बदनाम", "पोस्ट कर दूंगा", "पोस्ट कर दूँगा")),
    "secrecy": (("किसी को मत बताना", "किसी को न बताएं", "किसी को न बताएँ"),),
    "gift_cards": (("गिफ्ट कार्ड", "गिफ़्ट कार्ड"),),
    "crypto_payment": (("बिटकॉइन", "क्रिप्टो वॉलेट"),),
    "personal_info_request": (("आधार", "पासपोर्ट", "एमिरेट्स आईडी", "पहचान पत्र"),
                              ("भेजें", "भेजो", "अपडेट", "सत्यापित", "वेरिफाई")),
    "link_click": (("क्लिक करें", "लिंक पर", "नीचे दिए लिंक"),),
    "romance_money": (("मेरी जान", "जानू", "प्यार", "आई लव यू", "डार्लिंग"),
                      ("पैसे भेजो", "पैसे भेज दो", "पैसों की ज़रूरत", "पैसों की जरूरत", "टिकट", "अस्पताल", "कस्टम फीस")),
    "romance_profile": (("ऑनलाइन मिले", "कभी नहीं मिले", "डेटिंग ऐप"),),
    "recovery_offer": (("पैसे वापस दिला", "रकम वापस दिला", "पैसा वापस दिला", "रिकवरी एजेंट"),),
    "deposit_to_reserve": (("देखने से पहले एडवांस", "बिना देखे", "बुकिंग के लिए एडवांस"),),
    "rental_ad": (("किराए", "किराये", "किराया", "बुकिंग", "बुक करें"),
                  ("बाइक", "मोटरसाइकिल", "क्वाड बाइक", "बग्गी", "कैंप", "शिविर", "शैले", "फार्म हाउस", "रेस्ट हाउस", "कार", "गाड़ी")),
    "sale_ad": (("बिक्री", "बेचना", "बेच रहा", "कीमत"), ("कार", "गाड़ी", "मॉडल", "पोर्श", "मर्सिडीज़", "बाइक")),
    "advance_booking": (("एडवांस", "अग्रिम भुगतान", "बुकिंग फीस", "बुकिंग फ़ीस", "बुकिंग कन्फर्म", "डिपॉजिट"),),
    "owner_abroad": (("मालिक विदेश में", "मैं विदेश में हूँ", "मैं विदेश में हूं"),),
    "transfer_only": (("सिर्फ़ ट्रांसफ़र", "सिर्फ ट्रांसफर", "केवल ट्रांसफर", "कैश ऑन डिलीवरी नहीं"),),
    "charity_appeal": (("दान", "चंदा", "ज़कात", "जकात"), ("भेजें", "ट्रांसफर", "खाता नंबर", "लिंक")),
    "personal_account": (("निजी खाता", "मेरे निजी खाते"),),
    "visa_offer": (("वीज़ा", "वीजा", "रेज़िडेंसी", "वर्क परमिट"), ("गारंटी", "पक्का", "बिना शर्त", "24 घंटे में", "48 घंटे में")),
}
HINDI_UNLESS = {
    "otp_request": ("शेयर न करें", "किसी को न बताएं", "किसी को न बताएँ", "कभी नहीं मांग", "कभी नहीं माँग"),
    "payment_request": ("डिलीवरी पर भुगतान", "कैश ऑन डिलीवरी"),
}
# Russian phrases, kept together for review by a native speaker. Matching is on substrings, so a stem
# ("посылк") covers every ending (посылка, посылку, посылки).
RUSSIAN: dict[str, tuple[tuple[str, ...], ...]] = {
    "otp_request": (("код", "смс-код", "пароль из смс", "одноразов"),
                    ("отправьте", "отправь", "сообщите", "назовите", "продиктуйте", "пришлите", "скажите", "введите код")),
    "card_details": (("номер карты", "данные карты", "реквизиты карты", "срок действия", "cvv", "cvc"),),
    "account_suspended": (("ваш счет", "ваша карта", "ваш аккаунт"), ("заблокир", "приостанов", "заморож", "будет закрыт")),
    "bank_mention": (("банк",),),
    "delivery": (("посылк", "доставк", "курьер", "отправлени", "почта"),),
    "gov_impersonation": (("полиция", "штраф", "таможн", "суд", "министерств", "прокуратур"),),
    "payment_request": (("оплат", "заплат", "перевед", "переведите", "пошлин", "сбор"),),
    "urgency": (("срочно", "немедленно", "в течение 24 часов", "последний шанс", "сегодня же", "успейте"),),
    "prize": (("поздравляем", "вы выиграли", "выигрыш", "приз", "розыгрыш", "победител"),),
    "job_offer": (("работа на дому", "подработк", "удаленная работа", "зарплата", "доход в день", "заработок"),),
    "upfront_fee": (("визовый сбор", "оплата визы", "регистрационный взнос", "страховой депозит", "оплата оформления"),),
    "investment": (("инвестиц", "прибыль", "трейдинг", "доходность", "вложени"),),
    "guaranteed": (("гарантированн", "без риска", "удвоить деньги", "100% прибыль"),),
    "extortion_threat": (("фото", "видео", "переписк", "интимн"),
                         ("опубликую", "разошлю", "отправлю родным", "отправлю семье", "выложу", "все узнают")),
    "secrecy": (("никому не говорите", "никому не рассказывайте", "держите в секрете"),),
    "gift_cards": (("подарочн карт", "подарочные карты", "подарочную карту"),),
    "crypto_payment": (("биткоин", "криптокошел", "usdt"),),
    "personal_info_request": (("паспорт", "удостоверение личности", "emirates id", "id карт"),
                              ("отправьте", "пришлите", "обновите", "подтвердите", "верифиц")),
    "link_click": (("перейдите по ссылке", "нажмите на ссылку", "по ссылке ниже"),),
    "romance_money": (("любимая", "любимый", "дорогая", "люблю тебя", "милая"),
                      ("пришли деньги", "отправь деньги", "нужны деньги", "билет", "больниц", "таможенный сбор")),
    "romance_profile": (("познакомились онлайн", "никогда не виделись", "сайт знакомств"),),
    "recovery_offer": (("вернем ваши деньги", "вернуть деньги", "возврат средств", "агент по возврату"),),
    "deposit_to_reserve": (("предоплата до просмотра", "без просмотра", "залог для брони"),),
    "rental_ad": (("аренд", "прокат", "бронир", "забронир", "сдаю", "сдается"),
                  ("мотоцикл", "квадроцикл", "багги", "кемпинг", "лагерь в пустыне", "шале", "ферм", "дом отдыха", "автомобил", "машин")),
    "sale_ad": (("продаю", "продается", "продаётся", "продажа", "цена"), ("автомобил", "машин", "порше", "мерседес", "мотоцикл", "модель")),
    "advance_booking": (("предоплат", "задаток", "оплата брони", "подтвердить бронь", "для подтверждения брони", "депозит"),),
    "owner_abroad": (("владелец за границей", "я сейчас за границей", "хозяин уехал"),),
    "transfer_only": (("только перевод", "только предоплата", "без наложенного платежа"),),
    "charity_appeal": (("пожертв", "благотворител", "закят"), ("отправьте", "переведите", "номер счета", "ссылк")),
    "personal_account": (("личный счет", "на мою карту", "на мой счет"),),
    "visa_offer": (("виза", "визу", "резидентств", "разрешение на работу"), ("гарант", "без условий", "за 24 часа", "за 48 часов")),
}
RUSSIAN_UNLESS = {
    "otp_request": ("никому не сообщайте", "не сообщайте код", "никогда не спрашива", "не передавайте код",
                    "код отслеживания", "трек-код", "трек код"),
    "payment_request": ("оплата при получении", "наложенный платеж"),
}
_EXTRA = (HINDI, RUSSIAN)
_EXTRA_UNLESS = (HINDI_UNLESS, RUSSIAN_UNLESS)


def _with(signal: Signal) -> Signal:
    groups = list(signal.groups)
    for table in _EXTRA:
        for i, more in enumerate(table.get(signal.code, ())):
            if i < len(groups):
                groups[i] = groups[i] + more
    unless = signal.unless + tuple(p for table in _EXTRA_UNLESS for p in table.get(signal.code, ()))
    return replace(signal, groups=tuple(groups), unless=unless)


SIGNALS = tuple(_with(signal) for signal in SIGNALS)

SMALL_AMOUNT = re.compile(
    r"(?<![\d.,])\d{1,2}(?:[.,]\d{1,2})?\s?(?:درهم|دراهم|درہم|दिरहम|дирхам(?:ов|а|ы)?|aed|dhs|dh)\b"
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
    (("deposit_to_reserve", "payment_request"), 10),
    (("deposit_to_reserve", "owner_abroad"), 15),
    (("too_good_deal", "transfer_only"), 15),
    (("rental_ad", "advance_booking"), 30),
    (("rental_ad", "too_good_deal"), 15),
    (("rental_ad", "transfer_only"), 10),
    (("sale_ad", "advance_booking"), 30),
    (("sale_ad", "too_good_deal"), 20),
    (("sale_ad", "deposit_to_reserve"), 15),
    (("sale_ad", "owner_abroad"), 15),
    (("sale_ad", "transfer_only"), 10),
    (("charity_appeal", "personal_account"), 20),
    (("visa_offer", "upfront_fee"), 10),
    (("visa_offer", "payment_request"), 10),
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
