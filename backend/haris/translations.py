"""Load the user-facing text from the per-language files in `locales/`.

Every sentence Haris shows lives in one JSON file per language
(`locales/ar.json`, `en.json`, `ur.json`, `hi.json`), so a reviewer or a
partner authority can check and correct the wording without touching code,
and a new language is one new file. `tests/test_locales.py` checks that every
file has exactly the same keys.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .text import SUPPORTED_LANGS

LOCALES_DIR = Path(__file__).with_name("locales")


@lru_cache(maxsize=None)
def load(lang: str) -> dict:
    return json.loads((LOCALES_DIR / f"{lang}.json").read_text(encoding="utf-8"))


def section(lang: str, name: str):
    return load(lang)[name]


def table(name: str) -> dict:
    """One section as {key: {lang: value}}, keeping the order of the Arabic file."""
    out: dict = {}
    for lang in SUPPORTED_LANGS:
        for key, value in section(lang, name).items():
            out.setdefault(key, {})[lang] = value
    return out
