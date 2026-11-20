"""Text normalisation and language detection shared by every module.

Arabic text is normalised so that spelling variants match the same rule:
alef forms, taa marbuta, alef maqsura, diacritics and tatweel. Arabic-Indic
and Persian digits are converted to ASCII so amounts and numbers are found
whichever digits the sender used.
"""

from __future__ import annotations

import re
import unicodedata

SUPPORTED_LANGS = ("ar", "en", "ur", "hi", "ru")

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_ARABIC_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_ARABIC_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي"})

# Letters used in Urdu but not in standard Arabic.
_URDU_ONLY = re.compile(r"[ٹڈڑںےۓھہ]")
_ARABIC_SCRIPT = re.compile(r"[؀-ۿ]")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")


def normalize_digits(text: str) -> str:
    return text.translate(_DIGITS)


def normalize(text: str) -> str:
    """Lower-case, NFKC, unify Arabic spelling variants and digits."""
    text = unicodedata.normalize("NFKC", text)
    text = normalize_digits(text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.translate(_ARABIC_LETTERS)
    return text.lower().replace("ё", "е")  # Russian writes ё and е interchangeably


def detect_language(text: str) -> str:
    """Return 'ur', 'ar', 'hi', 'ru' or 'en' from the script the text is written in."""
    if _DEVANAGARI.search(text):
        return "hi"
    if _CYRILLIC.search(text):
        return "ru"
    if _URDU_ONLY.search(text):
        return "ur"
    if _ARABIC_SCRIPT.search(text):
        return "ar"
    return "en"


def pick_language(requested: str | None, text: str = "") -> str:
    if requested in SUPPORTED_LANGS:
        return requested
    return detect_language(text) if text else "ar"
