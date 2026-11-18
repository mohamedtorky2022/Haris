"""Step-by-step emergency plans for victims, and official reporting channels.

Contacts were checked against Abu Dhabi Police and Dubai Police announcements
(November 2026). The partner authority should confirm them before launch.
"""

from __future__ import annotations

CONTACTS = [
    {
        "id": "emergency",
        "value": "999",
        "label": {"ar": "الطوارئ (خطر مباشر)", "en": "Emergency (immediate danger)", "ur": "ایمرجنسی (فوری خطرہ)"},
    },
    {
        "id": "aman",
        "value": "8002626",
        "label": {
            "ar": "خدمة «أمان» - شرطة أبوظبي (اتصال مجاني)",
            "en": "Aman service - Abu Dhabi Police (toll-free call)",
            "ur": "امان سروس - ابوظبی پولیس (مفت کال)",
        },
    },
    {
        "id": "aman_sms",
        "value": "2828",
        "label": {"ar": "خدمة «أمان» (رسالة نصية)", "en": "Aman service (SMS)", "ur": "امان سروس (ایس ایم ایس)"},
    },
    {
        "id": "aman_email",
        "value": "aman@adpolice.gov.ae",
        "label": {"ar": "بريد خدمة «أمان»", "en": "Aman service e-mail", "ur": "امان سروس ای میل"},
    },
    {
        "id": "ecrime",
        "value": "https://www.ecrime.ae",
        "label": {
            "ar": "منصة eCrime - شرطة دبي (بلاغ إلكتروني)",
            "en": "eCrime platform - Dubai Police (online report)",
            "ur": "ای کرائم پلیٹ فارم - دبئی پولیس (آن لائن رپورٹ)",
        },
    },
    {
        "id": "dubai_police",
        "value": "901",
        "label": {"ar": "شرطة دبي (غير الطوارئ)", "en": "Dubai Police (non-emergency)", "ur": "دبئی پولیس (غیر ہنگامی)"},
    },
]

PLAYBOOKS: dict[str, dict] = {
    "money_sent": {
        "title": {
            "ar": "دفعت مالاً أو شاركت بيانات بطاقتي أو رمز التحقق",
            "en": "I paid, or shared my card details or a one-time code",
            "ur": "میں نے رقم دی، یا کارڈ کی معلومات یا او ٹی پی دے دیا",
        },
        "steps": {
            "ar": [
                "اتصل ببنكك فوراً على الرقم المكتوب خلف بطاقتك، واطلب إيقاف البطاقة وتجميد العملية.",
                "لا تحذف الرسائل أو المحادثات أو سجل المكالمات.",
                "التقط صوراً للشاشة: الرسالة، والرابط، ورقم المرسل، وإشعار الخصم.",
                "أبلغ الشرطة الآن: كل دقيقة تزيد صعوبة استرجاع المال.",
                "غيّر كلمة مرور تطبيق البنك وبريدك الإلكتروني من جهاز آمن.",
                "توقف عن التواصل مع المحتال تماماً.",
            ],
            "en": [
                "Call your bank now on the number on the back of your card. Ask them to block the card and stop the transaction.",
                "Do not delete the messages, chats or call log.",
                "Take screenshots: the message, the link, the sender's number and the debit alert.",
                "Report to the police now: every minute makes recovery harder.",
                "Change your banking app and e-mail passwords from a safe device.",
                "Stop all contact with the scammer.",
            ],
            "ur": [
                "فوراً کارڈ کی پشت پر لکھے نمبر پر بینک کو فون کریں اور کارڈ بند کروائیں۔",
                "پیغامات، چیٹس یا کال لاگ ڈیلیٹ نہ کریں۔",
                "اسکرین شاٹس لیں: پیغام، لنک، بھیجنے والے کا نمبر اور کٹوتی کا پیغام۔",
                "ابھی پولیس کو رپورٹ کریں: ہر منٹ رقم واپس لینا مشکل بناتا ہے۔",
                "محفوظ ڈیوائس سے بینک ایپ اور ای میل کا پاس ورڈ بدلیں۔",
                "فراڈیے سے ہر رابطہ بند کر دیں۔",
            ],
        },
    },
    "account_hacked": {
        "title": {
            "ar": "تم اختراق حسابي (واتساب، إنستغرام، البريد...)",
            "en": "My account was hacked (WhatsApp, Instagram, e-mail...)",
            "ur": "میرا اکاؤنٹ ہیک ہو گیا (واٹس ایپ، انسٹاگرام، ای میل...)",
        },
        "steps": {
            "ar": [
                "استخدم خيار «نسيت كلمة المرور» أو استعادة الحساب من التطبيق الرسمي.",
                "فعّل التحقق بخطوتين فور استعادة الحساب.",
                "أخبر أصدقاءك وعائلتك ألا يرسلوا مالاً أو رموزاً باسمك.",
                "راجع الأجهزة المتصلة بالحساب وأخرج أي جهاز لا تعرفه.",
                "إن طُلب منك مال لاستعادة الحساب، فلا تدفع وأبلغ الشرطة.",
            ],
            "en": [
                "Use 'Forgot password' or account recovery in the official app.",
                "Turn on two-step verification as soon as you are back in.",
                "Tell friends and family not to send money or codes to anyone using your name.",
                "Check the devices logged in to the account and remove any you do not know.",
                "If someone asks for money to return the account, do not pay. Report it.",
            ],
            "ur": [
                "سرکاری ایپ میں 'پاس ورڈ بھول گئے' یا اکاؤنٹ ریکوری استعمال کریں۔",
                "اکاؤنٹ واپس ملتے ہی دو مرحلہ تصدیق آن کریں۔",
                "دوستوں اور گھر والوں کو بتائیں کہ آپ کے نام پر کسی کو رقم یا کوڈ نہ بھیجیں۔",
                "اکاؤنٹ سے جڑے آلات چیک کریں اور نامعلوم آلات نکال دیں۔",
                "اگر اکاؤنٹ واپس کرنے کے لیے رقم مانگی جائے تو نہ دیں اور رپورٹ کریں۔",
            ],
        },
    },
    "extortion": {
        "title": {
            "ar": "أتعرض لابتزاز أو تهديد بنشر صور أو محادثات",
            "en": "Someone is threatening to publish my photos or chats",
            "ur": "کوئی میری تصاویر یا چیٹس شائع کرنے کی دھمکی دے رہا ہے",
        },
        "steps": {
            "ar": [
                "أنت لست مخطئاً، والمبتز هو من يرتكب الجريمة.",
                "لا تدفع: الدفع لا يوقف الابتزاز بل يزيده غالباً.",
                "لا تحذف المحادثات، والتقط صوراً للشاشة تُظهر الحساب والتهديد.",
                "توقف عن الرد، ولا ترسل أي صور أو مقاطع إضافية.",
                "أبلغ الشرطة الآن. البلاغات تُعامل بسرية.",
                "إن كنت دون 18 عاماً، أخبر أحد والديك أو شخصاً بالغاً تثق به.",
            ],
            "en": [
                "You are not to blame. The person threatening you is committing the crime.",
                "Do not pay: paying rarely ends it and often makes it worse.",
                "Do not delete the chats. Screenshot the account and the threats.",
                "Stop replying, and do not send any more photos or videos.",
                "Report it to the police now. Reports are handled confidentially.",
                "If you are under 18, tell a parent or an adult you trust.",
            ],
            "ur": [
                "آپ قصوروار نہیں ہیں۔ دھمکی دینے والا جرم کر رہا ہے۔",
                "رقم نہ دیں: ادائیگی سے یہ ختم نہیں ہوتا بلکہ بڑھ جاتا ہے۔",
                "چیٹس ڈیلیٹ نہ کریں۔ اکاؤنٹ اور دھمکیوں کے اسکرین شاٹس لیں۔",
                "جواب دینا بند کریں اور مزید تصاویر یا ویڈیو نہ بھیجیں۔",
                "ابھی پولیس کو رپورٹ کریں۔ رپورٹ رازداری سے ہوتی ہے۔",
                "اگر آپ کی عمر 18 سال سے کم ہے تو والدین یا کسی بھروسہ مند بڑے کو بتائیں۔",
            ],
        },
    },
    "identity_shared": {
        "title": {
            "ar": "أرسلت صورة الهوية أو جواز السفر لجهة مشبوهة",
            "en": "I sent my ID or passport to someone suspicious",
            "ur": "میں نے شناختی کارڈ یا پاسپورٹ کسی مشکوک کو بھیج دیا",
        },
        "steps": {
            "ar": [
                "أبلغ الشرطة لتوثيق أن بياناتك قد تُستخدم دون إذنك.",
                "أخبر بنكك واطلب مراقبة أي طلب جديد باسمك.",
                "راقب أي شريحة اتصال أو حساب أو قرض يُفتح باسمك.",
                "احتفظ بنسخة من المحادثة التي أرسلت فيها الوثيقة.",
            ],
            "en": [
                "Report it to the police so it is on record that your documents may be misused.",
                "Tell your bank and ask them to watch for new applications in your name.",
                "Watch for any SIM card, account or loan opened in your name.",
                "Keep a copy of the chat where you sent the document.",
            ],
            "ur": [
                "پولیس کو رپورٹ کریں تاکہ ریکارڈ رہے کہ آپ کی دستاویزات کا غلط استعمال ہو سکتا ہے۔",
                "بینک کو بتائیں اور اپنے نام پر نئی درخواستوں پر نظر رکھنے کو کہیں۔",
                "اپنے نام پر کھلنے والی سم، اکاؤنٹ یا قرض پر نظر رکھیں۔",
                "جس چیٹ میں دستاویز بھیجی اس کی کاپی رکھیں۔",
            ],
        },
    },
    "suspicious_only": {
        "title": {
            "ar": "وصلتني رسالة مشبوهة ولم أتفاعل معها",
            "en": "I got a suspicious message but did not respond",
            "ur": "مجھے مشکوک پیغام ملا لیکن میں نے جواب نہیں دیا",
        },
        "steps": {
            "ar": [
                "أحسنت: لا تضغط على الرابط ولا ترد.",
                "احظر الرقم أو الحساب، واستخدم خيار «الإبلاغ عن رسائل مزعجة» في التطبيق.",
                "أبلغ عنها للشرطة لتحمي غيرك من نفس الحملة.",
                "حذّر عائلتك، وخصوصاً كبار السن.",
            ],
            "en": [
                "Well done: do not tap the link and do not reply.",
                "Block the number or account, and use 'Report spam' in the app.",
                "Report it to the police to protect others from the same campaign.",
                "Warn your family, especially older relatives.",
            ],
            "ur": [
                "بہت اچھا: لنک پر کلک نہ کریں اور جواب نہ دیں۔",
                "نمبر یا اکاؤنٹ بلاک کریں اور ایپ میں 'اسپام رپورٹ کریں' استعمال کریں۔",
                "پولیس کو رپورٹ کریں تاکہ دوسرے لوگ محفوظ رہیں۔",
                "اپنے گھر والوں، خاص طور پر بزرگوں کو خبردار کریں۔",
            ],
        },
    },
}


def contacts(lang: str) -> list[dict]:
    return [{"id": c["id"], "value": c["value"], "label": c["label"][lang]} for c in CONTACTS]


def list_playbooks(lang: str) -> list[dict]:
    return [{"id": key, "title": pb["title"][lang]} for key, pb in PLAYBOOKS.items()]


def get_playbook(playbook_id: str, lang: str) -> dict | None:
    pb = PLAYBOOKS.get(playbook_id)
    if not pb:
        return None
    return {"id": playbook_id, "title": pb["title"][lang], "steps": pb["steps"][lang], "contacts": contacts(lang)}
