"""Every language file must have exactly the same keys, and lists of the same length."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SETS = {
    "backend": ROOT / "backend" / "haris" / "locales",
    "frontend": ROOT / "frontend" / "locales",
}
LANGS = ("ar", "en", "ur", "hi")


def shape(value):
    if isinstance(value, dict):
        return {k: shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return ["list", len(value)] if not value or not isinstance(value[0], (list, dict)) else [shape(v) for v in value]
    return "text"


@pytest.mark.parametrize("name", SETS)
def test_every_language_has_the_same_keys(name):
    files = {lang: json.loads((SETS[name] / f"{lang}.json").read_text(encoding="utf-8")) for lang in LANGS}
    reference = shape(files["en"])
    for lang, data in files.items():
        if name == "frontend":  # each language offers its own accents for dictation
            data = {k: v for k, v in data.items() if k != "dialects"}
            ref = {k: v for k, v in reference.items() if k != "dialects"}
        else:
            ref = reference
        assert shape(data) == ref, f"{name}/{lang}.json differs from en.json"


@pytest.mark.parametrize("name", SETS)
def test_no_empty_text(name):
    def walk(value, path):
        if isinstance(value, dict):
            for k, v in value.items():
                yield from walk(v, f"{path}.{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                yield from walk(v, f"{path}[{i}]")
        elif not str(value).strip():
            yield path
    for lang in LANGS:
        data = json.loads((SETS[name] / f"{lang}.json").read_text(encoding="utf-8"))
        assert not list(walk(data, lang)), f"empty text in {name}/{lang}.json"


def test_placeholders_match_across_languages():
    import re
    for name, folder in SETS.items():
        en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
        for lang in LANGS:
            data = json.loads((folder / f"{lang}.json").read_text(encoding="utf-8"))
            for key, value in en.items():
                if isinstance(value, str):
                    assert set(re.findall(r"\{\w+\}", value)) == set(re.findall(r"\{\w+\}", data[key])), (name, lang, key)
