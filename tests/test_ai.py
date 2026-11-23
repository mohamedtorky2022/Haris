"""The AI layer: choosing Claude or Gemini, Gemini's request format, and teaching by example."""

import io
import json

import pytest

from haris import examples, llm


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "HARIS_AI_PROVIDER", "GEMINI_MODEL"):
        monkeypatch.delenv(k, raising=False)
    llm._CACHE.clear()
    monkeypatch.setattr(llm, "_cooldown_until", 0.0)


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


def test_slow_reply_falls_back_instead_of_crashing(monkeypatch):
    import socket
    for provider, key in (("gemini", "GEMINI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")):
        monkeypatch.setenv(key, "k")
        monkeypatch.setenv("HARIS_AI_PROVIDER", provider)

        def slow(*a, **k):
            raise socket.timeout("The read operation timed out")

        monkeypatch.setattr(llm.urllib.request, "urlopen", slow)
        assert llm.assess("text", [], [], "en") is None


def _gemini_reply(text):
    return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode())


def test_same_message_is_answered_from_memory(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    calls = []
    monkeypatch.setattr(llm.urllib.request, "urlopen",
                        lambda req, timeout: calls.append(1) or _gemini_reply('{"risk":"high","category":"unknown"}'))
    assert llm.assess("same campaign text", [], [], "en")["risk"] == "high"
    assert llm.assess("same campaign text", [], [], "en")["risk"] == "high"
    assert len(calls) == 1


def test_rate_limit_pauses_calls(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    calls = []
    body = json.dumps({"error": {"code": 429, "details": [{"retryDelay": "37s"}]}}).encode()

    def limited(req, timeout):
        calls.append(1)
        raise llm.urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, io.BytesIO(body))

    monkeypatch.setattr(llm.urllib.request, "urlopen", limited)
    assert llm.assess("first", [], [], "en") is None
    assert llm.assess("second", [], [], "en") is None  # no call while cooling down
    assert len(calls) == 1
    assert 30 < llm._cooldown_until - llm.time.monotonic() <= 37


# --- A second model when the first one is paused -------------------------------------------------

class _Answer:
    def __init__(self, text):
        import json as _json
        self._body = _json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()

    def read(self, *_):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _too_many(url):
    import io
    import urllib.error
    return urllib.error.HTTPError(url, 429, "Too Many Requests", {},
                                  io.BytesIO(b'{"error":{"details":[{"retryDelay":"20s"}]}}'))


def _gemini_env(monkeypatch, fallback):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("HARIS_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_MODEL", "main-model")
    if fallback:
        monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "spare-model")
    else:
        monkeypatch.delenv("GEMINI_FALLBACK_MODEL", raising=False)
    monkeypatch.setattr(llm, "_cooldown_until", 0.0)
    monkeypatch.setattr(llm, "_fallback_until", 0.0)
    llm._CACHE.clear()


def test_the_fallback_model_answers_while_the_main_one_is_paused(monkeypatch):
    _gemini_env(monkeypatch, fallback=True)
    asked = []

    def urlopen(req, timeout=None):
        asked.append(req.full_url)
        if "main-model" in req.full_url:
            raise _too_many(req.full_url)
        return _Answer("from the spare")

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    assert llm._call("sys", "first", 50, 5) == "from the spare"
    assert llm._cooldown_until > llm.time.monotonic()        # the main model is paused
    assert not llm._cooling_down()                            # but Haris can still use the AI
    assert llm._call("sys", "second", 50, 5) == "from the spare"
    assert sum("main-model" in u for u in asked) == 1         # the paused model is not asked again


def test_without_a_fallback_nothing_changes(monkeypatch):
    _gemini_env(monkeypatch, fallback=False)
    monkeypatch.setattr(llm.urllib.request, "urlopen", lambda req, timeout=None: (_ for _ in ()).throw(_too_many(req.full_url)))
    assert llm._call("sys", "x", 50, 5) is None
    assert llm._cooling_down()                                # rules only, as before


def test_both_models_paused_means_rules_only(monkeypatch):
    _gemini_env(monkeypatch, fallback=True)
    monkeypatch.setattr(llm.urllib.request, "urlopen", lambda req, timeout=None: (_ for _ in ()).throw(_too_many(req.full_url)))
    assert llm._call("sys", "x", 50, 5) is None
    assert llm._cooling_down()
