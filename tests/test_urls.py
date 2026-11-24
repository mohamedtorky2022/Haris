from haris.urls import analyze_url, extract_urls


def test_extracts_http_www_and_bare_domains():
    urls = extract_urls("Visit https://a.com/x, www.b.ae and pay at fake-site.xyz/pay. Email me at x@y.com")
    assert "https://a.com/x" in urls
    assert "www.b.ae" in urls
    assert "fake-site.xyz/pay" in urls
    assert not any("y.com" in u for u in urls)


def test_brand_lookalike_and_risky_tld():
    report = analyze_url("https://emirates-post-ae.top/track")
    assert "brand_lookalike" in report.flags
    assert "risky_tld" in report.flags
    assert not report.official


def test_leetspeak_lookalike():
    assert "brand_lookalike" in analyze_url("https://ar4mex-delivery.com").flags


def test_official_domains():
    for url in ("https://www.emiratespost.ae/track", "https://www.dubaipolice.gov.ae", "https://u.ae", "https://es.adpolice.gov.ae"):
        report = analyze_url(url)
        assert report.official, url
        assert report.score == 0


def test_gov_ae_suffix_is_official():
    assert analyze_url("https://anything.gov.ae/path").official


def test_shortener_ip_and_at_symbol():
    assert "shortener" in analyze_url("https://bit.ly/abc").flags
    assert "ip_host" in analyze_url("http://185.22.10.4/login").flags
    assert "at_symbol" in analyze_url("https://bank.com@evil.example/login").flags


def test_query_string_not_sent_to_model():
    report = analyze_url("https://evil.xyz/pay?card=4111111111111111&name=ali")
    assert report.safe_for_model() == "evil.xyz/pay"


# --- TAMM, traffic fines, and short brand names ---------------------------------------

def test_tamm_is_protected_and_its_own_portal_is_official():
    from haris.urls import analyze_url
    assert analyze_url("https://tamm.abudhabi/en/fines").official
    for fake in ("https://tamm-abudhabi-fines.com/pay", "https://abudhabi-tamm.com", "https://tammpay.com"):
        assert "brand_lookalike" in analyze_url(fake).flags, fake


def test_short_brand_names_are_not_read_inside_ordinary_words():
    from haris.urls import analyze_url
    for genuine in ("https://portal.office.com", "https://startapp.io", "https://moist.com", "https://tammy.com"):
        assert "brand_lookalike" not in analyze_url(genuine).flags, genuine
    for fake in ("https://rta-fines.top", "https://rtafines.com", "https://payicp.com", "https://dhl-redelivery.info"):
        assert "brand_lookalike" in analyze_url(fake).flags, fake


def test_a_tamm_traffic_fine_message_is_high_risk():
    from haris.detector import analyze
    r = analyze("تطبيق تم: لديك مخالفة مرورية غير مدفوعة بقيمة 400 درهم. سدد خلال 24 ساعة لتجنب الغرامة: https://tamm-fines-ae.com/pay", "ar")
    assert r["risk"] == "high"


def test_global_brands_their_own_sites_and_infrastructure():
    from haris.urls import analyze_url as a
    for clean in ("https://amazon.de", "https://amazon.co.uk", "https://cloud.microsoft", "https://apple-dns.net",
                  "https://hicloud.com", "https://pineapple.com", "https://outlookindia.com", "https://xn--12c1ezaww.com",
                  "https://portal.office.com", "https://www.paypal.com/signin"):
        r = a(clean)
        assert r.official or r.score < 25, (clean, r.flags)
    for scam in ("https://appleid-verify.com", "https://icloud-login.com", "https://paypal-secure.top",
                 "https://download-outlook.com", "https://xn--pple-43d.com"):
        assert a(scam).score >= 25, scam


def test_free_hosts_and_machine_made_names():
    from haris.urls import analyze_url as a
    assert "free_host" in a("https://login-update-form.vercel.app").flags
    assert a("https://login-update-form.vercel.app").score >= 25
    assert "free_host" in a("https://storage.googleapis.com/bucket/page.html").flags
    assert "free_host" not in a("https://notion.site").flags  # the platform itself
    assert "random_label" in a("https://pub-9e06cf401c8a495490150ee84add9bc3.r2.dev").flags
