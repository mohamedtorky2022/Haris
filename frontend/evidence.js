// Takedown evidence for the authority (demo). Plain JavaScript; all text goes in with textContent only.
(() => {
  "use strict";

  const RISK = { high: "خطورة عالية", medium: "مشبوه", low: "لم تظهر مؤشرات واضحة" };
  const DRAFT = {
    registrar: "إلى مسجّل النطاق: طلب تعليق النطاق (بالإنجليزية)",
    hosting: "إلى جهة الاستضافة: طلب إزالة الصفحة (بالإنجليزية)",
    block_ar: "طلب حجب داخل الدولة (بالعربية)",
  };
  const EMAIL = /^[^\s@<>"]+@[^\s@<>"]+\.[A-Za-z]{2,}$/;
  // The query string often carries the victim's identifier: never keep it in the address bar or logs.
  const clean = (u) => {
    try { const x = new URL(u.includes("://") ? u : `http://${u}`); return `${x.protocol}//${x.host}${x.pathname}`; }
    catch { return u.split(/[?#]/)[0]; }
  };

  const form = document.getElementById("ask");
  const input = document.getElementById("url");
  const go = document.getElementById("go");
  const status = document.getElementById("status");
  const file = document.getElementById("file");
  const login = document.getElementById("login");
  const tokenInput = document.getElementById("token");

  let token = "";
  try { token = sessionStorage.getItem("haris.authority") || ""; } catch { /* storage blocked */ }

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "text") node.textContent = v;
      else if (k === "class") node.className = v;
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of [].concat(children)) if (c) node.append(c);
    return node;
  }

  function facts(rows) {
    const dl = el("dl", { class: "ev-facts" });
    for (const [label, value, ltr] of rows) {
      dl.append(el("dt", { text: label }));
      dl.append(value === undefined || value === null || value === ""
        ? el("dd", { class: "ev-missing", text: "غير متاح في السجل" })
        : el("dd", { class: ltr ? "ltr" : "", dir: ltr ? "ltr" : null, text: String(value) }));
    }
    return dl;
  }

  // Arabic counting of days: one, two (dual), 3-10 (plural), 11 and more (singular accusative).
  const days = (n) => (n === 0 ? "أقل من يوم" : n === 1 ? "يوم واحد" : n === 2 ? "يومان" : n <= 10 ? `${n} أيام` : `${n} يوماً`);

  function copyButton(text) {
    const b = el("button", { type: "button", text: "نسخ" });
    b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(text); b.textContent = "نُسخ ✓"; } catch { b.textContent = "تعذّر النسخ"; }
      setTimeout(() => { b.textContent = "نسخ"; }, 1800);
    });
    return b;
  }

  function draft(kind, d) {
    const box = el("div", { class: "ev-draft" });
    box.append(el("h4", { text: DRAFT[kind] || kind }));
    const to = kind === "block_ar" ? "عبر القناة الرسمية بين الجهتين" : d.to;
    box.append(facts([["إلى", to, kind !== "block_ar"], ["الموضوع", d.subject, kind !== "block_ar"]]));
    box.append(el("pre", { dir: kind === "block_ar" ? "rtl" : "ltr", text: d.body }));
    const btns = el("div", { class: "ev-btns" }, [copyButton(`${d.subject}\n\n${d.body}`)]);
    if (d.to && EMAIL.test(d.to)) {
      const href = `mailto:${encodeURIComponent(d.to)}?subject=${encodeURIComponent(d.subject)}&body=${encodeURIComponent(d.body)}`;
      btns.append(el("a", { class: "mail", href, text: "فتح في البريد" }));
    }
    box.append(btns);
    return box;
  }

  function render(ev) {
    file.replaceChildren();
    const s = ev.site;

    const head = el("div", { class: "ev-card" }, [
      el("div", { class: "ev-head" }, [
        el("span", { class: `ev-risk ${ev.risk}`, text: RISK[ev.risk] || ev.risk }),
        el("span", { class: "ev-domain", text: s.final_domain || ev.registrable }),
      ]),
      facts([["الرابط", ev.url, true], ["ينتهي إلى", s.final_url && s.final_url !== ev.url ? s.final_url : "نفس الرابط", s.final_url !== ev.url],
             ["وقت الفحص", ev.checked_at.replace("T", " ").replace("Z", " UTC"), true],
             ["الدرجة", `${s.score} / 100`, false]]),
    ]);
    if (ev.notes.length) head.append(el("div", { class: "ev-notes" }, ev.notes.map((n) => el("p", { text: n }))));
    file.append(head);

    const found = el("div", { class: "ev-card" }, [el("h3", { text: "ما وجده الفحص" })]);
    if (s.flag_labels.length) found.append(el("ul", { class: "ev-findings" }, s.flag_labels.map((t) => el("li", { text: t }))));
    else found.append(el("p", { class: "ev-missing", text: "لم تظهر مؤشرات في الصفحة نفسها." }));
    found.append(facts([
      ["عنوان الصفحة", s.title, false],
      ["ينتحل", s.ai && s.ai.impersonates, false],
      ["حكم الذكاء الاصطناعي", s.ai ? RISK[s.ai.risk] : null, false],
      ["التحويلات", s.redirects && s.redirects.length ? s.redirects.join(" ← ") : "لا يوجد", true],
      ["عمر النطاق", s.domain_age_days !== null && s.domain_age_days !== undefined ? days(s.domain_age_days) : null, false],
      ["بصمة الصفحة SHA-256", s.sha256, true],
    ]));
    file.append(found);

    const d = ev.domain;
    file.append(el("div", { class: "ev-card" }, [
      el("h3", { text: "مسجّل النطاق" }),
      facts([["النطاق", ev.registrable, true], ["المسجّل", d.registrar, true], ["رقم IANA", d.iana_id, true],
             ["بريد الإبلاغ عن الإساءة", d.abuse_email, true], ["هاتف الإبلاغ", d.abuse_phone, true],
             ["تاريخ التسجيل", d.registered, true], ["تاريخ الانتهاء", d.expires, true],
             ["خوادم الأسماء", d.nameservers && d.nameservers.join("، "), true]]),
    ]));

    const h = ev.hosting;
    file.append(el("div", { class: "ev-card" }, [
      el("h3", { text: "الاستضافة" }),
      facts([["عنوان الخادم", h.ip, true], ["المنصة المجانية", ev.free_host || "لا", !!ev.free_host], ["الشبكة", h.network, true],
             ["الجهة المالكة", h.organisation, true], ["الدولة", h.country, true],
             ["بريد الإبلاغ عن الإساءة", h.abuse_email, true]]),
    ]));

    const drafts = el("div", { class: "ev-card" }, [
      el("h3", { text: "مسودات الطلبات" }),
      el("p", { class: "ev-warn", text: "مسودات فقط: راجعها، وأكمل بيانات الضابط والجهة، ثم أرسلها بنفسك. «حارس» لا يرسل شيئاً." }),
    ]);
    for (const kind of ["registrar", "hosting", "block_ar"]) if (ev.drafts[kind]) drafts.append(draft(kind, ev.drafts[kind]));
    file.append(drafts);

    const print = el("button", { type: "button", text: "طباعة أو حفظ PDF" });
    print.addEventListener("click", () => window.print());
    file.append(el("div", { class: "ev-actions" }, [print]));
    file.hidden = false;
  }

  async function build(url) {
    go.disabled = true;
    status.className = "ev-status";
    status.textContent = "يفتح «حارس» الموقع ويقرأ سجلات التسجيل والاستضافة… قد يستغرق ذلك حتى 30 ثانية.";
    file.hidden = true;
    try {
      const res = await fetch("/api/authority/evidence", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { "X-Authority-Token": token } : {}) },
        body: JSON.stringify({ url }),
      });
      if (res.status === 401 || res.status === 403) {
        login.hidden = false;
        status.textContent = "أدخل رمز الدخول أولاً.";
        document.getElementById("login-error").textContent = token ? "رمز الدخول غير صحيح." : "";
        return;
      }
      if (res.status === 400) throw new Error("لا يمكن فحص هذا العنوان (عنوان داخلي أو غير صالح).");
      if (!res.ok) throw new Error("تعذّر إعداد الملف الآن. حاول مرة أخرى بعد دقيقة.");
      render(await res.json());
      status.textContent = "";
      try { history.replaceState(null, "", `?url=${encodeURIComponent(clean(url))}`); } catch { /* */ }
    } catch (err) {
      status.className = "ev-status err";
      status.textContent = err.message || "تعذّر الاتصال.";
    } finally {
      go.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const url = clean(input.value.trim());
    if (url) { input.value = url; build(url); }
  });

  login.addEventListener("submit", (e) => {
    e.preventDefault();
    token = tokenInput.value.trim();
    try { sessionStorage.setItem("haris.authority", token); } catch { /* keep in memory */ }
    login.hidden = true;
    if (input.value.trim()) build(input.value.trim());
  });

  const start = new URLSearchParams(location.search).get("url");
  if (start) { input.value = clean(start); build(clean(start)); }
})();
