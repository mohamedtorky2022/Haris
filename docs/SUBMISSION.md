# «حارس» · Haris — نص التسليم · Submission text

> نسخة تجريبية لهاكاثون الذكاء الاصطناعي للأمن 2026. لوحة الجهة المختصة نموذج تجريبي، وليست تابعة لشرطة أبوظبي أو لأي جهة حكومية.
> A demo for the AI for Security Hackathon 2026. The authority dashboard is a mock-up; it is not run by Abu Dhabi Police or any government body.

**الموقع · Live:** https://haris-uae.onrender.com
**واتساب · WhatsApp:** +971 50 312 3535
**الكود · Code:** https://github.com/mohamedtorky2022/Haris
**دليل اللجنة · Judges' guide:** [docs/JUDGES.md](JUDGES.md) · رمز دخول اللوحة يُرسل مع التسليم ولا يُنشر هنا.

---

## بالعربية

### سطر واحد

«حارس» مساعد ذكي على واتساب والويب، يفتح الرابط المشبوه بأمان ويحكم على الموقع نفسه بالذكاء الاصطناعي، ثم يجهّز للجهة المختصة ملف أدلة لإزالة الموقع الوهمي أو حجبه.

### المشكلة

روابط الاحتيال تصل إلى الجميع عبر الرسائل والواتساب، بخمس لغات على الأقل في الإمارات. وأغلب الفحص المتاح يحكم على **شكل** الرابط فقط، فيفوته نطاق جديد اسمه بريء، أو صفحة على منصة مواقع مجانية. وحتى حين يُكشف الموقع، لا يعرف أحد بسرعة مَن يُطلب منه إزالته.

### الحل

1. **يفحص الرابط من شكله:** انتحال اسم جهة معروفة، والامتدادات الخطرة، والروابط المختصرة، والحروف المتشابهة.
2. **يفتح الموقع نفسه بأمان:** يتتبع التحويلات، ويقرأ عمر النطاق من السجلات الرسمية (RDAP)، والشهادة، وقوائم التهديد، وما تطلبه الصفحة (بطاقة، كلمة مرور، رمز تحقق)، والجهة التي تنتحلها. ثم **يقرأ الذكاء الاصطناعي الصفحة** ويحكم عليها، ويشرح السبب بلغة المستخدم. لا يُشغَّل شيء من الصفحة، ويُحذف معرّف الضحية من الرابط قبل الزيارة.
3. **من الكشف إلى الإزالة:** لكل موقع وهمي يجهّز «حارس» للجهة المختصة ملف أدلة: مَن سجّل النطاق ومَن يستضيفه، وبريد الإبلاغ عن الإساءة لدى كلٍّ منهما من السجلات الرسمية، وبصمة SHA-256 للصفحة، وثلاث مسودات: تعليق النطاق، وإزالة الصفحة، وحجبه داخل الدولة. الضابط يراجع ويرسل، و«حارس» لا يرسل شيئاً بنفسه.
4. **الإبلاغ عن الإعلانات الوهمية:** استجابةً لتحذير شرطة أبوظبي في 22 نوفمبر 2026، يكشف «حارس» إعلانات البيع والتأجير الوهمية: سيارة بأقل بكثير من سعر السوق مع عربون قبل المعاينة، أو تأجير دراجات واستراحات وعزب ومخيمات بدفع مقدّم. ويقارن الذكاء الاصطناعي السعر بسعر السوق المعتاد للموديل. وبزر «أبلغ عن إعلان وهمي» يذهب الإعلان إلى رادار الحملات، أو يصبح بلاغاً كاملاً إن دفع المستخدم.
5. **إنذار مبكر قبل أول ضحية:** كل 6 ساعات يقرأ «حارس» سجلات الشهادات العامة، ويمسح الأسماء الشبيهة الأكثر استخداماً في الاحتيال (مثل tamm-fines) لـ13 جهة إماراتية، ويزور ما يجده بأمان، ثم يرتّبه في لوحة الرادار: «عاجل» أو «يستحق النظر»، ولكل نطاق ملف أدلة الإزالة. وجد أول فحص 33 نطاقاً شبيهاً لثلاث جهات، بينها نطاق يشبه «تم» سُجّل قبل يوم واحد.
6. **رقم الاتصال المزيّف:** إن ذكرت الرسالة «ديوا» أو بنكاً وطلبت الاتصال برقم ليس من أرقامه المنشورة، يقول «حارس» ذلك ويعطي الرقم الرسمي، لـ14 جهة أُخذت أرقامها من مواقعها الرسمية. ورسائل المخالفات المرورية باسم «تم» وUAE PASS تُكشف أيضاً.
7. **يكمل الطريق:** بلاغ بالصوت أو الكتابة أو لقطات الشاشة، ولوحة للجهة المختصة توجّه كل بلاغ إلى الفريق المناسب، ورادار يجمع البلاغات المتشابهة في حملة واحدة، وتنبيهات على واتساب.

### الأرقام (مُقاسة على الخادم الحيّ في 23 نوفمبر 2026)

- **0 إنذارات خاطئة** على 23 موقعاً حقيقياً: بنوك، وشرطة، وصفحات دخول، ومواقع أخبار تذكر البنوك.
- **83% من صفحات الاحتيال الحيّة كُشفت** (15 من 18) في قياس 24 نوفمبر على قائمة جديدة لم يُضبط النظام عليها، بعد 43% ثم 52% في الجولتين السابقتين. ومن كل الروابط، الميتة منها أيضاً، **40 من 60 (67%)**، و**صفر إنذارات خاطئة على أكثر 3000 موقع زيارةً في العالم**. أغلب ما فات صفحات تُبنى بالجافاسكريبت على منصات مجانية، وقراءتها تحتاج متصفحاً حقيقياً، وهي أول خطوة في التجربة الميدانية.
- **12 من 12** رسالة احتيال بصياغات جديدة كشفها الذكاء الاصطناعي، والقواعد وحدها 2 من 12.
- **دقة 100% واستدعاء 100%** على 75 رسالة عيّنة (47 احتيالاً و28 حقيقية)، وأمر واحد يقيس مجموعة اللجنة السرية من ملف CSV ويطبع الدقة والاستدعاء وF1 (`python scripts/evaluate.py --file set.csv`).
- **333 اختباراً آلياً.**

### لمن

الجميع: مواطنون ومقيمون وزوار، بالعربية والإنجليزية والأردية والهندية والروسية. وللأطفال إرشاد خاص، ولا يحتاج الزائر هوية إماراتية.

### التقنية

Python وFastAPI، وواجهة جافاسكريبت بسيطة، وGoogle Gemini مع قواعد شفافة تعمل وحدها إن توقف الذكاء الاصطناعي. البيانات الشخصية تُخفى قبل أن يراها النموذج. منشور على Render ويعمل على واتساب عبر Meta Cloud API.

---

## In English

### One line

Haris is an AI assistant on WhatsApp and the web that safely opens a suspicious link, judges the website itself with AI, and gives the authority a ready takedown file to have the fake site removed or blocked.

### The problem

Scam links reach everyone, by SMS and WhatsApp, in at least five languages in the UAE. Most checks judge only what a link **looks like**, so a brand-new domain with an innocent name, or a page on a free website builder, gets through. And when a site is caught, nobody quickly knows whom to ask to take it down.

### The solution

1. **Checks the link itself:** look-alike brand names, risky domain endings, shorteners, look-alike characters.
2. **Opens the website safely:** follows the redirects, reads the domain's age from the official registries (RDAP), the certificate, threat lists, what the page asks for (card, password, one-time code) and whom it imitates. Then **the AI reads the page** and gives a verdict with reasons in the user's language. Nothing on the page runs, and the victim's identifier is stripped from the link first.
3. **From detection to takedown:** for every fake site, the authority gets an evidence file: who registered the domain and who hosts it, each one's abuse contact from the official registries, a SHA-256 of the page, and three drafts: suspend the domain, take the page down, block it inside the UAE. The officer reviews and sends; Haris sends nothing itself.
4. **Reporting fake ads:** following Abu Dhabi Police's warning of 22 November 2026, Haris catches fake sale and rental ads: a car far below the market price with a deposit before viewing, or bikes, rest houses, farms and camps paid in advance. The AI compares the price with the usual market price for the model. "Report a fake ad" sends the ad to the campaign radar, or turns it into a full report if the person paid.
5. **Early warning, before the first victim:** every 6 hours Haris reads the public certificate logs and sweeps the look-alike names scammers use most (such as tamm-fines) for 13 UAE entities, visits what it finds safely, and ranks it on the radar dashboard as "urgent" or "worth a look", each with its takedown evidence file. The first pass found 33 look-alike names for three entities, among them a TAMM look-alike registered the day before.
6. **Fake helplines:** when a message names DEWA or a bank but gives a number that is not one it publishes, Haris says so and gives the official number, for 14 entities whose numbers were taken from their own websites. Traffic-fine messages in the name of TAMM and UAE PASS are caught too.
7. **The whole journey:** a report by voice, text or screenshots; a dashboard that routes each report to the right team; a radar that groups similar reports into one campaign; WhatsApp alerts.

### The numbers (measured on the live server, 23 November 2026)

- **0 false alarms** on 23 real websites: banks, police, sign-in pages, news sites that name banks.
- **83% of live phishing pages caught** (15 of 18) on 24 November, on a new list the system was not tuned on, up from 43% and then 52% in the earlier rounds. Of all links, dead ones included, **40 of 60 (67%)**, and **0 false alarms on the 3,000 most visited sites** in the world. Most misses are pages built by JavaScript on free website builders; reading them needs a headless browser, the first step of a pilot.
- **12 of 12** scams in new wording caught with the AI; rules alone 2 of 12.
- **100% precision and 100% recall** on 75 sample messages (47 scams, 28 genuine), and one command measures the committee's hidden set from a CSV file, printing precision, recall and F1 (`python scripts/evaluate.py --file set.csv`).
- **333 automated tests.**

### Who it serves

Everyone: citizens, residents and visitors, in Arabic, English, Urdu, Hindi and Russian. Children get their own guidance, and visitors need no Emirates ID.

### Technology

Python and FastAPI, a plain-JavaScript front end, Google Gemini with transparent rules that keep working if the AI pauses. Personal data is removed before the model sees anything. Hosted on Render, live on WhatsApp through Meta's Cloud API.

---

## نص فيديو العرض (3 دقائق) · Demo video script

سجّل شاشة الماك بـ QuickTime (File ← New Screen Recording). ولشاشة الآيفون: وصّله بالكابل، ثم في QuickTime اختر File ← New Movie Recording، واختر الآيفون من قائمة الكاميرا بجانب زر التسجيل. أو استخدم واتساب ويب على الماك. اقرأ النص بهدوء، والعمود الأول هو التوقيت.

| الوقت | ما يظهر على الشاشة | ما تقوله |
|---|---|---|
| 0:00 – 0:15 | شعار «حارس» والصفحة الرئيسية | «روابط الاحتيال والإعلانات الوهمية تصل إلى الجميع. و«حارس» لا يكتفي بشكل الرابط: يفتح الموقع نفسه ويحكم عليه، ثم يساعد الجهة المختصة على إزالته.» |
| 0:15 – 0:35 | في المحادثة: الصق رسالة احتيال بنك من دليل اللجنة | «رسالة تنتحل بنكاً. يردّ «حارس» خلال ثوانٍ: خطورة عالية، ولماذا، وماذا تفعل الآن، بلغة المستخدم.» |
| 0:35 – 1:05 | أرسل: «مرحباً، هذا الرابط الذي طلبته: https://haris-uae.onrender.com/demo/go» | «هنا الرسالة بريئة، والرابط لا يثير الشبهة. لكن «حارس» يفتحه بأمان، ويتتبع التحويل، فيجد صفحة بنك تطلب البطاقة وكلمة المرور ورمز التحقق. البنك خيالي، والصفحة تدريبية.» |
| 1:05 – 1:35 | «أبلغ عن إعلان وهمي» ← الصق إعلان البورش من دليل اللجنة ← Instagram ← «لا، لم أدفع» | «حذّرت شرطة أبوظبي قبل أيام من الإعلانات الوهمية. بورش بـ200 ألف درهم وعربون قبل المعاينة: «حارس» يكشفها، ويسأل أين رأيتها، ويرسلها إلى رادار الحملات لتحمي غيرك.» |
| 1:35 – 2:05 | لوحة الجهة المختصة ← رادار الحملات ← «الإعلانات الوهمية فقط» ← ثم «أدلة الإزالة» والصق رابط التدريب | «للضابط: الإعلانات الوهمية مجمّعة برقم المعلن ومنصاتها. ولكل موقع وهمي ملف أدلة: مَن سجّل النطاق ومَن يستضيفه وبريد الإبلاغ من السجلات الرسمية، وثلاث مسودات للإزالة والحجب.» |
| 2:05 – 2:30 | واتساب على الهاتف: أرسل كلمة «بلاغ» وابدأ بلاغاً صوتياً | «والضحية تبلّغ بصوتها أو بلقطة شاشة، فيصل البلاغ إلى الفريق المختص في اللوحة.» |
| 2:30 – 2:50 | شريحة «النسخة الأولية تعمل» | «قسنا على مواقع حيّة: صفر إنذارات خاطئة على 23 موقعاً حقيقياً، و83% كشف على صفحات احتيال حيّة لم يرها النظام من قبل. ونعرف الخطوة التالية: متصفح حقيقي للصفحات المبنية بالجافاسكريبت.» |
| 2:50 – 3:00 | الشعار وروابط الموقع وواتساب | «حارس: درعك الذكي. يحذّرك، يرشدك، يوصّل بلاغك.» |
