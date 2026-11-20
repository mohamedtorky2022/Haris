"""Teaching Haris by example.

Real fine-tuning is not offered on Gemini's free API, so Haris learns the way
large models learn best without retraining: before each check, the labelled
examples most similar to the new message are shown to the model with their
correct answers. Adding an example (scripts/teach.py) changes the very next
answer, with no training run and no cost.

Examples come from two files:
  data/samples/messages.json      the labelled test set (scam / legit)
  data/training/examples.jsonl    examples you add, one JSON object per line
Every example is redacted before it is saved or shown to the model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .redact import redact
from .text import normalize

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "data" / "samples" / "messages.json"
TRAINING = ROOT / "data" / "training" / "examples.jsonl"
LABELS = ("scam", "legit")


def _grams(text: str) -> frozenset[str]:
    """Character trigrams: they compare well across Arabic, Urdu, Hindi and English."""
    t = " ".join(normalize(text).split())
    return frozenset(t[i:i + 3] for i in range(max(0, len(t) - 2)))


@lru_cache(maxsize=1)
def _load_cached(mtimes: tuple) -> tuple[dict, ...]:
    items = []
    if SAMPLES.exists():
        for s in json.loads(SAMPLES.read_text(encoding="utf-8")):
            items.append({"text": s["text"], "label": s["label"], "category": s.get("category"), "note": s.get("note")})
    if TRAINING.exists():
        for line in TRAINING.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                if e.get("label") in LABELS and e.get("text"):
                    items.append({"text": e["text"], "label": e["label"], "category": e.get("category"), "note": e.get("note")})
    for e in items:
        e["text"] = redact(e["text"]).text
        e["grams"] = _grams(e["text"])
        e["key"] = " ".join(normalize(e["text"]).split())
    return tuple(items)


def load() -> tuple[dict, ...]:
    mt = tuple(p.stat().st_mtime if p.exists() else 0 for p in (SAMPLES, TRAINING))
    return _load_cached(mt)


def similar(redacted_text: str, k: int = 6) -> list[dict]:
    """The k most similar labelled examples, with both labels represented when possible.

    An example identical to the message being judged is never shown, so the
    model cannot copy the answer (and the evaluation stays honest).
    """
    target = _grams(redacted_text)
    skip = " ".join(normalize(redacted_text).split())
    scored = []
    for e in load():
        if e["key"] == skip:
            continue
        union = len(target | e["grams"]) or 1
        scored.append((len(target & e["grams"]) / union, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [e for _, e in scored[: max(0, k - 1)]]
    # keep at least one example of the other label, so the model sees a contrast
    if picked and len({e["label"] for e in picked}) == 1:
        other = next((e for _, e in scored[k - 1:] if e["label"] != picked[0]["label"]), None)
        if other:
            picked.append(other)
    elif len(scored) >= k:
        picked.append(scored[k - 1][1])
    return picked


def as_prompt(examples: list[dict]) -> str:
    if not examples:
        return ""
    lines = []
    for e in examples:
        extra = f" category={e['category']}" if e.get("category") else ""
        note = f" why: {e['note']}" if e.get("note") else ""
        lines.append(f'<example label="{e["label"]}"{extra}>{e["text"]}</example>{note}')
    return "<examples>\n" + "\n".join(lines) + "\n</examples>\n"


def add(text: str, label: str, category: str | None = None, note: str | None = None) -> dict:
    """Save a new labelled example (redacted) for Haris to learn from."""
    if label not in LABELS:
        raise ValueError(f"label must be one of {LABELS}")
    text = " ".join(text.split())
    if not text:
        raise ValueError("text is empty")
    entry = {"text": redact(text).text, "label": label}
    if category:
        entry["category"] = category
    if note:
        entry["note"] = " ".join(note.split())[:300]
    TRAINING.parent.mkdir(parents=True, exist_ok=True)
    with TRAINING.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry
