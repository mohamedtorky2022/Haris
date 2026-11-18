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

  const ago = (ts) => {
    const m = Math.max(0, Math.round((Date.now() / 1000 - ts) / 60));
    if (m < 1) return "الآن";
    if (m < 60) return `قبل ${m} دقيقة`;
    const h = Math.round(m / 60);
    return h < 24 ? `قبل ${h} ساعة` : `قبل ${Math.round(h / 24)} يوم`;
  };
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
      node.append(el("p", { class: "done", text: r.length
        ? `صدر التحذير الرسمي، وأُرسل طلب حظر (محاكاة) لشركات الاتصالات عن: ${r.map(shown).join("، ")}`
        : "صدر التحذير الرسمي لكل مستخدمي «حارس»." }));
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
      if (status === "confirmed") results[id] = r.block_requests;
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
    document.getElementById("updated").textContent = `آخر تحديث: ${new Date().toLocaleTimeString("ar-AE")} · يتحدّث تلقائياً كل 5 ثوانٍ`;
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
