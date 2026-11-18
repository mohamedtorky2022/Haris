from haris.playbooks import PLAYBOOKS, get_playbook, list_playbooks
from haris.report import build_report


def test_every_playbook_has_all_languages():
    for pb in PLAYBOOKS.values():
        for lang in ("ar", "en", "ur"):
            assert pb["title"][lang]
            assert len(pb["steps"][lang]) >= 3


def test_playbook_steps_line_up_across_languages():
    for key, pb in PLAYBOOKS.items():
        assert len(pb["steps"]["ar"]) == len(pb["steps"]["en"]) == len(pb["steps"]["ur"]), key


def test_get_playbook_includes_contacts():
    pb = get_playbook("money_sent", "en")
    assert any(c["value"] == "8002626" for c in pb["contacts"])
    assert get_playbook("nope", "en") is None
    assert len(list_playbooks("ar")) == len(PLAYBOOKS)


def test_report_contains_details_and_auto_found_identifiers():
    report = build_report({
        "incident_type": "money_sent",
        "description": "Called from 0501234567, sent me to http://emirates-post-ae.top and I paid.",
        "amount": "350",
        "scammer_identifiers": ["@fake_courier"],
        "steps_taken": ["Called the bank"],
    }, "en")
    assert report["reference"].startswith("HRS-")
    assert "350 AED" in report["markdown"]
    assert "0501234567" in report["identifiers_found"]
    assert "@fake_courier" in report["markdown"]
    assert "Called the bank" in report["html"]


def test_report_html_is_escaped():
    report = build_report({"description": "<script>alert(1)</script>"}, "ar")
    assert "<script>" not in report["html"]
    assert "&lt;script&gt;" in report["html"]
    assert 'dir="rtl"' in report["html"]
