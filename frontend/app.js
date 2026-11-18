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
      qWhen: "متى حدث ذلك؟ (مثال: اليوم الساعة 3 عصراً)",
      qDesc: "اشرح ما حدث بكلماتك: من تواصل معك، وماذا طلب، وماذا فعلت.",
      qAmount: "هل فقدت مالاً؟ اكتب المبلغ، أو اختر «لا يوجد».",
      qMethod: "كيف دفعت؟ (بطاقة، تحويل بنكي، عملات رقمية، بطاقات هدايا...)",
      qIds: "اكتب أرقام المحتال أو روابطه أو حساباته، كل واحد في سطر.",
      qEvidence: "ما الأدلة المتوفرة لديك؟ (لقطات شاشة، إيصال التحويل، رسائل، سجل مكالمات)",
      qSteps: "ما الذي فعلته حتى الآن؟ (مثال: اتصلت بالبنك وأوقفت البطاقة)",
      skip: "تخطَّ",
      none: "لا يوجد",
      needDesc: "أحتاج وصفاً قصيراً لما حدث حتى يكون البلاغ مفيداً.",
      reportReady: "ملف البلاغ جاهز. الرقم المرجعي: {ref}\n\nقدّمه للشرطة عبر خدمة «أمان» أو منصة eCrime، وأرفق لقطات الشاشة.",
      found: "وجدتُ في وصفك هذه البيانات وأضفتها للبلاغ:",
      download: "تنزيل الملف",
      downloadMd: "تنزيل نص البلاغ",
      print: "طباعة",
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
      qWhen: "When did it happen? (e.g. today at 3 pm)",
      qDesc: "Describe what happened in your own words: who contacted you, what they asked for, what you did.",
      qAmount: "Did you lose money? Type the amount, or choose 'None'.",
      qMethod: "How did you pay? (card, bank transfer, crypto, gift cards...)",
      qIds: "Type the scammer's numbers, links or accounts, one per line.",
      qEvidence: "What evidence do you have? (screenshots, transfer receipt, messages, call log)",
      qSteps: "What have you done so far? (e.g. called the bank and blocked the card)",
      skip: "Skip",
      none: "None",
      needDesc: "I need a short description of what happened for the report to be useful.",
      reportReady: "Your report is ready. Reference: {ref}\n\nFile it with the police through Aman or eCrime, and attach your screenshots.",
      found: "I found these details in your description and added them:",
      download: "Download report",
      downloadMd: "Download as text",
      print: "Print",
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
      qWhen: "یہ کب ہوا؟ (مثال: آج سہ پہر 3 بجے)",
      qDesc: "اپنے الفاظ میں بتائیں کیا ہوا: کس نے رابطہ کیا، کیا مانگا، آپ نے کیا کیا۔",
      qAmount: "کیا رقم کا نقصان ہوا؟ رقم لکھیں یا 'کوئی نہیں' چنیں۔",
      qMethod: "ادائیگی کیسے کی؟ (کارڈ، بینک ٹرانسفر، کرپٹو، گفٹ کارڈ...)",
      qIds: "فراڈیے کے نمبر، لنک یا اکاؤنٹس لکھیں، ہر ایک الگ لائن میں۔",
      qEvidence: "آپ کے پاس کیا ثبوت ہیں؟ (اسکرین شاٹس، ٹرانسفر کی رسید، پیغامات، کال لاگ)",
      qSteps: "اب تک آپ نے کیا کیا ہے؟ (مثال: بینک کو فون کر کے کارڈ بند کروایا)",
      skip: "چھوڑیں",
      none: "کوئی نہیں",
      needDesc: "رپورٹ کے لیے مختصر تفصیل ضروری ہے۔",
      reportReady: "رپورٹ تیار ہے۔ حوالہ نمبر: {ref}\n\nاسے امان یا ای کرائم کے ذریعے پولیس کو جمع کرائیں اور اسکرین شاٹس لگائیں۔",
      found: "آپ کی تفصیل میں یہ معلومات ملیں اور شامل کر دی گئیں:",
      download: "رپورٹ ڈاؤن لوڈ کریں",
      downloadMd: "متن ڈاؤن لوڈ کریں",
      print: "پرنٹ",
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
  let reportStep = 0;
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
    ]);
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

    const next = [[tr("checkAnother"), askCheck]];
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

  // ---- Guided report ----
  const REPORT_STEPS = [
    { key: "occurred_at", q: "qWhen", optional: true },
    { key: "description", q: "qDesc", required: true },
    { key: "amount", q: "qAmount", optional: true, noneChip: true },
    { key: "payment_method", q: "qMethod", optional: true },
    { key: "scammer_identifiers", q: "qIds", optional: true, list: true },
    { key: "evidence", q: "qEvidence", optional: true, list: true },
    { key: "steps_taken", q: "qSteps", optional: true, list: true },
  ];

  async function startReport(incidentType) {
    mode = "report";
    draft = { lang };
    reportStep = 0;
    if (typeof incidentType === "string") {
      draft.incident_type = incidentType;
      return askReportStep();
    }
    const items = await api(`/api/playbooks?lang=${lang}`);
    if (!items) return;
    bubble(tr("qType"));
    setChips(items.map((pb) => [pb.title, () => { draft.incident_type = pb.id; askReportStep(); }]));
  }

  function askReportStep() {
    const step = REPORT_STEPS[reportStep];
    if (!step) return submitReport();
    bubble(tr(step.q));
    const options = [];
    if (step.noneChip) options.push([tr("none"), () => answerReport("")]);
    if (step.optional) options.push([tr("skip"), () => answerReport("")]);
    setChips(options);
    input.focus();
  }

  function answerReport(value) {
    const step = REPORT_STEPS[reportStep];
    if (step.required && !value.trim()) {
      bubble(tr("needDesc"));
      return;
    }
    if (value.trim()) {
      draft[step.key] = step.list ? value.split(/[\n,،]+/).map((s) => s.trim()).filter(Boolean) : value.trim();
    }
    reportStep += 1;
    chips.replaceChildren();
    askReportStep();
  }

  async function submitReport() {
    mode = "check";
    const r = await api("/api/report", draft);
    if (!r) return;
    // ⁦...⁩ keeps the Latin reference number left-to-right inside Arabic/Urdu text.
    // Non-breaking hyphens (‑) stop the number wrapping across lines.
    const ref = `⁦${r.reference.replaceAll("-", "‑")}⁩`;
    const parts = [el("p", { text: tr("reportReady", { ref }) })];
    if (r.identifiers_found.length) parts.push(el("p", { text: tr("found") }), list(r.identifiers_found));
    const actions = el("div", { class: "actions" });
    const dl = (label, content, type, ext) => {
      const b = el("button", { type: "button", text: label });
      b.addEventListener("click", () => download(content, type, `${r.reference}.${ext}`));
      actions.append(b);
    };
    dl(tr("download"), r.html, "text/html", "html");
    dl(tr("downloadMd"), r.markdown, "text/markdown", "md");
    const printBtn = el("button", { type: "button", text: tr("print") });
    printBtn.addEventListener("click", () => printReport(r.html));
    actions.append(printBtn);
    parts.push(actions);
    bubble(parts);
    setChips([[tr("checkAnother"), askCheck], [tr("menuBack"), menu]]);
  }

  function download(content, type, filename) {
    const url = URL.createObjectURL(new Blob([content], { type: `${type};charset=utf-8` }));
    const a = el("a", { href: url, download: filename });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function printReport(htmlDoc) {
    const url = URL.createObjectURL(new Blob([htmlDoc], { type: "text/html;charset=utf-8" }));
    const w = window.open(url, "_blank", "noopener");
    if (!w) download(htmlDoc, "text/html", "haris-report.html");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  // ---- Input ----
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    bubble(text, true);
    input.value = "";
    autosize();
    chips.replaceChildren();
    if (mode === "report") answerReport(text);
    else check(text);
  });

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
    document.querySelectorAll(".langs button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
  }

  document.querySelectorAll(".langs button").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.lang === lang) return;
    applyLanguage(b.dataset.lang);
    chat.replaceChildren();
    start();
  }));

  function start() {
    bubble(tr("welcome"));
    menu();
  }

  applyLanguage("ar");
  start();
})();
