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
    "harassment": {
        "title": {
            "ar": "أتعرض لتنمّر أو تحرش أو سبّ وتشهير على الإنترنت",
            "en": "I'm being bullied, harassed or insulted online",
            "ur": "مجھے آن لائن تنگ، ہراساں یا بدنام کیا جا رہا ہے",
        },
        "steps": {
            "ar": [
                "لا ترد بالإساءة نفسها، فالرد المسيء قد يُحسب عليك أيضاً.",
                "التقط صوراً للشاشة تُظهر الحساب والتاريخ والكلام المسيء، ولا تحذفها.",
                "احظر الحساب، واستخدم خيار «الإبلاغ» في التطبيق نفسه.",
                "السب والتشهير والتحرش عبر الإنترنت جرائم يعاقب عليها القانون في الإمارات، فأبلغ الشرطة.",
                "إن كنت دون 18 عاماً، أخبر أحد والديك أو معلماً تثق به.",
                "إن كان في الكلام تهديد بإيذائك، اتصل بالطوارئ 999.",
            ],
            "en": [
                "Don't answer abuse with abuse: an insulting reply can count against you too.",
                "Screenshot the account, the date and the abusive words, and don't delete them.",
                "Block the account and use the app's own 'Report' option.",
                "Online insults, defamation and harassment are crimes under UAE law. Report it to the police.",
                "If you are under 18, tell a parent or a teacher you trust.",
                "If there is a threat to hurt you, call 999.",
            ],
            "ur": [
                "بدتمیزی کا جواب بدتمیزی سے نہ دیں، ایسا جواب آپ کے خلاف بھی جا سکتا ہے۔",
                "اکاؤنٹ، تاریخ اور توہین آمیز الفاظ کے اسکرین شاٹس لیں اور انہیں ڈیلیٹ نہ کریں۔",
                "اکاؤنٹ بلاک کریں اور ایپ میں 'رپورٹ' کا آپشن استعمال کریں۔",
                "متحدہ عرب امارات کے قانون میں آن لائن گالی، بدنامی اور ہراسانی جرم ہیں۔ پولیس کو رپورٹ کریں۔",
                "اگر آپ کی عمر 18 سال سے کم ہے تو والدین یا کسی بھروسہ مند استاد کو بتائیں۔",
                "اگر نقصان پہنچانے کی دھمکی ہو تو 999 پر کال کریں۔",
            ],
        },
    },
    "impersonation": {
        "title": {
            "ar": "أحدهم أنشأ حساباً مزيفاً باسمي أو بصورتي",
            "en": "Someone made a fake account with my name or photo",
            "ur": "کسی نے میرے نام یا تصویر سے جعلی اکاؤنٹ بنایا",
        },
        "steps": {
            "ar": [
                "التقط صوراً للشاشة للحساب المزيف ورابطه واسم المستخدم.",
                "أبلغ عن الحساب في التطبيق باختيار «انتحال شخصية»، واطلب من أصدقائك الإبلاغ عنه أيضاً.",
                "انشر من حسابك الحقيقي أن هناك حساباً مزيفاً، وأنك لا تطلب مالاً أو رموزاً من أحد.",
                "إن طلب الحساب المزيف أموالاً من أي شخص، فأبلغ الشرطة فوراً.",
                "اجعل صورك وقائمة أصدقائك خاصة، وفعّل التحقق بخطوتين.",
            ],
            "en": [
                "Screenshot the fake account, its link and its username.",
                "Report it in the app as 'impersonation', and ask your friends to report it too.",
                "Post from your real account that a fake one exists and that you never ask anyone for money or codes.",
                "If the fake account asked anyone for money, report it to the police now.",
                "Make your photos and friends list private, and turn on two-step verification.",
            ],
            "ur": [
                "جعلی اکاؤنٹ، اس کے لنک اور یوزرنیم کے اسکرین شاٹس لیں۔",
                "ایپ میں اسے 'نقالی' کے طور پر رپورٹ کریں اور دوستوں سے بھی رپورٹ کروائیں۔",
                "اپنے اصلی اکاؤنٹ سے بتائیں کہ جعلی اکاؤنٹ موجود ہے اور آپ کسی سے رقم یا کوڈ نہیں مانگتے۔",
                "اگر جعلی اکاؤنٹ نے کسی سے رقم مانگی ہے تو فوراً پولیس کو رپورٹ کریں۔",
                "اپنی تصاویر اور دوستوں کی فہرست پرائیویٹ کریں اور دو مرحلہ تصدیق آن کریں۔",
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
    "business_fraud": {
        "title": {
            "ar": "شركتي دفعت فاتورة مزيفة أو حوّلت مالاً بطلب من «المدير» أو «المورّد»",
            "en": "My business paid a fake invoice or a transfer asked for by the 'boss' or a 'supplier'",
            "ur": "میرے کاروبار نے جعلی انوائس یا 'باس' یا 'سپلائر' کے کہنے پر رقم بھیج دی",
        },
        "steps": {
            "ar": [
                "اتصل ببنك الشركة فوراً، واطلب استدعاء التحويل وتجميده لدى البنك المستلم.",
                "اتصل بالمورّد أو المدير على رقم تعرفه مسبقاً، لا على الرقم أو البريد الموجود في الطلب.",
                "احتفظ بالرسائل كاملة مع عناوين البريد والفاتورة وإيصال التحويل.",
                "غيّر كلمات مرور بريد الشركة وفعّل التحقق بخطوتين، فقد يكون البريد مخترقاً.",
                "أبلغ الشرطة الآن: كل ساعة تقلل فرصة استرجاع المبلغ.",
                "اعتمد قاعدة دائمة: أي تغيير في الحساب البنكي لمورّد يُؤكَّد بمكالمة هاتفية.",
            ],
            "en": [
                "Call the company's bank now and ask them to recall the transfer and freeze it at the receiving bank.",
                "Call the supplier or manager on a number you already know, not the number or e-mail in the request.",
                "Keep the full messages with e-mail addresses, the invoice and the transfer receipt.",
                "Change the company e-mail passwords and turn on two-step verification: the mailbox may be hacked.",
                "Report it to the police now: every hour lowers the chance of getting the money back.",
                "Make it a rule: any change to a supplier's bank details is confirmed by a phone call.",
            ],
            "ur": [
                "فوراً کمپنی کے بینک کو فون کریں اور ٹرانسفر واپس منگوانے اور وصول کرنے والے بینک میں روکنے کا کہیں۔",
                "سپلائر یا مینیجر کو پہلے سے معلوم نمبر پر فون کریں، درخواست میں دیے گئے نمبر یا ای میل پر نہیں۔",
                "پورے پیغامات، ای میل ایڈریس، انوائس اور ٹرانسفر کی رسید محفوظ رکھیں۔",
                "کمپنی کی ای میل کے پاس ورڈ بدلیں اور دو مرحلہ تصدیق آن کریں، ای میل ہیک ہو سکتی ہے۔",
                "ابھی پولیس کو رپورٹ کریں: ہر گھنٹہ رقم واپس ملنے کا امکان کم کرتا ہے۔",
                "اصول بنائیں: سپلائر کے بینک اکاؤنٹ میں کوئی بھی تبدیلی فون کال سے تصدیق ہو۔",
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
