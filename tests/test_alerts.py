"""Official warnings on WhatsApp: opt-in, opt-out, delivery to subscribers when a campaign is approved."""

import pytest

from haris import alerts, radar
from haris import whatsapp as wa
from haris.text import SUPPORTED_LANGS

SCAM = "عزيزي العميل، طردك محتجز. ادفع 5 دراهم عبر https://emirates-post-ae.top/track أو اتصل 0501234567"


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_RADAR_DB", str(tmp_path / "radar.db"))
    for k in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    wa.reset()


def live(monkeypatch):
    """Switch WhatsApp on and record what would be sent."""
    for k, v in (("WHATSAPP_TOKEN", "t"), ("WHATSAPP_PHONE_NUMBER_ID", "1"), ("WHATSAPP_VERIFY_TOKEN", "v"),
                 ("WHATSAPP_APP_SECRET", "s")):
        monkeypatch.setenv(k, v)
    sent = []
    monkeypatch.setattr(wa, "send", lambda to, message: sent.append((to, message)) or True)
    return sent


def approved_campaign() -> int:
    for i in range(10):
        radar.report(SCAM, f"device-{i}", "ar")
    camp = radar.campaigns()[0]
    return radar.decide(camp["id"], "confirmed")["broadcast_id"]


def text_msg(body, sender="971500000001"):
    return {"id": "m", "from": sender, "type": "text", "text": body, "reply_id": ""}


def test_only_whole_message_commands():
    assert alerts.command("تنبيهات") == "subscribe" and alerts.command("  ALERTS! ") == "subscribe"
    assert alerts.command("إيقاف") == "stop" and alerts.command("Stop") == "stop" and alerts.command("रोकें") == "stop"
    assert alerts.command("stop the transfer now and pay 500 AED here http://x.top") is None
    assert alerts.command("") is None


def test_subscribe_and_stop_on_whatsapp():
    reply = wa.handle(text_msg("تنبيهات"))[0]
    assert reply["interactive"]["body"]["text"] == alerts.TEXT["ar"]["subscribed"]
    assert alerts.is_subscribed("971500000001")
    again = wa.handle(text_msg("تنبيهات"))[0]
    assert again["interactive"]["body"]["text"] == alerts.TEXT["ar"]["already"]
    wa.handle(text_msg("STOP"))
    assert not alerts.is_subscribed("971500000001") and alerts.counts()["total"] == 0


def test_alerts_button_from_the_guide_and_after_a_report():
    guide = wa.handle({"id": "g", "from": "971500000002", "type": "interactive", "text": "", "reply_id": "guide:en"})[0]
    ids = [b["reply"]["id"] for b in guide["interactive"]["action"]["buttons"]]
    assert "alerts:en" in ids
    wa.handle({"id": "a", "from": "971500000002", "type": "interactive", "text": "", "reply_id": "alerts:en"})
    assert alerts.counts()["by_lang"]["en"] == 1


def test_texts_fit_whatsapp():
    for lang in SUPPORTED_LANGS:
        t = alerts.TEXT[lang]
        assert len(wa.TEXT[lang]["buttons"]["alerts"]) <= 20
        assert all(len(t[k]) <= wa.BODY_LIMIT for k in ("subscribed", "already", "stopped", "not_subscribed"))
        assert len(wa.TEXT[lang]["welcome"]) <= wa.BODY_LIMIT


def test_without_whatsapp_the_delivery_is_simulated():
    alerts.subscribe("971500000003", "ar")
    alerts.add_demo_subscribers(100)
    out = alerts.deliver(approved_campaign())
    assert out["mode"] == "simulated" and out["total"] == 101 and out["simulated"] == 101 and out["sent"] == 0
    assert alerts.history()[0]["done"] == 1


def test_live_delivery_in_each_language_and_never_to_demo_ids(monkeypatch):
    sent = live(monkeypatch)
    alerts.subscribe("971500000004", "ar")
    alerts.subscribe("971500000005", "en")
    alerts.add_demo_subscribers(50)
    out = alerts.deliver(approved_campaign(), pace=0)
    assert out["mode"] == "text" and out["sent"] == 2 and out["simulated"] == 50
    assert {to for to, _ in sent} == {"971500000004", "971500000005"}
    bodies = {to: m["text"]["body"] for to, m in sent}
    assert "تحذير رسمي" in bodies["971500000004"] and "إيقاف" in bodies["971500000004"]
    assert "Official warning" in bodies["971500000005"] and "STOP" in bodies["971500000005"]
    assert "+971501234567" in bodies["971500000004"]


def test_template_outside_the_24_hour_window(monkeypatch):
    sent = live(monkeypatch)
    monkeypatch.setenv("WHATSAPP_ALERT_TEMPLATE", "haris_official_warning")
    alerts.subscribe("971500000006", "ur")
    alerts.deliver(approved_campaign(), pace=0)
    (_, message), = sent
    assert message["type"] == "template" and message["template"]["name"] == "haris_official_warning"
    assert message["template"]["language"]["code"] == "ar"  # Urdu template not approved: the first listed one
    assert len(message["template"]["components"][0]["parameters"]) == 2


def test_approval_on_the_dashboard_sends_the_alert(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app import main

    monkeypatch.setattr(main, "_hits", main.defaultdict(main.deque))
    client = TestClient(main.app)
    alerts.add_demo_subscribers(1000)
    for i in range(10):
        radar.report(SCAM, f"device-{i}", "ar")
    camp = client.get("/api/authority/campaigns").json()[0]
    r = client.post(f"/api/authority/campaigns/{camp['id']}", json={"status": "confirmed"}).json()
    assert r["whatsapp_alert"]["total"] == 1000 and r["whatsapp_alert"]["mode"] == "simulated"
    a = client.get("/api/authority/alerts").json()
    assert a["sends"][0]["simulated"] == 1000 and a["sends"][0]["done"] == 1
