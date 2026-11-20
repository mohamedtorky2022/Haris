"""Report inbox: consent, triage, the victim's private status, the authority's actions, retention."""

import os
import stat
import time

import pytest

from haris import inbox


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_INBOX_DB", str(tmp_path / "inbox.db"))
    monkeypatch.delenv("HARIS_INBOX_RETENTION_DAYS", raising=False)


MONEY = {"incident_type": "money_sent", "occurred_at": "اليوم 8:12 م", "description": "سحبوا 1000 درهم من بطاقتي",
         "amount": "1000", "payment_method": "بطاقة", "scammer_identifiers": ["bank-secure-update.top"],
         "evidence": ["لقطة 1", "لقطة 2"]}


def test_triage_follows_the_blueprint():
    t = lambda **d: inbox.triage(inbox._fields(d))  # noqa: E731
    assert t(incident_type="harassment", description="قال سأقتلك") == "critical"
    assert t(incident_type="extortion", description="يبتز ابني على إنستغرام") == "critical"
    assert t(incident_type="extortion", description="يطلب مالاً مقابل عدم النشر") == "medium"
    assert t(incident_type="money_sent", occurred_at="قبل أقل من ساعة") == "financial"
    assert t(incident_type="money_sent", occurred_at="قبل أسبوع") == "medium"
    assert t(incident_type="business_fraud", occurred_at="today") == "financial"
    assert t(incident_type="suspicious_only") == "indicator"
    assert t(incident_type="not-a-type") == "indicator"


def test_submit_then_follow_with_the_private_token():
    r = inbox.submit(MONEY, "ar", "dubai", verified=True)
    assert r["reference"].startswith("HRS-") and r["priority"] == "financial" and r["status"] == "new"
    assert inbox.status(r["reference"], "wrong-token") is None
    s = inbox.status(r["reference"], r["token"])
    assert s["status_label"] == inbox.TEXT["ar"]["status"]["new"] and s["events"][0]["kind"] == "submitted"
    stored = inbox.detail(r["reference"])
    assert stored["fields"]["evidence_count"] == 2 and "evidence" not in stored["fields"]  # no screenshots kept
    assert stored["verified"] and stored["emirate"] == "dubai"


def test_keeps_the_report_file_number_once():
    a = inbox.submit(MONEY, "ar", "dubai", True, reference="HRS-20261121-ABC123")
    assert a["reference"] == "HRS-20261121-ABC123"
    b = inbox.submit(MONEY, "ar", "dubai", True, reference="HRS-20261121-ABC123")  # sent twice
    c = inbox.submit(MONEY, "ar", "dubai", True, reference="'; DROP TABLE reports; --")
    assert b["reference"] != a["reference"] and c["reference"].startswith("HRS-") and len(inbox.queue()["items"]) == 3


def test_token_is_stored_only_as_a_hash(tmp_path):
    r = inbox.submit(MONEY, "en", "sharjah", verified=False)
    raw = (tmp_path / "inbox.db").read_bytes()
    assert r["token"].encode() not in raw
    assert stat.S_IMODE(os.stat(tmp_path / "inbox.db").st_mode) == 0o600


def test_authority_flow_and_victim_sees_each_step():
    r = inbox.submit(MONEY, "ar", "abu_dhabi", verified=True)
    ref, token = r["reference"], r["token"]
    inbox.act(ref, "receive")
    with pytest.raises(ValueError):
        inbox.act(ref, "request_info", "")  # must say what is needed
    inbox.act(ref, "request_info", "أرسل اسم البنك وآخر 4 أرقام من البطاقة")
    s = inbox.status(ref, token)
    assert s["status"] == "info_requested" and s["events"][-1]["note"].startswith("أرسل اسم البنك")
    s = inbox.reply(ref, token, "بنك الإمارات، البطاقة المنتهية بـ 4417")
    assert s["status"] == "received" and s["events"][-1]["kind"] == "reply"
    done = inbox.act(ref, "close", "تم تجميد المبلغ وإعادته")
    assert done["status"] == "closed"
    assert inbox.act(ref, "receive") is None and inbox.reply(ref, token, "x") is None  # closed stays closed


def test_queue_puts_the_most_urgent_first_and_counts():
    inbox.submit({"incident_type": "suspicious_only"}, "en", "dubai", False)
    inbox.submit({"incident_type": "account_hacked"}, "en", "dubai", False)
    crit = inbox.submit({"incident_type": "extortion", "description": "threatens my daughter"}, "en", "ajman", False)
    money = inbox.submit(MONEY, "ar", "dubai", True)
    inbox.act(money["reference"], "receive")
    q = inbox.queue()
    assert [i["priority"] for i in q["items"]] == ["critical", "financial", "medium", "indicator"]
    assert q["items"][0]["reference"] == crit["reference"]
    assert q["stats"]["new"] == 3 and q["stats"]["urgent"] == 2 and q["stats"]["in_progress"] == 1
    assert q["stats"]["avg_minutes_to_receive"] is not None


def test_reports_are_deleted_after_the_retention_period(monkeypatch):
    r = inbox.submit(MONEY, "ar", "dubai", True)
    real = time.time
    monkeypatch.setattr(inbox.time, "time", lambda: real() + 8 * 24 * 3600)
    assert inbox.detail(r["reference"]) is None


def test_routes_need_consent_and_the_authority(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app import main
    from app.main import app

    monkeypatch.setattr(main, "_hits", main.defaultdict(main.deque))  # its own per-minute API limit
    client = TestClient(app)
    body = {**MONEY, "lang": "ar", "emirate": "dubai", "identity_confirmed": True}
    assert client.post("/api/reports", json=body).status_code == 400  # no consent
    r = client.post("/api/reports", json={**body, "consent": True}).json()
    ref, token = r["reference"], r["token"]
    assert client.get(f"/api/reports/{ref}").status_code == 404
    assert client.get(f"/api/reports/{ref}", headers={"x-report-token": token}).json()["status"] == "new"
    q = client.get("/api/authority/reports").json()
    assert q["items"][0]["reference"] == ref
    assert client.post(f"/api/authority/reports/{ref}", json={"action": "receive"}).json()["status"] == "received"
    assert client.get("/api/authority/reports", headers={"x-forwarded-for": "1.2.3.4"}).status_code == 403
