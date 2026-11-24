"""Precision, recall and F1 for the evaluation scripts, and a reader for a judge's own labelled file.

A judge can bring a hidden set as .csv (two columns, any header: the message or address, then the
label), .json (a list of {"text" or "url", "label"}) or .jsonl. Labels are read loosely:
scam / phishing / malicious / fraud / spam / 1 / true mean positive; legitimate / legit / benign / safe /
ham / genuine / 0 / false mean negative.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

POSITIVE = {"scam", "phishing", "malicious", "fraud", "spam", "bad", "1", "true", "yes", "positive"}
NEGATIVE = {"legitimate", "legit", "benign", "safe", "ham", "genuine", "good", "clean", "0", "false", "no", "negative"}


def label_of(raw) -> bool:
    """True for a scam or phishing label, False for a legitimate one."""
    value = str(raw).strip().lower()
    if value in POSITIVE:
        return True
    if value in NEGATIVE:
        return False
    raise SystemExit(f"Unknown label {raw!r}: use scam/phishing or legitimate (or 1/0).")


def read_labelled(path: str, field: str) -> list[dict]:
    """[{field: ..., "positive": bool}] from .csv, .json or .jsonl. field is "text" or "url"."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path} does not exist.")
    if p.suffix == ".csv":
        rows = [r for r in csv.reader(p.read_text(encoding="utf-8-sig").splitlines()) if r and any(c.strip() for c in r)]
        if rows and rows[0][-1].strip().lower() not in POSITIVE | NEGATIVE:
            rows = rows[1:]  # a header line
        items = [{field: ",".join(r[:-1]).strip(), "label": r[-1]} for r in rows]
    elif p.suffix == ".jsonl":
        items = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        items = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for it in items:
        value = it.get(field) or it.get("text") or it.get("url") or it.get("message")
        if value:
            out.append({**it, field: value, "positive": label_of(it["label"])})
    return out


def scores(tp: int, fp: int, fn: int, tn: int) -> dict:
    div = lambda a, b: a / b if b else None  # noqa: E731
    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = div(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1,
            "accuracy": div(tp + tn, tp + fp + fn + tn), "false_positive_rate": div(fp, fp + tn)}


def table(m: dict, positive: str = "scam") -> list[str]:
    """The confusion matrix and the scores, as markdown lines."""
    pct = lambda v: "n/a" if v is None else f"{v:.1%}"  # noqa: E731
    return [
        f"| | Haris: {positive} | Haris: not {positive} |",
        "|---|---:|---:|",
        f"| Really {positive} | {m['tp']} (caught) | {m['fn']} (missed) |",
        f"| Really legitimate | {m['fp']} (false alarm) | {m['tn']} (cleared) |",
        "",
        f"**Precision {pct(m['precision'])}** (of what Haris flagged, how much was really {positive}) · "
        f"**Recall {pct(m['recall'])}** (of the real {positive} cases, how many Haris caught) · "
        f"**F1 {pct(m['f1'])}** · accuracy {pct(m['accuracy'])} · false-alarm rate {pct(m['false_positive_rate'])}",
    ]
