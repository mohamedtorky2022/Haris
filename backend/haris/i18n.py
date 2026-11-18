"""User-facing text in Arabic, English and Urdu.

Every reason, piece of advice and label the assistant shows comes from here,
so wording can be reviewed by the partner authority in one place.
"""

from __future__ import annotations

RISK_LABELS = {
    "high": {"ar": "مؤشرات احتيال عالية", "en": "High risk of fraud", "ur": "دھوکہ دہی کا زیادہ خطرہ"},
    "medium": {"ar": "مؤشرات مشبوهة", "en": "Suspicious signs", "ur": "مشکوک علامات"},
    "low": {"ar": "لم نجد مؤشرات واضحة", "en": "No clear warning signs", "ur": "کوئی واضح خطرہ نہیں ملا"},
}

RISK_SUMMARY = {
    "high": {
        "ar": "لا تضغط على أي رابط، ولا ترسل أي بيانات أو أموال.",
        "en": "Do not click any link, and do not send any details or money.",
        "ur": "کسی لنک پر کلک نہ کریں، اور کوئی معلومات یا رقم نہ بھیجیں۔",
    },
    "medium": {
        "ar": "تمهّل، وتحقق من المرسل عبر قناته الرسمية قبل أي خطوة.",
        "en": "Slow down and check the sender through their official channel before doing anything.",
        "ur": "رکیں، اور کچھ بھی کرنے سے پہلے بھیجنے والے کی سرکاری ذریعے سے تصدیق کریں۔",
    },
    "low": {
        "ar": "هذا لا يعني أن الرسالة آمنة تماماً. تحقق دائماً من القناة الرسمية.",
        "en": "This does not mean the message is certainly safe. Always check the official channel.",
        "ur": "اس کا مطلب یہ نہیں کہ پیغام یقینی طور پر محفوظ ہے۔ ہمیشہ سرکاری ذریعے سے تصدیق کریں۔",
    },
}

CATEGORY_LABELS = {
    "otp_theft": {"ar": "سرقة رمز التحقق", "en": "One-time code theft", "ur": "او ٹی پی کی چوری"},
    "bank_impersonation": {"ar": "انتحال صفة بنك", "en": "Bank impersonation", "ur": "بینک کی نقالی"},
    "gov_impersonation": {"ar": "انتحال صفة جهة حكومية", "en": "Government impersonation", "ur": "سرکاری ادارے کی نقالی"},
    "delivery_scam": {"ar": "احتيال الطرود والتوصيل", "en": "Fake delivery", "ur": "جعلی ڈیلیوری"},
    "job_scam": {"ar": "وظيفة وهمية", "en": "Fake job offer", "ur": "جعلی نوکری"},
    "investment_scam": {"ar": "استثمار وهمي", "en": "Fake investment", "ur": "جعلی سرمایہ کاری"},
    "prize_scam": {"ar": "جائزة وهمية", "en": "Fake prize", "ur": "جعلی انعام"},
    "extortion": {"ar": "ابتزاز إلكتروني", "en": "Online extortion", "ur": "آن لائن بلیک میل"},
    "tech_support": {"ar": "دعم فني وهمي", "en": "Fake tech support", "ur": "جعلی ٹیکنیکل سپورٹ"},
    "phishing_link": {"ar": "رابط تصيّد", "en": "Phishing link", "ur": "فشنگ لنک"},
    "romance_scam": {"ar": "احتيال عاطفي", "en": "Romance scam", "ur": "محبت کا جھانسہ"},
    "recovery_scam": {"ar": "احتيال «استرداد الأموال»", "en": "Fake money recovery", "ur": "رقم واپسی کا جعلی وعدہ"},
    "unknown": {"ar": "غير محدد", "en": "Not identified", "ur": "نامعلوم"},
}

REASONS = {
    "romance_money": {
        "ar": "كلام عاطفي مع طلب مال أو تذاكر أو رسوم. هذا أسلوب الاحتيال العاطفي المعروف.",
        "en": "Affectionate words together with a request for money, tickets or fees. This is the classic romance scam.",
        "ur": "پیار بھری باتوں کے ساتھ رقم، ٹکٹ یا فیس کا مطالبہ۔ یہ محبت کے جھانسے کا عام طریقہ ہے۔",
    },
    "romance_profile": {
        "ar": "علاقة عبر الإنترنت مع شخص لم تلتقِ به، أو قصة عمل بعيد (منصة نفط، مهمة عسكرية).",
        "en": "An online relationship with someone never met in person, or a far-away job story (oil rig, military mission).",
        "ur": "کسی ایسے شخص سے آن لائن تعلق جس سے کبھی ملاقات نہیں ہوئی، یا دور کی نوکری کی کہانی۔",
    },
    "recovery_offer": {
        "ar": "تَعِد باسترداد أموال سُرقت منك. هذا احتيال ثانٍ يستهدف الضحايا، والشرطة لا تطلب رسوماً للاسترداد.",
        "en": "It promises to recover money you lost. This is a second scam aimed at victims; police never charge to recover funds.",
        "ur": "یہ کھوئی ہوئی رقم واپس دلانے کا وعدہ کرتا ہے۔ یہ متاثرین کے ساتھ دوسرا فراڈ ہے؛ پولیس رقم واپسی کی فیس نہیں لیتی۔",
    },
    "otp_request": {
        "ar": "تطلب الرسالة رمز التحقق (OTP). الجهات الرسمية لا تطلبه أبداً.",
        "en": "It asks for a one-time code (OTP). Official bodies never ask for it.",
        "ur": "یہ او ٹی پی مانگ رہا ہے۔ سرکاری ادارے کبھی یہ نہیں مانگتے۔",
    },
    "card_details": {
        "ar": "تطلب بيانات البطاقة البنكية.",
        "en": "It asks for bank card details.",
        "ur": "یہ بینک کارڈ کی تفصیلات مانگ رہا ہے۔",
    },
    "account_suspended": {
        "ar": "تهدد بإيقاف حسابك أو بطاقتك لتخيفك.",
        "en": "It threatens to block your account or card to scare you.",
        "ur": "یہ آپ کا اکاؤنٹ یا کارڈ بند کرنے کی دھمکی دے کر ڈرا رہا ہے۔",
    },
    "bank_mention": {
        "ar": "تستخدم اسم بنك.",
        "en": "It uses a bank's name.",
        "ur": "اس میں بینک کا نام استعمال ہوا ہے۔",
    },
    "gov_impersonation": {
        "ar": "تستخدم اسم جهة حكومية أو تتحدث عن مخالفة أو غرامة.",
        "en": "It uses a government body's name or mentions a fine.",
        "ur": "اس میں سرکاری ادارے کا نام یا جرمانے کا ذکر ہے۔",
    },
    "delivery": {
        "ar": "تتحدث عن طرد أو شحنة، وهذا أسلوب احتيال منتشر.",
        "en": "It talks about a parcel or delivery, a very common scam.",
        "ur": "یہ پارسل یا ڈیلیوری کی بات کر رہا ہے، جو عام فراڈ ہے۔",
    },
    "payment_request": {
        "ar": "تطلب منك الدفع أو التحويل.",
        "en": "It asks you to pay or transfer money.",
        "ur": "یہ آپ سے ادائیگی یا رقم بھیجنے کو کہہ رہا ہے۔",
    },
    "small_amount": {
        "ar": "تطلب مبلغاً صغيراً، وهي حيلة لسرقة بيانات بطاقتك.",
        "en": "It asks for a small amount, a trick to steal your card details.",
        "ur": "یہ چھوٹی رقم مانگ رہا ہے، جو کارڈ کی معلومات چرانے کی چال ہے۔",
    },
    "urgency": {
        "ar": "تضغط عليك بالاستعجال حتى لا تفكر.",
        "en": "It rushes you so you do not stop to think.",
        "ur": "یہ آپ کو جلدی کرنے پر مجبور کر رہا ہے تاکہ آپ سوچ نہ سکیں۔",
    },
    "prize": {
        "ar": "تعدك بجائزة لم تشارك في مسابقتها.",
        "en": "It promises a prize you never entered for.",
        "ur": "یہ ایسے انعام کا وعدہ کر رہا ہے جس میں آپ نے حصہ نہیں لیا۔",
    },
    "job_offer": {
        "ar": "عرض عمل سهل أو بدخل مرتفع غير واقعي.",
        "en": "An easy job or unrealistic income.",
        "ur": "آسان نوکری یا غیر حقیقی آمدنی کی پیشکش۔",
    },
    "upfront_fee": {
        "ar": "تطلب رسوماً مقدماً، وجهات التوظيف الحقيقية لا تفعل ذلك.",
        "en": "It asks for an upfront fee. Real employers do not.",
        "ur": "یہ پیشگی فیس مانگ رہا ہے۔ اصلی آجر ایسا نہیں کرتے۔",
    },
    "investment": {
        "ar": "تتحدث عن استثمار أو تداول أو أرباح.",
        "en": "It talks about investment, trading or profits.",
        "ur": "یہ سرمایہ کاری یا منافع کی بات کر رہا ہے۔",
    },
    "guaranteed": {
        "ar": "تعد بأرباح مضمونة، ولا يوجد استثمار حقيقي بأرباح مضمونة.",
        "en": "It promises guaranteed returns. No real investment does.",
        "ur": "یہ یقینی منافع کا وعدہ کر رہا ہے۔ کوئی اصلی سرمایہ کاری ایسا نہیں کرتی۔",
    },
    "extortion_threat": {
        "ar": "تهديد بنشر صور أو مقاطع أو محادثات. هذا ابتزاز وجريمة يعاقب عليها القانون.",
        "en": "A threat to publish photos, videos or chats. This is extortion, a crime.",
        "ur": "تصاویر یا ویڈیو شائع کرنے کی دھمکی۔ یہ بلیک میلنگ اور جرم ہے۔",
    },
    "secrecy": {
        "ar": "تطلب منك ألا تخبر أحداً.",
        "en": "It asks you to tell no one.",
        "ur": "یہ آپ سے کسی کو نہ بتانے کو کہہ رہا ہے۔",
    },
    "remote_access": {
        "ar": "تطلب تثبيت تطبيق يتيح التحكم بجهازك عن بعد.",
        "en": "It asks you to install an app that lets someone control your device.",
        "ur": "یہ ایسی ایپ انسٹال کرنے کو کہہ رہا ہے جس سے کوئی آپ کا فون کنٹرول کر سکے۔",
    },
    "gift_cards": {
        "ar": "تطلب الدفع ببطاقات هدايا، وهي طريقة دفع يفضلها المحتالون.",
        "en": "It asks for payment in gift cards, a scammer favourite.",
        "ur": "یہ گفٹ کارڈ سے ادائیگی مانگ رہا ہے، جو فراڈیوں کا پسندیدہ طریقہ ہے۔",
    },
    "crypto_payment": {
        "ar": "تطلب الدفع بالعملات الرقمية، ويصعب استرجاعها.",
        "en": "It asks for payment in crypto, which is hard to recover.",
        "ur": "یہ کرپٹو میں ادائیگی مانگ رہا ہے، جو واپس لینا مشکل ہے۔",
    },
    "personal_info_request": {
        "ar": "تطلب بيانات شخصية مثل الهوية أو جواز السفر.",
        "en": "It asks for personal details such as your ID or passport.",
        "ur": "یہ شناختی کارڈ یا پاسپورٹ جیسی ذاتی معلومات مانگ رہا ہے۔",
    },
    "link_click": {
        "ar": "تطلب منك الضغط على رابط.",
        "en": "It asks you to click a link.",
        "ur": "یہ آپ سے لنک پر کلک کرنے کو کہہ رہا ہے۔",
    },
    "suspicious_link": {
        "ar": "تحتوي على رابط مشبوه.",
        "en": "It contains a suspicious link.",
        "ur": "اس میں مشکوک لنک ہے۔",
    },
    "official_link": {
        "ar": "الرابط يتبع نطاقاً رسمياً معروفاً.",
        "en": "The link is on a known official domain.",
        "ur": "لنک ایک معروف سرکاری ڈومین کا ہے۔",
    },
}

URL_FLAGS = {
    "brand_lookalike": {
        "ar": "يقلّد اسم جهة معروفة لكنه ليس موقعها الرسمي",
        "en": "imitates a known brand but is not its official site",
        "ur": "معروف ادارے کی نقل ہے لیکن اس کی سرکاری ویب سائٹ نہیں",
    },
    "ip_host": {"ar": "يستخدم رقماً بدل اسم موقع", "en": "uses a raw IP address", "ur": "ویب سائٹ کے نام کی جگہ آئی پی نمبر"},
    "at_symbol": {"ar": "يخفي الوجهة الحقيقية بعلامة @", "en": "hides the real destination with @", "ur": "@ سے اصل منزل چھپاتا ہے"},
    "punycode": {"ar": "يستخدم حروفاً شبيهة لخداع العين", "en": "uses look-alike characters", "ur": "ملتے جلتے حروف استعمال کرتا ہے"},
    "risky_tld": {"ar": "امتداد نطاق يكثر استخدامه في الاحتيال", "en": "a domain ending often used in scams", "ur": "ایسا ڈومین جو اکثر فراڈ میں استعمال ہوتا ہے"},
    "shortener": {"ar": "رابط مختصر يخفي الوجهة", "en": "a short link that hides the destination", "ur": "مختصر لنک جو منزل چھپاتا ہے"},
    "many_hyphens": {"ar": "اسم نطاق فيه شرطات كثيرة", "en": "many hyphens in the domain", "ur": "ڈومین میں بہت سے ڈیش"},
    "many_subdomains": {"ar": "أجزاء كثيرة في اسم النطاق", "en": "many sub-domains", "ur": "بہت سے سب ڈومین"},
    "no_https": {"ar": "اتصال غير مشفّر", "en": "not encrypted (no https)", "ur": "غیر محفوظ کنکشن"},
}

ADVICE = {
    "general": {
        "ar": [
            "لا تشارك رمز التحقق أو بيانات بطاقتك مع أي شخص.",
            "تحقق من الجهة بالاتصال على رقمها الرسمي، وليس الرقم المرسل في الرسالة.",
            "إن كانت الرسالة احتيالية، أبلغ عنها عبر خدمة «أمان» 8002626 أو منصة ecrime.ae.",
        ],
        "en": [
            "Never share your one-time code or card details with anyone.",
            "Check with the organisation on its official number, not the one in the message.",
            "If it is a scam, report it to Aman on 8002626 or at ecrime.ae.",
        ],
        "ur": [
            "اپنا او ٹی پی یا کارڈ کی معلومات کسی کو نہ دیں۔",
            "ادارے کے سرکاری نمبر پر فون کر کے تصدیق کریں، پیغام والے نمبر پر نہیں۔",
            "اگر یہ فراڈ ہے تو امان سروس 8002626 یا ecrime.ae پر رپورٹ کریں۔",
        ],
    },
    "delivery_scam": {
        "ar": ["تتبّع شحنتك من تطبيق شركة الشحن أو موقعها الرسمي فقط."],
        "en": ["Track parcels only in the courier's own app or official website."],
        "ur": ["پارسل صرف کوریئر کی اپنی ایپ یا سرکاری ویب سائٹ سے ٹریک کریں۔"],
    },
    "bank_impersonation": {
        "ar": ["اتصل ببنكك على الرقم المكتوب خلف بطاقتك."],
        "en": ["Call your bank on the number printed on the back of your card."],
        "ur": ["اپنے بینک کو کارڈ کی پشت پر لکھے نمبر پر فون کریں۔"],
    },
    "gov_impersonation": {
        "ar": ["تحقق من المخالفات والرسوم من التطبيقات والمواقع الحكومية الرسمية فقط."],
        "en": ["Check fines and fees only in official government apps and websites."],
        "ur": ["جرمانے اور فیس صرف سرکاری ایپس اور ویب سائٹس پر چیک کریں۔"],
    },
    "otp_theft": {
        "ar": ["رمز التحقق يعني موافقتك على عملية. من يطلبه منك يريد استخدام حسابك."],
        "en": ["A one-time code approves a transaction. Anyone asking for it wants to use your account."],
        "ur": ["او ٹی پی کسی لین دین کی منظوری ہے۔ جو اسے مانگے وہ آپ کا اکاؤنٹ استعمال کرنا چاہتا ہے۔"],
    },
    "job_scam": {
        "ar": ["جهة التوظيف الحقيقية لا تطلب منك رسوماً للحصول على الوظيفة أو التأشيرة."],
        "en": ["Real employers never charge you for a job or a visa."],
        "ur": ["اصلی آجر نوکری یا ویزا کے لیے کبھی پیسے نہیں مانگتے۔"],
    },
    "investment_scam": {
        "ar": ["تحقق من ترخيص المنصة لدى الجهات الرقابية المالية قبل أي استثمار."],
        "en": ["Check that the platform is licensed by a financial regulator before investing."],
        "ur": ["سرمایہ کاری سے پہلے تصدیق کریں کہ پلیٹ فارم مالیاتی ریگولیٹر سے لائسنس یافتہ ہے۔"],
    },
    "prize_scam": {
        "ar": ["الجوائز الحقيقية لا تطلب منك دفع رسوم لاستلامها."],
        "en": ["Real prizes never ask you to pay a fee to claim them."],
        "ur": ["اصلی انعام لینے کے لیے کبھی فیس نہیں دینی پڑتی۔"],
    },
    "extortion": {
        "ar": [
            "لا تدفع ولا تتفاوض، فالدفع لا يوقف الابتزاز.",
            "لا تحذف المحادثات، واحتفظ بلقطات الشاشة كأدلة.",
            "أبلغ الشرطة فوراً، ولست وحدك. البلاغ يُعامل بسرية.",
        ],
        "en": [
            "Do not pay or negotiate. Paying does not stop extortion.",
            "Do not delete the chats. Keep screenshots as evidence.",
            "Report to the police now. You are not alone, and reports are handled confidentially.",
        ],
        "ur": [
            "رقم نہ دیں اور بات نہ کریں۔ ادائیگی سے بلیک میلنگ نہیں رکتی۔",
            "چیٹس ڈیلیٹ نہ کریں۔ اسکرین شاٹس بطور ثبوت رکھیں۔",
            "فوراً پولیس کو رپورٹ کریں۔ آپ اکیلے نہیں ہیں۔",
        ],
    },
    "tech_support": {
        "ar": ["لا تثبّت أي تطبيق تحكم عن بعد بطلب من شخص اتصل بك."],
        "en": ["Never install a remote-control app because a caller asked you to."],
        "ur": ["کسی کال کرنے والے کے کہنے پر ریموٹ کنٹرول ایپ کبھی انسٹال نہ کریں۔"],
    },
    "romance_scam": {
        "ar": ["لا ترسل مالاً لشخص لم تقابله وجهاً لوجه، مهما كانت القصة مؤثرة.", "اطلب مكالمة فيديو مباشرة، وتحدث مع شخص تثق به قبل أي قرار."],
        "en": ["Never send money to someone you haven't met in person, however moving the story.", "Ask for a live video call, and talk to someone you trust before deciding anything."],
        "ur": ["جس سے آمنے سامنے نہیں ملے اسے کبھی رقم نہ بھیجیں، کہانی جتنی بھی دکھ بھری ہو۔", "لائیو ویڈیو کال کا کہیں، اور فیصلے سے پہلے کسی بھروسہ مند سے بات کریں۔"],
    },
    "recovery_scam": {
        "ar": ["لا تدفع أي رسوم لاسترداد أموالك. تابع بلاغك مع الشرطة مباشرة عبر «أمان» 8002626 أو ecrime.ae."],
        "en": ["Never pay a fee to get your money back. Follow up your case with the police directly: Aman 8002626 or ecrime.ae."],
        "ur": ["رقم واپس لینے کے لیے کبھی فیس نہ دیں۔ اپنا کیس براہ راست پولیس سے دیکھیں: امان 8002626 یا ecrime.ae۔"],
    },
    "phishing_link": {
        "ar": ["اكتب عنوان الموقع الرسمي بنفسك بدلاً من الضغط على الرابط."],
        "en": ["Type the official website address yourself instead of tapping the link."],
        "ur": ["لنک پر کلک کرنے کے بجائے سرکاری ویب سائٹ کا پتہ خود لکھیں۔"],
    },
}


def t(table: dict, key: str, lang: str):
    entry = table.get(key, {})
    return entry.get(lang) or entry.get("en") or key
