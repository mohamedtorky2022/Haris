from haseen.urls import analyze_url, extract_urls


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
