"""The live website inspection, tested against pages this suite serves itself.

A real server runs on 127.0.0.1 and answers with the pages a victim would be sent to: a bank
look-alike asking for a card, a chain of redirects, a <meta refresh> hop, a form that posts to
another domain, and an ordinary page. Nothing leaves the machine: RDAP, Safe Browsing and the AI
are switched off in these tests, each of which is covered on its own below.
"""

import http.server
import threading

import pytest

from haris import sitecheck

# Captured before the fixtures below replace it, so the RDAP tests exercise the real function.
rdap_lookup = sitecheck.domain_age_days

PHISH = """<html><head><title>ADCB - تحديث البطاقة</title></head><body>
<h1>بنك أبوظبي التجاري</h1><p>تم إيقاف بطاقتك. حدّث بياناتك الآن.</p>
<form method="post" action="/submit">
  <input type="text" name="card_number" placeholder="رقم البطاقة">
  <input type="text" name="cvv" placeholder="CVV">
  <input type="password" name="password">
  <input type="text" name="otp" placeholder="رمز التحقق">
</form></body></html>"""

CLEAN = """<html><head><title>Corner Bakery</title></head><body>
<h1>Fresh bread daily</h1><p>Open from 7am. Call us to order.</p></body></html>"""

OFFSITE = """<html><head><title>Parcel</title></head><body>
<form action="https://collector.example.net/take"><input name="iban"></form></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/hop1"):
            self.send_response(302)
            self.send_header("Location", "/hop2")
            self.end_headers()
            return
        if self.path.startswith("/hop2"):
            body = f'<html><head><meta http-equiv="refresh" content="0;url=/phish"></head></html>'
        elif self.path.startswith("/phish"):
            body = PHISH
        elif self.path.startswith("/offsite"):
            body = OFFSITE
        elif self.path.startswith("/gone"):
            self.send_response(404)
            self.end_headers()
            return
        else:
            body = CLEAN
        encoded = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@pytest.fixture(scope="module")
def site():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(autouse=True)
def _allow_local(monkeypatch):
    monkeypatch.setenv("HARIS_SITE_CHECK", "1")
    monkeypatch.setenv("HARIS_SITE_ALLOW_LOCAL", "1")
    monkeypatch.delenv("GOOGLE_SAFE_BROWSING_KEY", raising=False)
    monkeypatch.setattr(sitecheck, "domain_age_days", lambda domain: None)
    sitecheck._CACHE.clear()


def inspect(url):
    return sitecheck.inspect(url, "ar", use_llm=False)


# --- What the visit finds ------------------------------------------------------

def test_a_bank_lookalike_page_is_caught(site):
    r = inspect(f"{site}/phish")
    assert r["reachable"] and r["status"] == 200
    assert "adcb" in r["brands"]
    assert {"brand_on_page", "card_form", "otp_form", "password_form", "brand_with_form"} <= set(r["flags"])
    assert r["score"] >= 55, r["flags"]


def test_an_ordinary_page_is_not_flagged(site):
    r = inspect(f"{site}/")
    assert r["reachable"]
    assert r["flags"] == []
    assert r["score"] == 0
    assert r["title"] == "Corner Bakery"


def test_redirects_are_followed_to_the_real_destination(site):
    r = inspect(f"{site}/hop1")
    assert r["final_url"].endswith("/phish"), r["redirects"]
    assert len(r["redirects"]) == 2  # a 302 and then a <meta refresh>
    assert "card_form" in r["flags"]


def test_a_form_posting_to_another_domain_is_flagged(site):
    assert "offsite_form" in inspect(f"{site}/offsite")["flags"]


def test_a_dead_link_is_reported_not_scored(site):
    r = inspect(f"{site}/gone")
    assert r["status"] == 404
    assert not r["reachable"]
    assert r["flags"] == []


# --- Refusing what must not be visited -------------------------------------------

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/admin",              # the server's own machine
    "http://169.254.169.254/latest/meta",  # the cloud metadata address
    "http://10.0.0.5/",
    "http://[::1]/",
    "http://localhost/",
    "ftp://example.com/x",
    "file:///etc/passwd",
])
def test_private_and_odd_addresses_are_refused(url, monkeypatch):
    monkeypatch.delenv("HARIS_SITE_ALLOW_LOCAL", raising=False)
    r = inspect(url)
    assert (r["error"] or "").startswith("refused"), r
    assert r["flags"] == []


def test_the_query_string_is_dropped_before_visiting(site):
    r = inspect(f"{site}/phish?victim=971501234567&id=abc")
    assert "victim" not in r["final_url"] and "971501234567" not in r["final_url"]


def test_the_visit_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("HARIS_SITE_CHECK", "0")
    assert not sitecheck.enabled()


# --- The pieces that reach other services --------------------------------------

def test_safe_browsing_is_skipped_without_a_key():
    assert sitecheck.safe_browsing("http://example.com/") is None


def test_safe_browsing_reads_a_match(monkeypatch):
    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_KEY", "test-key")
    monkeypatch.setattr(sitecheck.urllib.request, "urlopen",
                        lambda *a, **k: _FakeResponse(b'{"matches":[{"threatType":"SOCIAL_ENGINEERING"}]}'))
    assert sitecheck.safe_browsing("http://bad.example/") is True


def test_domain_age_is_read_from_rdap(monkeypatch):
    monkeypatch.setattr(sitecheck.urllib.request, "urlopen",
                        lambda *a, **k: _FakeResponse(
                            b'{"events":[{"eventAction":"registration","eventDate":"2026-11-01T00:00:00Z"}]}'))
    age = rdap_lookup("fresh-scam.top")
    assert age is not None and age < 60


def test_a_failing_rdap_lookup_does_not_break_the_check(monkeypatch):
    monkeypatch.setattr(sitecheck.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    assert rdap_lookup("example.com") is None


@pytest.mark.parametrize("domain,expected", [
    ("pay.adcb-update.top", "adcb-update.top"),
    ("a.b.example.co.uk", "example.co.uk"),
    ("fake.dubaipolice.gov.ae.scam.xyz", "scam.xyz"),
])
def test_the_registered_domain_is_picked_correctly(domain, expected):
    assert sitecheck.registrable(domain) == expected


def test_the_ai_verdict_raises_the_score(site, monkeypatch):
    monkeypatch.setattr(sitecheck.llm, "enabled", lambda: True)
    monkeypatch.setattr(sitecheck.llm, "_call", lambda *a, **k:
                        '{"risk":"high","impersonates":"ADCB","reasons":["تطلب بيانات بطاقتك"]}')
    r = sitecheck.inspect(f"{site}/phish", "ar", use_llm=True)
    assert r["ai"]["risk"] == "high" and r["ai"]["impersonates"] == "ADCB"
    assert "ai_high" in r["flags"]


def test_a_broken_ai_answer_is_ignored(site, monkeypatch):
    monkeypatch.setattr(sitecheck.llm, "enabled", lambda: True)
    monkeypatch.setattr(sitecheck.llm, "_call", lambda *a, **k: "sorry, I cannot help")
    r = sitecheck.inspect(f"{site}/phish", "ar", use_llm=True)
    assert r["ai"] is None
    assert not any(f.startswith("ai_") for f in r["flags"])


def test_the_page_text_is_redacted_before_the_model_sees_it(monkeypatch):
    seen = {}
    monkeypatch.setattr(sitecheck.llm, "enabled", lambda: True)
    monkeypatch.setattr(sitecheck.llm, "_call", lambda system, site, *a, **k: seen.setdefault("site", site) and None)
    sitecheck.ai_verdict({"final_domain": "x.top", "title": "t", "flags": [],
                          "domain_age_days": 2, "text": "ارسل 4532 0151 1283 0366 الان"}, "ar")
    assert "0151" not in seen["site"] and "[CARD]" in seen["site"]


class _FakeResponse:
    def __init__(self, body):
        self._body = body
        self.status = 200
        self.headers = {}

    def read(self, *_):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


# --- The whole check, from a message to a verdict ---------------------------------

def test_a_clean_looking_link_is_caught_once_the_site_is_visited(site, monkeypatch):
    """The point of the live visit: a domain whose name gives nothing away."""
    from haris import detector

    port = site.rsplit(":", 1)[1]
    monkeypatch.setattr(detector, "extract_urls", lambda text: [f"127.0.0.1:{port}/phish"])
    analyze = detector.analyze
    result = analyze("مرحباً، راجع الحساب هنا", "ar", use_llm=False)
    assert result["risk"] == "high", result
    assert "risky_website" in result["signals"]
    assert result["category"] == "phishing_link"
    site_view = result["links"][0]["site"]
    assert "brand_with_form" in site_view["flags"]
    assert any("تنتحل" in label for label in site_view["flag_labels"])


def test_an_ordinary_site_adds_nothing_to_the_verdict(site, monkeypatch):
    from haris import detector

    port = site.rsplit(":", 1)[1]
    monkeypatch.setattr(detector, "extract_urls", lambda text: [f"127.0.0.1:{port}/"])
    analyze = detector.analyze
    result = analyze("شوف المخبز الجديد", "ar", use_llm=False)
    # The visit finds nothing, so it adds nothing: the only risk left is the link being a bare
    # IP address, which the offline check flags on its own.
    assert "risky_website" not in result["signals"]
    assert result["links"][0]["site"]["flags"] == []
    assert result["links"][0]["site"]["reachable"]
    assert result["signals"] == ["suspicious_link"]


def test_the_api_returns_the_live_finding(site):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    answer = client.post("/api/site", json={"url": f"{site}/phish", "lang": "ar"})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["reachable"] and body["score"] >= 55
    assert body["flag_labels"] and body["language"] == "ar"


def test_the_api_refuses_an_internal_address(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.delenv("HARIS_SITE_ALLOW_LOCAL", raising=False)
    client = TestClient(app)
    assert client.post("/api/site", json={"url": "http://169.254.169.254/latest/meta"}).status_code == 400


# --- The TLS path that production uses (no proxy, a pinned connection) -------------

def test_an_invalid_certificate_is_flagged_over_https(tmp_path, monkeypatch):
    """Proves the direct HTTPS path works and that a bad certificate is caught.

    Render reaches sites directly (no proxy), so this exercises _PinnedHTTPS against a real TLS
    server with a self-signed certificate — exactly the "fake bank, days-old cert" shape.
    """
    import datetime
    import http.server
    import ssl
    import threading

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "fake-bank.top")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=30)).sign(key, hashes.SHA256()))
    key_file, cert_file = tmp_path / "k.pem", tmp_path / "c.pem"
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                           serialization.PrivateFormat.TraditionalOpenSSL,
                                           serialization.NoEncryption()))
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert_file), str(key_file))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("HARIS_SITE_ALLOW_LOCAL", "1")
        monkeypatch.delenv("HTTPS_PROXY", raising=False)
        monkeypatch.delenv("https_proxy", raising=False)
        monkeypatch.delenv("HARIS_SITE_PROXY", raising=False)
        monkeypatch.setattr(sitecheck, "domain_age_days", lambda d: None)
        sitecheck._CACHE.clear()
        r = sitecheck.inspect(f"https://127.0.0.1:{server.server_address[1]}/phish", "ar", use_llm=False)
        assert r["reachable"], r
        assert "bad_certificate" in r["flags"]  # self-signed, so verification failed
        assert "card_form" in r["flags"]         # and the page was still read
    finally:
        server.shutdown()
