"""WhatsApp channel: webhook security, reply building and WhatsApp's size limits."""

import hashlib
import hmac
import json

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
    assert wa.process(payload) == 1
    assert wa.process(payload) == 0  # Meta retried the same delivery
    assert sent[0][0] == "971501"


def test_process_limits_each_sender(monkeypatch):
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append(message) or True)
    for i in range(wa.PER_SENDER_LIMIT + 5):
        wa.process(webhook({"id": f"m{i}", "from": "971502", "type": "text", "text": {"body": "hi"}}))
    assert len(sent) == wa.PER_SENDER_LIMIT + 1
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
