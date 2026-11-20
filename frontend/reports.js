// Reports inbox for the authority (demo). Plain JavaScript; all text goes in with textContent only.
(() => {
  "use strict";

  const PRIORITY = { critical: "حرجة", financial: "عاجلة مالياً", medium: "متوسطة", indicator: "مؤشر" };
  const STATUS = { new: "جديد", received: "قيد المعالجة", info_requested: "بانتظار معلومات", closed: "مغلق" };
  const EVENT = { submitted: "أرسل المُبلّغ البلاغ", received: "تم الاستلام", info_requested: "طُلبت معلومات إضافية",
                  reply: "ردّ المُبلّغ", closed: "أُغلق البلاغ" };
  const EMIRATE = { abu_dhabi: "أبوظبي", dubai: "دبي", sharjah: "الشارقة", ajman: "عجمان",
                    umm_al_quwain: "أم القيوين", ras_al_khaimah: "رأس الخيمة", fujairah: "الفجيرة" };
  const INCIDENT = { money_sent: "احتيال مالي (دفع أو خصم)", account_hacked: "اختراق حساب", extortion: "ابتزاز إلكتروني",
                     harassment: "تحرّش أو تهديد", impersonation: "انتحال شخصية", privacy_violation: "انتهاك خصوصية أو تشهير",
                     device_hacked: "اختراق جهاز", identity_shared: "مشاركة بيانات الهوية", business_fraud: "احتيال على منشأة",
                     suspicious_only: "رسالة مشبوهة دون ضرر" };
  const LANG = { ar: "العربية", en: "الإنجليزية", ur: "الأردية", hi: "الهندية" };
  const HINT = {
    critical: "حالة حرجة: تواصل فوراً مع غرفة العمليات، واطلب من المُبلّغ الاتصال بـ 999 إن كان في خطر.",
    financial: "عاجلة مالياً: أبلغ وحدة الاحتيال في البنك الآن، فالساعة الأولى هي الأهم لتجميد المبلغ.",
  };

  const list = document.getElementById("list");
  const detail = document.getElementById("detail");
  const login = document.getElementById("login");
  const tokenInput = document.getElementById("token");
  const showClosed = document.getElementById("show-closed");
  const emirateFilter = document.getElementById("emirate");
  let token = "";
  try { token = sessionStorage.getItem("haris.authority") || ""; } catch { /* storage blocked */ }
  let selected = "";
  let lastDetail = "";

  for (const [k, v] of Object.entries(EMIRATE)) emirateFilter.append(el("option", { value: k, text: v }));

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
  const clock = (ts) => new Date(ts * 1000).toLocaleString("ar-AE", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" });
  const money = (r) => (r.amount ? `${r.amount} ${r.currency || "AED"}` : "");
  const ltr = (text) => el("bdi", { dir: "ltr", text });

  async function call(path, body) {
    const res = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json", ...(token ? { "X-Authority-Token": token } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401 || res.status === 403) {
      login.hidden = false;
      document.getElementById("login-error").textContent = token ? "رمز الدخول غير صحيح، تأكد منه وحاول مرة أخرى." : "";
      list.replaceChildren(el("p", { class: "empty", text: "أدخل رمز الدخول في الأعلى لعرض البلاغات." }));
      throw new Error("auth");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || String(res.status));
    login.hidden = true;
    document.getElementById("login-error").textContent = "";
    return data;
  }

  function row(r) {
    const b = el("button", { type: "button", class: `case ${r.priority} ${r.status}`, "aria-pressed": String(r.reference === selected) });
    b.append(el("span", { class: "top" }, [
      el("span", { class: `pr ${r.priority}`, text: PRIORITY[r.priority] }),
      el("span", { class: `sts ${r.status}`, text: STATUS[r.status] }),
      r.has_reply && r.status === "received" ? el("span", { class: "newreply", text: "ردّ المُبلّغ" }) : null,
      el("span", { class: "ref" }, ltr(r.reference)),
    ]));
    b.append(el("span", { class: "what", text: INCIDENT[r.incident_type] || r.incident_title }));
    b.append(el("p", { class: "meta", text: [EMIRATE[r.emirate], money(r), ago(r.created_at)].filter(Boolean).join(" · ") }));
    b.addEventListener("click", () => { selected = r.reference; lastDetail = ""; refresh(); });
    return b;
  }

  function facts(d) {
    const f = d.fields;
    const pairs = [
      ["النوع", INCIDENT[d.incident_type] || d.incident_title],
      ["الإمارة", `${EMIRATE[d.emirate]} (الجهة المختصة حسب إقامة المُبلّغ)`],
      ["وقت الحادثة", f.occurred_at || "—"],
      ["المبلغ", money(f) || "—"],
      ["طريقة الدفع", f.payment_method || "—"],
      ["الأدلة", f.evidence_count ? `${f.evidence_count} لقطة شاشة في ملف المُبلّغ (لا تُحفظ هنا)` : "—"],
      ["لغة المُبلّغ", LANG[d.lang] || d.lang],
      ["المُبلّغ", [f.reporter_name, f.reporter_contact].filter(Boolean).join(" · ") || "من الهوية الرقمية عند الربط"],
    ];
    const dl = el("dl", { class: "facts" });
    for (const [k, v] of pairs) dl.append(el("dt", { text: k }), el("dd", { text: v }));
    return dl;
  }

  function showDetail(d) {
    const key = JSON.stringify([d.status, d.events.length]);
    if (key === lastDetail && detail.dataset.ref === d.reference) return; // keep a note being typed
    lastDetail = key;
    detail.dataset.ref = d.reference;
    const parts = [
      el("div", { class: "head" }, [
        el("span", { class: `pr ${d.priority}`, text: PRIORITY[d.priority] }),
        el("span", { class: `sts ${d.status}`, text: STATUS[d.status] }),
        el("h2", {}, ltr(d.reference)),
      ]),
      el("span", { class: d.verified ? "verified" : "verified no",
                   text: d.verified ? "✔ هوية مؤكدة (تأكيد تجريبي، UAE PASS عند الربط الرسمي)" : "هوية غير مؤكدة" }),
    ];
    if (HINT[d.priority] && d.status !== "closed") parts.push(el("p", { class: `hint ${d.priority}`, text: HINT[d.priority] }));
    parts.push(facts(d));
    const f = d.fields;
    if (f.scammer_identifiers.length) {
      parts.push(el("h3", { text: "بيانات المحتال" }), el("div", { class: "ids" }, f.scammer_identifiers.map((i) => el("span", { class: "id" }, ltr(i)))));
    }
    if (f.steps_taken.length) parts.push(el("h3", { text: "ما فعله المُبلّغ" }), el("ul", {}, f.steps_taken.map((s) => el("li", { dir: "auto", text: s }))));
    parts.push(el("h3", { text: "ما حدث بكلمات المُبلّغ" }), el("blockquote", { dir: "auto", text: f.description || "—" }));
    parts.push(el("h3", { text: "سجل البلاغ" }), el("ol", { class: "timeline" }, d.events.map((e) =>
      el("li", { class: e.kind }, [el("time", { text: clock(e.ts) }), el("span", { text: EVENT[e.kind] || e.kind }),
                                   e.note ? el("span", { class: "note", dir: "auto", text: e.note }) : null]))));
    if (d.status !== "closed") parts.push(actions(d));
    detail.replaceChildren(...parts);
  }

  function actions(d) {
    const box = el("div", { class: "act" });
    const note = el("textarea", { id: "note", placeholder: "مثال: أرسل اسم البنك وآخر 4 أرقام من البطاقة" });
    const err = el("p", { class: "err", role: "alert" });
    box.append(el("label", { for: "note", text: "رسالة لصاحب البلاغ (تظهر له في «حارس»)" }), note);
    const row = el("div", { class: "actions" });
    const run = async (action) => {
      err.textContent = "";
      try { await call(`/api/authority/reports/${encodeURIComponent(d.reference)}`, { action, note: note.value.trim() }); }
      catch (e) { err.textContent = action === "request_info" && !note.value.trim() ? "اكتب المعلومات المطلوبة أولاً." : "تعذّر الحفظ، حاول مرة أخرى."; return; }
      lastDetail = "";
      refresh();
    };
    if (d.status === "new") {
      const b = el("button", { type: "button", class: "primary", text: "استلام البلاغ" });
      b.addEventListener("click", () => run("receive"));
      row.append(b);
    }
    const ask = el("button", { type: "button", text: "طلب معلومات" });
    ask.addEventListener("click", () => run("request_info"));
    row.append(ask, twoStep("إغلاق البلاغ", "اضغط مرة أخرى للإغلاق", () => run("close")));
    box.append(row, err);
    return box;
  }

  // A second click within 4 seconds confirms: no browser dialogs.
  function twoStep(label, confirmLabel, action) {
    const b = el("button", { type: "button", text: label });
    let armed = null;
    b.addEventListener("click", () => {
      if (armed) { clearTimeout(armed); armed = null; b.disabled = true; action(); return; }
      b.textContent = confirmLabel;
      b.classList.add("armed");
      armed = setTimeout(() => { armed = null; b.textContent = label; b.classList.remove("armed"); }, 4000);
    });
    return b;
  }

  async function refresh() {
    let q;
    try { q = await call("/api/authority/reports"); } catch { return; }
    const s = q.stats;
    document.getElementById("n-new").textContent = s.new;
    document.getElementById("n-urgent").textContent = s.urgent;
    document.getElementById("n-progress").textContent = s.in_progress;
    document.getElementById("n-closed").textContent = s.closed;
    document.getElementById("n-wait").textContent = s.avg_minutes_to_receive ?? "—";
    document.getElementById("retention").textContent = s.retention_days;
    const items = q.items.filter((r) => (showClosed.checked || r.status !== "closed") && (!emirateFilter.value || r.emirate === emirateFilter.value));
    list.replaceChildren(...(items.length ? items.map(row) : [el("p", { class: "empty", text: "لا توجد بلاغات." })]));
    document.getElementById("updated").textContent = `آخر تحديث: ${new Date().toLocaleTimeString("ar-AE")} · يتحدّث كل 5 ثوانٍ`;
    if (selected) {
      try { showDetail(await call(`/api/authority/reports/${encodeURIComponent(selected)}`)); }
      catch { selected = ""; detail.replaceChildren(el("p", { class: "empty", text: "اختر بلاغاً من القائمة لعرض تفاصيله." })); }
    }
  }

  login.addEventListener("submit", (e) => {
    e.preventDefault();
    token = tokenInput.value.trim();
    try { sessionStorage.setItem("haris.authority", token); } catch { /* keep in memory */ }
    refresh();
  });
  showClosed.addEventListener("change", refresh);
  emirateFilter.addEventListener("change", refresh);

  refresh();
  setInterval(refresh, 5000);
})();
