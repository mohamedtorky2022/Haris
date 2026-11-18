<p align="center"><img src="frontend/haris.svg" alt="Haris mascot" width="140"></p>

# Haris (حارس) — an AI assistant against cybercrime

> **حارس** مساعد ذكي يحمي كل من يعيش في الإمارات من الاحتيال والجرائم الإلكترونية، بلغته: يفحص الرسائل والروابط المشبوهة، ويرشد الضحية خطوة بخطوة، ويجهّز ملف بلاغ منظماً للشرطة. لا يحفظ رسائل المستخدمين، ويخفي بياناتهم الشخصية قبل أي تحليل.

Haris is a chat assistant that helps anyone in the UAE spot online scams, act fast when they have been scammed, and hand the police a complete report. It speaks Arabic, English and Urdu, and stores nothing users send.

This repository is the hackathon MVP: a FastAPI backend and a WhatsApp-style web chat.

---

## 1. The problem

Online fraud in the UAE reaches every group differently: fake parcel fees, bank and police impersonation, fake jobs aimed at migrant workers, investment scams, and extortion of teenagers. Three gaps make it worse:

1. **No one to ask in the moment.** When a suspicious SMS or call arrives, people have nobody to ask "is this real?" within seconds.
2. **Victims lose the first hour.** Money is most recoverable right after the fraud, but victims are panicked, don't know the steps, and sometimes delete the evidence or pay the extortionist.
3. **Reports arrive incomplete.** Police receive reports missing the timeline, the scammer's numbers and links, and the evidence, which slows the response.

Language makes all three worse: a large part of the population reads neither Arabic nor English comfortably.

## 2. The solution

Haris covers the three moments of a cybercrime:

| Moment | What Haris does |
| --- | --- |
| **Before** — a suspicious message arrives | Paste any message, link or offer. Haris rates the risk (low / medium / high), names the scam type, explains **why** in plain words, and says what to do. |
| **After** — "I've been scammed" | A step-by-step emergency plan for ten situations: money sent, account hacked, extortion, online bullying/harassment/defamation, a fake account in your name, being filmed or having photos or personal details posted without permission, a hacked device or ransomware (including SIM swap), ID shared, a business that paid a fake invoice or a fake "boss" request, and a suspicious message only. Each comes with the official reporting channels. |
| **Reporting** | The victim tells the story their own way: typed, spoken or as screenshots of the chat or the debit alert. For speech, the user picks their dialect once (Emirati/Gulf, Saudi, Egyptian, Levantine, Iraqi, Maghrebi; English and Urdu accents too), and after each dictation Haris suggests fixes for misheard words such as «ارا ماكس» → «أرامكس». The user approves the fix, and numbers are never changed. Haris pulls out the amount, time, payment method, steps already taken and the scammer's numbers, links and IBANs, asks only about what is still missing with ready-made answers, then shows a summary card where any line can be edited. The report opens in a new tab, downloads as a web page with the screenshots inside, or prints and saves as PDF. |
| **Early warning** — a message nobody fell for | "Report it to protect others" sends the sender's number, link and the redacted text to the **campaign radar** (demo). Reports that share a number, a link or the same text become one campaign. At 3 people Haris tells anyone who checks it "reported by N people"; at 10 people, or 3 with a link imitating an official body, the authority is alerted on its dashboard. Only the authority can approve a public warning, which then reaches every Haris user and sends a block request to the telecom providers (simulated). |

### What it covers today, and what is next

Haris starts with **fraud**, the most common and costly cybercrime, and is built so a new crime type is one playbook or one signal away.

- **Detects 15 scam types:** one-time code theft, bank and government impersonation, fake delivery, fake jobs, fake investments, fake prizes, extortion, fake tech support, phishing links, romance scams, fake "money recovery" offers aimed at people already scammed, fake shops, listings and rentals, fake charities, and fake visas or residency.
- **Guides and reports 10 situations** (listed above).
- **Next:** protecting children from grooming (with specialists reviewing the wording), voice calls and AI-cloned voices, QR codes and screenshot checks, attacks on businesses (data leaks, outages), and rumours and fake news.

Haris always presents itself as an assistant, **not** an official body, and never tells a user a message is "safe": the lowest rating is "no clear warning signs".

### Who it serves

The same engine serves every group; the scam patterns and advice cover parcel and payment scams (shoppers), OTP and bank impersonation (older people), fake jobs and visa fees (migrant workers, in Urdu), investment and crypto scams (investors), extortion (teenagers and women, with "you are not to blame, don't pay, don't delete, report" guidance) and fake tech support.

## 3. How it works

```
 Browser (web chat, AR / EN / UR)
        │  /api/check, /api/playbooks, /api/extract, /api/polish, /api/report
        ▼
 FastAPI app ── rate limit, security headers, input limits, no logging of content
        │
        ▼
 haris core (pure Python, no dependencies)
   ├─ text.py       normalise Arabic spelling and digits, detect language
   ├─ redact.py     remove card numbers (Luhn-checked), Emirates ID, IBAN, phones, e-mails
   ├─ rules.py      ~20 weighted scam signals in 3 languages, with "unless" exceptions
   ├─ urls.py       offline link analysis: look-alike brands, risky TLDs, shorteners, raw IPs
   ├─ detector.py   combines the above into a score, risk level and category
   ├─ llm.py        optional Claude second opinion on the REDACTED text
   ├─ intake.py     turns a free story and screenshots into report fields
   ├─ polish.py     fixes misheard words in dictated text (glossary + optional AI), never digits
   ├─ radar.py      campaign radar: groups reports, warns, escalates; the authority confirms (SQLite)
   ├─ playbooks.py  emergency plans + official contacts
   └─ report.py     builds the police report in memory
```

Full detail, including model choices and the privacy design, is in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## 4. Run it

Requirements: Python 3.9 or newer (macOS ships 3.9 with the Xcode tools).

```bash
git clone <this repo> haris && cd haris
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The API docs are at <http://127.0.0.1:8000/docs>.

**Optional — turn on the AI second opinion:**

```bash
cp .env.example .env                  # from the repo root, then put your key in .env
cd backend
uvicorn app.main:app --reload --env-file ../.env
```

Without a key, Haris runs entirely on its rules engine and works offline.

**Demo the campaign radar** (with the server running):

```bash
python scripts/radar_demo.py          # 10 people report the same fake-parcel campaign
```

Open <http://127.0.0.1:8000/authority.html> (the authority dashboard), approve the warning, then reload the chat: every user now sees the official warning, and any message from those numbers or links is rated high risk.

### Tests and evaluation

```bash
pip install -r requirements-dev.txt
pytest                                 # from the repo root
python scripts/evaluate.py             # accuracy on the labelled sample messages
```

On the 52 labelled samples in `data/samples/messages.json` (33 scams, 19 legitimate messages, in 3 languages), the rules engine alone catches **33 of 33 scams** with **0 of 19 false alarms**. These samples were written by the team while building the rules, so they show the rules behave as designed; they are **not** an independent accuracy measure (see trade-offs below).

### API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/check` | `{"text": "...", "lang": "ar|en|ur"}` → risk, category, reasons, advice, link analysis |
| `GET` | `/api/playbooks?lang=` | list of emergency situations |
| `GET` | `/api/playbooks/{id}?lang=` | steps + official contacts for one situation |
| `POST` | `/api/extract` | `{"text": "...", "images": ["data:image/jpeg;base64,..."], "lang": "ar"}` → report fields found, and the fields still missing |
| `POST` | `/api/polish` | `{"text": "...", "lang": "ar", "dialect": "ar-EG"}` → corrected text and the list of changed words (numbers never change) |
| `POST` | `/api/radar/report` | `{"text": "...", "lang": "ar", "reporter_id": "random-device-id"}` → the campaign it joined and how many people reported it |
| `GET` | `/api/radar/broadcasts?lang=` | official warnings the authority approved |
| `GET` | `/api/authority/campaigns` | campaigns for the authority dashboard (this computer only, or with `X-Authority-Token`) |
| `POST` | `/api/authority/campaigns/{id}` | `{"status": "confirmed" \| "dismissed"}`: approve the public warning and block request, or dismiss |
| `POST` | `/api/report` | build a police report (HTML + Markdown), nothing stored |
| `GET` | `/api/health` | status, and whether the AI second opinion is on |

## 5. Technical choices and trade-offs

**Rules first, AI second.** The core verdict comes from a transparent rules engine, and Claude is an optional second opinion.
- *Why:* every warning can be explained in one sentence, the system works with no internet or API key, it costs nothing per check, and it answers in milliseconds. That matters for a public-safety service where a partner authority must review what it says.
- *Trade-off:* rules only catch patterns someone wrote down. New scam wording slips through until a rule is added. The AI layer covers that gap when enabled.

**The AI can only raise the risk, never lower it.** If the rules say "high" and the model says "low", the user still sees "high". A missed scam costs far more than an extra warning.

**Redact before the model sees anything.** Card numbers, Emirates IDs, IBANs, phones and e-mails are replaced with placeholders, and link query strings are dropped, before any text is sent to Claude. The model doesn't need them to judge a scam.

**No AI SDK dependency.** `llm.py` calls the Claude API with the Python standard library, so the core installs with no third-party packages and the AI layer can be swapped without touching the rest.

**Web chat instead of WhatsApp for the MVP.** WhatsApp Business API approval takes weeks, so the demo runs as a WhatsApp-style web chat. The backend is channel-agnostic: a WhatsApp webhook would call the same `/api/check`.

**Stateless for users, one small store for scammers.** Checks, police reports, screenshots and dictation are never stored. The only stored data is the campaign radar: the sender's numbers, links and the redacted message text, sent only when the user taps "Report it". Nothing about the reporter is kept except a keyed hash of a random device id, so one device counts once. Reports are deleted after 30 days.
- *Trade-off:* this is the first data Haris keeps, so a real launch needs a data-sharing agreement, UAE hosting and verified reporters (for example UAE PASS).

**Reports alone never block a number.** People can report an innocent number on purpose, and scammers spoof real numbers. So the radar only warns ("reported by N people", never "this is a scammer") and alerts the authority; the public warning and the block request need a person at the authority to approve them.

**Fix dictation instead of training a speech model.** Transcription is done by the browser's own speech service, which we cannot train. We improve it in two cheap steps: the user's dialect is passed to the service, and a correction pass (a glossary of fraud terms, plus Claude when enabled) fixes misheard words.
- *Why:* it works today in every modern browser, costs nothing without the AI, and keeps audio off our servers.
- *Trade-off:* it can't fix what the service didn't hear at all. A trainable server-side model (Azure Custom Speech, which supports ar-AE, ar-EG, ar-SA and more; Urdu only as ur-IN) is the plan for the police pilot, hosted in a UAE region and trained on anonymised data from the partner.
- *Safety:* numbers, links and e-mails are swapped for tokens before the AI sees the text and put back after; an answer that loses, repeats or adds a digit is thrown away. The user always sees the changes and chooses.

**Plain JavaScript front end.** No framework and no build step, so judges can run it with one command, and the strict Content-Security-Policy (`script-src 'self'`) stays simple.

### What we left out

- **Reading screenshots without the AI.** With no API key, screenshots are attached to the report as evidence but not read. On-device text recognition would let the rules read them too.
- **The radar in production.** The demo radar runs on SQLite on the same server, counts one device as one person, and simulates the telecom block request. Production needs the partner's systems, verified reporters and a real block channel with the telecom providers.
- **Live link reputation.** Links are judged offline from their structure. Google Safe Browsing or a police blocklist would add a live check.
- **Training our own speech model.** Dictation accuracy depends on the browser's service. A trainable model (Azure Custom Speech or an open-source model hosted in the UAE) needs recordings with transcripts from the partner, so it is planned for the pilot.
- **Voice line for older people,** the family app for children and teenagers, and more languages (Hindi, Malayalam, Tagalog, Bengali).
- **Direct submission to the police.** Haris prepares the report; the user still files it. Direct submission needs an integration agreement.

### What we would do differently with more time

- Build the test set from **real, anonymised scam messages** supplied by the partner authority, measured separately from the rules, instead of samples we wrote ourselves.
- Have the **Arabic dialect and Urdu wording reviewed** by native speakers and by child-protection and victim-support specialists, especially the extortion guidance.
- Replace keyword weights with a **small fine-tuned classifier** trained on that data, keeping the rules as an explainable safety net.
- Store rules and advice text in a **reviewable content file** the partner authority can edit without a code change.

## 6. Privacy and safety summary

- Nothing users send is stored or logged, except a report the user chooses to send to the campaign radar: the sender's numbers and links and the redacted text, kept 30 days, with no data about the reporter. API responses carry `Cache-Control: no-store`.
- The authority dashboard opens only on the computer running Haris, or anywhere with the `HARIS_AUTHORITY_TOKEN` set.
- Personal data is redacted from text before any AI call; link query strings are dropped.
- Screenshots are resized in the browser, which also drops photo metadata such as location. They are sent to the AI only when it is switched on, are not stored, and go into the report file on the user's own device.
- Dictation uses the browser's built-in speech service (in Chrome this is Google's, in Safari Apple's); the user sees and can correct the text before it is sent.
- The model prompt treats the message strictly as data, so instructions hidden inside a scam message are ignored.
- Rate limiting, input size limits, strict security headers, and all server text rendered with `textContent` (no HTML injection).
- Haris is defensive only: it never visits, scans or contacts the links or numbers it analyses.
- Test data is synthetic. No real victim's data is in this repository.

Details: [`docs/TECHNICAL.md`](docs/TECHNICAL.md#privacy-design).

## 7. Project structure

```
haris/
├── README.md
├── requirements.txt            runtime: FastAPI, Uvicorn, Pydantic
├── requirements-dev.txt        tests: pytest, httpx
├── .env.example                optional AI settings (no real keys)
├── backend/
│   ├── app/main.py             FastAPI routes, middleware, static front end
│   └── haris/                 the core engine (pure Python)
├── frontend/                   index.html, styles.css, app.js
├── data/samples/messages.json  labelled synthetic test messages
├── scripts/evaluate.py         accuracy on the samples
├── scripts/radar_demo.py       sends 10 reports of one campaign, for a live demo
├── tests/                      unit and API tests
└── docs/
    ├── TECHNICAL.md            architecture, model choices, privacy design
    ├── Haris-presentation.pptx     presentation (English)
    └── Haris-presentation-ar.pptx  presentation (Arabic)
```

## 8. Third-party software and ownership

The code in this repository was written by the team for the hackathon. It uses these open-source packages under their licences: FastAPI (MIT), Uvicorn (BSD-3-Clause), Pydantic (MIT), and for tests pytest (MIT) and HTTPX (BSD-3-Clause). The optional AI layer calls the Anthropic Claude API under Anthropic's terms. The official contact numbers come from public Abu Dhabi Police and Dubai Police announcements and should be confirmed by the partner authority before launch.

## Team

| Name | Role |
| --- | --- |
| _to fill in_ | |
| _to fill in_ | |
| _to fill in_ | |
