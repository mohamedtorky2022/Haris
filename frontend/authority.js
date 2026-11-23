// Authority dashboard for the campaign radar (demo). Plain JavaScript, text rendered with textContent only.
(() => {
  "use strict";

  const STATUS = {
    escalated: "إنذار للجهة",
    warning: "تحذير في «حارس»",
    confirmed: "تم التعميم",
    collecting: "قيد التجميع",
    dismissed: "ليست احتيالاً",
  };
  const KIND = { phone: "رقم", domain: "رابط", email: "بريد", iban: "حساب بنكي" };

  const list = document.getElementById("list");
  const adsOnly = document.getElementById("ads-only");
  adsOnly.addEventListener("change", () => refresh());
  const login = document.getElementById("login");
  const tokenInput = document.getElementById("token");
  let token = "";
  try { token = sessionStorage.getItem("haris.authority") || ""; } catch { /* storage blocked */ }
  const results = {}; // campaign id -> block requests sent, shown after confirming
  const drafts = {};  // campaign id -> the warning being prepared: { node, versions, custom, edited }

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else node.setAttribute(k, v);
    }
    for (const c of [].concat(children)) if (c) node.append(c);
    return node;
  }

  // Arabic counting: one, two (dual), 3-10 (plural), 11 and more (singular).
  const count = (n, [one, two, few, many]) => (n === 1 ? one : n === 2 ? two : n <= 10 ? `${n} ${few}` : `${n} ${many}`);
  const ago = (ts) => {
    const m = Math.max(0, Math.round((Date.now() / 1000 - ts) / 60));
    if (m < 1) return "الآن";
    if (m < 60) return `قبل ${count(m, ["دقيقة", "دقيقتين", "دقائق", "دقيقة"])}`;
    const h = Math.round(m / 60);
    if (h < 24) return `قبل ${count(h, ["ساعة", "ساعتين", "ساعات", "ساعة"])}`;
    return `قبل ${count(Math.round(h / 24), ["يوم", "يومين", "أيام", "يوماً"])}`;
  };
  const num = (n) => n.toLocaleString("ar-AE");
  const LANG = { ar: "العربية", en: "الإنجليزية", ur: "الأردية", hi: "الهندية", ru: "الروسية" };
  const MODE = { simulated: "إرسال محاكى: واتساب غير مربوط", text: "واتساب مربوط: رسالة نصية", template: "واتساب مربوط: قالب معتمد من Meta" };
  const shown = (i) => (i.kind === "phone" ? `+${i.value}` : i.value);

  async function call(path, body) {
    const res = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json", ...(token ? { "X-Authority-Token": token } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401 || res.status === 403) { login.hidden = false; throw new Error("auth"); }
    if (!res.ok) throw new Error(String(res.status));
    login.hidden = true;
    return res.json();
  }

  function card(c) {
    const node = el("article", { class: `campaign ${c.status}` });
    node.append(el("div", { class: "head" }, [
      el("span", { class: `st ${c.status}`, text: STATUS[c.status] }),
      el("h2", { text: c.category_label }),
      c.lookalike_link ? el("span", { class: "flag", text: "رابط يقلّد جهة رسمية" }) : null,
      c.ad ? el("span", { class: "flag ad", text: "📢 إعلان وهمي" }) : null,
    ]));
    node.append(el("p", { class: "meta", text: `المُبلِّغون: ${c.people} · البلاغات: ${c.reports} · أول بلاغ ${ago(c.first_seen)} · آخر بلاغ ${ago(c.last_seen)}` }));
    if (c.ad && c.platforms && c.platforms.length) {
      node.append(el("p", { class: "platforms", text: `رآه المُبلِّغون على: ${c.platforms.join("، ")}` }));
    }
    if (c.identifiers.length) {
      node.append(el("div", { class: "ids" }, c.identifiers.map((i) =>
        el("span", { class: "id" }, [el("small", { text: KIND[i.kind] || i.kind }), el("bdi", { dir: "ltr", text: shown(i) }),
          // A website in the campaign: open its takedown evidence (registrar, host, abuse contacts, drafts).
          i.kind === "domain" ? el("a", { class: "ev-link", href: `evidence.html?url=${encodeURIComponent(`https://${i.value}`)}`,
                                          target: "_blank", rel: "noopener", text: " · ملف أدلة الإزالة ↗" }) : null]))));
    }
    node.append(el("blockquote", { text: c.sample }));
    if (c.ad) {
      node.append(el("p", { class: "ad-hint", text: "للإزالة: أبلغ المنصة عن الإعلان وحساب المعلن عبر نموذج الإبلاغ عن الاحتيال لديها، واعتمد التعميم أدناه ليصل التحذير للجميع ويُطلب حظر رقم المعلن. وإن كان في الحملة رابط موقع، فافتح ملف أدلة الإزالة بجانبه." }));
    }

    if (results[c.id]) {
      const r = results[c.id];
      node.append(el("p", { class: "done", text: r.blocks.length
        ? `صدر التحذير الرسمي، وأُرسل طلب حظر (محاكاة) لشركات الاتصالات عن: ${r.blocks.map(shown).join("، ")}`
        : "صدر التحذير الرسمي لكل مستخدمي «حارس»." }));
      if (r.wa) node.append(el("p", { class: "done", text: `📲 بدأ إرسال التحذير على واتساب إلى ${num(r.wa.total)} مشتركاً بلغاتهم. التقدّم في «تنبيهات واتساب» أعلاه.` }));
    }
    if (c.status !== "confirmed" && c.status !== "dismissed") {
      node.append(composer(c));
      const actions = el("div", { class: "actions" });
      const approve = twoStep("اعتماد التعميم وطلب الحظر", "اضغط مرة أخرى للتأكيد", "primary", () => decide(c.id, "confirmed"));
      approve.disabled = !drafts[c.id] || !drafts[c.id].versions;
      approve.title = approve.disabled ? "عاين التحذير بكل اللغات أولاً" : "";
      approve.dataset.approve = c.id;
      actions.append(approve);
      actions.append(twoStep("ليست احتيالاً", "اضغط مرة أخرى للتأكيد", "", () => decide(c.id, "dismissed")));
      node.append(actions);
    }
    return node;
  }

  // The warning, in every language, is seen by the officer before it goes out.
  const LANGS = [["ar", "العربية"], ["en", "الإنجليزية"], ["ur", "الأردية"], ["hi", "الهندية"], ["ru", "الروسية"]];
  function composer(c) {
    const d = (drafts[c.id] = drafts[c.id] || {});
    const box = el("div", { class: "composer" });
    const own = el("textarea", { class: "own", rows: "2", placeholder: "اختياري: اكتب نص التحذير بأسلوبكم، ويترجمه «حارس» إلى اللغات الأخرى. اتركه فارغاً لاستخدام النص الرسمي القياسي." });
    own.value = d.text || "";
    own.addEventListener("input", () => { d.text = own.value; });
    const show = el("button", { type: "button", text: d.versions ? "حدّث المعاينة" : "1. عاين التحذير بكل اللغات" });
    const out = el("div", { class: "versions" });
    const err = el("p", { class: "err", role: "alert" });
    show.addEventListener("click", async () => {
      show.disabled = true;
      err.textContent = "";
      show.textContent = d.text && d.text.trim() ? "يترجم «حارس» النص…" : "جارٍ التحضير…";
      try {
        const r = await call(`/api/authority/campaigns/${encodeURIComponent(c.id)}/preview`, { text: (d.text || "").trim() });
        Object.assign(d, { versions: r.versions, custom: r.custom, translated: r.translated, edited: {} });
        renderVersions(d, out);
        const approve = box.parentNode && box.parentNode.querySelector(`[data-approve="${c.id}"]`);
        if (approve) { approve.disabled = false; approve.title = ""; }
      } catch { err.textContent = "تعذّرت المعاينة، حاول مرة أخرى."; }
      show.disabled = false;
      show.textContent = "حدّث المعاينة";
    });
    if (d.versions) renderVersions(d, out);
    box.append(el("h3", { text: "📢 نص التحذير الذي سيصل للجميع" }), own, show, err, out);
    d.node = box;
    return box;
  }

  function renderVersions(d, out) {
    out.replaceChildren(...LANGS.map(([code, name]) => {
      const v = d.versions[code];
      const mine = d.custom && d.custom[code];
      const how = !d.custom ? "النص الرسمي القياسي"
        : d.translated[code] === false ? "⚠️ تعذّرت الترجمة: يظهر النص القياسي، ويمكنك كتابة نص هنا"
        : d.translated[code] ? "ترجمة آلية: راجعها وعدّلها إن لزم" : "نصك";
      const area = el("textarea", { dir: "auto", rows: "3" });
      area.value = (d.edited && d.edited[code]) ?? v.body;
      area.addEventListener("input", () => { d.edited[code] = area.value; });
      return el("div", { class: `version${mine ? "" : " standard"}` }, [
        el("div", { class: "vhead" }, [el("b", { text: name }), el("span", { text: how })]),
        el("strong", { dir: "auto", text: v.title }), area,
      ]);
    }));
  }

  // The text per language that goes out: the officer's edits win, then their own wording, then nothing (standard).
  function customOf(id) {
    const d = drafts[id];
    if (!d || !d.versions) return null;
    const own = {};
    for (const [code] of LANGS) {
      const edited = d.edited && d.edited[code] !== undefined && d.edited[code].trim() !== d.versions[code].body;
      if (edited) own[code] = d.edited[code].trim();
      else if (d.custom && d.custom[code]) own[code] = d.custom[code];
    }
    return Object.keys(own).length ? own : null;
  }

  // A second click within 4 seconds confirms: no browser dialogs.
  function twoStep(label, confirmLabel, cls, action) {
    const b = el("button", { type: "button", class: cls, text: label });
    let armed = null;
    b.addEventListener("click", () => {
      if (armed) { clearTimeout(armed); armed = null; b.disabled = true; action(); return; }
      b.textContent = confirmLabel;
      b.classList.add("armed");
      armed = setTimeout(() => { armed = null; b.textContent = label; b.classList.remove("armed"); }, 4000);
    });
    return b;
  }

  async function decide(id, status) {
    try {
      const custom = status === "confirmed" ? customOf(id) : null;
      const r = await call(`/api/authority/campaigns/${encodeURIComponent(id)}`, { status, ...(custom ? { custom } : {}) });
      delete drafts[id];
      if (status === "confirmed") results[id] = { blocks: r.block_requests, wa: r.whatsapp_alert };
    } catch { /* shown on next refresh */ }
    refresh();
  }

  async function refresh() {
    let items;
    try { items = await call("/api/authority/campaigns"); } catch { return; }
    for (const k of Object.keys(STATUS)) {
      const n = document.getElementById(`n-${k}`);
      if (n) n.textContent = items.filter((c) => c.status === k).length;
    }
    // A card with a warning being prepared is kept as it is, so a refresh never wipes what the officer is typing.
    const typing = document.activeElement && document.activeElement.closest && document.activeElement.closest(".campaign");
    if (typing && list.contains(typing)) { showAlerts(); return; }
    document.getElementById("n-ads").textContent = items.filter((c) => c.ad).length;
    const shownItems = adsOnly.checked ? items.filter((c) => c.ad) : items;
    list.replaceChildren(...(shownItems.length ? shownItems.map(card)
      : [el("p", { class: "empty", text: adsOnly.checked ? "لا توجد بلاغات عن إعلانات وهمية خلال آخر 24 ساعة." : "لا توجد بلاغات خلال آخر 24 ساعة." })]));
    showAlerts();
    document.getElementById("updated").textContent = `آخر تحديث: ${new Date().toLocaleTimeString("ar-AE")} · يتحدّث تلقائياً كل 5 ثوانٍ`;
  }

  async function showAlerts() {
    let a;
    try { a = await call("/api/authority/alerts"); } catch { return; }
    const subs = a.subscribers;
    document.getElementById("wa-subs").textContent = num(subs.total);
    document.getElementById("wa-langs").textContent = subs.total
      ? `(${Object.entries(subs.by_lang).filter(([, n]) => n).map(([l, n]) => `${LANG[l]} ${num(n)}`).join("، ")})` : "";
    document.getElementById("wa-mode").textContent = MODE[a.mode] || a.mode;
    document.getElementById("wa-sends").replaceChildren(...(a.sends.length ? a.sends.map((x) => {
      const reached = x.sent + x.simulated;
      const how = x.mode === "simulated" ? "محاكاة" : `وصل ${num(x.sent)}${x.failed ? `، تعذّر ${num(x.failed)}` : ""}${x.simulated ? `، ومحاكاة ${num(x.simulated)} تجريبي` : ""}`;
      return el("li", { class: x.done ? "" : "running" }, [
        el("strong", { text: x.title }),
        el("span", { text: `${ago(x.created_at)} · ${num(reached)} من ${num(x.total)} مشتركاً · ${how}${x.done ? "" : " · جارٍ الإرسال…"}` }),
      ]);
    }) : [el("li", { class: "empty", text: "لم يُرسل أي تحذير بعد. اعتماد أي حملة يرسله تلقائياً." })]));
  }

  login.addEventListener("submit", (e) => {
    e.preventDefault();
    token = tokenInput.value.trim();
    try { sessionStorage.setItem("haris.authority", token); } catch { /* keep in memory */ }
    refresh();
  });

  refresh();
  setInterval(refresh, 5000);
})();
