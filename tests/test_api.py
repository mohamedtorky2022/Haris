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

    monkeypatch.setenv("HARIS_AUTHORITY_TOKEN", "s3cret")
    assert client.get("/api/authority/campaigns").status_code == 401
    assert client.get("/api/authority/campaigns", headers={"x-authority-token": "s3cret"}).status_code == 200
