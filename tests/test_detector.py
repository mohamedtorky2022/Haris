import json
from pathlib import Path

import pytest

from haris import llm
from haris.detector import analyze
from haris.text import detect_language, normalize

SAMPLES = json.loads((Path(__file__).resolve().parents[1] / "data" / "samples" / "messages.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.mark.parametrize("sample", [s for s in SAMPLES if s["label"] == "scam"], ids=lambda s: s["id"])
def test_scams_are_flagged(sample):
    assert analyze(sample["text"])["risk"] in ("medium", "high")


@pytest.mark.parametrize("sample", [s for s in SAMPLES if s["label"] == "legit"], ids=lambda s: s["id"])
def test_legit_messages_are_not_flagged(sample):
    assert analyze(sample["text"])["risk"] == "low"


def test_language_detection():
    assert detect_language("مرحبا بك") == "ar"
    assert detect_language("آپ کا پارسل رکا ہوا ہے") == "ur"
    assert detect_language("Hello there") == "en"


def test_reply_language_follows_message_or_request():
    assert analyze("Your parcel is held, pay AED 5 now")["language"] == "en"
    assert analyze("Your parcel is held, pay AED 5 now", lang="ar")["language"] == "ar"


def test_small_amount_at_end_of_sentence():
    assert "small_amount" in analyze("Pay the fee of AED 7.50.", lang="en")["signals"]
    assert "small_amount" in analyze("ادفع 5 دراهم.", lang="ar")["signals"]
    assert "small_amount" not in analyze("Your rent of AED 7500 is due", lang="en")["signals"]


def test_arabic_spelling_variants_match():
    assert normalize("أرسل الرمز") == normalize("ارسل الرمز")


def test_low_risk_never_claims_safe():
    r = analyze("See you at 8 tonight", lang="en")
    assert r["risk"] == "low"
    assert "not mean" in r["summary"]
    assert r["category"] == "unknown"


def test_personal_data_counted_as_redacted():
    r = analyze("My card 4111 1111 1111 1111 was charged, they asked for the OTP, send it now")
    assert r["redacted"].get("CARD") == 1


def test_ai_opinion_can_only_raise_risk(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm, "assess", lambda *a, **k: {"risk": "high", "category": "unknown", "reasons": ["AI reason"], "advice": []})
    r = analyze("Hello, how are you?", lang="en")
    assert r["risk"] == "high"
    assert r["engine"] == "rules+ai"
    assert "AI reason" in r["reasons"]

    monkeypatch.setattr(llm, "assess", lambda *a, **k: {"risk": "low", "category": "unknown", "reasons": [], "advice": []})
    r = analyze("I have your videos. Pay 2000 USDT or I will send them to your family", lang="en")
    assert r["risk"] == "high"


def test_ai_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm, "assess", lambda *a, **k: None)
    r = analyze("Congratulations! You won. Pay AED 25 fee to claim your prize", lang="en")
    assert r["engine"] == "rules"
    assert r["risk"] == "high"


def test_llm_sees_redacted_text_only(monkeypatch):
    seen = {}
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    def fake(text, codes, links, lang):
        seen["text"], seen["links"] = text, links
        return None

    monkeypatch.setattr(llm, "assess", fake)
    analyze("Call 0501234567, card 4111 1111 1111 1111, pay at https://x.xyz/p?id=784199012345671", lang="en")
    assert "0501234567" not in seen["text"]
    assert "4111" not in seen["text"]
    assert seen["links"] == ["x.xyz/p"]


def test_llm_response_parsing():
    parsed = llm.parse('Here: {"risk":"medium","category":"job_scam","reasons":["a","b","c","d"],"advice":["x"]}')
    assert parsed["risk"] == "medium"
    assert len(parsed["reasons"]) == 3
    assert llm.parse('{"risk":"definitely safe"}') is None
    assert llm.parse("no json") is None


def test_romance_scam_needs_affection_and_a_money_request():
    r = analyze("My love, we met online and I need money for my flight ticket. Please send me 2000 dollars", use_llm=False)
    assert r["risk"] == "high" and r["category"] == "romance_scam"
    assert analyze("Hi darling, can you pay for the groceries on the way home?", use_llm=False)["risk"] == "low"
    assert analyze("حبيبي أرسل لي صورة الفاتورة لما توصل البيت", use_llm=False)["risk"] == "low"


def test_recovery_scam_is_flagged():
    r = analyze("نستطيع استرداد أموالك المسروقة خلال أسبوع. ادفع رسوم فتح الملف 900 درهم", use_llm=False)
    assert r["risk"] == "high" and r["category"] == "recovery_scam"


@pytest.mark.parametrize("text, category", [
    ("شقة في المرسى. المالك مسافر، حوّل عربون لحجز الشقة 1000 درهم قبل المعاينة", "shopping_scam"),
    ("iPhone 16 Pro 80% off! Clearance sale, bank transfer only, no cash on delivery", "shopping_scam"),
    ("تبرعك ينقذ حياة. حول على حسابي الشخصي رقم الحساب AE070331234567890123456", "charity_scam"),
    ("Golden visa guaranteed in 48 hours, no requirements. Pay the processing fee of AED 3500", "visa_scam"),
])
def test_shopping_charity_and_visa_scams(text, category):
    r = analyze(text, use_llm=False)
    assert r["risk"] == "high" and r["category"] == category


def test_paying_cash_on_delivery_is_not_a_warning():
    assert analyze("Your order has shipped. Pay cash on delivery.", use_llm=False)["risk"] == "low"


def test_hindi_is_detected_and_scored():
    from haris.text import detect_language
    assert detect_language("आपका पार्सल रुका है") == "hi"
    r = analyze("आपका बैंक खाता बंद कर दिया जाएगा। तुरंत अपना ओटीपी कोड भेजें।", use_llm=False)
    assert r["language"] == "hi" and r["risk"] == "high"
    assert r["risk_label"] == "धोखाधड़ी का बड़ा खतरा"
    assert analyze("आपका OTP 482913 है। इसे किसी के साथ शेयर न करें।", use_llm=False)["risk"] == "low"
