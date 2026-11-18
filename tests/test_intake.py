import base64

import pytest

from haris import intake, llm
from haris.intake import decode_images, extract, rules_extract

PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 100).decode()


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_arabic_story_fills_every_required_field():
    r = extract("أمس الساعة 8 مساءً وصلتني رسالة من 0501234567، دخلت الرابط emirates-post-ae.top وأدخلت بيانات "
                "بطاقتي وخُصم 350 درهم. اتصلت بالبنك وأوقفت البطاقة.", [], "ar")
    f = r["fields"]
    assert f["incident_type"] == "money_sent"
    assert (f["amount"], f["currency"], f["payment_method"]) == ("350", "AED", "card")
    assert "أمس" in f["occurred_at"]
    assert f["steps_taken"] == ["اتصلت بالبنك", "أوقفت البطاقة"]
    assert "0501234567" in f["scammer_identifiers"] and "emirates-post-ae.top" in f["scammer_identifiers"]
    assert r["missing"] == []


def test_only_missing_fields_are_asked():
    r = extract("I paid 120 AED by card for a parcel fee", [], "en")
    assert r["fields"]["incident_type"] == "money_sent"
    assert r["missing"] == ["occurred_at", "steps_taken"]


def test_extortion_and_crypto_currency():
    f = extract("Someone is threatening to publish my photos unless I pay 2000 USDT", [], "en")["fields"]
    assert f["incident_type"] == "extortion"
    assert (f["amount"], f["currency"], f["payment_method"]) == ("2000", "USDT", "crypto")


def test_urdu_transfer_means_money_lost():
    r = extract("کل شام کال آئی، ویزا فیس 1500 درہم بینک ٹرانسفر کیے AE070331234567890123456", [], "ur")
    assert r["fields"]["incident_type"] == "money_sent"
    assert r["fields"]["payment_method_label"] == "بینک ٹرانسفر"
    assert r["fields"]["scammer_identifiers"]


def test_chosen_incident_type_wins():
    r = extract("they keep messaging me", [], "en", incident_type="account_hacked")
    assert r["fields"]["incident_type"] == "account_hacked"
    assert "occurred_at" in r["missing"]


def test_empty_story_asks_for_description():
    assert extract("", [], "ar")["missing"][0] == "description"


def test_decode_images_validates_type_size_and_count():
    assert len(decode_images([PNG])) == 1
    assert decode_images(["data:image/gif;base64,R0lGOD", "not a data url", "data:image/png;base64,***"]) == []
    assert len(decode_images([PNG] * 5)) == intake.MAX_IMAGES
    huge = "data:image/png;base64," + base64.b64encode(b"0" * (intake.MAX_IMAGE_BYTES + 1)).decode()
    assert decode_images([huge]) == []


def test_images_without_ai_are_received_but_not_read():
    r = extract("", [PNG], "en")
    assert r["images_received"] == 1 and r["images_read"] is False


def test_ai_fills_gaps_but_rules_keep_their_values(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    seen = {}

    def fake(text, images, lang):
        seen["text"], seen["images"] = text, images
        return {"incident_type": "money_sent", "occurred_at": "18 Nov 20:12", "amount": "999", "currency": "AED",
                "payment_method": "transfer", "scammer_identifiers": ["@fake_courier"], "summary": "Paid a fake fee."}

    monkeypatch.setattr(llm, "extract", fake)
    r = extract("I paid 350 AED by card, scammer called from 0501234567", [PNG], "en")
    f = r["fields"]
    assert f["amount"] == "350" and f["payment_method"] == "card"  # rules values kept
    assert f["occurred_at"] == "18 Nov 20:12"  # gap filled by the AI
    assert "@fake_courier" in f["scammer_identifiers"] and "0501234567" in f["scammer_identifiers"]
    assert r["engine"] == "rules+ai" and r["images_read"] is True
    assert "0501234567" not in seen["text"]  # the story reaches the AI redacted
    assert seen["images"] and seen["images"][0][0] == "image/png"


def test_llm_extract_cleans_output(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm, "_call", lambda *a, **k: 'x {"incident_type":"hacking","amount":"AED 1,200",'
                        '"payment_method":"paypal","scammer_identifiers":["0559876543",""],"summary":"s"}')
    out = llm.extract("story", [], "en")
    assert out["incident_type"] is None and out["payment_method"] is None
    assert out["amount"] == "1200"
    assert out["scammer_identifiers"] == ["0559876543"]


def test_new_incident_types_are_recognised():
    assert rules_extract("someone made a fake account in my name on Instagram", "en")["incident_type"] == "impersonation"
    assert rules_extract("زميلي يتنمر علي ويسبني في مجموعة الواتساب", "ar")["incident_type"] == "harassment"
    assert rules_extract("We paid the supplier invoice to new bank details from an e-mail", "en")["incident_type"] == "business_fraud"


def test_business_fraud_asks_for_money_fields():
    r = extract("We paid a supplier invoice to new bank details", [], "en")
    assert r["fields"]["incident_type"] == "business_fraud"
    assert "amount" in r["missing"] and "payment_method" in r["missing"]


def test_privacy_and_device_incidents_are_recognised():
    assert rules_extract("someone posted my photos without my permission on Snapchat", "en")["incident_type"] == "privacy_violation"
    assert rules_extract("أحدهم نشر صوري دون إذني في مجموعة", "ar")["incident_type"] == "privacy_violation"
    r = extract("My laptop files are encrypted and they want a ransom in bitcoin. I disconnected it", [], "en")
    assert r["fields"]["incident_type"] == "device_hacked"
    assert "Took the device offline" in r["fields"]["steps_taken"]


def test_threat_to_publish_stays_extortion():
    assert rules_extract("صوروني دون إذني ويهددني بنشر الفيديو إن لم أدفع", "ar")["incident_type"] == "extortion"
