"""WhatsApp channel: webhook security, reply building and WhatsApp's size limits."""

import hashlib
import hmac
import json
import re

import pytest

from haris import whatsapp as wa
from haris.playbooks import list_playbooks
from haris.text import SUPPORTED_LANGS

SCAM_AR = ("عزيزي العميل، تم إيقاف بطاقتك. حدّث بياناتك فوراً عبر الرابط "
           "http://adcb-secure.top/verify وأرسل رمز التحقق")
LEGIT_EN = "Hi mom, dinner at 8?"


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_RADAR_DB", str(tmp_path / "radar.db"))
    monkeypatch.setenv("WHATSAPP_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123456")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-me")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "app-secret")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    wa.reset()
    yield
    wa.reset()


def text_msg(body, mid="wamid.1", sender="971500000001"):
    return {"id": mid, "from": sender, "type": "text", "text": body, "reply_id": ""}


def reply_msg(rid, sender="971500000001"):
    return {"id": "wamid.r", "from": sender, "type": "interactive", "text": "", "reply_id": rid}


def buttons(message):
    return [b["reply"] for b in message["interactive"]["action"]["buttons"]]


def webhook(*messages):
    return {"object": "whatsapp_business_account", "entry": [{"changes": [{"value": {"messages": list(messages)}}]}]}


# --- Security ---------------------------------------------------------------

def test_signature_is_required_and_checked():
    body = b'{"entry": []}'
    good = "sha256=" + hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()
    assert wa.valid_signature(body, good)
    assert not wa.valid_signature(body, "sha256=" + "0" * 64)
    assert not wa.valid_signature(body, None)
    assert not wa.valid_signature(body + b" ", good)


def test_unsigned_calls_refused_when_secret_missing(monkeypatch):
    monkeypatch.delenv("WHATSAPP_APP_SECRET")
    body = b"{}"
    assert not wa.valid_signature(body, "sha256=" + hmac.new(b"", body, hashlib.sha256).hexdigest())
    assert not wa.enabled()


def test_verify_subscription():
    assert wa.verify_subscription("subscribe", "verify-me", "42") == "42"
    assert wa.verify_subscription("subscribe", "wrong", "42") is None
    assert wa.verify_subscription("unsubscribe", "verify-me", "42") is None


# --- Reading webhooks -------------------------------------------------------

def test_incoming_reads_text_and_button_replies_and_ignores_statuses():
    payload = webhook(
        {"id": "a", "from": "971", "type": "text", "text": {"body": "hello"}},
        {"id": "b", "from": "971", "type": "interactive",
         "interactive": {"type": "button_reply", "button_reply": {"id": "guide:en", "title": "x"}}},
        {"id": "c", "from": "971", "type": "interactive",
         "interactive": {"type": "list_reply", "list_reply": {"id": "pb:ar:money_sent", "title": "x"}}},
    )
    payload["entry"][0]["changes"].append({"value": {"statuses": [{"id": "a", "status": "read"}]}})
    found = wa.incoming(payload)
    assert [m["id"] for m in found] == ["a", "b", "c"]
    assert found[0]["text"] == "hello"
    assert found[1]["reply_id"] == "guide:en" and found[2]["reply_id"] == "pb:ar:money_sent"


def test_greetings():
    for g in ["مرحباً حارس", "السلام عليكم", "Hi Haris!", "hello", "नमस्ते", ""]:
        assert wa.is_greeting(g), g
    assert not wa.is_greeting(SCAM_AR)


# --- Replies ----------------------------------------------------------------

def test_greeting_opens_the_menu():
    [m] = wa.handle(text_msg("مرحباً حارس"))
    assert [b["id"] for b in buttons(m)] == ["check:ar", "scammed:ar", "guide:ar"]


def test_scam_gets_high_risk_and_a_report_button():
    [m] = wa.handle(text_msg(SCAM_AR))
    body = m["interactive"]["body"]["text"]
    assert body.startswith("🔴") and len(body) <= wa.BODY_LIMIT
    assert buttons(m)[0]["id"].startswith("report:ar:")


def test_ordinary_message_gets_no_report_button():
    [m] = wa.handle(text_msg(LEGIT_EN))
    assert m["interactive"]["body"]["text"].startswith("⚪")
    assert not any(b["id"].startswith("report:") for b in buttons(m))


def test_report_button_sends_to_radar_once():
    [m] = wa.handle(text_msg(SCAM_AR))
    rid = buttons(m)[0]["id"]
    [thanks] = wa.handle(reply_msg(rid))
    assert thanks["interactive"]["body"]["text"].startswith(wa.TEXT["ar"]["reported"][:10])
    [again] = wa.handle(reply_msg(rid))  # the token is used up
    assert again["interactive"]["body"]["text"] == wa.TEXT["ar"]["report_expired"]


def test_reports_from_three_people_show_the_warning():
    for i in range(3):
        [m] = wa.handle(text_msg(SCAM_AR, sender=f"97150000000{i}"))
        wa.handle(reply_msg(buttons(m)[0]["id"], sender=f"97150000000{i}"))
    [m] = wa.handle(text_msg(SCAM_AR, sender="971509999999"))
    assert "👥" in m["interactive"]["body"]["text"]


def test_scammed_menu_lists_every_situation():
    for lang in SUPPORTED_LANGS:
        [m] = wa.handle(reply_msg(f"scammed:{lang}"))
        rows = m["interactive"]["action"]["sections"][0]["rows"]
        assert len(rows) == len(list_playbooks(lang)) <= 10
        assert all(len(r["title"]) <= 24 and len(r["description"]) <= 72 for r in rows)


def test_every_playbook_fits_whatsapp():
    for lang in SUPPORTED_LANGS:
        for p in list_playbooks(lang):
            out = wa.handle(reply_msg(f"pb:{lang}:{p['id']}"))
            assert out and all(len(json.dumps(m, ensure_ascii=False)) < 6000 for m in out)
            for m in out:
                if m["type"] == "text":
                    assert len(m["text"]["body"]) <= 4096
                else:
                    assert len(m["interactive"]["body"]["text"]) <= wa.BODY_LIMIT


def test_labels_fit_whatsapp_limits():
    for lang in SUPPORTED_LANGS:
        t = wa.TEXT[lang]
        assert all(len(v) <= 20 for v in t["buttons"].values()), lang
        assert len(t["footer"]) <= 60 and len(t["list_button"]) <= 20 and len(t["list_section"]) <= 24
        assert set(t["playbooks"]) == {p["id"] for p in list_playbooks(lang)}


def test_images_get_a_polite_answer():
    [m] = wa.handle({"id": "i", "from": "971", "type": "image", "text": "", "reply_id": ""})
    assert "واتساب" in m["interactive"]["body"]["text"]


def test_unknown_button_falls_back_to_the_menu():
    [m] = wa.handle(reply_msg("nonsense"))
    assert buttons(m)[0]["id"] == "check:ar"


# --- Processing a webhook ---------------------------------------------------

def test_process_replies_once_per_message(monkeypatch):
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append((to, message)) or True)
    payload = webhook({"id": "m1", "from": "971501", "type": "text", "text": {"body": "hello"}})
    assert wa.process(payload) == 3  # the welcome menu, Haris's contact card, the alerts notice
    assert wa.process(payload) == 0  # Meta retried the same delivery
    assert sent[0][0] == "971501"
    assert sent[1][1]["type"] == "contacts"
    assert sent[2][1]["text"]["body"] == wa.alerts.TEXT["en"]["auto_notice"]


def test_contact_card_is_sent_once_with_the_first_welcome(monkeypatch):
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append(message) or True)
    wa.process(webhook({"id": "c1", "from": "971503", "type": "text", "text": {"body": "مرحباً حارس"}}))
    wa.process(webhook({"id": "c2", "from": "971503", "type": "text", "text": {"body": "مرحبا"}}))
    cards = [m for m in sent if m["type"] == "contacts"]
    assert len(cards) == 1 and sent[1] is cards[0]
    card = cards[0]["contacts"][0]
    assert card["name"]["first_name"] == "حارس"
    assert card["phones"][0]["wa_id"] == "971503123535"
    assert "971503" not in wa._carded.items  # only a hash of the sender is kept


def test_process_limits_each_sender(monkeypatch):
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append(message) or True)
    for i in range(wa.PER_SENDER_LIMIT + 5):
        wa.process(webhook({"id": f"m{i}", "from": "971502", "type": "text", "text": {"body": "hi"}}))
    assert len(sent) == wa.PER_SENDER_LIMIT + 3  # the first welcome also carries the contact card and the alerts notice
    assert sent[-1]["text"]["body"] == wa.TEXT["en"]["too_many"]


# --- HTTP routes ------------------------------------------------------------

def test_webhook_routes(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    ok = client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "verify-me",
                                                 "hub.challenge": "1158201444"})
    assert ok.status_code == 200 and ok.text == "1158201444"
    assert client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "no",
                                                   "hub.challenge": "1"}).status_code == 403

    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append(message) or True)
    body = json.dumps(webhook({"id": "h1", "from": "971503", "type": "text", "text": {"body": SCAM_AR}})).encode()
    assert client.post("/webhook/whatsapp", content=body,
                       headers={"x-hub-signature-256": "sha256=bad"}).status_code == 401
    sig = "sha256=" + hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()
    r = client.post("/webhook/whatsapp", content=body, headers={"x-hub-signature-256": sig,
                                                                "content-type": "application/json"})
    assert r.status_code == 200 and r.json() == {"received": True}
    assert sent and sent[0]["interactive"]["body"]["text"].startswith("🔴")
    assert client.get("/api/health").json()["whatsapp_enabled"] is True


# --- Filing a report on WhatsApp ----------------------------------------------

def test_filing_a_report_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    sender = "971500000009"
    [m] = wa.handle(reply_msg("pb:ar:money_sent", sender))
    assert "file:ar" in [b["id"] for b in buttons(m)]
    [m] = wa.handle(reply_msg("file:ar", sender))
    assert m["interactive"]["body"]["text"] == wa.TEXT["ar"]["file"]["file_ask"]
    story = "اليوم حوّلت 2500 درهم عبر تحويل بنكي لرقم 0501234567 بعد رسالة تقول إن حسابي موقوف"
    [m] = wa.handle(text_msg(story, sender=sender))
    rows = m["interactive"]["action"]["sections"][0]["rows"]
    assert len(rows) == 7 and rows[1]["id"] == "em:ar:dubai"
    [m] = wa.handle(reply_msg("em:ar:dubai", sender))
    body = m["interactive"]["body"]["text"]
    assert "2500" in body and "دبي" in body and "+971500000009" in body
    assert [b["id"] for b in buttons(m)] == ["send:ar", "edit:ar", "cancel:ar"]
    [m] = wa.handle(reply_msg("send:ar", sender))
    text = m["interactive"]["body"]["text"]
    ref = re.search(r"HRS-\d{8}-[0-9A-F]{6}", text).group(0)
    from haris import inbox
    case = inbox.detail(ref)
    assert case and case["emirate"] == "dubai"
    # nothing left in memory, and a second "send" does not file twice
    [m] = wa.handle(reply_msg("send:ar", sender))
    assert m["interactive"]["body"]["text"] == wa.TEXT["ar"]["file"]["file_expired"]


def test_filing_can_be_cancelled_and_nothing_is_saved(monkeypatch, tmp_path):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    sender = "971500000010"
    wa.handle(reply_msg("file:en", sender))
    wa.handle(text_msg("Someone took 300 AED from my card", sender=sender))
    [m] = wa.handle(reply_msg("cancel:en", sender))
    assert m["interactive"]["body"]["text"] == wa.TEXT["en"]["file"]["file_cancelled"]
    assert not (tmp_path / "inbox.db").exists() or not __import__("haris").inbox.queue().get("cases")


def test_typing_report_starts_filing():
    [m] = wa.handle(text_msg("بلاغ", sender="971500000011"))
    assert m["interactive"]["body"]["text"] == wa.TEXT["ar"]["file"]["file_ask"]


def test_voice_note_and_screenshot_in_a_report(monkeypatch, tmp_path):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    monkeypatch.setattr(wa, "download_media", lambda mid: (b"bytes", "image/jpeg" if mid == "img" else "audio/ogg; codecs=opus"))
    monkeypatch.setattr(wa.llm, "transcribe", lambda data, mime: "أمس دفعت 900 درهم ببطاقتي لموقع توصيل مزيف")
    sender = "971500000012"
    wa.handle(reply_msg("file:ar", sender))
    [m] = wa.handle({"id": "i1", "from": sender, "type": "image", "media_id": "img", "mime": "image/jpeg", "text": "", "reply_id": ""})
    assert "(1)" in m["text"]["body"]
    out = wa.handle({"id": "a1", "from": sender, "type": "audio", "media_id": "aud", "mime": "audio/ogg", "text": "", "reply_id": ""})
    assert "900" in out[0]["text"]["body"]  # the transcript is shown back
    assert out[1]["interactive"]["type"] == "list"  # then the emirate list
    [m] = wa.handle(reply_msg("em:ar:sharjah", sender))
    body = m["interactive"]["body"]["text"]
    assert "900" in body and wa.TEXT["ar"]["file"]["labels"]["images"] in body
    [m] = wa.handle(reply_msg("send:ar", sender))
    ref = re.search(r"HRS-\d{8}-[0-9A-F]{6}", m["interactive"]["body"]["text"]).group(0)
    from haris import inbox
    assert inbox.detail(ref)["fields"]["evidence_count"] == 1
    assert inbox.whatsapp_of(ref) == sender


def test_authority_actions_reach_the_victim_and_the_answer_comes_back(monkeypatch, tmp_path):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append((to, message)) or True)
    monkeypatch.setattr(wa, "enabled", lambda: True)
    from haris import inbox
    sender = "971500000013"
    case = inbox.submit({"incident_type": "account_hacked", "description": "اختُرق حسابي"}, "ar", "dubai", False)
    inbox.link_whatsapp(case["reference"], sender)
    inbox.act(case["reference"], "receive")
    inbox.act(case["reference"], "request_info", "متى لاحظت الاختراق؟")
    assert sent[0][0] == sender and case["reference"] in sent[0][1]["text"]["body"]
    assert "متى لاحظت الاختراق؟" in sent[1][1]["text"]["body"]
    [m] = wa.handle(text_msg("صباح أمس الساعة 9", sender=sender))
    assert case["reference"] in m["interactive"]["body"]["text"]
    detail = inbox.detail(case["reference"])
    assert detail["status"] == "received" and detail["events"][-1]["note"] == "صباح أمس الساعة 9"
    inbox.act(case["reference"], "close", "تم استرداد الحساب")
    assert "تم استرداد الحساب" in sent[-1][1]["text"]["body"]
    # with no open question, the next message is checked as usual
    [m] = wa.handle(text_msg("hello there friend how are you", sender=sender))
    assert case["reference"] not in m["interactive"]["body"]["text"]


def test_everyone_who_writes_gets_the_alerts_and_stop_is_remembered(monkeypatch):
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append(message) or True)
    wa.process(webhook({"id": "s1", "from": "971504", "type": "text", "text": {"body": "هل هذه رسالة احتيال؟ حسابك موقوف"}}))
    assert wa.alerts.is_subscribed("971504")
    assert sent[-1]["text"]["body"] == wa.alerts.TEXT["ar"]["auto_notice"]
    wa.process(webhook({"id": "s2", "from": "971504", "type": "text", "text": {"body": "إيقاف"}}))
    assert not wa.alerts.is_subscribed("971504")
    wa.process(webhook({"id": "s3", "from": "971504", "type": "text", "text": {"body": "مرحبا"}}))
    assert not wa.alerts.is_subscribed("971504")  # not added back after STOP
    wa.process(webhook({"id": "s4", "from": "971504", "type": "text", "text": {"body": "تنبيهات"}}))
    assert wa.alerts.is_subscribed("971504")


def test_a_bad_paste_in_the_host_settings_is_cleaned(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", 'EAAtoken123\nWHATSAPP_PHONE_NUMBER_ID=999')
    monkeypatch.setenv("WHATSAPP_APP_SECRET", ' "abc" ')
    s = wa.settings()
    assert s["token"] == "EAAtoken123" and s["app_secret"] == "abc"
