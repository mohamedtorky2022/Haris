"""Translation between victim and authority: tokens keep numbers safe, the original always stays."""

import json
import re

import pytest

from haris import inbox, llm, translate


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    llm._CACHE.clear()


def fake_model(monkeypatch, answer):
    """answer(system, masked_text) -> the translation the 'model' returns."""
    calls = []

    def call(system, content, max_tokens, timeout):
        masked = re.search(r"<text>\n(.*)\n</text>", content, re.S).group(1)
        calls.append((system, masked))
        if '"lines"' in system:  # several short items: one answer each
            return json.dumps({"lines": [answer(system, x) for x in json.loads(masked)]}, ensure_ascii=False)
        return json.dumps({"text": answer(system, masked)}, ensure_ascii=False)

    monkeypatch.setattr(llm, "enabled", lambda: True)
    monkeypatch.setattr(llm, "model_name", lambda: "test-model")
    monkeypatch.setattr(llm, "_call", call)
    return calls


def test_numbers_and_links_never_reach_the_model_and_come_back_exact(monkeypatch):
    calls = fake_model(monkeypatch, lambda s, m: m.replace("नौकरी के नाम पर", "باسم وظيفة").replace("दिरहम लिए", "درهم أُخذت"))
    out = translate.translate("नौकरी के नाम पर 1,800 दिरहम लिए https://visa-fee.top", "hi", "ar")
    assert out["ok"] and "1,800" in out["text"] and "https://visa-fee.top" in out["text"]
    assert "1,800" not in calls[0][1] and "visa-fee" not in calls[0][1]
    assert "Arabic" in calls[0][0] and "Hindi" in calls[0][0]


def test_an_answer_that_changes_a_number_is_refused(monkeypatch):
    fake_model(monkeypatch, lambda s, m: "خُصم 9999 درهم")
    out = translate.translate("मुझसे 3400 दिरहम कटे", "hi", "ar")
    assert not out["ok"] and out["text"] == ""


def test_without_ai_nothing_is_translated(monkeypatch):
    monkeypatch.setattr(llm, "enabled", lambda: False)
    assert translate.translate("my card was charged", "en", "ar") == {"text": "", "ok": False, "engine": None}
    assert translate.translate("نص عربي", "ar", "ar")["ok"]


def test_hindi_report_reaches_the_officer_in_arabic_with_the_original(monkeypatch):
    fake_model(monkeypatch, lambda s, m: "\n".join(f"[ع] {line}" for line in m.split("\n")))
    r = inbox.submit({"incident_type": "money_sent", "occurred_at": "आज सुबह", "description": "निवेश ऐप ने पैसे लिए",
                      "payment_method": "बैंक ट्रांसफर", "steps_taken": ["बैंक को फ़ोन किया"]}, "hi", "dubai", True)
    d = inbox.detail(r["reference"])
    tr = d["fields"]["translation"]
    assert tr["ok"] and tr["from"] == "hi" and tr["description"] == "[ع] निवेश ऐप ने पैसे लिए"
    assert tr["occurred_at"].startswith("[ع]") and tr["payment_method"].startswith("[ع]") and len(tr["steps_taken"]) == 1
    assert d["fields"]["description"] == "निवेश ऐप ने पैसे लिए"  # the original is kept
    assert not d["needs_translator"]


def test_a_threat_is_caught_in_the_translation_too(monkeypatch):
    fake_model(monkeypatch, lambda s, m: "قال إنه سيقتلني إن لم أدفع" if "threat" not in m else m)
    r = inbox.submit({"incident_type": "extortion", "description": "वो बहुत डरा रहा है"}, "hi", "ajman", True)
    assert r["priority"] == "critical"


def test_officer_note_reaches_the_victim_in_their_language_and_the_reply_comes_back_in_arabic(monkeypatch):
    fake_model(monkeypatch, lambda s, m: ("[اردو] " if "Urdu" in s.split("into")[1][:12] else "[عربي] ") + m)
    r = inbox.submit({"incident_type": "account_hacked", "description": "میرا واٹس ایپ ہیک ہو گیا"}, "ur", "sharjah", False)
    ref, token = r["reference"], r["token"]
    inbox.act(ref, "request_info", "أرسل اسم الحساب المخترق")
    seen = inbox.status(ref, token)["events"][-1]
    assert seen["note"].startswith("[اردو]") and seen["original"] == "أرسل اسم الحساب المخترق"
    inbox.reply(ref, token, "میرا اکاؤنٹ")
    last = inbox.detail(ref)["events"][-1]
    assert last["note"] == "میرا اکاؤنٹ" and last["note_ar"].startswith("[عربي]")


def test_when_translation_fails_the_case_is_flagged(monkeypatch):
    monkeypatch.setattr(llm, "enabled", lambda: False)
    inbox.submit({"incident_type": "money_sent", "description": "my card was charged"}, "en", "dubai", True)
    inbox.submit({"incident_type": "money_sent", "description": "خُصم من بطاقتي"}, "ar", "dubai", True)
    q = inbox.queue()
    assert q["stats"]["needs_translator"] == 1 and q["stats"]["by_lang"]["en"] == 1 and q["stats"]["by_lang"]["ar"] == 1


def test_an_untranslated_english_word_gets_one_more_try(monkeypatch):
    answers = iter(["أخذوا المال تحت pretext الوظيفة", "أخذوا المال بحجة الوظيفة"])
    calls = fake_model(monkeypatch, lambda s, m: next(answers))
    out = translate.translate("नौकरी के नाम पर पैसे लिए", "hi", "ar")
    assert out["ok"] and out["text"] == "أخذوا المال بحجة الوظيفة" and len(calls) == 2
    assert "pretext" in calls[1][0]


def test_names_in_latin_letters_are_fine(monkeypatch):
    fake_model(monkeypatch, lambda s, m: "اخترقوا حسابي على Instagram")
    assert translate.translate("मेरा Instagram अकाउंट हैक हो गया", "hi", "ar")["ok"]


def test_short_items_come_back_one_for_one(monkeypatch):
    fake_model(monkeypatch, lambda s, m: {"आज सुबह": "اليوم صباحاً", "क्रिप्टो (USDT)": "عملات رقمية (USDT)"}[m])
    out = translate.translate_lines(["आज सुबह", "क्रिप्टो (USDT)"], "hi", "ar")
    assert out["ok"] and out["lines"] == ["اليوم صباحاً", "عملات رقمية (USDT)"]


def test_merged_items_are_refused(monkeypatch):
    monkeypatch.setattr(llm, "enabled", lambda: True)
    monkeypatch.setattr(llm, "_call", lambda *a: json.dumps({"lines": ["اليوم صباحاً العملات المشفرة (USDT)"]}, ensure_ascii=False))
    assert not translate.translate_lines(["आज सुबह", "क्रिप्टो (USDT)"], "hi", "ar")["ok"]


def test_an_invented_token_gets_one_more_try(monkeypatch):
    answers = iter(["يرسل لي شتائم كل يوم [#1]", "يرسل لي شتائم كل يوم"])
    calls = fake_model(monkeypatch, lambda s, m: next(answers))
    out = translate.translate("کوئی مجھے روز گالیاں بھیج رہا ہے", "ur", "ar")
    assert out["ok"] and out["text"] == "يرسل لي شتائم كل يوم" and "none" in calls[1][0]


def test_a_visitors_nationality_is_translated_too(monkeypatch):
    fake_model(monkeypatch, lambda s, m: {"British": "بريطاني"}.get(m, "[ع] " + m))
    r = inbox.submit({"incident_type": "money_sent", "description": "my card was charged"}, "en", "dubai", True,
                     visitor={"nationality": "British", "departure": "within_3_days"})
    assert inbox.detail(r["reference"])["fields"]["translation"]["nationality"] == "بريطاني"
