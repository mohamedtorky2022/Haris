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
  const login = document.getElementById("login");
  const tokenInput = document.getElementById("token");
  let token = "";
  try { token = sessionStorage.getItem("haris.authority") || ""; } catch { /* storage blocked */ }
  const results = {}; // campaign id -> block requests sent, shown after confirming

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
  const LANG = { ar: "العربية", en: "الإنجليزية", ur: "الأردية", hi: "الهندية" };
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
    ]));
    node.append(el("p", { class: "meta", text: `المُبلِّغون: ${c.people} · البلاغات: ${c.reports} · أول بلاغ ${ago(c.first_seen)} · آخر بلاغ ${ago(c.last_seen)}` }));
    if (c.identifiers.length) {
      node.append(el("div", { class: "ids" }, c.identifiers.map((i) =>
        el("span", { class: "id" }, [el("small", { text: KIND[i.kind] || i.kind }), el("bdi", { dir: "ltr", text: shown(i) })]))));
    }
    node.append(el("blockquote", { text: c.sample }));

    if (results[c.id]) {
      const r = results[c.id];
      node.append(el("p", { class: "done", text: r.blocks.length
        ? `صدر التحذير الرسمي، وأُرسل طلب حظر (محاكاة) لشركات الاتصالات عن: ${r.blocks.map(shown).join("، ")}`
        : "صدر التحذير الرسمي لكل مستخدمي «حارس»." }));
      if (r.wa) node.append(el("p", { class: "done", text: `📲 بدأ إرسال التحذير على واتساب إلى ${num(r.wa.total)} مشتركاً بلغاتهم. التقدّم في «تنبيهات واتساب» أعلاه.` }));
    }
    if (c.status !== "confirmed" && c.status !== "dismissed") {
      const actions = el("div", { class: "actions" });
      actions.append(twoStep("اعتماد التعميم وطلب الحظر", "اضغط مرة أخرى للتأكيد", "primary", () => decide(c.id, "confirmed")));
      actions.append(twoStep("ليست احتيالاً", "اضغط مرة أخرى للتأكيد", "", () => decide(c.id, "dismissed")));
      node.append(actions);
    }
    return node;
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
      const r = await call(`/api/authority/campaigns/${encodeURIComponent(id)}`, { status });
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
    list.replaceChildren(...(items.length ? items.map(card) : [el("p", { class: "empty", text: "لا توجد بلاغات خلال آخر 24 ساعة." })]));
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
