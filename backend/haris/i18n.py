"""User-facing text in every supported language.

The wording itself lives in `locales/<lang>.json` (see translations.py), so it
can be reviewed by the partner authority in one place per language.
"""

from __future__ import annotations

from .translations import table

RISK_LABELS = table("risk_labels")
RISK_SUMMARY = table("risk_summary")
CATEGORY_LABELS = table("categories")
REASONS = table("reasons")
URL_FLAGS = table("url_flags")
ADVICE = table("advice")


def t(table: dict, key: str, lang: str):
    entry = table.get(key, {})
    return entry.get(lang) or entry.get("en") or key
