"""The scores the evaluation scripts print for a judge's hidden set."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import metrics  # noqa: E402


def test_precision_recall_f1():
    m = metrics.scores(tp=8, fp=2, fn=2, tn=88)
    assert m["precision"] == 0.8 and m["recall"] == 0.8 and round(m["f1"], 3) == 0.8
    assert m["accuracy"] == 0.96 and round(m["false_positive_rate"], 4) == round(2 / 90, 4)
    assert metrics.scores(0, 0, 0, 5)["precision"] is None  # nothing flagged: no precision to speak of


def test_a_judges_csv_with_a_header_and_loose_labels(tmp_path):
    f = tmp_path / "set.csv"
    f.write_text('message,label\n"Pay now, or else: http://x.top",1\nHi mum,ham\nUAE PASS expired,Phishing\n', encoding="utf-8")
    rows = metrics.read_labelled(str(f), "text")
    assert [r["positive"] for r in rows] == [True, False, True]
    assert rows[0]["text"] == "Pay now, or else: http://x.top"


def test_json_and_jsonl(tmp_path):
    (tmp_path / "a.json").write_text('[{"url": "https://dewa-pay.com", "label": "malicious"}]', encoding="utf-8")
    (tmp_path / "b.jsonl").write_text('{"text": "hello", "label": "benign"}\n', encoding="utf-8")
    assert metrics.read_labelled(str(tmp_path / "a.json"), "url")[0]["positive"] is True
    assert metrics.read_labelled(str(tmp_path / "b.jsonl"), "text")[0]["positive"] is False
