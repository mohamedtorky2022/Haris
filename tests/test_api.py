"""API tests. Skipped automatically if FastAPI's test client is not installed."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_check_flags_scam():
    r = client.post("/api/check", json={"text": "Aramex: pay AED 5 now at https://aramex-pay.top", "lang": "en"})
    assert r.status_code == 200
    assert r.json()["risk"] == "high"
    assert r.headers["cache-control"] == "no-store"


def test_check_validates_input():
    assert client.post("/api/check", json={"text": ""}).status_code == 422
    assert client.post("/api/check", json={"text": "x" * 5001}).status_code == 422
    assert client.post("/api/check", json={"text": "hi", "lang": "fr"}).status_code == 422


def test_playbooks_and_report():
    assert client.get("/api/playbooks?lang=ur").status_code == 200
    assert client.get("/api/playbooks/extortion?lang=ar").json()["steps"]
    assert client.get("/api/playbooks/unknown").status_code == 404
    r = client.post("/api/report", json={"lang": "en", "incident_type": "extortion", "description": "threats"})
    assert r.status_code == 200
    assert r.json()["reference"].startswith("HRS-")


def test_security_headers_and_frontend():
    r = client.get("/")
    assert r.status_code == 200
    assert "Content-Security-Policy" in r.headers


def test_extract_endpoint():
    r = client.post("/api/extract", json={"lang": "en", "text": "I paid 120 AED by card yesterday"})
    assert r.status_code == 200
    body = r.json()
    assert body["fields"]["amount"] == "120"
    assert body["missing"] == ["steps_taken"]
    assert client.post("/api/extract", json={"images": ["x"] * 4}).status_code == 422


def test_polish_endpoint():
    r = client.post("/api/polish", json={"lang": "en", "text": "they wanted the o t p 4471", "dialect": "en-IN"})
    assert r.status_code == 200
    assert r.json()["text"] == "they wanted the OTP 4471"
    assert client.post("/api/polish", json={"text": "x", "dialect": "bad value"}).status_code == 422


def test_radar_report_and_authority_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_RADAR_DB", str(tmp_path / "radar.db"))
    monkeypatch.delenv("HARIS_AUTHORITY_TOKEN", raising=False)
    text = "Your parcel is on hold. Pay AED 5 at https://emirates-post-ae.top/pay or call 0501234567"
    for i in range(3):
        r = client.post("/api/radar/report", json={"text": text, "lang": "en", "reporter_id": f"device-{i:04d}"})
        assert r.status_code == 200
    campaigns = client.get("/api/authority/campaigns").json()  # the test client counts as this computer
    assert campaigns[0]["status"] == "escalated"
    assert client.post(f"/api/authority/campaigns/{campaigns[0]['id']}", json={"status": "confirmed"}).status_code == 200
    assert client.get("/api/radar/broadcasts?lang=en").json()[0]["title"].startswith("Official warning")
    assert client.post("/api/check", json={"text": "call 0501234567", "lang": "en"}).json()["radar"]["broadcast"]

    # Through a tunnel the request comes from this computer but carries a forwarding header.
    assert client.get("/api/authority/campaigns", headers={"cf-connecting-ip": "203.0.113.9"}).status_code == 403

    monkeypatch.setenv("HARIS_AUTHORITY_TOKEN", "s3cret")
    assert client.get("/api/authority/campaigns").status_code == 401
    assert client.get("/api/authority/campaigns", headers={"x-authority-token": "s3cret"}).status_code == 200


# --- Voice notes recorded in the app ------------------------------------------------

def _wav_data_url(seconds=1):
    import base64, io, wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\x00\x01" * 16000 * seconds)
    return "data:audio/wav;base64," + base64.b64encode(buf.getvalue()).decode()


def test_transcribe_returns_the_words(monkeypatch):
    from haris import llm
    seen = {}
    def fake(audio, media_type):
        seen["type"] = media_type
        seen["size"] = len(audio)
        return "وصلتني رسالة من البنك تطلب رمز التحقق"
    monkeypatch.setattr(llm, "transcribe", fake)
    r = client.post("/api/transcribe", json={"audio": _wav_data_url(), "lang": "ar"})
    assert r.status_code == 200
    assert r.json() == {"text": "وصلتني رسالة من البنك تطلب رمز التحقق"}
    assert seen["type"] == "audio/wav" and seen["size"] > 30000


def test_transcribe_says_so_when_the_ai_cannot_hear(monkeypatch):
    from haris import llm
    monkeypatch.setattr(llm, "transcribe", lambda audio, media_type: None)
    r = client.post("/api/transcribe", json={"audio": _wav_data_url()})
    assert r.status_code == 503


def test_transcribe_refuses_what_is_not_audio(monkeypatch):
    from haris import llm
    monkeypatch.setattr(llm, "transcribe", lambda audio, media_type: "x")
    assert client.post("/api/transcribe", json={"audio": "data:image/png;base64," + "A" * 2000}).status_code == 422
    assert client.post("/api/transcribe", json={"audio": "data:audio/wav;base64,@@@" + "A" * 2000}).status_code == 422
    assert client.post("/api/transcribe", json={"audio": "data:audio/wav;base64," + "AAAA" * 20}).status_code == 422
