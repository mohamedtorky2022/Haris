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
