import json

from haris import llm, polish as polish_mod
from haris.polish import apply_glossary, mask, polish, unmask, word_changes


def test_glossary_fixes_common_mishearings():
    assert apply_glossary("وصلتني رسالة من ارا ماكس على واتس اب", "ar") == "وصلتني رسالة من أرامكس على واتساب"
    assert apply_glossary("طلبوا الأو تي بي", "ar") == "طلبوا الأو تي بي"  # glued to a word: left alone
    assert apply_glossary("they asked for the o t p on whats app", "en") == "they asked for the OTP on WhatsApp"
    assert apply_glossary("میں نے او ٹی پی دیا", "ur") == "میں نے OTP دیا"


def test_correct_text_is_left_alone():
    result = polish("وصلتني رسالة من أرامكس على واتساب", "ar")
    assert result["changes"] == []


def test_glossary_never_touches_numbers():
    text = "حولت 4500 درهم إلى اي بان AE070331234567890123456"
    out = polish(text, "ar")["text"]
    assert "4500" in out and "AE070331234567890123456" in out


def test_mask_and_unmask_round_trip():
    masked, kept = mask("call 050 123 4567 or a@b.com https://x.ae/p")
    assert "050" not in masked and "a@b.com" not in masked and "https" not in masked
    assert unmask(masked, kept) == "call 050 123 4567 or a@b.com https://x.ae/p"


def test_unmask_rejects_lost_repeated_or_new_numbers():
    masked, kept = mask("paid 300 on 12/5")
    assert unmask(masked.replace("[#2]", ""), kept) is None
    assert unmask(masked + " [#1]", kept) is None
    assert unmask(masked + " 7", kept) is None


def test_word_changes_ignore_punctuation():
    assert word_changes("ارسلو رابط", "ارسلو رابط.") == []
    assert word_changes("ارسلو رابط", "أرسلوا رابط") == [{"from": "ارسلو", "to": "أرسلوا"}]


def _fake_ai(monkeypatch, reply_text):
    seen = {}

    def fake_call(system, content, max_tokens, timeout):
        seen["content"] = content
        return json.dumps({"text": reply_text(content)})

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm, "_call", fake_call)
    return seen


def test_ai_fix_is_used_and_numbers_never_leave(monkeypatch):
    seen = _fake_ai(monkeypatch, lambda c: "اتصل بي واحد من البنك من الرقم [#1] وطلب الرمز.")
    result = polish("اتصل بي واحد من البنقس من الرقم 0501234567 وطلب الرمز", "ar", "ar-AE")
    assert "0501234567" not in seen["content"]
    assert result["engine"] == "rules+ai"
    assert result["text"] == "اتصل بي واحد من البنك من الرقم 0501234567 وطلب الرمز."
    assert {"from": "البنقس", "to": "البنك"} in result["changes"]


def test_ai_answer_that_changes_a_number_is_rejected(monkeypatch):
    _fake_ai(monkeypatch, lambda c: "حولت 9000 درهم")
    result = polish("حولت 4500 درهم", "ar")
    assert result["engine"] == "rules" and result["text"] == "حولت 4500 درهم"


def test_ai_answer_that_rewrites_too_much_is_rejected(monkeypatch):
    _fake_ai(monkeypatch, lambda c: "x")
    assert polish("وصلتني رسالة غريبة من رقم مجهول", "ar")["engine"] == "rules"


def test_dialect_name_reaches_the_prompt(monkeypatch):
    prompts = []
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(llm, "_call", lambda system, *a: prompts.append(system) or None)
    polish_mod.polish("ده كان واحد بيكلمني", "ar", "ar-EG")
    assert "Egyptian Arabic" in prompts[0]
