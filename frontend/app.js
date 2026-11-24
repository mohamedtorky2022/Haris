/* Haris web chat. Plain JavaScript, no build step, no third-party code.
   Nothing is saved in the browser: the conversation lives only in this page. */
(() => {
  "use strict";

  // All wording lives in locales/<lang>.json, one file per language, loaded at start.
  const LANGS = ["ar", "en", "ur", "hi", "ru"];
  const RTL = new Set(["ar", "ur"]);
  const UI = {};
  async function loadLocales() {
    await Promise.all(LANGS.map(async (l) => {
      const res = await fetch(`locales/${l}.json`);
      UI[l] = await res.json();
    }));
  }


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
      [tr("fakeAd"), startFakeAd],
      [tr("howTo"), showGuide],
      ...(myCases().length ? [[tr("myReports"), showCases]] : []),
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
  async function check(text, then) {
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
          link.site ? siteCard(link.site) : null,
        ]));
      }
    }
    if (r.advice.length) parts.push(el("h3", { text: tr("advice") }), list(r.advice));
    const redactedCount = Object.values(r.redacted).reduce((a, b) => a + b, 0);
    const notes = [r.engine === "rules+ai" ? tr("engineAi") : tr("engineRules")];
    if (redactedCount) notes.unshift(tr("redacted", { n: redactedCount }));
    parts.push(el("p", { class: "note", text: notes.join(" · ") }));
    bubble(parts);
    if (then) return then(r);

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
    if (pb.child) {
      // Haris guides a child; the report itself goes to the Child Protection Centre's specialists.
      bubble([el("h3", { text: `🧒 ${pb.child.title}` }), list(pb.child.tips), ...contactsBlock(pb.child.contacts).slice(1)]);
    }
    if (pb.visitor) {
      // A tourist has no Emirates ID and a card from a bank abroad: the same plan, a few things differ.
      const v = pb.visitor;
      bubble([el("h3", { text: `🧳 ${v.title}` }), list(v.tips), ...contactsBlock(v.contacts).slice(1)]);
    }
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
        : c.id.endsWith("_sms") ? `sms:${c.value}` : `tel:${c.value.replace(/\s/g, "")}`;
      const a = el("a", { href, text: c.value.replace("https://", "") });
      if (href.startsWith("http")) { a.setAttribute("target", "_blank"); a.setAttribute("rel", "noopener noreferrer"); }
      return el("div", { class: "contact" }, [el("span", { text: c.label }), a]);
    })];
  }

  // ---- Campaign radar: a message nobody fell for still helps catch the campaign ----
  // What the live visit of the website found: where the link really ends, how old the domain is,
  // and what the page asks for. Shown under the link it belongs to.
  function siteCard(site) {
    const lines = [];
    if (site.final_domain) lines.push(`${tr("siteFinal")} ${site.final_domain}`);
    if (site.redirects && site.redirects.length) lines.push(tr("siteRedirects", { n: site.redirects.length }));
    lines.push(site.domain_age_days === null || site.domain_age_days === undefined
      ? tr("siteAgeUnknown")
      : tr("siteAge", { n: site.domain_age_days }));
    if (site.ai && site.ai.impersonates) lines.push(tr("siteImpersonates", { who: site.ai.impersonates }));
    const findings = site.flag_labels || [];
    return el("div", { class: `site-card${findings.length ? " risky" : ""}` }, [
      el("div", { class: "site-head", text: tr("siteVisited") }),
      site.title ? el("div", { class: "site-title", text: site.title }) : null,
      el("div", { class: "site-facts", text: lines.join(" · ") }),
      findings.length ? list(findings) : el("div", { class: "site-clean", text: site.reachable ? tr("siteClean") : tr("siteUnreachable") }),
    ]);
  }

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

  // ---- Report a fake ad (sale or rental), as Abu Dhabi Police asked the public to ----
  // 1. Paste the ad, its link, or a screenshot of it. 2. Haris checks it. 3. Where was it seen?
  // 4. Paid nothing: it goes to the campaign radar, grouped by the advertiser's number or link.
  //    Paid: it becomes a full report to the authority, with the ad already in the story.
  const PLATFORMS = ["Instagram", "Facebook", "TikTok", "Snapchat", "Dubizzle", "X", "WhatsApp / Telegram"];

  function startFakeAd() {
    mode = "fakead";
    bubble(tr("adAsk"));
    showTools(true);
    input.focus();
  }

  async function adReceived(text, images) {
    showTools(false);
    let ad = text;
    if (images.length) {  // a screenshot of the ad: the AI reads it into text and the advertiser's details
      const r = await api("/api/extract", { lang, text, images, incident_type: "suspicious_only" });
      const f = (r && r.fields) || {};
      const read = [f.description, ...(f.scammer_identifiers || [])].filter(Boolean).join("\n");
      if (r && !r.images_read && !text) { bubble(tr("adImageNotRead")); return startFakeAd(); }
      ad = [text, read].filter(Boolean).join("\n");
    }
    if (!ad) return startFakeAd();
    await check(ad, () => adWhere(ad, images));
  }

  function adWhere(ad, images) {
    bubble(tr("adWhere"));
    setChips([...PLATFORMS.map((p) => [p, () => adPaid(ad, images, p)]), [tr("adOther"), () => adPaid(ad, images, tr("adOther"))]]);
  }

  function adPaid(ad, images, platform) {
    bubble(tr("adPaid"));
    setChips([[tr("adPaidNo"), () => confirmReport(`[${tr("adTag")} · ${platform}]\n${ad}`)],
              [tr("adPaidYes"), () => adToReport(ad, images, platform)]]);
  }

  async function adToReport(ad, images, platform) {
    mode = "report";
    phase = "story";
    draft = { lang, incident_type: "money_sent" };
    reportImages = [];
    urgentShown = false;
    const items = await api(`/api/playbooks?lang=${lang}`);
    if (items) incidentTitles = Object.fromEntries(items.map((pb) => [pb.id, pb.title]));
    bubble(tr("adToReport"));
    await sendStory(tr("adStory", { platform, ad }), images);
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
    // Extortion and leaked photos: the evidence is the account and the threats, never a private photo.
    const sensitive = ["extortion", "privacy_violation"].includes(draft.incident_type);
    bubble(sensitive ? [el("p", { text: tr("qStory") }), el("p", { class: "radar-line", text: tr("noPrivateImages") })] : tr("qStory"));
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
      return Array.isArray(v) ? v.join(RTL.has(lang) ? "، " : ", ") : (v || "");
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
    fileReference = r.reference;
    setChips([[tr("sendAuthority"), chooseResidency], [tr("checkAnother"), askCheck], [tr("menuBack"), menu]]);
  }

  // ---- Send the report to the authority (demo), then follow its status ----
  // Only the reference number and a private token are kept on this device, to follow the status.
  const EMIRATES = ["abu_dhabi", "dubai", "sharjah", "ajman", "umm_al_quwain", "ras_al_khaimah", "fujairah"];
  const myCases = () => { try { return JSON.parse(store.get("haris.cases") || "[]"); } catch { return []; } };
  let fileReference = "";
  const refText = (ref) => `⁦${ref.replaceAll("-", "‑")}⁩`;

  // Residents confirm with UAE PASS and their Emirates ID; visitors have none, so they take their own path.
  let visitor = null;

  function chooseResidency() {
    bubble(tr("residencyQ"));
    setChips([[tr("resident"), () => { visitor = null; chooseEmirate(); }],
              [tr("visitor"), () => { visitor = {}; chooseEmirate(); }],
              [tr("minor"), minorHandoff]]);
  }

  // Under 18: Haris does not take a child's report into its own inbox. The Child Protection Centre's
  // specialists handle it, or a parent sends it with their own identity.
  function minorHandoff() {
    visitor = null;
    bubble([el("p", { text: tr("minorHandoff") }), ...contactsBlock([
      { id: "child_protection_moi", value: "116111", label: tr("childMoi") },
      { id: "child_protection_moe", value: "80085", label: tr("childMoe") },
    ]).slice(1), el("p", { class: "note", text: tr("noPrivateImages") })]);
    setChips([[tr("parentSends"), () => { bubble(tr("parentNote")); chooseEmirate(); }], [tr("menuBack"), menu]]);
  }

  function chooseEmirate() {
    bubble(tr(visitor ? "qStaying" : "qEmirate"));
    setChips(EMIRATES.map((e) => [UI[lang].emirates[e], () => (visitor ? askDeparture(e) : authorityConsent(e))]));
  }

  function askDeparture(emirate) {
    bubble(tr("departureQ"));
    setChips(["within_3_days", "within_week", "later", "unknown"].map((d) =>
      [tr(`dep_${d}`), () => { visitor.departure = d; askVisitorText("nationality", emirate); }]));
  }

  // Two typed answers (nationality, then a contact for after they fly), each one can be skipped.
  let visitorStep = null;
  function askVisitorText(field, emirate) {
    visitorStep = { field, emirate };
    mode = "visitor";
    bubble(tr(field === "nationality" ? "nationalityQ" : "contactAbroadQ"));
    setChips([[tr("skip"), () => visitorAnswer("")]]);
    input.focus();
  }

  function visitorAnswer(text) {
    const { field, emirate } = visitorStep;
    visitor[field === "nationality" ? "nationality" : "contact_abroad"] = text.trim();
    if (field === "nationality") return askVisitorText("contact", emirate);
    mode = "check";
    visitorStep = null;
    authorityConsent(emirate);
  }

  async function authorityConsent(emirate) {
    let days = 7;
    try { days = (await (await fetch("/api/health")).json()).inbox_retention_days || days; } catch { /* keep the default */ }
    if (visitor) {
      bubble([el("p", { text: tr("authConsentVisitor", { days }) }), el("p", { class: "note", text: tr("uaePassDemo") })]);
      setChips([[tr("uaePassVisitor"), () => sendToAuthority(emirate, "uae_pass_visitor")],
                [tr("passportVerify"), () => sendToAuthority(emirate, "passport")], [tr("cancel"), menu]]);
      return;
    }
    bubble([el("p", { text: tr("authConsent", { days }) }), el("p", { class: "note", text: tr("uaePassDemo") })]);
    setChips([[tr("uaePass"), () => sendToAuthority(emirate)], [tr("cancel"), menu]]);
  }

  async function sendToAuthority(emirate, visitorIdentity) {
    bubble(tr(visitorIdentity === "passport" ? "passportDone" : "uaePassDone"));
    const body = { ...draft, lang, emirate, consent: true, identity_confirmed: true, reference: fileReference };
    if (visitor) {
      body.visitor = { ...visitor, identity: visitorIdentity };
      if (!body.reporter_contact && visitor.contact_abroad) body.reporter_contact = visitor.contact_abroad;
    }
    const r = await api("/api/reports", body);
    if (!r) return;
    store.set("haris.cases", JSON.stringify([{ ref: r.reference, token: r.token, emirate }, ...myCases()].slice(0, 10)));
    bubble([el("p", { text: tr("sentAuthority", { ref: refText(r.reference), emirate: UI[lang].emirates[emirate], status: r.status_label }) }),
            el("p", { class: "note", text: tr("trackHint") }), visitor ? el("p", { class: "radar-line", text: tr("visitorSent") }) : null]);
    visitor = null;
    setChips([[tr("myReports"), showCases], [tr("menuBack"), menu]]);
  }

  async function caseStatus(c) {
    try {
      const res = await fetch(`/api/reports/${encodeURIComponent(c.ref)}`, { headers: { "X-Report-Token": c.token } });
      return res.ok ? await res.json() : null;
    } catch { return undefined; }
  }

  async function showCases() {
    const cases = myCases();
    if (!cases.length) { bubble(tr("noReports")); setChips([[tr("menuBack"), menu]]); return; }
    const stop = typing();
    const found = await Promise.all(cases.map(caseStatus));
    stop();
    markSeen(cases, found);
    if (found.some((f) => f === null)) bubble(tr("caseGone"));
    const rows = [];
    cases.forEach((c, i) => { if (found[i]) rows.push(caseView(c, found[i])); });
    if (rows.length) bubble(rows);
    const w = cases.findIndex((c, i) => found[i] && found[i].status === "info_requested");
    if (w >= 0) {
      // The authority is waiting: whatever the person types next is their answer, not a message to check.
      askReply(cases[w], found[w]);
      setChips([[tr("refresh"), showCases], [tr("menuBack"), menu]]);
      return;
    }
    setChips([[tr("refresh"), showCases], [tr("menuBack"), menu]]);
  }

  // What changed in a case since the person last looked, told by Haris in a sentence.
  function caseNews(c, s) {
    const fresh = s.events.slice(c.seen || 1);  // the first event is their own "sent"
    const lines = [];
    for (const e of fresh) {
      if (e.kind === "received") lines.push(tr("newsReceived", { ref: refText(c.ref) }));
      if (e.kind === "closed") lines.push(e.note ? tr("newsClosedNote", { ref: refText(c.ref), note: e.note }) : tr("newsClosed", { ref: refText(c.ref) }));
    }
    return lines;
  }

  // found[i]: the status, null when the case is gone (deleted after the retention period), undefined when offline.
  function markSeen(cases, found) {
    store.set("haris.cases", JSON.stringify(cases.flatMap((c, i) => (found[i] === null ? []
      : [found[i] ? { ...c, seen: found[i].events.length } : c]))));
  }

  // When Haris opens: news about the person's reports first, then any question from the authority.
  async function pendingQuestion() {
    const cases = myCases();
    if (!cases.length) return false;
    const found = await Promise.all(cases.map(caseStatus));
    const news = cases.flatMap((c, i) => (found[i] ? caseNews(c, found[i]) : []));
    if (news.length) bubble(news.map((t) => el("p", { text: t })));
    markSeen(cases, found);
    const w = cases.findIndex((c, i) => found[i] && found[i].status === "info_requested");
    if (w < 0) return false;
    askReply(cases[w], found[w]);
    setChips([[tr("myReports"), showCases], [tr("menuBack"), menu]]);
    return true;
  }

  function caseView(c, s) {
    return el("div", { class: `case-card ${s.status}` }, [
      el("strong", { text: tr("caseStatus", { ref: refText(s.reference), status: s.status_label }) }),
      el("ol", { class: "case-events" }, s.events.map((e) => el("li", {}, [
        el("span", { text: `${new Date(e.ts * 1000).toLocaleString(lang === "ar" ? "ar-AE" : lang, { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" })} · ${e.label}` }),
        e.note && e.kind !== "reply" ? el("small", { class: "case-from", text: tr("fromAuthority") }) : null,
        e.note ? el("q", { dir: "auto", text: e.note }) : null,
        e.original ? el("small", { class: "case-original", dir: "auto", text: tr("noteOriginal", { text: e.original }) }) : null,
      ]))),
    ]);
  }

  let replyCase = null;
  function askReply(c, s) {
    replyCase = c;
    mode = "reply";
    const asked = s && [...s.events].reverse().find((e) => e.kind === "info_requested");
    bubble(asked && asked.note
      ? [el("p", { text: tr("infoWaiting", { ref: refText(c.ref), note: asked.note }) }), el("p", { class: "note", text: tr("authoritySafety") })]
      : tr("qAddInfo"));
    input.focus();
  }

  async function sendReply(text) {
    const c = replyCase;
    const stop = typing();  // a reply in another language is translated for the authority: a few seconds
    try {
      const res = await fetch(`/api/reports/${encodeURIComponent(c.ref)}/reply`, {
        method: "POST", headers: { "Content-Type": "application/json", "X-Report-Token": c.token }, body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error();
      stop();
      mode = "check";
      replyCase = null;
      bubble(tr("infoSent"));
    } catch {
      stop();
      bubble(tr("error"));  // still in reply mode: sending again answers the same question
    }
    setChips([[tr("myReports"), showCases], [tr("menuBack"), menu]]);
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
    stopVoice(false);
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
    else if (mode === "fakead") adReceived(text, images);
    else if (mode === "reply" && text) sendReply(text);
    else if (mode === "visitor" && text) visitorAnswer(text);
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

  const store = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode: keep for this visit only */ } },
  };
  const chosenDialect = {};
  let recognizer = null;
  let heard = false;
  let micNoteShown = false;

  // ---- Voice notes: recorded here as WAV, heard on the server (Gemini), never stored ----
  // Works where the browser has no dictation (iPhone home-screen app, Firefox). The words come
  // back into the box for the user to check before sending.
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const canRecord = Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && AudioCtx);
  const VOICE_MAX = 60; // seconds
  let voice = null;
  micBtn.hidden = !(canRecord || Speech);

  async function startVoice() {
    const ctx = new AudioCtx(); // made inside the tap, so iPhone lets it run
    voice = { ctx, chunks: [], started: Date.now(), placeholder: input.placeholder, stream: null, source: null, node: null, timer: null };
    const v = voice;
    micBtn.classList.add("recording");
    micBtn.setAttribute("aria-pressed", "true");
    try {
      if (ctx.state === "suspended") await ctx.resume();
      v.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    } catch {
      await stopVoice(false);
      bubble(tr("micError"));
      return;
    }
    if (voice !== v) { v.stream.getTracks().forEach((t) => t.stop()); return; } // stopped while asking
    v.source = ctx.createMediaStreamSource(v.stream);
    v.node = ctx.createScriptProcessor(4096, 1, 1);
    v.node.onaudioprocess = (e) => { if (voice === v) v.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0))); };
    v.source.connect(v.node);
    v.node.connect(ctx.destination);
    v.started = Date.now();
    const tick = () => {
      if (voice !== v) return;
      const sec = Math.floor((Date.now() - v.started) / 1000);
      input.placeholder = tr("voiceListening", { time: `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}` });
      if (sec >= VOICE_MAX) stopVoice(true);
    };
    tick();
    v.timer = setInterval(tick, 500);
  }

  async function stopVoice(send) {
    const v = voice;
    if (!v) return;
    voice = null;
    clearInterval(v.timer);
    try { if (v.source) v.source.disconnect(); if (v.node) v.node.disconnect(); } catch { /* already disconnected */ }
    if (v.stream) v.stream.getTracks().forEach((t) => t.stop());
    try { await v.ctx.close(); } catch { /* already closed */ }
    input.placeholder = v.placeholder;
    micBtn.classList.remove("recording");
    micBtn.setAttribute("aria-pressed", "false");
    if (!send || !v.chunks.length || Date.now() - v.started < 800) return;

    const audio = wavDataUrl(v.chunks, v.ctx.sampleRate);
    const stop = typing();
    let text = null;
    let status = 0;
    try {
      const res = await fetch("/api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio, lang }),
      });
      status = res.status;
      if (res.ok) text = (await res.json()).text;
    } catch { /* offline */ }
    stop();
    if (!text) { bubble(status === 429 ? tr("tooMany") : tr("voiceFailed")); return; }
    input.value = input.value.trim() ? `${input.value.trim()} ${text}` : text;
    autosize();
    input.focus();
    bubble(tr("voiceHeard"));
  }

  // 16-bit mono WAV at 16 kHz: small, and every speech model reads it.
  function wavDataUrl(chunks, rate) {
    const target = Math.min(16000, rate);
    const total = chunks.reduce((n, c) => n + c.length, 0);
    const all = new Float32Array(total);
    let at = 0;
    for (const c of chunks) { all.set(c, at); at += c.length; }
    const ratio = rate / target;
    const n = Math.floor(total / ratio);
    const view = new DataView(new ArrayBuffer(44 + n * 2));
    const str = (off, t) => { for (let i = 0; i < t.length; i++) view.setUint8(off + i, t.charCodeAt(i)); };
    str(0, "RIFF"); view.setUint32(4, 36 + n * 2, true); str(8, "WAVE"); str(12, "fmt ");
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, target, true); view.setUint32(28, target * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    str(36, "data"); view.setUint32(40, n * 2, true);
    for (let i = 0; i < n; i++) {
      const from = Math.floor(i * ratio);
      const to = Math.max(from + 1, Math.min(total, Math.floor((i + 1) * ratio)));
      let sum = 0;
      for (let j = from; j < to; j++) sum += all[j];
      const x = Math.max(-1, Math.min(1, sum / (to - from)));
      view.setInt16(44 + i * 2, x < 0 ? x * 0x8000 : x * 0x7fff, true);
    }
    const bytes = new Uint8Array(view.buffer);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return `data:audio/wav;base64,${btoa(bin)}`;
  }

  function dialect() {
    const saved = chosenDialect[lang] || store.get(`haris.dialect.${lang}`);
    return UI[lang].dialects.some(([code]) => code === saved) ? saved : null;
  }

  micBtn.addEventListener("click", () => {
    if (voice) return stopVoice(true);
    if (recognizer) return stopDictation(true);
    if (canRecord) return startVoice();
    if (!dialect() && UI[lang].dialects.length > 1) return askDialect(startDictation);
    startDictation();
  });

  function askDialect(then) {
    const choices = el("div", { class: "actions" });
    const node = bubble([el("p", { text: tr("dialectQ") }), choices]);
    for (const [code, name] of UI[lang].dialects) {
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
    recognizer.lang = dialect() || UI[lang].dialects[0][0];
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
    const arrow = RTL.has(lang) ? "←" : "→";
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
    document.documentElement.dir = RTL.has(lang) ? "rtl" : "ltr";
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
    stopVoice(false);
    applyLanguage(b.dataset.lang);
    chat.replaceChildren();
    showTools(false);
    start();
  }));

  async function start() {
    bubble(tr("welcome"));
    await showBroadcasts();
    if (!(await pendingQuestion())) menu();
  }

  loadLocales().then(() => {
    applyLanguage("ar");
    start();
  });
})();
