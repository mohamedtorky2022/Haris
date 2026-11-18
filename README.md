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
| **After** — "I've been scammed" | A step-by-step emergency plan for the situation (money sent, account hacked, extortion, ID shared, suspicious message only), with the official reporting channels. |
| **Reporting** | A guided conversation builds a structured police report (timeline, amount, scammer identifiers, evidence, steps taken). Haris pulls phone numbers, e-mails, IBANs and links out of the victim's description automatically. The report opens in a new tab, downloads as a web page, or prints and saves as PDF. |

Haris always presents itself as an assistant, **not** an official body, and never tells a user a message is "safe": the lowest rating is "no clear warning signs".

### Who it serves

The same engine serves every group; the scam patterns and advice cover parcel and payment scams (shoppers), OTP and bank impersonation (older people), fake jobs and visa fees (migrant workers, in Urdu), investment and crypto scams (investors), extortion (teenagers and women, with "you are not to blame, don't pay, don't delete, report" guidance) and fake tech support.

## 3. How it works

```
 Browser (web chat, AR / EN / UR)
        │  POST /api/check, GET /api/playbooks, POST /api/report
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

### Tests and evaluation

```bash
pip install -r requirements-dev.txt
pytest                                 # from the repo root
python scripts/evaluate.py             # accuracy on the labelled sample messages
```

On the 34 labelled samples in `data/samples/messages.json` (22 scams, 12 legitimate messages, in 3 languages), the rules engine alone catches **22 of 22 scams** with **0 of 12 false alarms**. These samples were written by the team while building the rules, so they show the rules behave as designed; they are **not** an independent accuracy measure (see trade-offs below).

### API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/check` | `{"text": "...", "lang": "ar|en|ur"}` → risk, category, reasons, advice, link analysis |
| `GET` | `/api/playbooks?lang=` | list of emergency situations |
| `GET` | `/api/playbooks/{id}?lang=` | steps + official contacts for one situation |
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

**Stateless by design.** There is no database. Reports are built in memory and returned to the browser. This removes the biggest privacy risk, at the cost of features that need memory (see below).

**Plain JavaScript front end.** No framework and no build step, so judges can run it with one command, and the strict Content-Security-Policy (`script-src 'self'`) stays simple.

### What we left out

- **Screenshots and images.** Many scams arrive as images. The next step is to send screenshots to Claude's vision model, after on-device blurring of personal data.
- **The community radar.** Spotting a new campaign when many people report the same text or link needs anonymised storage and a data-sharing agreement with the partner authority. We left it out rather than store data without that agreement.
- **Live link reputation.** Links are judged offline from their structure. Google Safe Browsing or a police blocklist would add a live check.
- **Voice line for older people,** the family app for children and teenagers, and more languages (Hindi, Malayalam, Tagalog, Bengali).
- **Direct submission to the police.** Haris prepares the report; the user still files it. Direct submission needs an integration agreement.

### What we would do differently with more time

- Build the test set from **real, anonymised scam messages** supplied by the partner authority, measured separately from the rules, instead of samples we wrote ourselves.
- Have the **Arabic dialect and Urdu wording reviewed** by native speakers and by child-protection and victim-support specialists, especially the extortion guidance.
- Replace keyword weights with a **small fine-tuned classifier** trained on that data, keeping the rules as an explainable safety net.
- Store rules and advice text in a **reviewable content file** the partner authority can edit without a code change.

## 6. Privacy and safety summary

- Nothing users send is stored or logged. API responses carry `Cache-Control: no-store`.
- Personal data is redacted before any AI call; link query strings are dropped.
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
