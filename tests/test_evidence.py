"""The takedown evidence file: registry records read correctly, nothing guessed, nothing personal leaked."""

import pytest

from haris import evidence, sitecheck

# The shapes registries really return: the registrar's abuse contact nested inside the registrar entity.
DOMAIN_RDAP = {
    "ldhName": "SECURE-ADCB-LOGIN.TOP",
    "status": ["client transfer prohibited"],
    "events": [{"eventAction": "registration", "eventDate": "2026-11-20T08:00:00Z"},
               {"eventAction": "expiration", "eventDate": "2027-11-20T08:00:00Z"}],
    "nameservers": [{"ldhName": "NS1.EXAMPLE-DNS.NET"}, {"ldhName": "NS2.EXAMPLE-DNS.NET"}],
    "entities": [{
        "roles": ["registrar"],
        "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "Example Registrar, Inc."]]],
        "publicIds": [{"type": "IANA Registrar ID", "identifier": "9999"}],
        "entities": [{"roles": ["abuse"], "vcardArray": ["vcard", [
            ["email", {}, "text", "abuse@example-registrar.test"], ["tel", {"type": "voice"}, "uri", "tel:+1.5550100"]]]}],
    }],
}
IP_RDAP = {
    "name": "EXAMPLE-HOSTING-NET", "country": "US", "startAddress": "203.0.113.0", "endAddress": "203.0.113.255",
    "entities": [{"roles": ["registrant"], "vcardArray": ["vcard", [["fn", {}, "text", "Example Hosting LLC"]]],
                  "entities": [{"roles": ["abuse"], "vcardArray": ["vcard", [["email", {}, "text", "abuse@example-hosting.test"]]]}]}],
}
SITE = {
    "url": "https://secure-adcb-login.top/verify", "final_url": "https://secure-adcb-login.top/verify",
    "final_domain": "secure-adcb-login.top", "reachable": True, "status": 200, "redirects": [],
    "title": "ADCB — تحديث البطاقة", "domain_age_days": 3, "cert_age_days": 2,
    "flags": ["brand_on_page", "card_form", "otp_form", "brand_with_form", "new_domain"], "brands": ["adcb"],
    "ai": {"risk": "high", "impersonates": "ADCB", "reasons": []}, "score": 100, "sha256": "ab" * 32, "error": None,
}


def test_the_registrar_and_its_abuse_contact_are_read():
    facts = evidence.registrar_facts(DOMAIN_RDAP)
    assert facts["registrar"] == "Example Registrar, Inc."
    assert facts["iana_id"] == "9999"
    assert facts["abuse_email"] == "abuse@example-registrar.test"
    assert facts["abuse_phone"] == "+1.5550100"
    assert facts["registered"] == "2026-11-20" and facts["expires"] == "2027-11-20"
    assert facts["nameservers"] == ["ns1.example-dns.net", "ns2.example-dns.net"]


def test_the_host_and_its_abuse_contact_are_read():
    facts = evidence.network_facts(IP_RDAP)
    assert facts == {"network": "EXAMPLE-HOSTING-NET", "country": "US", "range": "203.0.113.0 – 203.0.113.255",
                     "organisation": "Example Hosting LLC", "abuse_email": "abuse@example-hosting.test"}


def test_a_missing_record_gives_nothing_rather_than_a_guess():
    assert evidence.registrar_facts(None) == {}
    assert evidence.network_facts(None) == {}
    assert "abuse_email" not in evidence.registrar_facts({"entities": [{"roles": ["registrar"], "vcardArray": ["vcard", []]}]})


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(sitecheck, "inspect", lambda url, lang="en", use_llm=True: dict(SITE))
    monkeypatch.setattr(evidence, "_rdap", lambda path: DOMAIN_RDAP if path.startswith("domain/") else IP_RDAP)
    monkeypatch.setattr(evidence, "_ip", lambda host: "203.0.113.7")


def test_the_whole_file_and_its_drafts(offline):
    ev = evidence.build("https://secure-adcb-login.top/verify?id=971501234567")
    assert ev["risk"] == "high" and ev["registrable"] == "secure-adcb-login.top"
    assert ev["hosting"]["ip"] == "203.0.113.7"
    reg, host, block = ev["drafts"]["registrar"], ev["drafts"]["hosting"], ev["drafts"]["block_ar"]
    assert reg["to"] == "abuse@example-registrar.test" and host["to"] == "abuse@example-hosting.test"
    assert "suspend" in reg["body"] and "take it down" in host["body"]
    assert "ab" * 32 in reg["body"] and "203.0.113.7" in block["body"]
    assert "registered 3 days ago" in reg["body"]
    assert "حجب" in block["subject"] and "[اسم الضابط]" in block["body"]


def test_no_victim_identifier_reaches_the_evidence(offline, monkeypatch):
    # The real inspect drops the query string; make the stub do the same as the real one would.
    monkeypatch.setattr(sitecheck, "inspect", lambda url, lang="en", use_llm=True: dict(SITE, url=sitecheck._clean(url)))
    ev = evidence.build("https://secure-adcb-login.top/verify?victim=971501234567")
    assert "971501234567" not in str(ev)


def test_a_free_website_builder_points_to_the_platform(offline, monkeypatch):
    monkeypatch.setattr(sitecheck, "inspect", lambda url, lang="en", use_llm=True: dict(
        SITE, url="https://mail-update-1.square.site/", final_url="https://mail-update-1.square.site/",
        final_domain="mail-update-1.square.site", flags=["free_host", "password_form"], brands=[]))
    ev = evidence.build("https://mail-update-1.square.site/")
    assert ev["free_host"] == "square.site"
    assert any("square.site" in n for n in ev["notes"])
    assert "square.site" in ev["drafts"]["hosting"]["body"]


def test_the_training_page_is_marked_so_no_one_sends_its_drafts(offline, monkeypatch):
    monkeypatch.setattr(sitecheck, "inspect", lambda url, lang="en", use_llm=True: dict(SITE, brands=["falconbank"]))
    ev = evidence.build("https://haris-uae.onrender.com/demo/go")
    assert any("موقع التدريب" in n for n in ev["notes"])
    assert "fictional" in ev["drafts"]["registrar"]["body"]


def test_an_unreachable_site_still_gets_its_registry_facts(offline, monkeypatch):
    monkeypatch.setattr(sitecheck, "inspect", lambda url, lang="en", use_llm=True: dict(
        SITE, reachable=False, status=None, flags=["new_domain"], sha256=None))
    ev = evidence.build("https://secure-adcb-login.top/")
    assert ev["domain"]["registrar"] == "Example Registrar, Inc."
    assert any("لا يستجيب" in n for n in ev["notes"])


def test_the_evidence_api_needs_the_authority_code(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("HARIS_AUTHORITY_TOKEN", "secret-code")
    monkeypatch.setenv("HARIS_SITE_CHECK", "1")
    client = TestClient(app)
    assert client.post("/api/authority/evidence", json={"url": "https://x.top/"}).status_code == 401
