<p align="center"><img src="frontend/haris.svg" alt="Haris mascot" width="140"></p>

# Haris (حارس) — an AI assistant against cybercrime

> **حارس** مساعد ذكي يحمي كل من يعيش في الإمارات من الاحتيال والجرائم الإلكترونية، بلغته: يفحص الرسائل والروابط المشبوهة، ويرشد الضحية خطوة بخطوة، ويجهّز ملف بلاغ منظماً للشرطة. لا يحفظ رسائل المستخدمين، ويخفي بياناتهم الشخصية قبل أي تحليل.

Haris is a chat assistant that helps anyone in the UAE spot online scams, act fast when they have been scammed, and hand the police a complete report. It speaks Arabic, English, Urdu, Hindi and Russian, works for visitors without an Emirates ID, and stores nothing users send unless they choose to send a report.

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
| **Sending it** — to the authority (demo) | "Send it to the authority": the victim picks their emirate, reads exactly what will be sent and for how long it is kept, confirms their identity (UAE PASS, simulated in the demo), and the report reaches the **reports dashboard** with the same reference number as their file. Haris sorts it: **critical** (a threat to life, or a child involved), **financial** (money lost in the last 24 hours, when the bank can still freeze it), **medium**, or **indicator**. The officer receives it, asks for more information, or closes it with a note, and the victim follows every step in "My reports" and answers in the chat. A report written in **Hindi, Urdu, English or Russian reaches the officer in Arabic**, with the victim's own words beside it and their language flagged so the case can go to an officer who speaks it; the officer writes in Arabic and the victim reads the note in their own language. |
| **Visitors** — no Emirates ID | Every check, plan and report file works without any ID. When sending a report, Haris asks "do you live here or are you visiting?". A visitor picks the emirate they are staying in, when they leave, their nationality and a contact for after they fly, and confirms their identity with a UAE PASS visitor account (passport) or their passport (both simulated in the demo). A visitor leaving within 3 days moves up the queue, and the officer sees "suggest the Tourism Police", who follow a visitor's case even after they leave. Every plan ends with tips for visitors: a card from a bank abroad, the embassy, travel insurance, and the Tourism Police numbers. |
| **Children** — under 18 | Haris checks messages and guides a child like anyone else, and the extortion, harassment and leaked-photos plans end with a section for under-18s: "it is not your fault", tell an adult you trust, never send or attach a private photo, and the Child Protection Centre (116111 and the Hemayati app) and the Ministry of Education's unit (80085). At sending, "I'm under 18" does **not** put a child's report into Haris's inbox: Haris hands it to the Child Protection Centre's specialists, or a parent continues and sends it with their own identity. |
| **Early warning** — a message nobody fell for | "Report it to protect others" sends the sender's number, link and the redacted text to the **campaign radar** (demo). Reports that share a number, a link or the same text become one campaign. At 3 people Haris tells anyone who checks it "reported by N people"; at 10 people, or 3 with a link imitating an official body, the authority is alerted on its dashboard. Only the authority can approve a public warning, which then reaches every Haris user, goes out as a **WhatsApp alert to everyone who subscribed** (by sending «تنبيهات» / ALERTS) in the language they chose, after the officer has seen it in all five languages (the standard wording, or the authority's own text translated by Haris and editable), and sends a block request to the telecom providers (simulated). |

### What it covers today, and what is next

Haris starts with **fraud**, the most common and costly cybercrime, and is built so a new crime type is one playbook or one signal away.

- **Detects 15 scam types:** one-time code theft, bank and government impersonation, fake delivery, fake jobs, fake investments, fake prizes, extortion, fake tech support, phishing links, romance scams, fake "money recovery" offers aimed at people already scammed, fake shops, listings and rentals, fake charities, and fake visas or residency.
- **Guides and reports 10 situations** (listed above).
- **Next:** protecting children from grooming (with specialists reviewing the wording), voice calls and AI-cloned voices, QR codes and screenshot checks, attacks on businesses (data leaks, outages), and rumours and fake news.

### Using it

Open Haris and pick a language. The menu offers four things: **check a message or link**, **I've been scammed, what now?**, **prepare a police report**, and **how do I use Haris?**, a short in-app guide in Arabic, English and Urdu that explains the three steps and how reporting an ignored scam protects others. Once a report has been sent to the authority, **My reports** appears too, with its status and any message from the officer.

The next version, a mobile app and a WhatsApp channel, is designed in an official government style: home and quick check, check result, report by voice or screenshots, report summary, official warnings and the campaign radar, and the same flows inside a WhatsApp business chat.

**Campaign poster: «حارس» درعك الذكي ("Haris, your smart shield").** An A3 poster shows the name, that line, and three words for what Haris does (يحذّرك · يرشدك · يوصّل بلاغك: it warns you, guides you, and carries your report). Below them a golden shield holds the map of the UAE, its seven emirates linked by a digital network, while viruses, fake links and phishing hooks bounce off its edge; Haris stands beside it. Scanning the QR code at the bottom opens WhatsApp straight to a chat with Haris, where people save the contact and forward suspicious messages. The source is in `docs/poster/` (`poster.html` and a rendered `haris-poster.png`). The QR holds a placeholder message until the official WhatsApp number is live; then `qr.svg` is regenerated with the `wa.me/<number>` link.

Haris always presents itself as an assistant, **not** an official body, and never tells a user a message is "safe": the lowest rating is "no clear warning signs".

### Who it serves

The same engine serves every group; the scam patterns and advice cover parcel and payment scams (shoppers), OTP and bank impersonation (older people), fake jobs and visa fees (migrant workers, in Urdu and Hindi), investment and crypto scams (investors), extortion (teenagers and women, with "you are not to blame, don't pay, don't delete, report" guidance) and fake tech support.

## 3. How it works

```
 Browser (web chat, AR / EN / UR / HI / RU)   WhatsApp (Cloud API)
        │  /api/check, /api/playbooks, …          │  /webhook/whatsapp (signed by Meta)
        ▼                                         ▼
 FastAPI app ── rate limit, security headers, input limits, no logging of content
        │
        ▼
 haris core (pure Python, no dependencies)
   ├─ text.py       normalise Arabic spelling and digits, detect language
   ├─ redact.py     remove card numbers (Luhn-checked), Emirates ID, IBAN, phones, e-mails
   ├─ rules.py      30 weighted scam signals in 5 languages, with "unless" exceptions
   ├─ urls.py       offline link analysis: look-alike brands, risky TLDs, shorteners, raw IPs
   ├─ detector.py   combines the above into a score, risk level and category
   ├─ llm.py        the AI layer (Claude or Gemini) on the REDACTED text
   ├─ examples.py   teaching by example: similar labelled messages shown to the model
   ├─ intake.py     turns a free story and screenshots into report fields
   ├─ polish.py     fixes misheard words in dictated text (glossary + optional AI), never digits
   ├─ radar.py      campaign radar: groups reports, warns, escalates; the authority confirms (SQLite)
   ├─ inbox.py      reports sent to the authority (demo): triage, routing by emirate, status, auto-delete (SQLite)
   ├─ translate.py  victim ↔ authority translation; numbers and links never reach the model
   ├─ whatsapp.py   WhatsApp channel: checks Meta's signature, replies with buttons and lists
   ├─ alerts.py     official warnings on WhatsApp: opt-in subscribers, delivery when a campaign is approved
   ├─ translations.py  loads all wording from locales/<lang>.json (one file per language)
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

**Turn on the AI** (Claude or Gemini):

```bash
cp .env.example .env                  # from the repo root, then put one key in .env
cd backend
uvicorn app.main:app --reload --env-file ../.env
```

- **Claude:** `ANTHROPIC_API_KEY` from the Claude Console. Claude Max, Ultra and Team plans include monthly API credits.
- **Gemini, free:** `GEMINI_API_KEY` from Google AI Studio (aistudio.google.com/apikey). The free tier needs no card; Google may use free-tier requests to improve its products, which is one more reason Haris redacts personal data first.

`GET /api/health` shows which provider and model are answering. Without a key, Haris runs entirely on its rules engine and works offline.

**Teach Haris by example.** Fine-tuning is not offered on Gemini's free API, so Haris learns from labelled examples instead: before each check, the most similar examples and their correct answers are shown to the model. A new example changes the next answer, with no training run:

```bash
python scripts/teach.py scam "message text" --category bank_impersonation --why "asks for the OTP"
python scripts/teach.py legit "a real message" --why "no link, asks for nothing"
python scripts/evaluate.py --ai       # measure rules + AI on the labelled set
```

Examples are redacted before they are saved in `data/training/examples.jsonl`. The model never sees the message it is judging among its examples, so the evaluation stays honest.

**Demo the campaign radar** (with the server running):

```bash
python scripts/radar_demo.py          # 10 people report the same fake-parcel campaign
```

Open <http://127.0.0.1:8000/authority.html> (the authority dashboard), approve the warning, then reload the chat: every user now sees the official warning, and any message from those numbers or links is rated high risk.

To show the WhatsApp alert going out, add fictional subscribers first: `python scripts/alerts_demo.py` (2,400 in five languages). After the approval, "WhatsApp alerts" on the same page counts the delivery. Fictional subscribers are never sent anything; a real phone that sends «تنبيهات» to the Haris number gets the warning for real once WhatsApp is connected.

**Demo the reports dashboard** (with the server running):

```bash
python scripts/inbox_demo.py --clear  # 30 fictional reports: 5 languages, visitors, 7 emirates, the past 5 days
```

Open <http://127.0.0.1:8000/reports.html>. The queue puts the critical cases first (a threat to life, a child in an extortion), then money lost in the last hours; some cases are already received, waiting for information, or closed. Open a case, press "Receive", then "Ask for information" with a note. In the chat, "My reports" now shows the note, and the victim's answer appears in the case log. To try it end to end, prepare a report in the chat and press "Send it to the authority".

**Connect WhatsApp** (free, with Meta's test number):

1. In [Meta for Developers](https://developers.facebook.com), create an app and add the WhatsApp product. Meta gives you a free test number that can message up to 5 phone numbers you verify.
2. Put the access token, the Phone number ID and the app secret in `.env`, and choose any long random `WHATSAPP_VERIFY_TOKEN` (see `.env.example`). Restart the server with `--env-file ../.env`.
3. Give the server a public HTTPS address, for example with a free Cloudflare quick tunnel: `cloudflared tunnel --url http://localhost:8000`.
4. In Meta's WhatsApp > Configuration, set the callback URL to `https://<tunnel address>/webhook/whatsapp`, type the same verify token, and subscribe to the `messages` field.
5. Send "مرحباً" or "hi" to the test number from a verified phone. Haris answers with buttons: check a message, I've been scammed, how to use it.

The test number cannot receive messages from the public. For the poster's QR code, Haris needs its own WhatsApp Business number.

**Journey video** (Arabic, narrated, about 4:10; English, captions only, about 3:40). It opens on the campaign poster and its QR code, shows the problem in a few seconds, then follows three people, each in their own scene:

- **Ahmed, a resident of Abu Dhabi:** a forwarded parcel scam gets a "high risk" rating before he pays; later a card scam gets the emergency plan, a voice note becomes the report file, and he sends it with his consent and UAE PASS. The authority's screen then shows the report at the top of the queue as "urgent, money", with the step to take now, and Ahmed is told when the officer takes it.
- **Anna, a visitor from Russia with no Emirates ID:** she writes in Russian, confirms her identity with her passport and says she leaves within 3 days. On the authority's screen the visitor badge moves her report up, her story is in Arabic with the Russian original below, and the Tourism Police are suggested. The officer asks in Arabic, Anna gets the question in Russian in Haris's voice, and her reply comes back in Arabic.
- **A 15-year-old student:** Haris tells him it is not his fault, asks for no personal data, and hands him to child protection (116111) or to a parent.

Then the community part (the campaign radar, the warning previewed in five languages and approved by the officer, the WhatsApp alert reaching every subscriber in their language), privacy, how Haris works (with the local rules carrying on if the AI is down), what Haris does, what comes next (training on real data, more cases, direct links with the police, banks and telecom providers, more languages), and a closing card with the QR code. The Arabic captions are in Modern Standard Arabic. In the English version the authority's screen is shown in English and labelled as such, because the real screen is in Arabic. The Arabic version is narrated in Modern Standard Arabic by the neural voice Hamdan (ar-AE), generated with FreeTTS.ai; the English version has captions only. `voice.py` cuts the long recordings into one clip per caption at the pauses between lines, trims the silences, starts each caption with its line, and lengthens a scene when its lines need more time. Haris speaks the narration: his mouth opens with the loudness of the voice in each frame, he blinks every 3 seconds, and he nods and points at the screen with every line, all on one GSAP timeline (`vendor/gsap.min.js`) that the renderer seeks frame by frame, so every render is identical. The music is calm and composed in code (`journey.py`), so there is no licence to clear, and it steps back while the narrator speaks. Names, numbers and reference codes are fictional, and every screen is labelled as a demo.

```bash
bash docs/video/fetch_fonts.sh        # IBM Plex Arabic and Devanagari (Open Font License)
python3 docs/video/journey.py all     # needs ffmpeg and Playwright's Chromium; writes docs/video/out/Haris-journey-<lang>.mp4
python3 docs/video/journey.py ar --stills 33,73   # draw single frames at those seconds, to check a scene
python3 docs/video/voice.py lines ar     # the lines to narrate (out/voice-ar/lines.json, chunks.json)
python3 docs/video/voice.py split ar     # cut hamdan1.mp3, hamdan2.mp3, hamdan3.mp3 into one clip per line
python3 docs/video/voice.py timing ar    # measure the clips; journey.py then times the scenes to them
```

Scenes, timings and captions are in `docs/video/journey.json`, and the drawing is `docs/video/journey.html`. The poster is rendered from `docs/poster/poster.html` with `python3 docs/poster/render.py docs/poster/poster.html docs/poster/haris-poster.png` (it uses the local fonts, so it works offline). An earlier narrated version (`render.py`, voices from `build_voice.sh`) is kept for reference.

### Tests and evaluation

```bash
pip install -r requirements-dev.txt
pytest                                 # from the repo root
python scripts/evaluate.py             # accuracy on the labelled sample messages
python scripts/evaluate.py --ai --hard # rules + AI on wording the rules were not written for
```

| Set | Rules only | Rules + Gemini |
|---|---|---|
| `messages.json`: 37 scams, 22 genuine, 4 languages | 37/37 caught, 0/22 false alarms | 37/37 caught, 0/22 false alarms (AI answered 59/59) |
| `hard.json`: 12 scams in new wording, 8 genuine messages that look suspicious | **2/12** caught, 0/8 false alarms | **12/12** caught, 0/8 false alarms (AI answered 20/20) |

Measured on 20 November 2026 with `gemini-3.5-flash-lite` on the free tier. The first set was written while building the rules, so it shows they behave as designed; the hard set was written afterwards, is never shown to the model as an example, and shows what the AI adds: "my phone broke, this is my new number", a fake CEO asking for gift cards, a fake landlord abroad, a "wrong number" that turns to crypto. Both sets are small and written by us; a real accuracy figure needs genuine, anonymised messages from the partner authority.

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
| `POST` | `/api/reports` | the report fields plus `emirate`, `consent: true`, `identity_confirmed`, `reference` → the reference, the priority and a private status token |
| `GET` | `/api/reports/{ref}` | the status and the authority's messages, with the `X-Report-Token` header |
| `POST` | `/api/reports/{ref}/reply` | `{"text": "..."}`: the victim adds the information asked for |
| `GET` | `/api/authority/reports` | the queue, most urgent first, and the counters (authority only) |
| `POST` | `/api/authority/reports/{ref}` | `{"action": "receive" \| "request_info" \| "close", "note": "..."}` (authority only) |
| `GET` | `/api/authority/campaigns` | campaigns for the authority dashboard (this computer only, or with `X-Authority-Token`) |
| `POST` | `/api/authority/campaigns/{id}` | `{"status": "confirmed" \| "dismissed"}`: approve the public warning, the WhatsApp alert and the block request, or dismiss |
| `POST` | `/api/authority/campaigns/{id}/preview` | `{"text": "..."}` (optional): the warning in all five languages, the authority's own text translated (authority only) |
| `GET` | `/api/authority/alerts` | WhatsApp alert subscribers by language, the delivery mode, and the last deliveries (authority only) |
| `POST` | `/api/report` | build a police report (HTML + Markdown), nothing stored |
| `GET` | `/api/health` | status, and whether the AI second opinion and WhatsApp are on |
| `GET` | `/webhook/whatsapp` | Meta's one-time check of the verify token |
| `POST` | `/webhook/whatsapp` | incoming WhatsApp messages (refused unless signed with the app secret) |

## 5. Technical choices and trade-offs

**Rules first, AI second.** The core verdict comes from a transparent rules engine, and an AI model (Claude, or Gemini on its free tier) is the second opinion.
- *Why:* every warning can be explained in one sentence, the system works with no internet or API key, it costs nothing per check, and it answers in milliseconds. That matters for a public-safety service where a partner authority must review what it says.
- *Trade-off:* rules only catch patterns someone wrote down. New scam wording slips through until a rule is added. The AI layer covers that gap when enabled.

**The AI can only raise the risk, never lower it.** If the rules say "high" and the model says "low", the user still sees "high". A missed scam costs far more than an extra warning.

**Redact before the model sees anything.** Card numbers, Emirates IDs, IBANs, phones and e-mails are replaced with placeholders, and link query strings are dropped, before any text is sent to the model. The model doesn't need them to judge a scam.

**No AI SDK dependency.** `llm.py` calls the Claude and Gemini APIs with the Python standard library, so the core installs with no third-party packages and the provider is one setting (`HARIS_AI_PROVIDER`).

**Teach by example, not by fine-tuning.** Fine-tuning needs a large labelled set of real UAE messages and, for Gemini, a paid cloud account. Showing the model the most similar labelled examples works with any provider, costs nothing, and a correction takes effect on the next check.
- *Trade-off:* the examples make each prompt a little longer, and the model can still disagree with them; the rules engine stays the safety net.

**Web chat first, WhatsApp on the test number.** A public WhatsApp Business number needs Meta's approval, so the main demo is a WhatsApp-style web chat. The WhatsApp channel is built and runs on Meta's free test number, which reaches up to 5 verified phones: it calls the same engine, so a check gives the same answer on both channels.

**Stateless for users, one small store for scammers.** Checks, police reports, screenshots and dictation are never stored. The only stored data is the campaign radar: the sender's numbers, links and the redacted message text, sent only when the user taps "Report it". Nothing about the reporter is kept except a keyed hash of a random device id, so one device counts once. Reports are deleted after 30 days.
- *Trade-off:* this is the first data Haris keeps, so a real launch needs a data-sharing agreement, UAE hosting and verified reporters (for example UAE PASS).

**A report is kept only when the victim sends it, and only for 7 days.** Sending a report straight to the authority means it must wait somewhere until an officer opens it. The inbox keeps it only after the victim has seen everything that will be sent and pressed send, deletes it automatically after `HARIS_INBOX_RETENTION_DAYS` (7) whatever its status, and never stores the screenshots: they stay in the victim's own file. The victim follows the case with the reference number and a private token, stored on the server only as a hash.
- *Trade-off:* in the demo the database is a plain SQLite file readable only by the server's user, not encrypted, and UAE PASS is simulated. A launch needs the partner's own case system, encryption at rest, UAE hosting and the real UAE PASS sign-in.

**Translate, but keep the original.** Many victims in the UAE write Hindi, Urdu, English or Russian, and most officers read Arabic first. So the victim's words are translated into Arabic when the report arrives, and each officer note is translated into the victim's language, using the same AI model as the checks. The victim's original always travels with the translation, because it is the evidence and a machine translation can miss a nuance, and the dashboard flags the reporter's language so a supervisor can hand the case to an officer who speaks it.
- *Safety:* as in dictation correction, numbers, amounts, links and e-mails are swapped for tokens before the model sees the text and put back after. An answer that loses, adds or changes a token or a digit, or leaves words untranslated, gets one more try and is otherwise refused: the case is then marked "needs a translator", and nothing is lost.
- *Trade-off:* the text goes to the AI provider (outside the UAE in this demo); names in it are not removed, because the officer needs them. A launch uses a model hosted in the UAE.

**Children are guided by Haris, and their reports go to child-protection specialists.** The UAE already has a dedicated channel, the Ministry of Interior's Child Protection Centre (116111 and the Hemayati app), with people trained for a frightened child or a threat at home. Taking children's reports into Haris would mean holding children's data, which the UAE data law restricts, and the risk of a child uploading a private photo as evidence. So Haris does what it does well (checks, first steps, the report file) and then hands over.
- *Trade-off:* a child who cannot call does not get Haris's follow-up in "My reports". A partnership with the Child Protection Centre could add a direct, specialist-run channel later.

**Visitors report with their passport.** UAE PASS already lets visitors open an account with a passport or a GCC national ID, and Dubai Police's eCrime takes a passport number instead of an Emirates ID, so a visitor's path needs no new kind of identity, only different questions: where they are staying, when they leave, and how to reach them after they fly.
- *Trade-off:* the demo stores the nationality and the contact abroad but not the passport number; a launch takes the verified identity from UAE PASS.

**Triage by simple rules a supervisor can read.** The priority comes from the situation and a few words, not from a model: a threat to life or a child in an extortion, harassment or privacy case is critical; money lost in the last 24 hours is financial, because the first hour decides whether the bank can freeze it; older fraud and the other situations are medium; a message nobody fell for is an indicator. The officer sees why at the top of the case.

**WhatsApp alerts only for people who asked.** WhatsApp lets a business message only people who opted in, and a message outside 24 hours of the user's last one must use a template Meta has approved. So a user subscribes by sending «تنبيهات» (ALERTS, or the button in the guide and after a report) and leaves with «إيقاف» (STOP); approving a campaign sends the warning to every subscriber in their language, as a template when `WHATSAPP_ALERT_TEMPLATE` is set.
- *Trade-off:* this keeps subscribers' WhatsApp numbers, the one piece of personal data needed to send, until they leave. Reaching everyone in the UAE, not only subscribers, needs the authority's own channel (for example a telecom cell broadcast), which Haris can feed but not replace.

**Reports alone never block a number.** People can report an innocent number on purpose, and scammers spoof real numbers. So the radar only warns ("reported by N people", never "this is a scammer") and alerts the authority; the public warning and the block request need a person at the authority to approve them.

**Fix dictation instead of training a speech model.** Transcription is done by the browser's own speech service, which we cannot train. We improve it in two cheap steps: the user's dialect is passed to the service, and a correction pass (a glossary of fraud terms, plus Claude when enabled) fixes misheard words.
- *Why:* it works today in every modern browser, costs nothing without the AI, and keeps audio off our servers.
- *Trade-off:* it can't fix what the service didn't hear at all. A trainable server-side model (Azure Custom Speech, which supports ar-AE, ar-EG, ar-SA and more; Urdu only as ur-IN) is the plan for the police pilot, hosted in a UAE region and trained on anonymised data from the partner.
- *Safety:* numbers, links and e-mails are swapped for tokens before the AI sees the text and put back after; an answer that loses, repeats or adds a digit is thrown away. The user always sees the changes and chooses.

**One file per language.** Every sentence the user sees is in `frontend/locales/<lang>.json` (the chat) and `backend/haris/locales/<lang>.json` (results, advice, plans, the report, the radar). A reviewer corrects wording without touching code, a new language is one new file in each folder, and `tests/test_locales.py` fails if any language is missing a key, has a different number of steps, or loses a `{placeholder}`. The Hindi and Russian text was drafted with AI help and needs a native speaker's review before launch. Russian, the fifth language, was added in about an hour and a half: two language files, a list of Russian scam phrases, and the Cyrillic script in language detection.

**Plain JavaScript front end.** No framework and no build step, so judges can run it with one command, and the strict Content-Security-Policy (`script-src 'self'`) stays simple.

### What we left out

- **Reading screenshots without the AI.** With no API key, screenshots are attached to the report as evidence but not read. On-device text recognition would let the rules read them too.
- **The radar in production.** The demo radar runs on SQLite on the same server, counts one device as one person, and simulates the telecom block request. Production needs the partner's systems, verified reporters and a real block channel with the telecom providers.
- **Live link reputation.** Links are judged offline from their structure. Google Safe Browsing or a police blocklist would add a live check.
- **Training our own speech model.** Dictation accuracy depends on the browser's service. A trainable model (Azure Custom Speech or an open-source model hosted in the UAE) needs recordings with transcripts from the partner, so it is planned for the pilot.
- **Voice line for older people,** the family app for children and teenagers, and more languages (Malayalam, Tagalog, Bengali).
- **Real submission to the police.** The reports dashboard shows how sending, triage and follow-up would work, but it is a demo: the reports go to our own inbox, not to the police, and UAE PASS is simulated. Real submission needs an integration agreement and the partner's case system.

### What we would do differently with more time

- Build the test set from **real, anonymised scam messages** supplied by the partner authority, measured separately from the rules, instead of samples we wrote ourselves.
- Have the **Arabic dialect, Urdu, Hindi and Russian wording reviewed** by native speakers and by child-protection and victim-support specialists, especially the extortion guidance.
- Replace keyword weights with a **small fine-tuned classifier** trained on that data, keeping the rules as an explainable safety net.
- Store rules and advice text in a **reviewable content file** the partner authority can edit without a code change.

## 6. Privacy and safety summary

- Nothing users send is stored or logged, except two things the user chooses to send: a report to the campaign radar (the sender's numbers and links and the redacted text, kept 30 days, with no data about the reporter), and a report sent to the authority (the report fields without screenshots, kept 7 days). API responses carry `Cache-Control: no-store`.
- Reports sent to the authority in Hindi, Urdu, English or Russian are translated by the AI provider, with numbers, amounts, links and e-mails kept on the server as tokens. The translation is stored next to the original in the same case.
- WhatsApp alert subscribers: the WhatsApp number and language of people who sent «تنبيهات», kept until they send «إيقاف», readable only by the server's user. Fictional demo subscribers are never messaged.
- On the user's device the chat keeps only the reference numbers and status tokens of reports they sent, so they can follow them.
- The authority dashboards open only on the computer running Haris, or anywhere with the `HARIS_AUTHORITY_TOKEN` set. Behind a tunnel or proxy (requests carrying `X-Forwarded-For` or `CF-Connecting-IP`) the token is always required.
- Personal data is redacted from text before any AI call; link query strings are dropped.
- WhatsApp webhooks are accepted only when signed with the app secret. Message text is never logged; a risky message is kept in memory for 30 minutes only, so the user can still tap "Report to protect".
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
│   └── haris/                 the core engine (pure Python), including the WhatsApp channel
├── frontend/                   index.html, styles.css, app.js; reports.html and authority.html (the authority's demo dashboards)
├── data/samples/messages.json  labelled synthetic test messages
├── scripts/evaluate.py         accuracy on the samples
├── scripts/radar_demo.py       sends 10 reports of one campaign, for a live demo
├── scripts/alerts_demo.py      adds fictional WhatsApp alert subscribers (never messaged)
├── scripts/inbox_demo.py       fills the reports dashboard with 30 fictional reports
├── tests/                      unit and API tests
└── docs/
    ├── TECHNICAL.md            architecture, model choices, privacy design
    ├── poster/                 campaign poster (HTML source, QR, UAE map, rendered PNG)
    ├── video/                  journey video (Arabic and English) and an earlier narrated version
    ├── Haris-presentation.pptx     presentation (English)
    └── Haris-presentation-ar.pptx  presentation (Arabic)
```

## 8. Third-party software and ownership

The code in this repository was written for the hackathon by Mohamed Ibrahim, with Claude (Anthropic) used as an AI coding assistant; the idea, the product decisions and the review of every change are his. It uses these open-source packages under their licences: FastAPI (MIT), Uvicorn (BSD-3-Clause), Pydantic (MIT), and for tests pytest (MIT) and HTTPX (BSD-3-Clause). The optional AI layer calls the Anthropic Claude API or the Google Gemini API under each provider's terms. The official contact numbers come from public Abu Dhabi Police and Dubai Police announcements and should be confirmed by the partner authority before launch.

## Team

| Name | Role |
| --- | --- |
| Mohamed Ibrahim | Idea, product, design and development |

Built with Claude (Anthropic) as an AI coding assistant.
