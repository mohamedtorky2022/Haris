import pytest

from haris import radar
from haris.detector import analyze

SCAM = "عزيزي العميل، طردك محتجز بسبب عنوان غير مكتمل. ادفع 5 دراهم خلال 24 ساعة: https://emirates-post-ae.top/track أو اتصل 0501234567"
SAME_CAMPAIGN_OTHER_NUMBER = "عزيزي العميل، طردك محتجز بسبب عنوان غير مكتمل. ادفع 7 دراهم خلال 24 ساعة: https://parcel-uae.click/x أو اتصل 0559876543"


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_RADAR_DB", str(tmp_path / "radar.db"))
    monkeypatch.setenv("HARIS_RADAR_WARN", "3")
    monkeypatch.setenv("HARIS_RADAR_ESCALATE", "10")


def test_keys_include_sender_details_and_the_message_text():
    kinds = dict(radar.keys_of(SCAM))
    assert kinds["phone"] == "971501234567"
    assert kinds["domain"] == "emirates-post-ae.top"
    assert "template" in kinds


def test_same_text_from_another_number_is_the_same_campaign():
    assert radar.template_of(SCAM) == radar.template_of(SAME_CAMPAIGN_OTHER_NUMBER)


def test_status_climbs_with_distinct_people_only():
    radar.report(SCAM, "device-1", "ar")
    radar.report(SCAM, "device-1", "ar")  # the same device twice counts once
    assert radar.campaigns()[0]["status"] == "collecting"
    radar.report(SCAM, "device-2", "ar")
    radar.report(SAME_CAMPAIGN_OTHER_NUMBER, "device-3", "ar")
    c = radar.campaigns()[0]
    assert c["people"] == 3 and c["reports"] == 4
    assert {"kind": "phone", "value": "971559876543"} in c["identifiers"]


def test_lookalike_link_escalates_early_and_plain_messages_need_ten_people():
    for i in range(3):
        radar.report(SCAM, f"d{i}", "ar")
    assert radar.campaigns()[0]["status"] == "escalated"  # imitates Emirates Post
    plain = "مرحبا، فرصة عمل من المنزل براتب يومي ممتاز، تواصل معي على واتساب 0567778899 للتفاصيل"
    for i in range(9):
        radar.report(plain, f"p{i}", "ar")
    statuses = {c["category"]: c["status"] for c in radar.campaigns()}
    assert "warning" in statuses.values()
    radar.report(plain, "p9", "ar")
    assert [c["status"] for c in radar.campaigns()].count("escalated") == 2


def test_only_the_authority_confirms_and_then_everyone_is_warned():
    for i in range(10):
        radar.report(SCAM, f"d{i}", "ar")
    c = radar.campaigns()[0]
    assert radar.broadcasts() == []
    decision = radar.decide(c["id"], "confirmed")
    assert decision["simulated"] and {"kind": "phone", "value": "971501234567"} in decision["block_requests"]
    b = radar.broadcasts("en")[0]
    assert "Official warning" in b["title"] and "+971501234567" in b["body"]

    # A new message from the same number now comes back high risk with the official warning.
    text = "Hello, call me back on 0501234567 about your parcel"
    result = radar.annotate(analyze(text, "en", use_llm=False), text, "en")
    assert result["risk"] == "high" and result["radar"]["broadcast"]
    assert result["reasons"][0].startswith("The authority confirmed")


def test_dismissed_campaigns_show_nothing():
    for i in range(3):
        radar.report(SCAM, f"d{i}", "ar")
    radar.decide(radar.campaigns()[0]["id"], "dismissed")
    result = radar.annotate(analyze(SCAM, "ar", use_llm=False), SCAM, "ar")
    assert result["radar"]["message"] is None and result["radar"]["broadcast"] is None


def test_reporter_ids_and_card_numbers_are_not_stored(tmp_path):
    radar.report("Pay now with card 4111 1111 1111 1111 at https://bad-pay.top", "my-secret-device-id", "en")
    raw = (tmp_path / "radar.db").read_bytes()
    assert b"my-secret-device-id" not in raw and b"4111 1111" not in raw
