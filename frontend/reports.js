// Reports inbox for the authority (demo). Plain JavaScript; all text goes in with textContent only.
(() => {
  "use strict";

  const PRIORITY = { critical: "حرجة", financial: "عاجلة مالياً", medium: "متوسطة", indicator: "مؤشر" };
  const STATUS = { new: "جديد", received: "قيد المعالجة", info_requested: "بانتظار معلومات", closed: "مغلق" };
  const EVENT = { submitted: "أرسل المُبلّغ البلاغ", received: "تم الاستلام", info_requested: "طُلبت معلومات إضافية",
                  reply: "ردّ المُبلّغ", closed: "أُغلق البلاغ", assigned: "التوزيع", team_step: "إجراء الفريق" };
  const TEAM = { protection: "الحماية العاجلة", financial: "الفريق المالي", telecom: "الأرقام والاتصالات",
                 digital: "الحسابات والبريد والروابط", radar: "رادار الحملات" };
  const TEAM_SHORT = { protection: "الحماية", financial: "المالي", telecom: "الاتصالات", digital: "الحسابات", radar: "الرادار" };
  const TEAM_ICON = { protection: "🛑", financial: "💰", telecom: "📞", digital: "📧", radar: "📡" };
  const holder = (r) => r.routing.team || r.routing.suggested.lead;
  const EMIRATE = { abu_dhabi: "أبوظبي", dubai: "دبي", sharjah: "الشارقة", ajman: "عجمان",
                    umm_al_quwain: "أم القيوين", ras_al_khaimah: "رأس الخيمة", fujairah: "الفجيرة" };
  const INCIDENT = { money_sent: "احتيال مالي (دفع أو خصم)", account_hacked: "اختراق حساب", extortion: "ابتزاز إلكتروني",
                     harassment: "تحرّش أو تهديد", impersonation: "انتحال شخصية", privacy_violation: "انتهاك خصوصية أو تشهير",
                     device_hacked: "اختراق جهاز", identity_shared: "مشاركة بيانات الهوية", business_fraud: "احتيال على منشأة",
                     suspicious_only: "رسالة مشبوهة دون ضرر" };
  const LANG = { ar: "العربية", en: "الإنجليزية", ur: "الأردية", hi: "الهندية", ru: "الروسية" };
  const DEPARTURE = { within_3_days: "يغادر الدولة خلال 3 أيام", within_week: "يغادر خلال أسبوع", later: "يغادر بعد أكثر من أسبوع", unknown: "موعد المغادرة غير معروف" };
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
  const langFilter = document.getElementById("lang");
  const visitorsOnly = document.getElementById("visitors-only");
  let token = "";
  try { token = sessionStorage.getItem("haris.authority") || ""; } catch { /* storage blocked */ }
  let selected = "";
  let lastDetail = "";
  let view = "all";  // all, unassigned, or a team
  try { view = sessionStorage.getItem("haris.view") || "all"; } catch { /* storage blocked */ }

  for (const [k, v] of Object.entries(EMIRATE)) emirateFilter.append(el("option", { value: k, text: v }));
  for (const [k, v] of Object.entries(LANG)) langFilter.append(el("option", { value: k, text: v }));

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
  // Always UAE time (Asia/Dubai), whatever the officer's device is set to.
  const TZ = "Asia/Dubai";
  const clock = (ts) => new Date(ts * 1000).toLocaleString("ar-AE", { timeZone: TZ, hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" });
  const dayOf = (d) => d.toLocaleDateString("en-CA", { timeZone: TZ });
  const when = (ts) => {
    const d = new Date(ts * 1000);
    const time = d.toLocaleTimeString("ar-AE", { timeZone: TZ, hour: "numeric", minute: "2-digit" });
    const today = dayOf(d) === dayOf(new Date());
    const day = today ? "اليوم" : d.toLocaleDateString("ar-AE", { timeZone: TZ, day: "numeric", month: "short" });
    return `${day} ${time} (${ago(ts)})`;
  };
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
      list.replaceChildren(el("p", { class: "empty", text: "أدخل رمز الدخول لعرض البلاغات." }));
      throw new Error("auth");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.detail || String(res.status)), { status: res.status });
    login.hidden = true;
    document.getElementById("login-error").textContent = "";
    return data;
  }

  // Time left before the team's deadline, or how late the case is.
  function sla(r) {
    if (r.status === "closed") return el("span", { class: "sla", text: "—" });
    const left = r.routing.deadline - Date.now() / 1000;
    const m = Math.round(Math.abs(left) / 60);
    const span = m < 60 ? `${m} د` : m < 1440 ? `${Math.round(m / 60)} س` : `${Math.round(m / 1440)} ي`;
    return el("span", { class: `sla${left < 0 ? " late" : left < 3600 ? " soon" : ""}`, text: left < 0 ? `متأخر ${span}` : `باقٍ ${span}` });
  }

  function teamTag(r) {
    const t = holder(r);
    return el("span", { class: `team-tag${r.routing.team ? "" : " suggest"}`, title: r.routing.team ? "الفريق المسؤول" : "توزيع مقترح لم يُعتمد بعد",
      text: `${TEAM_ICON[t]} ${TEAM_SHORT[t]}${r.routing.team ? "" : " (مقترح)"}` });
  }

  function row(r) {
    const b = el("button", { type: "button", class: `case ${r.priority} ${r.status}`, "aria-pressed": String(r.reference === selected) });
    b.append(
      el("span", { class: "bar" }),
      el("span", {}, [el("span", { class: "ref" }, ltr(r.reference)), el("small", { text: when(r.created_at) })]),
      el("span", { class: "what" }, [
        el("span", { text: INCIDENT[r.incident_type] || r.incident_title }),
        el("span", { class: `pr ${r.priority}`, text: PRIORITY[r.priority] }),
        r.channel === "whatsapp" ? el("span", { class: "lang-chip wa", text: "📱 واتساب" }) : null,
        r.campaign ? el("span", { class: "lang-chip camp", text: `📡 حملة · ${r.campaign.people}` }) : null,
        r.lang !== "ar" ? el("span", { class: "lang-chip", text: `🗣️ ${LANG[r.lang]}` }) : null,
        r.visitor ? el("span", { class: `lang-chip visitor${r.leaving_soon ? " soon" : ""}`, text: r.leaving_soon ? "🧳 يغادر قريباً" : "🧳 زائر" }) : null,
        r.needs_translator ? el("span", { class: "lang-chip warn", text: "يحتاج مترجماً" }) : null,
        r.has_reply && r.status === "received" ? el("span", { class: "newreply", text: "● ردّ المُبلّغ" }) : null,
      ]),
      el("span", { text: [EMIRATE[r.emirate], money(r)].filter(Boolean).join(" · ") }),
      teamTag(r),
      sla(r),
      el("span", { class: `sts ${r.status}`, text: STATUS[r.status] }),
    );
    if (fresh.has(r.reference)) b.classList.add("fresh");
    b.addEventListener("click", () => { selected = r.reference; lastDetail = ""; refresh(); });
    return b;
  }

  // A translated value with the victim's own words beside it.
  const both = (translated, original) => (translated && translated !== original ? `${translated}  ←  ${original}` : original || "—");

  function facts(d) {
    const f = d.fields;
    const tr = f.translation || {};
    const pairs = [
      ["النوع", INCIDENT[d.incident_type] || d.incident_title],
      ["الإمارة", d.fields.visitor ? `${EMIRATE[d.emirate]} (حيث يقيم الزائر الآن)` : `${EMIRATE[d.emirate]} (الجهة المختصة حسب إقامة المُبلّغ)`],
      ["وقت الحادثة", both(tr.occurred_at, f.occurred_at)],
      ["المبلغ", money(f) || "—"],
      ["طريقة الدفع", both(tr.payment_method, f.payment_method)],
      ["الأدلة", f.evidence_count ? `${f.evidence_count} لقطة شاشة في ملف المُبلّغ (لا تُحفظ هنا)` : "—"],
      ["لغة المُبلّغ", LANG[d.lang] || d.lang],
      // \u2066…\u2069 keeps a phone number or e-mail left-to-right inside the Arabic line.
      ["المُبلّغ", [f.reporter_name, f.reporter_contact && `\u2066${f.reporter_contact}\u2069`].filter(Boolean).join(" · ") || "من الهوية الرقمية عند الربط"],
    ];
    const dl = el("dl", { class: "facts" });
    for (const [k, v] of pairs) dl.append(el("dt", { text: k }), el("dd", { text: v }));
    return dl;
  }

  function showDetail(d) {
    const key = JSON.stringify([d.status, d.events.length, d.routing.team, Math.floor(Date.now() / 60000)]);
    if (key === lastDetail && detail.dataset.ref === d.reference) return; // keep a note being typed
    lastDetail = key;
    detail.dataset.ref = d.reference;
    const parts = [
      el("div", { class: "head" }, [
        el("span", { class: `pr ${d.priority}`, text: PRIORITY[d.priority] }),
        el("span", { class: `sts ${d.status}`, text: STATUS[d.status] }),
        el("h2", {}, ltr(d.reference)),
      ]),
      el("span", { class: d.verified ? "verified" : "verified no", text: !d.verified ? "هوية غير مؤكدة"
        : (d.fields.visitor || {}).identity === "uae_pass_visitor" ? "✔ هوية زائر مؤكدة بحساب UAE PASS للزوار (تأكيد تجريبي)"
        : (d.fields.visitor || {}).identity === "passport" ? "✔ هوية زائر مؤكدة بجواز السفر (تأكيد تجريبي)"
        : "✔ هوية مؤكدة (تأكيد تجريبي، UAE PASS عند الربط الرسمي)" }),
    ];
    if (d.status !== "closed") parts.push(routeCard(d));
    else parts.push(el("p", { class: "verified", text: `الفريق المسؤول: ${TEAM[holder(d)]}` }));
    const v = d.fields.visitor;
    if (v) {
      const nat = (d.fields.translation || {}).nationality;
      const who = ["🧳 المُبلّغ زائر وليس مقيماً", v.nationality ? `الجنسية: ${nat && nat !== v.nationality ? `${nat} (${v.nationality})` : v.nationality}` : "",
                   DEPARTURE[v.departure]].filter(Boolean).join(" · ");
      parts.push(el("div", { class: `visitor-banner${v.departure === "within_3_days" ? " soon" : ""}` }, [
        el("strong", { text: who }),
        el("span", { text: `يُقترح تحويله لشرطة السياحة في ${EMIRATE[d.emirate]}، فهي تتابع قضايا الزوار حتى بعد مغادرتهم.${v.departure === "within_3_days" ? " تقدّم البلاغ في الطابور لأن المُبلّغ يغادر قريباً: خذ إفادته وبيانات بنكه قبل سفره." : ""}` }),
        v.contact_abroad ? el("span", {}, ["التواصل بعد سفره: ", ltr(v.contact_abroad)]) : null,
      ]));
    }
    if (HINT[d.priority] && d.status !== "closed") parts.push(el("p", { class: `hint ${d.priority}`, text: HINT[d.priority] }));
    const f = d.fields;
    const tr = f.translation || {};
    if (d.lang !== "ar") {
      parts.push(el("p", { class: `lang-banner${tr.ok ? "" : " warn"}`, text: tr.ok
        ? `🗣️ لغة المُبلّغ: ${LANG[d.lang]}. يُفضّل إسناد البلاغ لموظف يتحدث ${LANG[d.lang]}. كلمات المُبلّغ مترجمة آلياً إلى العربية والأصل معها، ورسائلك تصله مترجمة إلى ${LANG[d.lang]}.`
        : `🗣️ لغة المُبلّغ: ${LANG[d.lang]}. تعذّرت الترجمة الآلية، فالبلاغ يحتاج موظفاً يتحدث ${LANG[d.lang]} أو مترجماً.` }));
    }
    parts.push(facts(d));
    if (f.scammer_identifiers.length) {
      parts.push(el("h3", { text: "بيانات المحتال" }), el("div", { class: "ids" }, f.scammer_identifiers.map((i) => el("span", { class: "id" }, ltr(i)))));
    }
    if (f.steps_taken.length) {
      const steps = tr.steps_taken && tr.steps_taken.length === f.steps_taken.length ? tr.steps_taken : null;
      parts.push(el("h3", { text: "ما فعله المُبلّغ" }), el("ul", {}, f.steps_taken.map((s, i) =>
        el("li", { dir: "auto", text: steps ? both(steps[i], s) : s }))));
    }
    parts.push(el("h3", { text: "ما حدث بكلمات المُبلّغ" }));
    if (tr.ok && tr.description) {
      parts.push(el("blockquote", { class: "translated", text: tr.description }),
        el("details", { class: "original" }, [el("summary", { text: `النص الأصلي (${LANG[d.lang]}) · ترجمة آلية، ارجع للأصل عند الشك` }),
                                               el("blockquote", { dir: "auto", text: f.description })]));
    } else {
      parts.push(el("blockquote", { dir: "auto", text: f.description || "—" }));
    }
    parts.push(el("h3", { text: "سجل البلاغ" }), el("ol", { class: "timeline" }, d.events.map((e) =>
      el("li", { class: e.kind }, [el("time", { text: clock(e.ts) }), el("span", { text: eventLabel(e) }), ...noteOf(e, d)]))));
    if (d.status !== "closed") parts.push(actions(d));
    detail.replaceChildren(...parts);
  }

  function eventLabel(e) {
    if (e.kind === "assigned") return `${TEAM_ICON[e.team] || ""} أُحيل إلى ${TEAM[e.team] || e.team}${e.accepted ? " (اعتماد التوزيع المقترح)" : ""}`;
    if (e.kind === "team_step") return `${TEAM_ICON[e.team] || ""} ${TEAM[e.team] || ""}: ${e.label || e.step}`;
    return EVENT[e.kind] || e.kind;
  }

  // The routing card: Haris's suggestion and why, the team that holds the case, its deadline,
  // the move to another team, and the steps the holding team can record.
  function routeCard(d) {
    const r = d.routing, s = r.suggested;
    const box = el("div", { class: "route" });
    const err = el("p", { class: "err", role: "alert" });
    const post = async (body) => {
      err.textContent = "";
      try { await call(`/api/authority/reports/${encodeURIComponent(d.reference)}`, body); }
      catch { err.textContent = "تعذّر الحفظ، حاول مرة أخرى."; return; }
      lastDetail = ""; refresh();
    };
    if (!r.team) {
      box.append(el("div", { class: "rt" }, [el("b", { text: "✨ توزيع مقترح من «حارس»:" }),
        el("span", { class: "team-tag", text: `${TEAM_ICON[s.lead]} ${TEAM[s.lead]}` }),
        ...s.also.map((t) => el("span", { class: "team-tag suggest", text: `يشارك: ${TEAM_ICON[t]} ${TEAM[t]}` }))]));
      box.append(el("ul", {}, s.why.map((w) => el("li", { text: w }))));
      const ok = el("button", { type: "button", class: "primary", text: `اعتماد وإحالة إلى ${TEAM[s.lead]}` });
      ok.addEventListener("click", () => post({ action: "assign", team: s.lead }));
      box.append(el("div", { class: "row" }, [ok]));
    } else {
      box.append(el("div", { class: "rt" }, [el("b", { text: "لدى:" }),
        el("span", { class: "team-tag", text: `${TEAM_ICON[r.team]} ${TEAM[r.team]}` }),
        ...r.also.map((t) => el("span", { class: "team-tag suggest", text: `يشارك: ${TEAM_ICON[t]} ${TEAM[t]}` }))]));
    }
    const left = r.deadline - Date.now() / 1000;
    box.append(el("p", { class: `deadline sla${left < 0 ? " late" : left < 3600 ? " soon" : ""}`,
      text: `مهلة ${TEAM[holder(d)]}: ${left < 0 ? "تجاوزها البلاغ" : "تنتهي"} ${clock(r.deadline)}` }));
    if (d.campaign) {
      box.append(el("p", { class: "lang-chip camp", text: `📡 بيانات المحتال جزء من حملة على الرادار: ${d.campaign.label} · ${d.campaign.people} مُبلّغين` }));
    }
    // Move to another team, with a short reason kept in the log.
    const pick = el("select", { "aria-label": "تحويل إلى فريق" }, [el("option", { value: "", text: "تحويل إلى فريق…" }),
      ...Object.keys(TEAM).filter((t) => t !== holder(d) || !r.team).map((t) => el("option", { value: t, text: `${TEAM_ICON[t]} ${TEAM[t]}` }))]);
    const why = el("input", { type: "text", placeholder: "سبب التحويل (اختياري)", maxlength: "200" });
    const move = el("button", { type: "button", text: "تحويل" });
    move.addEventListener("click", () => { if (pick.value) post({ action: "assign", team: pick.value, note: why.value.trim() }); });
    box.append(el("div", { class: "row" }, [pick, why, move]));
    // The steps of the team that holds the case, and of the teams that share it.
    const done = new Set(d.events.filter((e) => e.kind === "team_step").map((e) => `${e.team}:${e.step}`));
    for (const t of [holder(d), ...(r.team ? r.also : s.also)]) {
      const steps = (d.team_steps || {})[t] || [];
      if (!steps.length) continue;
      box.append(el("h3", { text: `${TEAM_ICON[t]} إجراءات ${TEAM[t]} (تجريبية: تُسجَّل في سجل البلاغ)` }));
      box.append(el("div", { class: "steps-box" }, steps.map((st) => {
        const k = `${t}:${st.id}`;
        const b = el("button", { type: "button", class: done.has(k) ? "done" : "", text: `${done.has(k) ? "✔ " : ""}${st.label}` });
        if (!done.has(k)) b.addEventListener("click", () => post({ action: "team_step", team: t, step: st.id }));
        return b;
      })));
    }
    box.append(err);
    return box;
  }

  // What the officer reads in the log: the victim's reply in Arabic with the original, or the officer's
  // own note with the version the victim received in their language.
  function noteOf(e, d) {
    if (!e.note) return [];
    if (e.kind === "reply" && e.note_ar) {
      return [el("span", { class: "note translated", text: e.note_ar }), el("span", { class: "note small", dir: "auto", text: `الأصل: ${e.note}` })];
    }
    if (e.kind === "reply" && d.lang !== "ar") {
      return [el("span", { class: "note", dir: "auto", text: e.note }), el("span", { class: "lang-chip warn", text: "لم يُترجم: يحتاج مترجماً" })];
    }
    const parts = [el("span", { class: "note", dir: "auto", text: e.note })];
    if (e.note_victim) parts.push(el("span", { class: "note small", dir: "auto", text: `وصلت للمُبلّغ بـ${LANG[d.lang]}: ${e.note_victim}` }));
    if (e.untranslated) parts.push(el("span", { class: "lang-chip warn", text: `وصلت بالعربية فقط: تعذّرت الترجمة إلى ${LANG[d.lang]}` }));
    return parts;
  }

  function actions(d) {
    const box = el("div", { class: "act" });
    const note = el("textarea", { id: "note", placeholder: "مثال: أرسل اسم البنك وآخر 4 أرقام من البطاقة" });
    const err = el("p", { class: "err", role: "alert" });
    box.append(el("label", { for: "note", text: d.lang === "ar" ? "رسالة لصاحب البلاغ (تظهر له في «حارس»)"
      : `رسالة لصاحب البلاغ: اكتبها بالعربية، وتصله مترجمة إلى ${LANG[d.lang]} ومعها نصك` }), note,
      el("p", { class: "hint-small", text: "تصله في محادثة «حارس» على أنها سؤال من الجهة المختصة، ومعها تذكير بأن الجهة لا تطلب رمز تحقق أو كلمة مرور أو رقم بطاقة. فلا تطلب أياً منها." }));
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

  // A report that arrives while the dashboard is open is announced: a banner, a short tone, and the count in the tab title.
  let known = null;
  const fresh = new Set();
  function chime() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [880, 1175].forEach((f, i) => {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = f; o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0.0001, ctx.currentTime + i * 0.18);
        g.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + i * 0.18 + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + i * 0.18 + 0.16);
        o.start(ctx.currentTime + i * 0.18); o.stop(ctx.currentTime + i * 0.18 + 0.17);
      });
    } catch { /* sound is optional */ }
  }
  function announce(items) {
    const refs = new Set(items.map((r) => r.reference));
    if (known) {
      const arrived = items.filter((r) => !known.has(r.reference));
      if (arrived.length) {
        arrived.forEach((r) => fresh.add(r.reference));
        const banner = document.getElementById("arrived");
        banner.textContent = `📥 وصل ${arrived.length === 1 ? "بلاغ جديد" : `${arrived.length} بلاغات جديدة`}: ${arrived.map((r) => r.reference).join("، ")} · ${when(arrived[0].created_at)}`;
        banner.hidden = false;
        document.title = `(${fresh.size}) البلاغات الواردة | لوحة الجهة المختصة`;
        chime();
      }
    }
    known = refs;
  }
  document.getElementById("arrived").addEventListener("click", (e) => {
    e.currentTarget.hidden = true; fresh.clear(); document.title = "البلاغات الواردة | لوحة الجهة المختصة"; refresh();
  });

  async function refresh() {
    let q;
    const live = document.getElementById("live");
    try { q = await call("/api/authority/reports"); live.className = "live"; live.lastChild.textContent = " متصل"; }
    catch { live.className = "live off"; live.lastChild.textContent = " غير متصل"; return; }
    announce(q.items);
    const s = q.stats;
    const open = q.items.filter((r) => r.status !== "closed").length;
    document.getElementById("k-today").textContent = s.today;
    document.getElementById("k-open").textContent = open;
    document.getElementById("k-late").textContent = s.late;
    document.getElementById("k-unassigned").textContent = s.unassigned;
    const m = s.avg_minutes_to_receive;
    document.getElementById("k-wait").textContent = m == null ? "—" : m < 90 ? `${Math.round(m)} دقيقة` : `${(m / 60).toFixed(1)} ساعة`;
    document.getElementById("k-amount").textContent = `${(s.amount_open || 0).toLocaleString("ar-AE")} د.إ`;
    queues(q, open);
    document.getElementById("retention").textContent = s.retention_days;
    document.getElementById("by-lang").textContent = Object.entries(s.by_lang || {}).filter(([, n]) => n)
      .map(([l, n]) => `${LANG[l]} ${n}`).join(" · ") + (s.needs_translator ? ` · يحتاج مترجماً ${s.needs_translator}` : "")
      + (s.visitors ? ` · 🧳 زوار ${s.visitors}${s.leaving_soon ? ` (يغادر قريباً ${s.leaving_soon})` : ""}` : "");
    const inView = (r) => view === "all" || (view === "unassigned" ? !r.routing.team : view === "late" ? r.routing.late
      : holder(r) === view || (r.routing.team ? r.routing.also : r.routing.suggested.also).includes(view));
    const items = q.items.filter((r) => inView(r) && (showClosed.checked || r.status !== "closed") && (!emirateFilter.value || r.emirate === emirateFilter.value)
      && (!langFilter.value || r.lang === langFilter.value) && (!visitorsOnly.checked || r.visitor));
    list.replaceChildren(...(items.length ? items.map(row) : [el("p", { class: "empty", text: "لا توجد بلاغات." })]));
    document.getElementById("updated").textContent = `آخر تحديث: ${new Date().toLocaleTimeString("ar-AE", { timeZone: TZ })} بتوقيت الإمارات · يتحدّث كل 5 ثوانٍ`;
    if (selected) {
      try { showDetail(await call(`/api/authority/reports/${encodeURIComponent(selected)}`)); }
      catch (e) {
        // Only a case that no longer exists closes; a slow or busy moment keeps it open until the next refresh.
        if (e.status === 404) { selected = ""; detail.replaceChildren(el("p", { class: "empty", text: "لم يعد هذا البلاغ موجوداً." })); }
      }
    }
  }

  // The side rail: every team's open cases, a red dot when one is past its deadline.
  function queues(q, open) {
    const nav = document.getElementById("queues");
    const s = q.stats;
    const entries = [["all", "🗂️", "كل البلاغات", open, false], ["unassigned", "✨", "بانتظار التوزيع", s.unassigned, false],
      ["late", "⏰", "متأخرة عن المهلة", s.late, s.late > 0],
      ...Object.keys(TEAM).map((t) => [t, TEAM_ICON[t], TEAM[t], s.teams[t].open, s.teams[t].late > 0])];
    nav.replaceChildren(...entries.map(([id, ic, label, n, late], i) => {
      const b = el("button", { type: "button", class: `q${i === 3 ? " sep" : ""}`, "aria-pressed": String(view === id) },
        [el("span", { class: "ic", text: ic }), el("span", { text: label }), late ? el("span", { class: "late", title: "فيها بلاغ متأخر" }) : null,
         el("span", { class: "n", text: String(n) })]);
      b.addEventListener("click", () => { view = id; try { sessionStorage.setItem("haris.view", id); } catch { /* */ } refresh(); });
      return b;
    }));
    const title = entries.find(([id]) => id === view);
    document.getElementById("queue-title").textContent = title ? `${title[1]} ${title[2]}` : "كل البلاغات";
  }

  // A live clock in UAE time, and whether the last refresh reached the server.
  const clockEl = document.getElementById("clock");
  const tick = () => { clockEl.textContent = new Date().toLocaleString("ar-AE", { timeZone: TZ, weekday: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" }); };
  tick(); setInterval(tick, 1000);

  login.addEventListener("submit", (e) => {
    e.preventDefault();
    token = tokenInput.value.trim();
    try { sessionStorage.setItem("haris.authority", token); } catch { /* keep in memory */ }
    refresh();
  });
  showClosed.addEventListener("change", refresh);
  emirateFilter.addEventListener("change", refresh);
  langFilter.addEventListener("change", refresh);
  visitorsOnly.addEventListener("change", refresh);

  refresh();
  setInterval(refresh, 5000);
})();
