// The full Arabic deck for «حارس»: technical build, the stages from message to takedown,
// measured results, then the goals and the development roadmap.
//   node docs/deck/build_full_deck.js <media dir> <out.pptx>
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const JSZip = require("/opt/npm-tools/node_modules/jszip");

const SKILL = process.env.PPTX_SKILL;
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));
const MEDIA = process.argv[2];
const OUT = process.argv[3];
const M = (f) => path.join(MEDIA, f);

const THEME = {
  name: "Haris",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "1E2B2A", lt1: "FFFFFF", dk2: "0A4740", lt2: "EEF4F2",
    accent1: "0A4740", accent2: "E0B23A", accent3: "B42318", accent4: "2E7D6B", accent5: "5B6B6A", accent6: "D6E4DF",
    hlink: "1F5FBF", folHlink: "6B4FA0",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.rtlMode = true;
pres.title = "«حارس» درعك الذكي";
pres.author = "Haris";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333, L = 0.6, R = W - 0.6, CW = R - L;
const RTL = { rtlMode: true, lang: "ar-AE", align: "right" };

// --- layouts --------------------------------------------------------------
const FOOT = "«حارس» · نسخة أولية تعمل · هاكاثون الذكاء الاصطناعي للأمن 2026";
pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: L, y: 0.28, w: CW, h: 0.32, fontSize: 13, bold: true, color: C.accent4, align: "right", valign: "middle", margin: 0, rtlMode: true }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: L, y: 0.6, w: CW, h: 0.8, fontSize: 30, bold: true, color: C.text2, align: "right", valign: "middle", margin: 0, rtlMode: true }, text: "" } },
    { text: { text: FOOT, options: { x: R - 8, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent5, align: "right", margin: 0, rtlMode: true } } },
  ],
  slideNumber: { x: L, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent5, align: "left" },
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: L, y: 0.28, w: CW, h: 0.32, fontSize: 13, bold: true, color: C.accent2, align: "right", valign: "middle", margin: 0, rtlMode: true }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: L, y: 0.6, w: CW, h: 0.8, fontSize: 30, bold: true, color: C.background1, align: "right", valign: "middle", margin: 0, rtlMode: true }, text: "" } },
  ],
  slideNumber: { x: L, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "left" },
});

// --- helpers --------------------------------------------------------------
const icons = {};
async function icon(name, hex) {
  const key = name + hex;
  if (!icons[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + hex, size: 256 }));
    const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
    icons[key] = "image/png;base64," + buf.toString("base64");
  }
  return icons[key];
}
const sections = new Set();
function slideOf(master, section, kicker, title) {
  if (!sections.has(section)) { pres.addSection({ title: section }); sections.add(section); }
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (kicker) s.addText(kicker, { placeholder: "kicker", ...RTL });
  if (title) s.addText(title, { placeholder: "title", ...RTL });
  return s;
}
function T(s, text, o) {
  s.addText(text, { isTextBox: true, margin: 0, valign: "top", fontSize: 15, color: C.text1, ...RTL, ...o });
}
function card(s, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: o.fill || C.background2 }, line: { color: o.line || o.fill || C.background2, width: o.lineW || 1 },
    objectName: o.name,
  });
}
async function dot(s, x, y, d, iconName, o = {}) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: o.fill || C.accent1 }, line: { color: o.fill || C.accent1 } });
  if (iconName) s.addImage({ data: await icon(iconName, o.iconHex || "FFFFFF"), x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5 });
  if (o.num !== undefined) T(s, String(o.num), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: o.numSize || 18, bold: true, color: o.numColor || C.background1 });
}
function shadow() { return { type: "outer", color: "0A2E2A", opacity: 0.18, blur: 8, offset: 3, angle: 90 }; }
function pic(s, file, x, y, w, h, alt) { s.addImage({ path: M(file), x, y, w, h, altText: alt, shadow: shadow() }); }

// rows of icon + head + body, right-aligned, in a column [x, x+w]
async function rows(s, items, x, y, w, rowH, o = {}) {
  const d = o.d || 0.62;
  for (let i = 0; i < items.length; i++) {
    const [ic, head, body] = items[i];
    const yy = y + i * rowH;
    if (o.cards) card(s, x, yy, w, rowH - 0.14);
    const pad = o.cards ? 0.2 : 0;
    await dot(s, x + w - d - pad, yy + (o.cards ? (rowH - 0.14 - d) / 2 : 0.02), d, o.numbers ? null : ic, o.numbers ? { num: i + 1 } : {});
    const tw = w - d - 0.25 - pad * 2;
    const ty = yy + (o.cards ? 0.12 : 0);
    T(s, head, { x: x + pad, y: ty, w: tw, h: 0.36, fontSize: o.headSize || 17, bold: true, color: C.text2 });
    if (body) T(s, body, { x: x + pad, y: ty + 0.38, w: tw, h: rowH - 0.55, fontSize: o.bodySize || 14, color: C.text1 });
  }
}

(async () => {
  // 1 · title ---------------------------------------------------------------
  {
    const s = slideOf("DARK", "البداية", null, null);
    s.addImage({ path: M("image-1-1.png"), x: 0.9, y: 1.45, w: 4.1, h: 4.1, altText: "شخصية «حارس»" });
    T(s, "«حارس»", { x: 5.6, y: 1.15, w: 7.13, h: 1.3, fontSize: 66, bold: true, color: C.accent2 });
    T(s, "درعك الذكي ضد الروابط والمواقع والإعلانات الوهمية", { x: 5.6, y: 2.45, w: 7.13, h: 1.0, fontSize: 24, bold: true, color: C.background1 });
    T(s, "مساعد ذكي على واتساب والويب يفتح الرابط المشبوه بأمان ويحكم على الموقع نفسه، ويرشد الضحية في الساعة الأولى، ويجهّز للجهة المختصة ملف أدلة لإزالة الموقع الوهمي.",
      { x: 5.6, y: 3.55, w: 7.13, h: 1.1, fontSize: 16, color: C.accent6 });
    const chips = ["يحذّرك", "يرشدك", "يوصّل بلاغك"];
    chips.forEach((c, i) => {
      const cw = 1.75, cx = R - (i + 1) * cw - i * 0.2;
      card(s, cx, 4.75, cw, 0.55, { fill: C.accent4 });
      T(s, c, { x: cx, y: 4.75, w: cw, h: 0.55, align: "center", valign: "middle", fontSize: 16, bold: true, color: C.background1 });
    });
    T(s, "هاكاثون الذكاء الاصطناعي للأمن 2026 · كشف الروابط والمواقع الوهمية في الجرائم الإلكترونية والاحتيال المالي",
      { x: 5.6, y: 5.75, w: 7.13, h: 0.5, fontSize: 14, color: C.accent2, bold: true });
    T(s, "نسخة تجريبية للمسابقة: لوحة الجهة المختصة نموذج تجريبي، وليست تابعة لأي جهة حكومية. الأسماء والأرقام في الأمثلة خيالية.",
      { x: L, y: 6.85, w: CW, h: 0.4, fontSize: 11, color: C.accent6 });
  }

  // 2 · problem ---------------------------------------------------------------
  {
    const s = slideOf("LIGHT", "البداية", "المشكلة", "الاحتيال يبدأ برابط يبدو بريئاً، وينتهي بموقع يبقى يعمل");
    const items = [
      ["FaLink", "الرابط يبدو بريئاً", "أغلب الفحص المتاح يحكم على شكل الرابط فقط، فيمرّ نطاق جديد اسمه بريء، أو صفحة على منصة مواقع مجانية."],
      ["FaClock", "الضحية لا تعرف ما تفعل", "الساعة الأولى هي الأهم لإيقاف المبلغ، لكن الضحية لا تعرف بمن تتصل أولاً ولا كيف تبلّغ، وقد لا تتكلم العربية."],
      ["FaServer", "الموقع الوهمي يبقى", "حتى حين يُكشف الموقع، لا يعرف أحد بسرعة مَن سجّل النطاق ومَن يستضيفه، ولمن يُرسل طلب الإزالة."],
    ];
    const cw = (CW - 2 * 0.3) / 3;
    for (let i = 0; i < 3; i++) {
      const x = R - (i + 1) * cw - i * 0.3, [ic, h, b] = items[i];
      card(s, x, 1.65, cw, 3.55);
      await dot(s, x + cw - 0.3 - 0.85, 1.95, 0.85, ic);
      T(s, h, { x: x + 0.3, y: 2.95, w: cw - 0.6, h: 0.5, fontSize: 19, bold: true, color: C.text2 });
      T(s, b, { x: x + 0.3, y: 3.55, w: cw - 0.6, h: 1.55, fontSize: 15 });
    }
    card(s, L, 5.5, CW, 1.15, { fill: "FFF4D6", line: HEX.accent2 });
    await dot(s, R - 0.25 - 0.65, 5.75, 0.65, "FaBullhorn", { fill: C.accent2, iconHex: "3A2A00" });
    T(s, [{ text: "والإعلانات الوهمية أيضاً: ", options: { bold: true } },
      { text: "سيارة بأقل بكثير من سعر السوق مع عربون قبل المعاينة، أو تأجير استراحات وعزب ومخيمات بدفع مقدّم. وقد حذّرت شرطة أبوظبي منها في 22 نوفمبر 2026." }],
      { x: L + 0.3, y: 5.62, w: CW - 1.4, h: 0.95, fontSize: 15, color: "3A2A00", valign: "middle" });
  }

  // 3 · agenda ---------------------------------------------------------------
  {
    const s = slideOf("LIGHT", "البداية", "محتوى العرض", "أربعة أجزاء: من البناء إلى الرؤية");
    const parts = [
      ["البناء التقني", "البنية، ومحرك الكشف، والفحص الحي للموقع، والخصوصية"],
      ["مراحل «حارس» بالتفصيل", "من أول رسالة مشبوهة حتى إزالة الموقع الوهمي وتحذير الناس"],
      ["النتائج المقاسة", "أرقام من الخادم الحيّ على مواقع احتيال حقيقية"],
      ["الأهداف ومراحل التطوير", "الهدف، والتحديث التالي في كل هاتف، والتطور خلال أشهر"],
    ];
    const cw = (CW - 0.3) / 2, ch = 2.35;
    for (let i = 0; i < 4; i++) {
      const col = i % 2, row = Math.floor(i / 2);
      const x = R - (col + 1) * cw - col * 0.3, y = 1.7 + row * (ch + 0.3);
      card(s, x, y, cw, ch);
      await dot(s, x + cw - 0.35 - 1.1, y + (ch - 1.1) / 2, 1.1, null, { num: i + 1, numSize: 36 });
      T(s, parts[i][0], { x: x + 0.35, y: y + 0.6, w: cw - 1.9, h: 0.5, fontSize: 22, bold: true, color: C.text2 });
      T(s, parts[i][1], { x: x + 0.35, y: y + 1.15, w: cw - 1.9, h: 0.8, fontSize: 15 });
    }
  }

  // ====================== 1 · technical build ===============================
  const S1 = "1 · البناء التقني";
  // 4 · architecture
  {
    const s = slideOf("LIGHT", S1, S1, "نواة واحدة خلف قنوات بسيطة، ولوحة للجهة المختصة");
    const y = 1.6, h = 4.35;
    const cols = [
      { x: 9.43, w: 3.3, head: "القنوات", ic: "FaWhatsapp", items: ["واتساب للأعمال", "دردشة الويب", "خمس لغات: العربية والإنجليزية والأردية والهندية والروسية", "نص، أو رسالة صوتية، أو لقطات شاشة"] },
      { x: 4.53, w: 4.2, head: "نواة «حارس»", ic: "FaShieldAlt", dark: true, items: ["محرك الكشف: قواعد شفافة وذكاء اصطناعي", "الفحص الحي للموقع", "ملف أدلة الإزالة", "البلاغات والإحالة", "رادار الحملات والتنبيهات"] },
      { x: 0.6, w: 3.3, head: "الجهة المختصة", ic: "FaUniversity", items: ["لوحة تفرز كل بلاغ إلى الفريق المناسب", "أدلة الإزالة بنقرة", "اعتماد التحذيرات قبل إرسالها", "سؤال المُبلّغ من اللوحة"] },
    ];
    for (const c of cols) {
      card(s, c.x, y, c.w, h, c.dark ? { fill: C.accent1 } : {});
      await dot(s, c.x + c.w - 0.25 - 0.7, y + 0.25, 0.7, c.ic, c.dark ? { fill: C.background1, iconHex: HEX.accent1 } : {});
      T(s, c.head, { x: c.x + 0.2, y: y + 0.3, w: c.w - 1.3, h: 0.6, fontSize: 18, bold: true, valign: "middle", color: c.dark ? C.accent2 : C.text2 });
      T(s, c.items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < c.items.length - 1 } })),
        { x: c.x + 0.25, y: y + 1.15, w: c.w - 0.5, h: h - 1.35, fontSize: 15, paraSpaceAfter: 8, color: c.dark ? C.background1 : C.text1 });
    }
    for (const ax of [8.86, 3.96]) s.addShape(pres.shapes.LEFT_ARROW, { x: ax, y: y + h / 2 - 0.25, w: 0.45, h: 0.5, fill: { color: C.accent2 }, line: { color: C.accent2 } });
    const chips = ["البيانات الشخصية تُخفى قبل أن يراها الذكاء الاصطناعي", "إن توقف الذكاء الاصطناعي تعمل القواعد وحدها", "ولا يرسل «حارس» شيئاً للجهات بنفسه"];
    const cw = (CW - 0.6) / 3;
    chips.forEach((t, i) => {
      const x = R - (i + 1) * cw - i * 0.3;
      card(s, x, 6.15, cw, 0.62, { fill: C.background1, line: HEX.accent6 });
      T(s, t, { x: x + 0.15, y: 6.15, w: cw - 0.3, h: 0.62, align: "center", valign: "middle", fontSize: 13, bold: true, color: C.accent4 });
    });
  }
  // 5 · detection engine
  {
    const s = slideOf("LIGHT", S1, S1, "القواعد تحكم، والذكاء الاصطناعي رأي ثانٍ");
    await rows(s, [
      ["FaListUl", "قواعد شفافة", "16 نوعاً من الاحتيال: انتحال البنوك والجهات، رمز التحقق، الطرود والوظائف والجوائز، الابتزاز، والإعلانات الوهمية. كل تحذير يُشرح بجملة واحدة."],
      ["FaRobot", "الذكاء الاصطناعي: Gemini 3.5 Flash-Lite", "يقرأ الرسالة والصفحة، ويفهم الصياغات التي لم تُكتب لها قاعدة، ويقارن سعر الإعلان بسعر السوق المعتاد في الإمارات."],
      ["FaUserSecret", "الخصوصية قبل النموذج", "رقم البطاقة ورمز التحقق والهوية والهاتف تُخفى قبل أن يرى النموذج أي شيء."],
      ["FaCogs", "لا يتوقف أبداً", "إن ضغطت الرسائل أو تعطل النموذج، يردّ «حارس» من قواعده المحلية خلال ثوانٍ."],
    ], 6.75, 1.65, 5.98, 1.3, { cards: true, headSize: 16, bodySize: 13 });
    s.addChart(pres.charts.BAR, [{ name: "كُشف", labels: ["القواعد وحدها", "القواعد + الذكاء الاصطناعي"], values: [2, 12] }], {
      x: L, y: 2.15, w: 5.8, h: 4.05, barDir: "col", chartColors: [HEX.accent5, HEX.accent1],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 18, dataLabelFontBold: true, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
      valAxisMaxVal: 12, valAxisMinVal: 0, valAxisMajorUnit: 4, valAxisHidden: true, valGridLine: { color: "E3EAE8", size: 0.5 }, catGridLine: { style: "none" },
      catAxisLabelColor: HEX.dk1, catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt", showLegend: false, barGapWidthPct: 70,
    });
    T(s, "رسائل احتيال بصياغات جديدة: كم كُشف من 12", { x: L, y: 1.65, w: 5.8, h: 0.45, fontSize: 16, bold: true, color: C.text2, align: "center" });
    T(s, "مُقاس في 23 نوفمبر 2026 على 12 رسالة احتيال بصياغات لم تُكتب لها قواعد.", { x: L, y: 6.3, w: 5.8, h: 0.4, fontSize: 12, color: C.accent5, align: "center" });
  }
  // 6 · live site check
  {
    const s = slideOf("LIGHT", S1, S1, "الفحص الحي: يزور الموقع بأمان قبل أن يحكم");
    const steps = [
      ["FaLock", "زيارة آمنة", "عناوين عامة فقط، والمنفذان 80 و443، ولا يُشغَّل شيء من الصفحة، ويُحذف معرّف الضحية من الرابط أولاً."],
      ["FaRoute", "يتتبع كل تحويل", "حتى الصفحة الأخيرة، ولو مرّ الرابط بأداة اختصار أو بموقع آخر."],
      ["FaDatabase", "يراجع السجلات", "عمر النطاق من RDAP، والشهادة، وقوائم Google Safe Browsing."],
      ["FaSearch", "يقرأ الصفحة", "ما تطلبه: رقم البطاقة، وكلمة المرور، ورمز التحقق، والجهة التي تنتحلها."],
      ["FaRobot", "حكم الذكاء الاصطناعي", "يقرأ نص الصفحة ويحكم عليها، ويشرح السبب بلغة المستخدم."],
      ["FaBalanceScale", "درجة خطورة موزونة", "كل مؤشر له وزن واضح، فيُعرف سبب كل حكم."],
    ];
    const cw = (CW - 0.6) / 3, ch = 2.05;
    for (let i = 0; i < 6; i++) {
      const col = i % 3, row = Math.floor(i / 3);
      const x = R - (col + 1) * cw - col * 0.3, y = 1.6 + row * (ch + 0.25);
      card(s, x, y, cw, ch);
      await dot(s, x + cw - 0.25 - 0.62, y + 0.25, 0.62, steps[i][0]);
      T(s, steps[i][1], { x: x + 0.25, y: y + 0.3, w: cw - 1.25, h: 0.5, fontSize: 17, bold: true, color: C.text2, valign: "middle" });
      T(s, steps[i][2], { x: x + 0.25, y: y + 0.98, w: cw - 0.5, h: ch - 1.05, fontSize: 14 });
    }
    const w8 = ["قائمة تهديد: 60", "حكم عالٍ من الذكاء الاصطناعي: 40", "جهة معروفة مع نموذج: 35", "نطاق جديد: 30"];
    T(s, "أمثلة على أوزان المؤشرات:", { x: 9.6, y: 6.28, w: 3.13, h: 0.45, fontSize: 13, bold: true, color: C.accent4, valign: "middle" });
    const widths = [1.35, 2.55, 2.45, 1.25, 1.2, 1.5];
    let x = 9.45;
    for (let i = 0; i < 4; i++) {
      x -= widths[i];
      card(s, x, 6.3, widths[i] - 0.1, 0.42, { fill: C.background1, line: HEX.accent6 });
      T(s, w8[i], { x, y: 6.3, w: widths[i] - 0.1, h: 0.42, fontSize: 12, align: "center", valign: "middle", color: C.text1 });
    }
  }
  // 7 · privacy + tech
  {
    const s = slideOf("LIGHT", S1, S1, "خصوصية بالتصميم، وتقنيات بسيطة يمكن تشغيلها اليوم");
    T(s, "الخصوصية والأمان", { x: 6.95, y: 1.6, w: 5.78, h: 0.45, fontSize: 19, bold: true, color: C.accent4 });
    await rows(s, [
      ["FaUserShield", "لا شيء يُرسل إلا بموافقتك", "يرى المُبلّغ ما سيُرسل، ويؤكد هويته بمحاكاة UAE PASS، أو بجواز السفر إن كان زائراً."],
      ["FaEyeSlash", "لا نحفظ رسائلك", "الفحص لا يُحفظ، والرادار يحفظ رقم المحتال ورابطه والنص بعد الإخفاء فقط."],
      ["FaTrashAlt", "البلاغ يُحذف بعد 7 أيام", "والتنبيهات تتوقف بكلمة STOP متى شئت."],
      ["FaShieldAlt", "حماية الخادم عند زيارة المواقع", "لا عناوين داخلية، ولا منافذ غير 80 و443، ولا تشغيل لأي كود من الصفحة."],
    ], 6.95, 2.2, 5.78, 1.1, { headSize: 16, bodySize: 13 });
    T(s, "التقنيات", { x: L, y: 1.6, w: 5.8, h: 0.45, fontSize: 19, bold: true, color: C.accent4 });
    const tech = ["Python", "FastAPI", "JavaScript", "Gemini 3.5", "PostgreSQL", "Render", "Meta Cloud API", "RDAP", "Safe Browsing", "Playwright"];
    const tw = 1.82, th = 0.55;
    tech.forEach((t, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const x = L + 5.8 - (col + 1) * tw - col * 0.17, y = 2.2 + row * (th + 0.17);
      card(s, x, y, tw, th, { fill: C.background2 });
      s.addText(t, { isTextBox: true, x, y, w: tw, h: th, align: "center", valign: "middle", fontSize: 14, bold: true, color: C.text2, margin: 0 });
    });
    card(s, L, 5.25, 5.8, 1.45, { fill: C.accent1 });
    T(s, "286", { x: L + 3.4, y: 5.3, w: 2.2, h: 1.35, fontSize: 54, bold: true, color: C.accent2, align: "center", valign: "middle" });
    T(s, "اختباراً آلياً تعمل مع كل تعديل، والخادم منشور ويعمل على واتساب الآن.", { x: L + 0.3, y: 5.3, w: 3.1, h: 1.35, fontSize: 15, color: C.background1, valign: "middle" });
  }

  // ====================== 2 · stages ==========================================
  const S2 = "2 · مراحل «حارس» بالتفصيل";
  const STAGES = [
    ["FaCommentDots", "يفحص الرسالة", "حكم وأسباب بلغة المستخدم"],
    ["FaGlobe", "يفتح الموقع", "يحكم على الموقع نفسه"],
    ["FaBullhorn", "الإعلان الوهمي", "يكشفه ويقارن السعر بالسوق"],
    ["FaLifeRing", "يرشد الضحية", "خطة الساعة الأولى"],
    ["FaMicrophone", "يرتّب البلاغ", "بالصوت أو الكتابة أو الصور"],
    ["FaUniversity", "يوجّه البلاغ", "إلى الفريق المختص"],
    ["FaFileSignature", "يجهّز أدلة الإزالة", "مَن يستضيف ومَن سجّل"],
    ["FaBroadcastTower", "يحذّر الجميع", "رادار الحملات والتنبيهات"],
  ];
  // 8 · overview
  {
    const s = slideOf("LIGHT", S2, S2, "ثماني مراحل: من أول رسالة مشبوهة حتى إزالة الموقع");
    const cw = (CW - 3 * 0.3) / 4, ch = 2.3;
    for (let i = 0; i < 8; i++) {
      const col = i % 4, row = Math.floor(i / 4);
      const x = R - (col + 1) * cw - col * 0.3, y = 1.65 + row * (ch + 0.3);
      card(s, x, y, cw, ch, row === 0 ? {} : { fill: "E4EFEB" });
      await dot(s, x + cw - 0.25 - 0.75, y + 0.25, 0.75, STAGES[i][0]);
      T(s, String(i + 1), { x: x + 0.25, y: y + 0.2, w: 0.8, h: 0.8, fontSize: 34, bold: true, color: C.accent6, align: "left" });
      T(s, STAGES[i][1], { x: x + 0.25, y: y + 1.2, w: cw - 0.5, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
      T(s, STAGES[i][2], { x: x + 0.25, y: y + 1.68, w: cw - 0.5, h: 0.45, fontSize: 14 });
    }
    T(s, "المراحل 1 إلى 5 للمستخدم على واتساب والويب، و6 إلى 8 للجهة المختصة في لوحتها.", { x: L, y: 6.55, w: CW, h: 0.35, fontSize: 13, color: C.accent5 });
  }
  function stageKicker(n) { return `${S2} · المرحلة ${n}`; }
  // 9 · stages 1-2
  {
    const s = slideOf("LIGHT", S2, `${S2} · المرحلتان 1 و2`, "يفحص الرسالة، ثم يفتح الموقع بنفسه ويحكم عليه");
    pic(s, "image1.png", L, 1.6, 3.2, 5.07, "نتيجة فحص الموقع في محادثة «حارس»");
    pic(s, "demo-page.png", L + 3.45, 1.6, 2.67, 5.07, "صفحة التدريب: بنك الصقر الوطني الخيالي");
    const x = 7.0, w = R - 7.0;
    card(s, x, 1.6, w, 1.05, { fill: "DCF8C6" });
    T(s, [{ text: "رسالة تصل للمستخدم: ", options: { bold: true } }, { text: "«مرحباً، هذا الرابط الذي طلبته»" }],
      { x: x + 0.2, y: 1.7, w: w - 0.4, h: 0.4, fontSize: 14, valign: "middle" });
    s.addText("haris-uae.onrender.com/demo/go", { isTextBox: true, x: x + 0.2, y: 2.12, w: w - 0.4, h: 0.4, fontSize: 14, bold: true, color: HEX.hlink, align: "right", valign: "middle", margin: 0, rtlMode: false, objectName: "link-9" });
    card(s, x, 2.85, w, 0.75, { fill: C.background2 });
    T(s, [{ text: "من شكل الرسالة والرابط فقط: ", options: { bold: true } }, { text: "«لم نجد مؤشرات واضحة»" }], { x: x + 0.2, y: 2.85, w: w - 0.4, h: 0.75, fontSize: 15, valign: "middle", color: C.accent5 });
    card(s, x, 3.8, w, 0.75, { fill: "FCE8E6", line: HEX.accent3 });
    T(s, [{ text: "بعد أن يزور «حارس» الموقع: ", options: { bold: true } }, { text: "خطورة عالية، رابط تصيّد", options: { bold: true, color: HEX.accent3 } }], { x: x + 0.2, y: 3.8, w: w - 0.4, h: 0.75, fontSize: 15, valign: "middle" });
    const found = ["يتحوّل الرابط إلى صفحة بنك على منصة مجانية ليست نطاقه", "تطلب رقم البطاقة وكلمة المرور ورمز التحقق", "الذكاء الاصطناعي يقرأ الصفحة ويشرح السبب بلغة المستخدم", "ويقول له ماذا يفعل الآن: لا تُدخل شيئاً، وبلّغ بضغطة"];
    T(s, found.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < found.length - 1 } })), { x, y: 4.75, w, h: 1.9, fontSize: 14, paraSpaceAfter: 6 });
  }
  // 10 · stage 3 fake ads
  {
    const s = slideOf("LIGHT", S2, stageKicker(3), "يكشف إعلانات البيع والتأجير الوهمية");
    pic(s, "ad-1.png", 4.25, 1.6, 2.4, 5.14, "محادثة الإبلاغ عن إعلان وهمي");
    pic(s, "radar-ad.png", L, 1.6, 3.4, 1.63, "الإعلان الوهمي في رادار الحملات");
    T(s, "في لوحة الجهة: الحملة بشارة «إعلان وهمي» والمنصات التي رآه عليها المُبلّغون، ويمكن عرض الإعلانات الوهمية وحدها.", { x: L, y: 3.4, w: 3.4, h: 1.2, fontSize: 13, color: C.accent5 });
    card(s, L, 4.75, 3.4, 1.99, { fill: "FFF4D6", line: HEX.accent2 });
    T(s, [{ text: "مثال حقيقي الشكل: ", options: { bold: true, breakLine: true } }, { text: "سيارة فاخرة موديل 2024 بـ200 ألف درهم، وسعرها في السوق نحو 380 ألفاً، «بداعي السفر»، وعربون 1000 درهم قبل المعاينة." }],
      { x: L + 0.2, y: 4.85, w: 3.0, h: 1.8, fontSize: 13, color: "3A2A00" });
    const x = 7.0, w = R - 7.0;
    T(s, "ما يكشفه «حارس»", { x, y: 1.6, w, h: 0.42, fontSize: 17, bold: true, color: C.accent4 });
    const ind = [["سعر أقل بكثير من السوق", "يقارنه الذكاء الاصطناعي بسعر الموديل المعتاد"], ["عربون قبل المعاينة", "أو دفع مقدّم لتأجير دراجة أو استراحة أو عزبة أو مخيم"], ["ذريعة الاستعجال", "«بداعي السفر»، «آخر فرصة»، «تحويل فقط»"]];
    await rows(s, ind.map(([h, b]) => ["FaExclamationTriangle", h, b]), x, 2.1, w, 0.95, { d: 0.5, headSize: 15, bodySize: 13 });
    T(s, "ثم يسأل سؤالين", { x, y: 5.0, w, h: 0.4, fontSize: 17, bold: true, color: C.accent4 });
    const fw = (w - 0.2) / 2;
    card(s, x + fw + 0.2, 5.45, fw, 1.25, { fill: C.background2 });
    T(s, [{ text: "لم تدفع؟", options: { bold: true, breakLine: true } }, { text: "يذهب الإعلان إلى رادار الحملات ليحمي غيرك." }], { x: x + fw + 0.35, y: 5.52, w: fw - 0.3, h: 1.1, fontSize: 13 });
    card(s, x, 5.45, fw, 1.25, { fill: "FCE8E6" });
    T(s, [{ text: "دفعت؟", options: { bold: true, breakLine: true } }, { text: "يبدأ بلاغ كامل والإعلان فيه، مع خطة الساعة الأولى." }], { x: x + 0.15, y: 5.52, w: fw - 0.3, h: 1.1, fontSize: 13 });
  }
  // 11 · stages 4-5
  {
    const s = slideOf("LIGHT", S2, `${S2} · المرحلتان 4 و5`, "يرشد الضحية في الساعة الأولى، ويرتّب البلاغ عنها");
    pic(s, "v-report.png", L, 1.6, 3.06, 5.08, "ملف البلاغ وتأكيد الهوية");
    pic(s, "v-help.png", L + 3.3, 1.6, 3.06, 5.08, "خطة الطوارئ بعد دفع المال");
    const x = 7.3, w = R - 7.3;
    await dot(s, R - 0.6, 1.62, 0.6, null, { num: 4 });
    T(s, "يرشد فوراً", { x, y: 1.66, w: w - 0.8, h: 0.5, fontSize: 19, bold: true, color: C.text2 });
    const a = ["اتصل بالبنك أولاً ليوقف المبلغ", "أوقف البطاقة وغيّر كلمات المرور", "احتفظ بالأدلة، وأرقام البلاغ الرسمية جاهزة"];
    T(s, a.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1 } })), { x, y: 2.3, w, h: 1.4, fontSize: 15, paraSpaceAfter: 6 });
    await dot(s, R - 0.6, 3.92, 0.6, null, { num: 5 });
    T(s, "بلاغ بطريقتك", { x, y: 3.96, w: w - 0.8, h: 0.5, fontSize: 19, bold: true, color: C.text2 });
    const b = ["احكِ ما حدث كتابةً أو برسالة صوتية، وأرسل حتى 5 لقطات شاشة", "«حارس» يصحح الإملاء ويستخرج المبلغ والوقت والإمارة في ملخص قابل للتعديل", "تأكيد الهوية بمحاكاة UAE PASS، أو بجواز السفر للزائر", "رقم مرجعي فوراً، وإشعار على واتساب مع كل خطوة"];
    T(s, b.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < b.length - 1 } })), { x, y: 4.6, w, h: 2.1, fontSize: 15, paraSpaceAfter: 6 });
  }
  // 12 · stage 6 authority dashboard
  {
    const s = slideOf("LIGHT", S2, stageKicker(6), "كل بلاغ يصل إلى الفريق القادر على التصرف فيه");
    pic(s, "image-11-1.png", L, 1.7, 6.55, 4.58, "لوحة الجهة المختصة");
    T(s, "لوحة الجهة المختصة: البلاغات بتوقيت الإمارات، والأولوية لما يحتاج تصرفاً عاجلاً.", { x: L, y: 6.38, w: 6.55, h: 0.35, fontSize: 12, color: C.accent5, align: "center" });
    await rows(s, [
      ["FaBolt", "الحماية العاجلة", "ابتزاز أو خطر مباشر على شخص"],
      ["FaMoneyBillWave", "الفريق المالي", "دفع أو تحويل: الساعة الأولى تُحسب"],
      ["FaPhoneAlt", "الأرقام والاتصالات", "مكالمات ورسائل من أرقام منتحِلة"],
      ["FaAt", "الحسابات والبريد والروابط", "اختراق حساب أو موقع وهمي"],
      ["FaSatelliteDish", "رادار الحملات", "رسائل وإعلانات تتكرر بين الناس"],
    ], 7.45, 1.65, R - 7.45, 0.86, { d: 0.55, headSize: 16, bodySize: 13 });
    card(s, 7.45, 6.0, R - 7.45, 0.72, { fill: C.background2 });
    T(s, "يقترح «حارس» الفريق وسببه، والضابط يعتمد أو يحوّل أو يسأل المُبلّغ، والسؤال يصله بلغته على واتساب.", { x: 7.6, y: 6.0, w: R - 7.75, h: 0.72, fontSize: 13, valign: "middle" });
  }
  // 13 · stage 7 evidence
  {
    const s = slideOf("LIGHT", S2, stageKicker(7), "من الكشف إلى إزالة الموقع: ملف أدلة جاهز بنقرة واحدة");
    pic(s, "image2.png", L, 1.6, 5.0, 5.05, "ملف أدلة الإزالة لصفحة التدريب");
    await rows(s, [
      ["FaIdCard", "مَن سجّل النطاق", "المسجّل ورقمه لدى IANA وبريد الإبلاغ وهاتفه، من سجل RDAP للنطاق نفسه."],
      ["FaServer", "مَن يستضيفه", "عنوان الخادم والشركة المالكة وبريد الإبلاغ، من سجل RDAP للعنوان."],
      ["FaFingerprint", "دليل على ما رآه «حارس»", "بصمة SHA-256 للصفحة ووقت الفحص، لملف القضية."],
      ["FaEnvelopeOpenText", "ثلاث مسودات جاهزة", "تعليق النطاق، وإزالة الصفحة، وحجبه داخل الدولة."],
    ], 6.0, 1.6, R - 6.0, 1.12, { cards: true, headSize: 16, bodySize: 13 });
    T(s, "الضابط يراجع ويرسل، و«حارس» نفسه لا يرسل شيئاً.", { x: 6.0, y: 6.15, w: R - 6.0, h: 0.5, fontSize: 15, bold: true, color: C.accent4, valign: "middle" });
  }
  // 14 · stage 8 radar & alerts
  {
    const s = slideOf("LIGHT", S2, stageKicker(8), "رادار الحملات: رسالة تجاهلتها تحمي الجميع");
    pic(s, "v-radar.png", L, 1.6, 6.3, 4.72, "رادار الحملات وتحذير بخمس لغات");
    await rows(s, [
      ["", "البلاغات المتشابهة تتجمّع", "نفس الرقم أو الرابط أو الصياغة، من أشخاص مختلفين، في حملة واحدة."],
      ["", "الحملة تظهر في الرادار", "عدد البلاغات خلال 24 ساعة، والمنصات، ورقم المعلن في الإعلانات الوهمية."],
      ["", "تحذير بخمس لغات", "يترجمه «حارس»، ويراجعه الضابط قبل اعتماده. القرار دائماً للجهة المختصة."],
      ["", "يصل إلى المشتركين على واتساب", "كلٌّ بلغته، قبل أن يقع غيرهم ضحية. ويتوقف بكلمة STOP."],
    ], 7.25, 1.6, R - 7.25, 1.2, { numbers: true, headSize: 16, bodySize: 13 });
  }
  // 15 · everyone
  {
    const s = slideOf("LIGHT", S2, S2, "يخدم كل من يعيش في الإمارات أو يزورها، بلغته");
    pic(s, "v-visitor.png", L, 1.6, 3.06, 5.08, "زائرة تبلّغ بالروسية");
    const aud = [
      ["FaPlaneDeparture", "الزوار", "لا يحتاجون هوية إماراتية: جواز السفر يكفي، وشارة «يغادر خلال 3 أيام» تقدّم بلاغهم، وتُقترح شرطة السياحة."],
      ["FaChild", "الأطفال", "يطمئنهم «حارس» بأنهم ليسوا مخطئين، ولا يطلب بيانات، ويوجّههم إلى خط حماية الطفل 116111 أو وليّ الأمر."],
      ["FaUserFriends", "كبار السن", "كلمات بسيطة، ويمكنهم التحدث بدل الكتابة."],
      ["FaLanguage", "العمال والمقيمون", "العربية والإنجليزية والأردية والهندية والروسية، والضابط يقرأ كل شيء بالعربية مع النص الأصلي."],
    ];
    const gx = 4.0, gw = R - gx, cw = (gw - 0.3) / 2, ch = 2.4;
    for (let i = 0; i < 4; i++) {
      const col = i % 2, row = Math.floor(i / 2);
      const x = R - (col + 1) * cw - col * 0.3, y = 1.6 + row * (ch + 0.28);
      card(s, x, y, cw, ch);
      await dot(s, x + cw - 0.25 - 0.6, y + 0.25, 0.6, aud[i][0]);
      T(s, aud[i][1], { x: x + 0.25, y: y + 0.3, w: cw - 1.3, h: 0.5, fontSize: 18, bold: true, color: C.text2, valign: "middle" });
      T(s, aud[i][2], { x: x + 0.25, y: y + 1.0, w: cw - 0.5, h: ch - 1.1, fontSize: 14 });
    }
  }

  // ====================== 3 · results ==========================================
  const S3 = "3 · النتائج المقاسة";
  {
    const s = slideOf("LIGHT", S3, S3, "مُقاس على الخادم الحيّ، على مواقع احتيال حقيقية");
    const stats = [["0 من 23", "إنذار خاطئ على مواقع حقيقية: بنوك وشرطة وصفحات دخول وأخبار"], ["52%", "من مواقع الاحتيال الحيّة كُشفت (17 من 33) على قائمة لم يُضبط عليها"], ["12 من 12", "رسالة بصياغة جديدة كشفها الذكاء الاصطناعي"], ["286", "اختباراً آلياً"]];
    const cw = (CW - 0.9) / 4;
    stats.forEach(([n, l], i) => {
      const x = R - (i + 1) * cw - i * 0.3;
      card(s, x, 1.6, cw, 2.05, i === 1 ? { fill: C.accent1 } : {});
      T(s, n, { x: x + 0.2, y: 1.7, w: cw - 0.4, h: 0.85, fontSize: 38, bold: true, align: "center", valign: "middle", color: i === 1 ? C.accent2 : C.text2 });
      T(s, l, { x: x + 0.2, y: 2.58, w: cw - 0.4, h: 1.0, fontSize: 13, align: "center", color: i === 1 ? C.background1 : C.text1 });
    });
    s.addChart(pres.charts.BAR, [{ name: "نسبة الكشف", labels: ["الجولة الأولى", "الجولة الثانية"], values: [43, 52] }], {
      x: L, y: 4.4, w: 5.6, h: 2.4, barDir: "col", chartColors: [HEX.accent5, HEX.accent1],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 16, dataLabelFontBold: true, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0\"%\"",
      valAxisMaxVal: 100, valAxisMinVal: 0, valAxisHidden: true, valGridLine: { color: "E3EAE8", size: 0.5 }, catGridLine: { style: "none" },
      catAxisLabelColor: HEX.dk1, catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", showLegend: false, barGapWidthPct: 90,
    });
    T(s, "نسبة كشف مواقع الاحتيال الحيّة في جولتي القياس", { x: L, y: 3.95, w: 5.6, h: 0.42, fontSize: 15, bold: true, color: C.text2, align: "center" });
    const x = 6.6, w = R - 6.6;
    T(s, "ماذا يعني ذلك", { x, y: 3.95, w, h: 0.42, fontSize: 17, bold: true, color: C.accent4 });
    const m = ["صفر إنذارات خاطئة: لا يخيف «حارس» الناس من مواقع بنوكهم وجهاتهم الرسمية", "أغلب ما فات صفحات تُبنى بالجافاسكريبت على منصات مجانية، وقراءتها تحتاج متصفحاً حقيقياً", "المتصفح الحقيقي هو أول خطوة في مرحلة التدريب، والهدف كشف أكثر من 80%"];
    T(s, m.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < m.length - 1 } })), { x, y: 4.45, w, h: 2.3, fontSize: 15, paraSpaceAfter: 8 });
  }

  // ====================== 4 · goals & roadmap ===================================
  const S4 = "4 · الأهداف ومراحل التطوير";
  // 17 · goal
  {
    const s = slideOf("DARK", S4, S4, "الهدف: درع ذكي يحمي في كل لحظة");
    const g = [
      ["FaShieldAlt", "قبل الجريمة", "يحذّرك قبل أن تضغط على الرابط أو تدفع العربون"],
      ["FaLifeRing", "أثناءها", "يرشدك إن وقعت، خطوة بخطوة، في الساعة الأولى"],
      ["FaMicrophone", "بعدها", "يوصّل بلاغك بلغتك إلى الفريق المختص"],
      ["FaFileSignature", "عند المصدر", "يساعد على إزالة الموقع الوهمي وتحذير الجميع"],
    ];
    const cw = (CW - 0.9) / 4;
    for (let i = 0; i < 4; i++) {
      const x = R - (i + 1) * cw - i * 0.3;
      card(s, x, 1.9, cw, 3.7, { fill: "13574F" });
      await dot(s, x + (cw - 1.0) / 2, 2.2, 1.0, g[i][0], { fill: C.accent2, iconHex: "2B2200" });
      T(s, g[i][1], { x: x + 0.25, y: 3.4, w: cw - 0.5, h: 0.55, fontSize: 22, bold: true, color: C.accent2, align: "center" });
      T(s, g[i][2], { x: x + 0.25, y: 4.0, w: cw - 0.5, h: 1.4, fontSize: 15, color: C.background1, align: "center" });
    }
    for (let i = 0; i < 3; i++) {
      const x = R - (i + 1) * cw - i * 0.3 - 0.3;
      s.addShape(pres.shapes.LEFT_ARROW, { x: x + 0.02, y: 3.6, w: 0.26, h: 0.32, fill: { color: C.accent2 }, line: { color: C.accent2 } });
    }
    T(s, "من أول رسالة مشبوهة حتى إزالة الموقع الوهمي، بلغة كل من يعيش في الإمارات.", { x: L, y: 6.0, w: CW, h: 0.6, fontSize: 18, color: C.accent6, align: "center" });
  }
  // 18 · next update phones
  {
    const s = slideOf("LIGHT", S4, `${S4} · التحديث التالي`, "التحديث التالي: مساعد ذكي في كل هاتف، مثل سيري");
    const ph = [["image3.png", "على أي تطبيق", "«يا حارس، هل هذا حقيقي؟»: يقرأ الشاشة ويقارن السعر"], ["image4.png", "رسالة نصية", "يفحص الرابط قبل أن تضغطه، وينقل الاحتيال جانباً"], ["image5.png", "مكالمة واردة", "ينبّهك على شاشة المكالمة إن كان الرقم مُبلَّغاً عنه"], ["image6.png", "«وقعت في الفخ»", "بصوتك: يتصل بالبنك أولاً، ثم يوصّل البلاغ"]];
    const cw = CW / 4, pw = 1.75, phh = pw * 1240 / 600;
    ph.forEach(([f, h, b], i) => {
      const x = R - (i + 1) * cw;
      s.addImage({ path: M(f), x: x + (cw - pw) / 2, y: 1.55, w: pw, h: phh, altText: h });
      T(s, h, { x: x + 0.15, y: 5.25, w: cw - 0.3, h: 0.4, fontSize: 17, bold: true, color: C.text2, align: "center" });
      T(s, b, { x: x + 0.15, y: 5.68, w: cw - 0.3, h: 0.75, fontSize: 13, align: "center" });
    });
    T(s, "على أندرويد يكون «حارس» المساعد الافتراضي، وعلى آيفون يعمل مع سيري («يا سيري، اسأل حارس») وزر الإجراء وقائمة المشاركة. العقل يعمل اليوم، وما بقي هو تطبيق الهاتف.",
      { x: L, y: 6.45, w: CW, h: 0.5, fontSize: 12, color: C.accent5, align: "center" });
  }
  // 19 · roadmap
  {
    const s = slideOf("LIGHT", S4, S4, "التطور خلال أشهر: من التدريب إلى درع وطني كامل");
    const st = [
      ["FaGraduationCap", "الشهر 1–2", "التدريب", "يتعلم من البلاغات التي يؤكدها الضباط، ويقرأ كل الصفحات بمتصفح حقيقي.", "الهدف: كشف أكثر من 80%"],
      ["FaMobileAlt", "الشهر 3–4", "في كل هاتف", "مساعد مثل سيري: يفحص الرسائل تلقائياً، وينبّه أثناء المكالمات، ويقرأ الشاشة بأمرك.", "تطبيق أندرويد وآيفون"],
      ["FaLink", "الشهر 5–6", "الربط الرسمي", "البلاغ يدخل نظام القضايا مباشرة، مع UAE PASS، وقائمة الحظر الرسمية، ورقم قصير للرسائل.", "شريك حكومي"],
      ["FaShieldAlt", "بعدها", "الدرع الوطني", "فحص روابط الرسائل على مستوى الشبكة قبل أن تصل إلى الهاتف، وداخل التطبيقات الرسمية.", "قبل أن تصل الرسالة"],
    ];
    const cw = (CW - 0.9) / 4, ly = 2.25;
    s.addShape(pres.shapes.LINE, { x: L + cw / 2, y: ly, w: CW - cw, h: 0, line: { color: C.accent6, width: 4 } });
    for (let i = 0; i < 4; i++) {
      const x = R - (i + 1) * cw - i * 0.3, [ic, when, name, body, tag] = st[i];
      T(s, when, { x, y: 1.5, w: cw, h: 0.35, fontSize: 15, bold: true, color: C.accent4, align: "center" });
      await dot(s, x + (cw - 0.8) / 2, ly - 0.4, 0.8, ic, i === 0 ? { fill: C.accent2, iconHex: "2B2200" } : {});
      card(s, x, 2.95, cw, 3.1, i === 0 ? { fill: "FFF4D6", line: HEX.accent2 } : {});
      T(s, name, { x: x + 0.25, y: 3.1, w: cw - 0.5, h: 0.5, fontSize: 21, bold: true, color: C.text2 });
      T(s, body, { x: x + 0.25, y: 3.7, w: cw - 0.5, h: 1.5, fontSize: 15 });
      card(s, x + 0.2, 5.3, cw - 0.4, 0.55, { fill: i === 0 ? C.accent2 : C.accent1 });
      T(s, tag, { x: x + 0.2, y: 5.3, w: cw - 0.4, h: 0.55, fontSize: 13, bold: true, align: "center", valign: "middle", color: i === 0 ? "2B2200" : C.background1 });
    }
    card(s, L, 6.25, CW, 0.55, { fill: C.accent1 });
    T(s, "الهدف النهائي: حماية تبدأ قبل أن تصل رسالة الاحتيال إلى الهاتف، وبلاغ يصل إلى الفريق المختص في دقائق.", { x: L + 0.3, y: 6.25, w: CW - 0.6, h: 0.55, fontSize: 15, bold: true, color: C.background1, align: "center", valign: "middle" });
  }
  // 20 · closing
  {
    const s = slideOf("DARK", S4, null, null);
    card(s, L + 0.3, 1.25, 4.4, 4.9, { fill: C.background1 });
    s.addImage({ path: path.resolve(__dirname, "../poster/haris-qr-whatsapp-official.png"), x: L + 0.6, y: 1.45, w: 3.8, h: 3.8, altText: "رمز واتساب الرسمي لـ«حارس»" });
    T(s, "امسح الرمز بكاميرا الهاتف", { x: L + 0.3, y: 5.4, w: 4.4, h: 0.5, fontSize: 15, bold: true, color: C.text2, align: "center" });
    T(s, "جرّب «حارس» الآن", { x: 5.8, y: 1.3, w: R - 5.8, h: 0.9, fontSize: 44, bold: true, color: C.accent2 });
    T(s, "يحذّرك، يرشدك، يوصّل بلاغك.", { x: 5.8, y: 2.25, w: R - 5.8, h: 0.6, fontSize: 24, bold: true, color: C.background1 });
    const links = [["FaWhatsapp", "واتساب", "+971 50 312 3535"], ["FaGlobe", "الموقع", "haris-uae.onrender.com"], ["FaGithub", "الكود", "github.com/mohamedtorky2022/Haris"]];
    for (let i = 0; i < links.length; i++) {
      const y = 3.3 + i * 0.85;
      await dot(s, R - 0.6, y, 0.6, links[i][0], { fill: C.accent4 });
      T(s, links[i][1], { x: R - 2.1, y, w: 1.3, h: 0.6, fontSize: 18, bold: true, color: C.accent2, valign: "middle" });
      s.addText(links[i][2], { isTextBox: true, x: 5.8, y, w: R - 2.2 - 5.8, h: 0.6, fontSize: 18, color: C.background1, valign: "middle", align: "right", margin: 0, rtlMode: false, objectName: "link-" + i });
    }
    T(s, "لا يجب أن يواجه أحد المحتال وحده.", { x: 5.8, y: 6.0, w: R - 5.8, h: 0.5, fontSize: 18, color: C.accent6, bold: true });
  }

  await pres.writeFile({ fileName: OUT });
  // every Arabic paragraph right-to-left, including placeholders and continuation paragraphs;
  // the three link boxes on the last slide stay left-to-right
  const zip = await JSZip.loadAsync(require("fs").readFileSync(OUT));
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/(slides|slideLayouts)\/[^/]+\.xml$/.test(n))) {
    let xml = await zip.file(name).async("string");
    xml = xml.replace(/<p:sp>[\s\S]*?<\/p:sp>/g, (sp) => {
      if (/name="link-\d"/.test(sp) || !/[\u0600-\u06FF]/.test(sp)) return sp;
      return sp.replace(/<a:pPr(?![^>]*rtl=)/g, '<a:pPr rtl="1"').replace(/<a:p>(?!<a:pPr)/g, '<a:p><a:pPr rtl="1"/>');
    });
    zip.file(name, xml);
  }
  require("fs").writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
