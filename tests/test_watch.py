"""Early warning from the Certificate Transparency logs: new look-alike domains before any report."""

import time

import pytest

from haris import watch


@pytest.fixture(autouse=True)
def fresh_radar(tmp_path, monkeypatch):
    monkeypatch.setenv("HARIS_RADAR_DB", str(tmp_path / "radar.db"))
    monkeypatch.setattr(watch.sitecheck, "inspect", lambda url, lang="ar", use_llm=True: {
        "reachable": True, "score": 85, "title": "UAE PASS Login", "flags": ["brand_with_form"],
        "final_domain": url.split("/")[2], "domain_age_days": 3, "uae": True})
    monkeypatch.setattr(watch, "sweep_dns", lambda terms, workers=32: [])


def _iso(seconds_ago: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - seconds_ago))


ENTRIES = [
    {"name_value": "uaepass-verify-login.com\nwww.uaepass-verify-login.com", "not_before": _iso(3600 * 5)},
    {"name_value": "*.uaepass.ae", "not_before": _iso(3600)},                        # the real one
    {"name_value": "uaepass.jo", "not_before": _iso(3600)},                          # the brand abroad
    {"name_value": "old-uaepass-update.xyz", "not_before": _iso(86400 * 40)},        # too old
    {"name_value": "uaepass-update.top", "not_before": _iso(86400 * 2)},
]


def test_candidates_keeps_only_new_look_alikes():
    found = watch.candidates("uaepass", ENTRIES, time.time() - 14 * 86400)
    names = {f["domain"] for f in found}
    assert names == {"uaepass-verify-login.com", "www.uaepass-verify-login.com", "uaepass-update.top"}
    assert all(f["brand"] == "UAE PASS" and "brand_lookalike" in f["flags"] for f in found)


def test_run_saves_visits_and_lists_them(monkeypatch):
    monkeypatch.setattr(watch, "fetch_ct", lambda term, timeout=45: ENTRIES if term == "uaepass" else [])
    out = watch.run(["uaepass", "tamm"])
    assert out["new"] == 3 and out["errors"] == []
    listing = watch.listing()
    assert listing["total"] == 3 and listing["running"] is False
    assert listing["items"][0]["domain"].endswith("uaepass-verify-login.com")  # newest first
    assert any(i["live"] and i["live"]["score"] == 85 for i in listing["items"])
    assert watch.run(["uaepass"])["new"] == 0  # the same names are not counted twice


def test_a_slow_log_does_not_stop_the_run(monkeypatch):
    def flaky(term, timeout=45):
        if term == "adcb":
            raise TimeoutError
        return ENTRIES if term == "uaepass" else []
    monkeypatch.setattr(watch, "fetch_ct", flaky)
    out = watch.run(["adcb", "uaepass"])
    assert out["new"] == 3 and out["errors"] == ["crt.sh adcb: TimeoutError"]


def test_a_checked_message_says_the_domain_was_spotted_early(monkeypatch):
    monkeypatch.setattr(watch, "fetch_ct", lambda term, timeout=45: ENTRIES)
    watch.run(["uaepass"])
    from haris.detector import analyze
    text = "UAE PASS: your digital identity expires today, verify now: https://uaepass-update.top/login"
    result = watch.annotate(analyze(text, "en"), text, "en")
    assert result["reasons"][0].startswith("Haris spotted this early")
    assert result["radar"]["spotted"]["domain"] == "uaepass-update.top"
    ar = watch.annotate(analyze(text, "ar"), text, "ar")
    assert "رصده «حارس» مبكراً" in ar["reasons"][0]


def test_look_alike_names_cover_the_usual_bait_and_skip_the_real_site():
    names = watch.permutations("dewa")
    assert {"dewa-pay.com", "dewalogin.online", "pay-dewa.top", "dewagov.info"} <= names
    assert "dewa.gov.ae" not in names and len(names) > 800


def test_the_dns_sweep_keeps_names_that_resolve(monkeypatch):
    monkeypatch.undo()  # the real sweep, with name resolution faked
    live = {"dewa-pay.com", "dewalogin.online"}
    monkeypatch.setattr(watch, "_resolves", lambda name: name in live)
    found = watch.sweep_dns(["dewa"], workers=4)
    assert {f["domain"] for f in found} == live
    assert all(f["source"] == "dns" and f["brand"] == "DEWA" for f in found)


def test_a_name_that_forwards_to_the_brand_is_dropped_and_live_scams_come_first(monkeypatch):
    monkeypatch.setattr(watch, "fetch_ct", lambda term, timeout=45: [])
    monkeypatch.setattr(watch, "sweep_dns", lambda terms, workers=32: [
        {"domain": d, "brand": "DEWA", "source": "dns", "issued_at": None, "score": 40, "flags": ["brand_lookalike"]}
        for d in ("dewa-pay.com", "dewaonline.com", "dewa.xyz")])
    pages = {"dewa-pay.com": ("dewa-pay.com", True, 90, ["card_form", "brand_with_form"], True),
             "dewaonline.com": ("www.dewa.gov.ae", True, 0, [], True),
             "dewa.xyz": ("dewa.xyz", False, 0, [], False)}
    def inspect(url, lang="ar", use_llm=True):
        final, up, score, flags, uae = pages[url.split("/")[2]]
        return {"reachable": up, "score": score, "flags": flags, "final_domain": final, "domain_age_days": 5,
                "title": "", "uae": uae}
    monkeypatch.setattr(watch.sitecheck, "inspect", inspect)
    watch.run(["dewa"])
    listing = watch.listing()
    assert [i["domain"] for i in listing["items"]] == ["dewa-pay.com", "dewa.xyz"]
    assert listing["risky"] == 1 and listing["live"] == 1 and listing["new"] == 2
    assert watch.spotted("dewaonline.com") is None  # the brand's own redirect is never "spotted"


def test_a_new_page_with_the_brand_word_but_not_aimed_at_the_uae_is_not_urgent():
    gambling = {"live": {"reachable": True, "score": 55, "uae": False, "flags": ["new_domain", "brand_on_page"]}}
    uae_page = {"live": {"reachable": True, "score": 55, "uae": True, "flags": ["new_domain", "brand_on_page"]}}
    asks = {"live": {"reachable": True, "score": 40, "uae": False, "flags": ["otp_form"]}}
    assert not watch.risky(gambling) and watch.risky(uae_page) and watch.risky(asks)
    assert [watch.tier(x) for x in (gambling, uae_page, asks)] == ["review", "urgent", "urgent"]
    parked = {"live": {"reachable": True, "score": 15, "uae": False, "flags": ["offsite_form"]}}
    assert watch.tier(parked) == "low"
