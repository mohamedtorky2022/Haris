/* Haris web chat. Plain JavaScript, no build step, no third-party code.
   Nothing is saved in the browser: the conversation lives only in this page. */
(() => {
  "use strict";

  const UI = {
    ar: {
      name: "حارس",
      status: "مساعد ذكي · ليس جهة رسمية",
      placeholder: "الصق الرسالة المشبوهة هنا...",
      inputLabel: "اكتب رسالتك",
      welcome: "مرحباً، أنا «حارس». أساعدك على كشف الاحتيال الإلكتروني، وأرشدك إن وقعت ضحية له.\n\nلا أحفظ رسائلك، وأخفي بياناتك الشخصية قبل تحليلها.",
      menu: "كيف أساعدك؟",
      check: "افحص رسالة أو رابط",
      help: "تعرضت لاحتيال، ماذا أفعل؟",
      report: "جهّز ملف بلاغ",
      askCheck: "الصق الرسالة أو الرابط أو العرض الذي وصلك، وسأفحصه لك.",
      checkAnother: "افحص رسالة أخرى",
      interacted: "تفاعلت معها",
      reasons: "لماذا؟",
      advice: "ماذا تفعل الآن؟",
      links: "الروابط",
      official: "نطاق رسمي",
      redacted: "أخفيتُ {n} من بياناتك الشخصية قبل التحليل.",
      engineAi: "التحليل: قواعد + ذكاء اصطناعي",
      engineRules: "التحليل: قواعد الكشف",
      pickSituation: "ما الذي حدث معك؟",
      steps: "خطوات الآن، بالترتيب:",
      contacts: "أين تبلّغ:",
      menuBack: "القائمة الرئيسية",
      qType: "لنجهّز ملف البلاغ. ما نوع ما حدث؟",
      qWhen: "متى حدث ذلك؟ اختر، أو اكتب الوقت.",
      qDesc: "اشرح ما حدث بكلماتك: من تواصل معك، وماذا طلب، وماذا فعلت.",
      qAmount: "كم المبلغ الذي فقدته؟ اكتب الرقم، أو اختر «لا يوجد».",
      qMethod: "كيف دفعت؟",
      qIds: "اكتب أرقام المحتال أو روابطه أو حساباته، كل واحد في سطر.",
      qEvidence: "ما الأدلة المتوفرة لديك؟ (لقطات شاشة، إيصال التحويل، رسائل، سجل مكالمات)",
      qSteps: "ماذا فعلت حتى الآن؟",
      skip: "تخطَّ",
      none: "لا يوجد",
      needDesc: "أحتاج وصفاً قصيراً لما حدث حتى يكون البلاغ مفيداً.",
      reportReady: "ملف البلاغ جاهز. الرقم المرجعي: {ref}\n\nقدّمه للشرطة عبر خدمة «أمان» أو منصة eCrime، وأرفق لقطات الشاشة.",
      found: "وجدتُ في وصفك هذه البيانات وأضفتها للبلاغ:",
      view: "عرض البلاغ",
      download: "تنزيل البلاغ",
      print: "طباعة أو حفظ PDF",
      qStory: "احكِ ما حدث بطريقتك: اكتب، أو اضغط الميكروفون وتكلّم، أو أرفق لقطات شاشة للمحادثة أو لإشعار الخصم. كلما ذكرت تفاصيل أكثر، قلّت أسئلتي.",
      qStoryMore: "أضف ما تريد: نصاً، أو كلاماً بالميكروفون، أو لقطات شاشة.",
      dontKnow: "لا أعرف",
      imagesRead: "قرأتُ لقطات الشاشة وأضفت ما وجدته فيها للبلاغ.",
      imagesNotRead: "أرفقتُ لقطات الشاشة كأدلة في الملف. قراءة محتواها تحتاج تفعيل الذكاء الاصطناعي.",
      urgentBank: "إن لم تفعل بعد: اتصل ببنكك الآن على الرقم المكتوب خلف بطاقتك واطلب إيقافها. كل دقيقة مهمة لاسترجاع المال.",
      summaryTitle: "ملخص البلاغ",
      summaryHint: "راجع البيانات، واضغط «تعديل» بجانب أي سطر لتصحيحه.",
      edit: "تعديل",
      createFile: "صحيح، أنشئ الملف",
      addMore: "أضف تفاصيل أو صوراً",
      screenshot: "لقطة شاشة",
      attached: "الأدلة المرفقة",
      attach: "إرفاق لقطة شاشة",
      mic: "تحدّث بدل الكتابة",
      micNote: "خدمة الإملاء في متصفحك تحوّل كلامك إلى نص، ثم يراجعه حارس ويقترح تصحيح الكلمات التي ربما سُمعت خطأً. راجع النص قبل إرساله.",
      dialectQ: "بأي لهجة ستتكلم؟ اختيار لهجتك يجعل الإملاء يفهمك بدقة أكبر.",
      dialectSet: "اللهجة: {name}. يمكنك تغييرها في أي وقت.",
      changeDialect: "تغيير اللهجة",
      polished: "راجعت النص، وهذه كلمات ربما سُمعت خطأً:",
      polishNote: "الأرقام وأرقام الهواتف والروابط لا تتغيّر أبداً.",
      useFixed: "استخدم النص المصحّح",
      keepMine: "أبقِ نصّي كما هو",
      fixedUsed: "تم. النص المصحّح في خانة الكتابة، راجعه ثم أرسله.",
      reportIt: "أبلغ عنها لحماية غيري",
      reportConsent: "سيُرسل إلى رادار الحملات: رقم المرسل ورابطه ونص الرسالة بعد إخفاء أي بيانات شخصية فيها. لن يُرسل أي شيء عنك.",
      sendReport: "أرسل البلاغ",
      cancel: "إلغاء",
      reportThanksFirst: "شكراً، وصل بلاغك. أنت أول من أبلغ عن هذه الرسالة.",
      reportThanks: "شكراً، وصل بلاغك. عدد من أبلغوا عن هذه الحملة حتى الآن: {n}.",
      reportEscalated: "وصلت البلاغات إلى الحد الذي يُرسَل عنده إنذار إلى الجهة المختصة لمراجعتها.",
      reportConfirmed: "هذه الحملة أكّدتها الجهة المختصة، وصدر عنها تحذير رسمي.",
      radarAsk: "الصق الرسالة التي وصلتك وسأرسلها إلى رادار الحملات، حتى تُكتشف الحملة إذا وصلت لآخرين.",
      officialAlerts: "تحذيرات رسمية نشطة",
      howTo: "كيف أستخدم «حارس»؟",
      guideTitle: "«حارس» في ثلاث خطوات",
      guide: [
        ["قبل أن تتفاعل: افحص", "الصق أي رسالة أو رابط مشبوه. يخبرك «حارس» بدرجة الخطورة، ولماذا، وماذا تفعل."],
        ["إن وقعت المشكلة: اتبع الخطة", "اختر حالتك، مثل «دفعت مالاً» أو «اختُرق حسابي»، فتظهر لك خطوات فورية بالترتيب مع أرقام البلاغ الرسمية."],
        ["للتبليغ: احكِ بطريقتك", "اكتب أو تكلّم بلهجتك أو أرفق لقطات شاشة. يسألك «حارس» عن الناقص فقط، ثم يجهّز ملف البلاغ لتقدّمه للشرطة."],
      ],
      guideCommunity: "احمِ غيرك: إذا وصلتك رسالة احتيال ولم تتفاعل معها، اضغط «أبلغ عنها لحماية غيري». كل بلاغ يساعد على كشف الحملة مبكراً، فتعتمد الجهة المختصة تحذيراً يصل للجميع.",
      guidePrivacy: "لا يحفظ «حارس» محادثاتك ولا بياناتك الشخصية، وهو مساعد ذكي وليس جهة رسمية.",
      micError: "تعذّر تشغيل الميكروفون. تأكد من السماح للمتصفح باستخدامه، أو اكتب بدلاً منه.",
      maxImages: "يمكن إرفاق 3 صور كحد أقصى في كل مرة.",
      removeImage: "إزالة الصورة",
      tLessHour: "قبل أقل من ساعة",
      tToday: "اليوم",
      tYesterday: "أمس",
      tOlder: "قبل أكثر من يومين",
      pCard: "بطاقة بنكية",
      pTransfer: "تحويل بنكي",
      pCrypto: "عملات رقمية",
      pGift: "بطاقات هدايا",
      pCash: "نقداً",
      pOther: "طريقة أخرى",
      sBank: "اتصلت بالبنك",
      sCard: "أوقفت البطاقة",
      sNothing: "لم أفعل شيئاً بعد",
      f_incident_type: "نوع الحادثة",
      f_occurred_at: "متى",
      f_description: "ماذا حدث",
      f_amount: "المبلغ",
      f_payment_method: "طريقة الدفع",
      f_scammer_identifiers: "بيانات المحتال",
      f_evidence: "الأدلة",
      f_steps_taken: "ما فعلته",
      error: "تعذّر الاتصال بالخادم. حاول مرة أخرى.",
      tooMany: "طلبات كثيرة. انتظر دقيقة ثم حاول.",
    },
    en: {
      name: "Haris",
      status: "AI assistant · not an official body",
      placeholder: "Paste the suspicious message here...",
      inputLabel: "Type your message",
      welcome: "Hi, I'm Haris. I help you spot online scams, and guide you if you have been a victim.\n\nI don't store your messages, and I hide your personal details before analysing them.",
      menu: "How can I help?",
      check: "Check a message or link",
      help: "I've been scammed, what now?",
      report: "Prepare a police report",
      askCheck: "Paste the message, link or offer you received and I'll check it.",
      checkAnother: "Check another message",
      interacted: "I responded to it",
      reasons: "Why?",
      advice: "What to do now",
      links: "Links",
      official: "official domain",
      redacted: "I hid {n} piece(s) of your personal data before analysis.",
      engineAi: "Analysis: rules + AI",
      engineRules: "Analysis: detection rules",
      pickSituation: "What happened?",
      steps: "Do this now, in order:",
      contacts: "Where to report:",
      menuBack: "Main menu",
      qType: "Let's prepare your report. What happened?",
      qWhen: "When did it happen? Pick one, or type the time.",
      qDesc: "Describe what happened in your own words: who contacted you, what they asked for, what you did.",
      qAmount: "Did you lose money? Type the amount, or choose 'None'.",
      qMethod: "How did you pay?",
      qIds: "Type the scammer's numbers, links or accounts, one per line.",
      qEvidence: "What evidence do you have? (screenshots, transfer receipt, messages, call log)",
      qSteps: "What have you done so far?",
      skip: "Skip",
      none: "None",
      needDesc: "I need a short description of what happened for the report to be useful.",
      reportReady: "Your report is ready. Reference: {ref}\n\nFile it with the police through Aman or eCrime, and attach your screenshots.",
      found: "I found these details in your description and added them:",
      view: "View report",
      download: "Download report",
      print: "Print or save as PDF",
      qStory: "Tell me what happened, your way: type it, tap the microphone and speak, or attach screenshots of the chat or the debit alert. The more you share, the fewer questions I'll ask.",
      qStoryMore: "Add anything else: text, speech or screenshots.",
      dontKnow: "Not sure",
      imagesRead: "I read your screenshots and added what I found to the report.",
      imagesNotRead: "I attached your screenshots to the file as evidence. Reading what they show needs the AI to be switched on.",
      urgentBank: "If you haven't yet: call your bank now on the number on the back of your card and ask them to block it. Every minute counts.",
      summaryTitle: "Report summary",
      summaryHint: "Check the details. Tap Edit next to any line to correct it.",
      edit: "Edit",
      createFile: "Looks right, create the file",
      addMore: "Add details or images",
      screenshot: "Screenshot",
      attached: "Attached evidence",
      attach: "Attach a screenshot",
      mic: "Speak instead of typing",
      micNote: "Your browser's dictation turns your speech into text. Haris then checks it and suggests fixes for words that were probably misheard. Check the text before you send it.",
      dialectQ: "Which accent will you speak in? Choosing it helps dictation understand you better.",
      dialectSet: "Accent: {name}. You can change it any time.",
      changeDialect: "Change accent",
      polished: "I checked the text. These words were probably misheard:",
      polishNote: "Numbers, phone numbers and links are never changed.",
      useFixed: "Use the corrected text",
      keepMine: "Keep my text",
      fixedUsed: "Done. The corrected text is in the message box: check it, then send.",
      reportIt: "Report it to protect others",
      reportConsent: "This goes to the campaign radar: the sender's number and link, and the message text with any personal details removed. Nothing about you is sent.",
      sendReport: "Send the report",
      cancel: "Cancel",
      reportThanksFirst: "Thank you, your report arrived. You are the first to report this message.",
      reportThanks: "Thank you, your report arrived. {n} people have reported this campaign so far.",
      reportEscalated: "Reports have reached the level where the authority is alerted to review it.",
      reportConfirmed: "The authority has confirmed this campaign and issued an official warning.",
      radarAsk: "Paste the message you got and I'll send it to the campaign radar, so the campaign is spotted if others get it too.",
      officialAlerts: "Active official warnings",
      howTo: "How do I use Haris?",
      guideTitle: "Haris in three steps",
      guide: [
        ["Before you respond: check", "Paste any suspicious message or link. Haris tells you how risky it is, why, and what to do."],
        ["If something happened: follow the plan", "Pick your situation, such as 'I paid' or 'My account was hacked', for immediate steps in order and the official reporting numbers."],
        ["To report: tell it your way", "Type, speak in your own accent, or attach screenshots. Haris asks only for what's missing, then prepares the report for you to give the police."],
      ],
      guideCommunity: "Protect others: if you get a scam message and don't respond, tap 'Report it to protect others'. Every report helps spot the campaign early, so the authority can approve a warning that reaches everyone.",
      guidePrivacy: "Haris doesn't keep your chats or personal details. It is an assistant, not an official body.",
      micError: "Couldn't start the microphone. Allow the browser to use it, or type instead.",
      maxImages: "You can attach up to 3 images at a time.",
      removeImage: "Remove image",
      tLessHour: "Less than an hour ago",
      tToday: "Today",
      tYesterday: "Yesterday",
      tOlder: "More than two days ago",
      pCard: "Bank card",
      pTransfer: "Bank transfer",
      pCrypto: "Crypto",
      pGift: "Gift cards",
      pCash: "Cash",
      pOther: "Other",
      sBank: "Called the bank",
      sCard: "Blocked the card",
      sNothing: "Nothing yet",
      f_incident_type: "Type",
      f_occurred_at: "When",
      f_description: "What happened",
      f_amount: "Amount",
      f_payment_method: "Payment method",
      f_scammer_identifiers: "Scammer details",
      f_evidence: "Evidence",
      f_steps_taken: "Steps taken",
      error: "Could not reach the server. Please try again.",
      tooMany: "Too many requests. Please wait a minute.",
    },
    ur: {
      name: "حارس",
      status: "اے آئی معاون · سرکاری ادارہ نہیں",
      placeholder: "مشکوک پیغام یہاں پیسٹ کریں...",
      inputLabel: "اپنا پیغام لکھیں",
      welcome: "السلام علیکم، میں حارس ہوں۔ میں آن لائن فراڈ پہچاننے میں مدد کرتا ہوں، اور اگر آپ کے ساتھ فراڈ ہو جائے تو رہنمائی کرتا ہوں۔\n\nمیں آپ کے پیغامات محفوظ نہیں کرتا۔",
      menu: "میں کیسے مدد کروں؟",
      check: "پیغام یا لنک چیک کریں",
      help: "میرے ساتھ فراڈ ہوا، اب کیا کروں؟",
      report: "پولیس رپورٹ تیار کریں",
      askCheck: "جو پیغام، لنک یا پیشکش ملی ہے وہ پیسٹ کریں، میں چیک کروں گا۔",
      checkAnother: "دوسرا پیغام چیک کریں",
      interacted: "میں نے جواب دیا",
      reasons: "کیوں؟",
      advice: "اب کیا کریں",
      links: "لنکس",
      official: "سرکاری ڈومین",
      redacted: "تجزیے سے پہلے آپ کی {n} ذاتی معلومات چھپا دی گئیں۔",
      engineAi: "تجزیہ: اصول + اے آئی",
      engineRules: "تجزیہ: اصول",
      pickSituation: "کیا ہوا؟",
      steps: "ابھی یہ کریں، اسی ترتیب سے:",
      contacts: "کہاں رپورٹ کریں:",
      menuBack: "مین مینو",
      qType: "آئیے رپورٹ تیار کریں۔ کیا ہوا؟",
      qWhen: "یہ کب ہوا؟ چنیں یا وقت لکھیں۔",
      qDesc: "اپنے الفاظ میں بتائیں کیا ہوا: کس نے رابطہ کیا، کیا مانگا، آپ نے کیا کیا۔",
      qAmount: "کیا رقم کا نقصان ہوا؟ رقم لکھیں یا 'کوئی نہیں' چنیں۔",
      qMethod: "ادائیگی کیسے کی؟",
      qIds: "فراڈیے کے نمبر، لنک یا اکاؤنٹس لکھیں، ہر ایک الگ لائن میں۔",
      qEvidence: "آپ کے پاس کیا ثبوت ہیں؟ (اسکرین شاٹس، ٹرانسفر کی رسید، پیغامات، کال لاگ)",
      qSteps: "اب تک آپ نے کیا کیا ہے؟",
      skip: "چھوڑیں",
      none: "کوئی نہیں",
      needDesc: "رپورٹ کے لیے مختصر تفصیل ضروری ہے۔",
      reportReady: "رپورٹ تیار ہے۔ حوالہ نمبر: {ref}\n\nاسے امان یا ای کرائم کے ذریعے پولیس کو جمع کرائیں اور اسکرین شاٹس لگائیں۔",
      found: "آپ کی تفصیل میں یہ معلومات ملیں اور شامل کر دی گئیں:",
      view: "رپورٹ دیکھیں",
      download: "رپورٹ ڈاؤن لوڈ کریں",
      print: "پرنٹ یا پی ڈی ایف",
      qStory: "اپنے طریقے سے بتائیں کیا ہوا: لکھیں، یا مائیک دبا کر بولیں، یا چیٹ یا کٹوتی کے پیغام کا اسکرین شاٹ لگائیں۔ جتنی زیادہ تفصیل، اتنے کم سوال۔",
      qStoryMore: "مزید کچھ شامل کریں: متن، آواز یا اسکرین شاٹ۔",
      dontKnow: "معلوم نہیں",
      imagesRead: "میں نے اسکرین شاٹس پڑھ کر ان کی معلومات رپورٹ میں شامل کر دیں۔",
      imagesNotRead: "اسکرین شاٹس فائل میں بطور ثبوت لگا دیے گئے۔ ان کا مواد پڑھنے کے لیے اے آئی آن ہونا ضروری ہے۔",
      urgentBank: "اگر ابھی تک نہیں کیا: فوراً کارڈ کی پشت پر لکھے نمبر پر بینک کو فون کریں اور کارڈ بند کروائیں۔ ہر منٹ اہم ہے۔",
      summaryTitle: "رپورٹ کا خلاصہ",
      summaryHint: "تفصیلات دیکھیں، اور غلطی درست کرنے کے لیے لائن کے ساتھ 'ترمیم' دبائیں۔",
      edit: "ترمیم",
      createFile: "درست ہے، فائل بنائیں",
      addMore: "مزید تفصیل یا تصاویر",
      screenshot: "اسکرین شاٹ",
      attached: "منسلک ثبوت",
      attach: "اسکرین شاٹ لگائیں",
      mic: "لکھنے کے بجائے بولیں",
      micNote: "آپ کے براؤزر کی ڈکٹیشن آواز کو متن میں بدلتی ہے، پھر حارس اسے دیکھ کر غلط سنے گئے الفاظ کی درستی تجویز کرتا ہے۔ بھیجنے سے پہلے متن دیکھ لیں۔",
      dialectQ: "آپ کس لہجے میں بولیں گے؟ لہجہ چننے سے ڈکٹیشن آپ کو بہتر سمجھتی ہے۔",
      dialectSet: "لہجہ: {name}۔ آپ اسے کبھی بھی بدل سکتے ہیں۔",
      changeDialect: "لہجہ بدلیں",
      polished: "میں نے متن دیکھا، یہ الفاظ شاید غلط سنے گئے:",
      polishNote: "نمبر، فون نمبر اور لنکس کبھی نہیں بدلے جاتے۔",
      useFixed: "درست متن استعمال کریں",
      keepMine: "میرا متن رکھیں",
      fixedUsed: "ہو گیا۔ درست متن لکھنے کی جگہ میں ہے، دیکھ کر بھیج دیں۔",
      reportIt: "دوسروں کی حفاظت کے لیے رپورٹ کریں",
      reportConsent: "یہ مہم ریڈار کو جائے گا: بھیجنے والے کا نمبر اور لنک، اور پیغام کا متن ذاتی معلومات ہٹا کر۔ آپ کے بارے میں کچھ نہیں بھیجا جائے گا۔",
      sendReport: "رپورٹ بھیجیں",
      cancel: "منسوخ",
      reportThanksFirst: "شکریہ، آپ کی رپورٹ مل گئی۔ آپ اس پیغام کی رپورٹ کرنے والے پہلے شخص ہیں۔",
      reportThanks: "شکریہ، آپ کی رپورٹ مل گئی۔ اب تک {n} لوگ اس مہم کی رپورٹ کر چکے ہیں۔",
      reportEscalated: "رپورٹس اس حد تک پہنچ گئی ہیں جہاں متعلقہ ادارے کو جائزے کے لیے اطلاع دی جاتی ہے۔",
      reportConfirmed: "متعلقہ ادارے نے اس مہم کی تصدیق کر کے سرکاری انتباہ جاری کیا ہے۔",
      radarAsk: "جو پیغام آیا ہے وہ یہاں چسپاں کریں، میں اسے مہم ریڈار کو بھیج دوں گا تاکہ دوسروں تک پہنچے تو مہم پکڑی جائے۔",
      officialAlerts: "فعال سرکاری انتباہات",
      howTo: "حارس کیسے استعمال کریں؟",
      guideTitle: "حارس تین مرحلوں میں",
      guide: [
        ["جواب دینے سے پہلے: چیک کریں", "کوئی بھی مشکوک پیغام یا لنک چسپاں کریں۔ حارس بتاتا ہے کہ خطرہ کتنا ہے، کیوں، اور کیا کریں۔"],
        ["اگر کچھ ہو گیا: منصوبے پر عمل کریں", "اپنی صورتحال چنیں، جیسے 'میں نے رقم دی' یا 'اکاؤنٹ ہیک ہو گیا'، فوری اقدامات ترتیب سے اور سرکاری رپورٹ نمبر ملیں گے۔"],
        ["رپورٹ کے لیے: اپنے طریقے سے بتائیں", "لکھیں، اپنے لہجے میں بولیں، یا اسکرین شاٹ لگائیں۔ حارس صرف کمی والی بات پوچھتا ہے، پھر پولیس کے لیے رپورٹ تیار کرتا ہے۔"],
      ],
      guideCommunity: "دوسروں کی حفاظت کریں: اگر فراڈ کا پیغام آئے اور آپ جواب نہ دیں تو 'دوسروں کی حفاظت کے لیے رپورٹ کریں' دبائیں۔ ہر رپورٹ مہم کو جلد پکڑنے میں مدد دیتی ہے، تاکہ ادارہ سب کے لیے انتباہ جاری کرے۔",
      guidePrivacy: "حارس آپ کی چیٹس یا ذاتی معلومات محفوظ نہیں کرتا۔ یہ ایک معاون ہے، سرکاری ادارہ نہیں۔",
      micError: "مائیک شروع نہیں ہو سکا۔ براؤزر کو اجازت دیں یا لکھ دیں۔",
      maxImages: "ایک وقت میں زیادہ سے زیادہ 3 تصاویر لگائی جا سکتی ہیں۔",
      removeImage: "تصویر ہٹائیں",
      tLessHour: "ایک گھنٹے سے کم پہلے",
      tToday: "آج",
      tYesterday: "کل",
      tOlder: "دو دن سے زیادہ پہلے",
      pCard: "بینک کارڈ",
      pTransfer: "بینک ٹرانسفر",
      pCrypto: "کرپٹو",
      pGift: "گفٹ کارڈ",
      pCash: "نقد",
      pOther: "دیگر",
      sBank: "بینک کو فون کیا",
      sCard: "کارڈ بند کروایا",
      sNothing: "ابھی کچھ نہیں کیا",
      f_incident_type: "قسم",
      f_occurred_at: "کب",
      f_description: "کیا ہوا",
      f_amount: "رقم",
      f_payment_method: "ادائیگی کا طریقہ",
      f_scammer_identifiers: "فراڈیے کی معلومات",
      f_evidence: "ثبوت",
      f_steps_taken: "اٹھائے گئے اقدامات",
      error: "سرور سے رابطہ نہیں ہو سکا۔ دوبارہ کوشش کریں۔",
      tooMany: "بہت زیادہ درخواستیں۔ ایک منٹ انتظار کریں۔",
    },
  };

  const chat = document.getElementById("chat");
  const chips = document.getElementById("chips");
  const form = document.getElementById("composer");
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("send");

  let lang = "ar";
  let mode = "check"; // check | report
  let draft = {};
  const tr = (key, vars = {}) => UI[lang][key].replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");

  // ---- DOM helpers (textContent only: no HTML from the server is ever injected) ----
  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else node.setAttribute(k, v);
    }
    for (const child of [].concat(children)) if (child) node.append(child);
    return node;
  }

  function scroll() { chat.scrollTop = chat.scrollHeight; }

  function bubble(content, out = false) {
    const node = el("div", { class: out ? "msg out" : "msg" });
    if (typeof content === "string") node.textContent = content;
    else node.append(...[].concat(content));
    chat.append(node);
    scroll();
    return node;
  }

  function list(items, ordered = false) {
    return el(ordered ? "ol" : "ul", {}, items.map((t) => el("li", { text: t })));
  }

  function setChips(options) {
    chips.replaceChildren(...options.map(([label, action]) => {
      const b = el("button", { type: "button", text: label });
      b.addEventListener("click", () => { bubble(label, true); chips.replaceChildren(); action(); });
      return b;
    }));
  }

  function typing() {
    const node = el("div", { class: "msg typing", "aria-label": "..." }, [el("span"), el("span"), el("span")]);
    chat.append(node);
    scroll();
    return () => node.remove();
  }

  async function api(path, body) {
    const stop = typing();
    sendBtn.disabled = true;
    try {
      const res = await fetch(path, body
        ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
        : {});
      if (res.status === 429) throw new Error(tr("tooMany"));
      if (!res.ok) throw new Error(tr("error"));
      return await res.json();
    } catch (err) {
      bubble(err.message && !err.message.startsWith("Failed") ? err.message : tr("error"));
      return null;
    } finally {
      stop();
      sendBtn.disabled = false;
    }
  }

  // ---- Menu ----
  function menu() {
    mode = "check";
    bubble(tr("menu"));
    setChips([
      [tr("check"), askCheck],
      [tr("help"), chooseSituation],
      [tr("report"), startReport],
      [tr("howTo"), showGuide],
    ]);
  }

  function showGuide() {
    const steps = el("ol", { class: "guide" }, UI[lang].guide.map(([title, body]) =>
      el("li", {}, [el("strong", { text: title }), el("span", { text: body })])));
    bubble([el("h3", { text: tr("guideTitle") }), steps,
      el("p", { class: "radar-line", text: tr("guideCommunity") }), el("p", { class: "note", text: tr("guidePrivacy") })]);
    setChips([[tr("check"), askCheck], [tr("help"), chooseSituation], [tr("report"), startReport]]);
  }

  function askCheck() {
    mode = "check";
    bubble(tr("askCheck"));
    input.focus();
  }

  // ---- Check a message ----
  async function check(text) {
    const r = await api("/api/check", { text, lang });
    if (!r) return;
    const parts = [
      el("div", { class: `risk ${r.risk}` }, [
        el("span", { class: "dot", "aria-hidden": "true" }),
        el("span", { text: r.risk_label }),
        r.category !== "unknown" ? el("span", { class: "cat", text: r.category_label }) : null,
      ]),
      el("p", { text: r.summary }),
    ];
    if (r.radar && r.radar.broadcast) parts.unshift(officialAlert(r.radar.broadcast));
    if (r.radar && r.radar.message) parts.push(el("p", { class: "radar-line", text: r.radar.message }));
    if (r.reasons.length) parts.push(el("h3", { text: tr("reasons") }), list(r.reasons));
    if (r.links.length) {
      parts.push(el("h3", { text: tr("links") }));
      for (const link of r.links) {
        const flags = link.official ? [tr("official")] : link.flag_labels;
        parts.push(el("div", { class: link.official ? "link-card official" : "link-card" }, [
          el("code", { text: link.domain || link.url }),
          flags.length ? el("div", { class: "flags", text: flags.join(" · ") }) : null,
        ]));
      }
    }
    if (r.advice.length) parts.push(el("h3", { text: tr("advice") }), list(r.advice));
    const redactedCount = Object.values(r.redacted).reduce((a, b) => a + b, 0);
    const notes = [r.engine === "rules+ai" ? tr("engineAi") : tr("engineRules")];
    if (redactedCount) notes.unshift(tr("redacted", { n: redactedCount }));
    parts.push(el("p", { class: "note", text: notes.join(" · ") }));
    bubble(parts);

    const next = [[tr("reportIt"), () => confirmReport(text)], [tr("checkAnother"), askCheck]];
    if (r.risk !== "low") next.push([tr("interacted"), chooseSituation]);
    next.push([tr("report"), startReport], [tr("menuBack"), menu]);
    setChips(next);
  }

  // ---- Victim help ----
  async function chooseSituation() {
    const items = await api(`/api/playbooks?lang=${lang}`);
    if (!items) return;
    bubble(tr("pickSituation"));
    setChips(items.map((pb) => [pb.title, () => showPlaybook(pb.id)]));
  }

  async function showPlaybook(id) {
    const pb = await api(`/api/playbooks/${encodeURIComponent(id)}?lang=${lang}`);
    if (!pb) return;
    bubble([el("h3", { text: pb.title }), el("p", { text: tr("steps") }), list(pb.steps, true)]);
    bubble(contactsBlock(pb.contacts));
    setChips([
      ...(id === "suspicious_only" ? [[tr("reportIt"), askRadar]] : []),
      [tr("report"), () => startReport(id)],
      [tr("menuBack"), menu],
    ]);
  }

  function contactsBlock(contacts) {
    return [el("h3", { text: tr("contacts") }), ...contacts.map((c) => {
      const href = c.value.startsWith("http") ? c.value
        : c.value.includes("@") ? `mailto:${c.value}`
        : c.id.endsWith("_sms") ? `sms:${c.value}` : `tel:${c.value}`;
      const a = el("a", { href, text: c.value.replace("https://", "") });
      if (href.startsWith("http")) { a.setAttribute("target", "_blank"); a.setAttribute("rel", "noopener noreferrer"); }
      return el("div", { class: "contact" }, [el("span", { text: c.label }), a]);
    })];
  }

  // ---- Campaign radar: a message nobody fell for still helps catch the campaign ----
  function officialAlert(b) {
    return el("div", { class: "official-alert", role: "alert" }, [
      el("strong", { text: b.title }),
      el("p", { text: b.body }),
      el("span", { class: "badge", text: b.demo }),
    ]);
  }

  function reporterId() {
    let id = store.get("haris.reporter");
    if (!id) {
      id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`).replace(/[^A-Za-z0-9-]/g, "");
      store.set("haris.reporter", id);
    }
    return id;
  }

  function askRadar() {
    mode = "radar";
    bubble(tr("radarAsk"));
    input.focus();
  }

  function confirmReport(text) {
    mode = "check";
    bubble(tr("reportConsent"));
    setChips([[tr("sendReport"), () => sendRadarReport(text)], [tr("cancel"), menu]]);
  }

  async function sendRadarReport(text) {
    const r = await api("/api/radar/report", { text, lang, reporter_id: reporterId() });
    if (!r) return;
    const c = r.campaign;
    const lines = [el("p", { text: !c || c.people <= 1 ? tr("reportThanksFirst") : tr("reportThanks", { n: c.people }) })];
    if (c && c.status === "escalated") lines.push(el("p", { class: "radar-line", text: tr("reportEscalated") }));
    if (c && c.status === "confirmed") lines.push(el("p", { class: "radar-line", text: tr("reportConfirmed") }));
    bubble(lines);
    setChips([[tr("checkAnother"), askCheck], [tr("menuBack"), menu]]);
  }

  async function showBroadcasts() {
    try {
      const res = await fetch(`/api/radar/broadcasts?lang=${lang}`);
      const items = res.ok ? await res.json() : [];
      if (items.length) bubble([el("h3", { text: tr("officialAlerts") }), ...items.map(officialAlert)]);
    } catch { /* the radar is optional */ }
  }

  // ---- Report: "tell it your way, Haris sorts it out" ----
  // 1. The victim tells the story: typed, dictated (mic) or as screenshots (clip).
  // 2. /api/extract pulls out what it can; only the missing fields are asked, with ready answers.
  // 3. A summary card shows every field; any line can be edited before the file is made.
  let phase = "";          // story | more | field | edit | summary
  let queue = [];          // missing fields still to ask
  let editing = "";        // the field being asked or edited
  let reportImages = [];   // screenshots added to this report (data: URLs)
  let incidentTitles = {}; // incident id -> title, from /api/playbooks
  let urgentShown = false;

  const FIELD_CHIPS = {
    occurred_at: () => ["tLessHour", "tToday", "tYesterday", "tOlder"].map((k) => [tr(k), tr(k)]),
    payment_method: () => ["pCard", "pTransfer", "pCrypto", "pGift", "pCash", "pOther"].map((k) => [tr(k), tr(k)]),
    steps_taken: () => ["sBank", "sCard", "sNothing"].map((k) => [tr(k), tr(k)]),
    amount: () => [[tr("none"), ""]],
  };
  const FIELD_QUESTION = { occurred_at: "qWhen", amount: "qAmount", payment_method: "qMethod", steps_taken: "qSteps", description: "qDesc" };

  async function startReport(incidentType) {
    mode = "report";
    draft = { lang };
    reportImages = [];
    urgentShown = false;
    const items = await api(`/api/playbooks?lang=${lang}`);
    if (!items) return;
    incidentTitles = Object.fromEntries(items.map((pb) => [pb.id, pb.title]));
    if (typeof incidentType === "string") {
      draft.incident_type = incidentType;
      return askStory();
    }
    bubble(tr("qType"));
    setChips([...items.map((pb) => [pb.title, () => { draft.incident_type = pb.id; askStory(); }]), [tr("dontKnow"), askStory]]);
  }

  function askStory() {
    phase = "story";
    bubble(tr("qStory"));
    showTools(true);
    input.focus();
  }

  async function sendStory(text, images) {
    const r = await api("/api/extract", { lang, text, images, incident_type: draft.incident_type || null });
    if (!r) return;
    const f = r.fields;
    if (phase === "more" && draft.description && text) f.description = `${draft.description}\n${text}`;
    for (const key of ["incident_type", "occurred_at", "description", "amount", "currency"]) if (f[key]) draft[key] = f[key];
    if (f.payment_method_label) draft.payment_method = f.payment_method_label;
    for (const key of ["scammer_identifiers", "steps_taken"]) {
      if (f[key]) draft[key] = [...new Set([...(draft[key] || []), ...f[key]])];
    }
    reportImages.push(...images);
    if (reportImages.length) draft.evidence = reportImages.map((_, i) => `${tr("screenshot")} ${i + 1}`);
    if (images.length) bubble(r.images_read ? tr("imagesRead") : tr("imagesNotRead"));
    if (["money_sent", "business_fraud"].includes(draft.incident_type) && !urgentShown) { bubble(tr("urgentBank")); urgentShown = true; }
    queue = phase === "more" ? [] : r.missing.slice();
    nextMissing();
  }

  function nextMissing() {
    if (!queue.length) return showSummary();
    askField(queue[0], "field");
  }

  function askField(key, how) {
    phase = how;
    editing = key;
    showTools(false);
    if (key === "incident_type") {
      bubble(tr("qType"));
      return setChips(Object.entries(incidentTitles).map(([id, title]) => [title, () => answerField(id)]));
    }
    bubble(tr(FIELD_QUESTION[key] || "qDesc"));
    const chipsFor = FIELD_CHIPS[key];
    setChips(chipsFor ? chipsFor().map(([label, value]) => [label, () => answerField(value)]) : []);
    input.focus();
  }

  function answerField(value) {
    const key = editing;
    value = (value || "").trim();
    if (key === "description" && !value) return bubble(tr("needDesc"));
    if (key === "steps_taken" || key === "scammer_identifiers") {
      draft[key] = value ? value.split(/[\n,،]+/).map((x) => x.trim()).filter(Boolean) : [];
    } else if (value) {
      draft[key] = key === "amount" ? value.replace(/[^\d.,٠-٩]/g, "") || value : value;
    } else {
      delete draft[key];
    }
    chips.replaceChildren();
    if (phase === "field") { queue.shift(); return nextMissing(); }
    showSummary();
  }

  function showSummary() {
    phase = "summary";
    showTools(false);
    const val = (key) => {
      const v = draft[key];
      if (key === "incident_type") return incidentTitles[v] || "";
      if (key === "amount") return v ? `${v} ${draft.currency || "AED"}` : "";
      if (key === "evidence") return reportImages.length ? `${reportImages.length} × ${tr("screenshot")}` : "";
      return Array.isArray(v) ? v.join("، ") : (v || "");
    };
    const rows = ["incident_type", "occurred_at", "description", "amount", "payment_method", "scammer_identifiers", "evidence", "steps_taken"];
    const card = el("div", { class: "summary" }, rows.map((key) => {
      const text = val(key);
      const shown = text.length > 220 ? `${text.slice(0, 220)}…` : text;
      const row = el("div", { class: "summary-row" }, [
        el("span", { class: "summary-label", text: tr(`f_${key}`) }),
        el("span", { class: text ? "summary-value" : "summary-value empty", text: shown || "—" }),
      ]);
      if (key !== "evidence") {
        const b = el("button", { type: "button", class: "summary-edit", text: tr("edit"), "aria-label": `${tr("edit")}: ${tr(`f_${key}`)}` });
        b.addEventListener("click", () => { chips.replaceChildren(); askField(key, "edit"); });
        row.append(b);
      }
      return row;
    }));
    bubble([el("h3", { text: tr("summaryTitle") }), el("p", { class: "note", text: tr("summaryHint") }), card]);
    setChips([[tr("createFile"), submitReport], [tr("addMore"), () => { phase = "more"; bubble(tr("qStoryMore")); showTools(true); input.focus(); }]]);
  }

  async function submitReport() {
    mode = "check";
    phase = "";
    showTools(false);
    const r = await api("/api/report", draft);
    if (!r) return;
    const html = withEvidence(r.html);
    // ⁦...⁩ keeps the Latin reference number left-to-right inside Arabic/Urdu text.
    // Non-breaking hyphens (‑) stop the number wrapping across lines.
    const ref = `⁦${r.reference.replaceAll("-", "‑")}⁩`;
    const parts = [el("p", { text: tr("reportReady", { ref }) })];
    if (r.identifiers_found.length) parts.push(el("p", { text: tr("found") }), list(r.identifiers_found));
    const actions = el("div", { class: "actions" });
    const button = (label, onClick) => {
      const b = el("button", { type: "button", text: label });
      b.addEventListener("click", onClick);
      actions.append(b);
    };
    button(tr("view"), () => openReport(html, false));
    button(tr("download"), () => download(html, "text/html", `${r.reference}.html`));
    button(tr("print"), () => openReport(html, true));
    parts.push(actions);
    bubble(parts);
    setChips([[tr("checkAnother"), askCheck], [tr("menuBack"), menu]]);
  }

  // Adds the screenshots to the report file itself, so the police see the evidence.
  function withEvidence(htmlDoc) {
    if (!reportImages.length) return htmlDoc;
    const imgs = reportImages.map((src, i) => `<img src="${src}" alt="${tr("screenshot")} ${i + 1}">`).join("");
    return htmlDoc.replace("<footer>", `<h2>${tr("attached")}</h2><div class="evidence">${imgs}</div><footer>`);
  }

  function download(content, type, filename) {
    const url = URL.createObjectURL(new Blob([content], { type: `${type};charset=utf-8` }));
    const a = el("a", { href: url, download: filename });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // Opens the report in a new tab. The tab inherits this page's Content-Security-Policy,
  // which blocks inline styles, so the report's <style> is swapped for report.css.
  function openReport(htmlDoc, andPrint) {
    const styled = htmlDoc.replace(/<style>[\s\S]*?<\/style>/, `<link rel="stylesheet" href="${location.origin}/report.css">`);
    const url = URL.createObjectURL(new Blob([styled], { type: "text/html;charset=utf-8" }));
    const w = window.open(url, "_blank");
    if (!w) {
      download(htmlDoc, "text/html", "haris-report.html"); // pop-ups blocked: fall back to a download
    } else if (andPrint) {
      w.addEventListener("load", () => setTimeout(() => w.print(), 300));
    }
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  // ---- Input ----
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    stopDictation(false);
    const text = input.value.trim();
    const images = pending.slice();
    if (!text && !images.length) return;
    const out = [];
    if (text) out.push(el("p", { text }));
    if (images.length) out.push(el("div", { class: "thumbs" }, images.map((src) => el("img", { src, alt: tr("screenshot") }))));
    bubble(out, true);
    input.value = "";
    clearPending();
    autosize();
    chips.replaceChildren();
    if (mode === "report" && (phase === "story" || phase === "more")) sendStory(text, images);
    else if (mode === "report" && (phase === "field" || phase === "edit")) answerField(text);
    else if (mode === "report" && phase === "summary") { phase = "more"; sendStory(text, images); }
    else if (mode === "radar" && text) confirmReport(text);
    else if (text) check(text);
  });

  // ---- Screenshots: resized in the browser (which also drops photo metadata) ----
  const attachBtn = document.getElementById("attach");
  const fileInput = document.getElementById("file");
  const strip = document.getElementById("pending");
  const MAX_IMAGES = 3;
  let pending = [];

  function showTools(on) { attachBtn.hidden = !on; if (!on) clearPending(); }

  attachBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async () => {
    for (const file of [...fileInput.files]) {
      if (pending.length >= MAX_IMAGES) { bubble(tr("maxImages")); break; }
      if (!file.type.startsWith("image/")) continue;
      try { pending.push(await shrink(file)); } catch { bubble(tr("error")); }
    }
    fileInput.value = "";
    renderPending();
  });

  async function shrink(file) {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.85);
  }

  function renderPending() {
    strip.replaceChildren(...pending.map((src, i) => {
      const remove = el("button", { type: "button", class: "remove", "aria-label": tr("removeImage"), text: "×" });
      remove.addEventListener("click", () => { pending.splice(i, 1); renderPending(); });
      return el("div", { class: "pending-item" }, [el("img", { src, alt: `${tr("screenshot")} ${i + 1}` }), remove]);
    }));
  }
  function clearPending() { pending = []; renderPending(); }

  // ---- Dictation (the browser's own speech service; hidden where unsupported) ----
  // The user picks their dialect once (remembered in this browser), and after each
  // dictation /api/polish suggests fixes for misheard words. Numbers are never changed.
  const micBtn = document.getElementById("mic");
  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  const DIALECTS = {
    ar: [["ar-AE", "إماراتية / خليجية"], ["ar-SA", "سعودية"], ["ar-EG", "مصرية"], ["ar-JO", "شامية"], ["ar-IQ", "عراقية"], ["ar-MA", "مغاربية"]],
    en: [["en-US", "American"], ["en-GB", "British"], ["en-IN", "Indian"], ["en-PH", "Filipino"]],
    ur: [["ur-PK", "پاکستانی اردو"], ["ur-IN", "ہندوستانی اردو"]],
  };
  const store = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode: keep for this visit only */ } },
  };
  const chosenDialect = {};
  let recognizer = null;
  let heard = false;
  let micNoteShown = false;
  micBtn.hidden = !Speech;

  function dialect() {
    const saved = chosenDialect[lang] || store.get(`haris.dialect.${lang}`);
    return DIALECTS[lang].some(([code]) => code === saved) ? saved : null;
  }

  micBtn.addEventListener("click", () => {
    if (recognizer) return stopDictation(true);
    if (!dialect()) return askDialect(startDictation);
    startDictation();
  });

  function askDialect(then) {
    const choices = el("div", { class: "actions" });
    const node = bubble([el("p", { text: tr("dialectQ") }), choices]);
    for (const [code, name] of DIALECTS[lang]) {
      const b = el("button", { type: "button", text: name, "aria-pressed": String(code === dialect()) });
      b.addEventListener("click", () => {
        chosenDialect[lang] = code;
        store.set(`haris.dialect.${lang}`, code);
        node.replaceChildren(el("p", { text: tr("dialectSet", { name }) }));
        if (then) then();
      });
      choices.append(b);
    }
  }

  function startDictation() {
    if (!Speech) return;
    if (!micNoteShown) {
      const change = el("button", { type: "button", text: tr("changeDialect") });
      change.addEventListener("click", () => { stopDictation(false); change.remove(); askDialect(null); });
      bubble([el("p", { text: tr("micNote") }), el("div", { class: "actions" }, [change])]);
      micNoteShown = true;
    }
    const base = input.value ? `${input.value} ` : "";
    heard = false;
    recognizer = new Speech();
    recognizer.lang = dialect() || DIALECTS[lang][0][0];
    recognizer.continuous = true;
    recognizer.interimResults = true;
    recognizer.onresult = (e) => {
      input.value = base + [...e.results].map((r) => r[0].transcript).join(" ");
      heard = true;
      autosize();
    };
    recognizer.onerror = (e) => {
      if (e.error !== "no-speech" && e.error !== "aborted") bubble(tr("micError"));
      stopDictation(heard);
    };
    recognizer.onend = () => stopDictation(true);
    recognizer.start();
    micBtn.classList.add("recording");
    micBtn.setAttribute("aria-pressed", "true");
  }

  // polishAfter: false when the text is being sent right away or the language changes.
  function stopDictation(polishAfter = false) {
    const wasOn = Boolean(recognizer);
    if (recognizer) { const r = recognizer; recognizer = null; try { r.stop(); } catch { /* already stopped */ } }
    micBtn.classList.remove("recording");
    micBtn.setAttribute("aria-pressed", "false");
    if (wasOn && polishAfter && heard && input.value.trim().length >= 6) polishDictation();
    heard = false;
  }

  async function polishDictation() {
    const original = input.value;
    let r = null;
    try {
      const res = await fetch("/api/polish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: original, lang, dialect: dialect() }),
      });
      if (res.ok) r = await res.json();
    } catch { /* offline: keep the text as it is */ }
    if (!r || !r.changes.length || r.text.trim() === original.trim()) return;
    const arrow = lang === "en" ? "→" : "←";
    const actions = el("div", { class: "actions" });
    const node = bubble([
      el("p", { text: tr("polished") }),
      list(r.changes.map((c) => `${c.from || "—"} ${arrow} ${c.to || "—"}`)),
      el("p", { class: "note", text: tr("polishNote") }),
      actions,
    ]);
    const done = (message) => { actions.remove(); if (message) node.append(el("p", { class: "note", text: message })); };
    const button = (label, onClick) => {
      const b = el("button", { type: "button", text: label });
      b.addEventListener("click", onClick);
      actions.append(b);
    };
    button(tr("useFixed"), () => {
      // Words dictated or typed after the check are kept.
      input.value = input.value.startsWith(original) ? r.text + input.value.slice(original.length) : r.text;
      autosize();
      input.focus();
      done(tr("fixedUsed"));
    });
    button(tr("keepMine"), () => { done(""); input.focus(); });
    button(tr("changeDialect"), () => { done(""); askDialect(null); });
  }

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  function autosize() {
    input.rows = Math.min(5, Math.max(1, input.value.split("\n").length));
  }
  input.addEventListener("input", autosize);

  // ---- Language ----
  function applyLanguage(next) {
    lang = next;
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "en" ? "ltr" : "rtl";
    document.getElementById("bot-name").textContent = tr("name");
    document.getElementById("bot-status").textContent = tr("status");
    document.getElementById("input-label").textContent = tr("inputLabel");
    input.placeholder = tr("placeholder");
    document.getElementById("attach").setAttribute("aria-label", tr("attach"));
    document.getElementById("mic").setAttribute("aria-label", tr("mic"));
    document.querySelectorAll(".langs button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
  }

  document.querySelectorAll(".langs button").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.lang === lang) return;
    stopDictation(false);
    applyLanguage(b.dataset.lang);
    chat.replaceChildren();
    showTools(false);
    start();
  }));

  async function start() {
    bubble(tr("welcome"));
    await showBroadcasts();
    menu();
  }

  applyLanguage("ar");
  start();
})();
