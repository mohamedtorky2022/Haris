"""The AI layer: choosing Claude or Gemini, Gemini's request format, and teaching by example."""

import io
import json

import pytest

from haris import examples, llm


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "HARIS_AI_PROVIDER", "GEMINI_MODEL"):
        monkeypatch.delenv(k, raising=False)


def test_provider_follows_the_keys(monkeypatch):
    assert llm.provider() is None and not llm.enabled()
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert llm.provider() == "gemini" and llm.model_name() == llm.GEMINI_DEFAULT_MODEL
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert llm.provider() == "anthropic"
    monkeypatch.setenv("HARIS_AI_PROVIDER", "gemini")
    assert llm.provider() == "gemini"


def test_gemini_request_and_reply(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-key")
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.header_items())
        seen["body"] = json.loads(request.data)
        reply = {"candidates": [{"content": {"parts": [{"text": "thinking", "thought": True},
                                                       {"text": '{"risk":"high","category":"otp_theft","reasons":["r"],"advice":[]}'}]}}]}
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    out = llm.assess("Send me the code [PHONE]", ["otp_request"], [], "en")
    assert out["risk"] == "high" and out["category"] == "otp_theft"
    assert "gemini-3.5-flash-lite:generateContent" in seen["url"]
    assert "secret-key" not in seen["url"]  # the key goes in a header, never the URL
    assert seen["headers"]["X-goog-api-key"] == "secret-key"
    assert seen["body"]["systemInstruction"]["parts"][0]["text"].startswith("You are the fraud-analysis")
    assert "<examples>" in seen["body"]["contents"][0]["parts"][0]["text"]


def test_gemini_parts_carry_screenshots():
    parts = llm.gemini_parts([{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAA"}},
                              {"type": "text", "text": "story"}])
    assert parts == [{"inline_data": {"mime_type": "image/png", "data": "AAA"}}, {"text": "story"}]


def test_gemini_failure_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")

    def boom(*a, **k):
        raise llm.urllib.error.URLError("offline")

    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    assert llm.assess("text", [], [], "ar") is None


def test_similar_examples_never_include_the_message_itself():
    sample = json.loads(examples.SAMPLES.read_text(encoding="utf-8"))[0]
    from haris.redact import redact
    red = redact(sample["text"]).text
    picked = examples.similar(red)
    assert picked and all(e["key"] != " ".join(red.split()).lower() for e in picked)
    assert all(e["text"] != red for e in picked)
    assert {e["label"] for e in picked} == {"scam", "legit"}


def test_teaching_saves_a_redacted_example(tmp_path, monkeypatch):
    monkeypatch.setattr(examples, "TRAINING", tmp_path / "examples.jsonl")
    entry = examples.add("Your card 4111 1111 1111 1111 is blocked, call 0501234567", "scam", "bank_impersonation", "asks to call")
    saved = json.loads((tmp_path / "examples.jsonl").read_text(encoding="utf-8"))
    assert saved == entry
    assert "4111" not in entry["text"] and "0501234567" not in entry["text"]
    assert any("bank_impersonation" == e.get("category") for e in examples.load())
    with pytest.raises(ValueError):
        examples.add("x", "maybe")
