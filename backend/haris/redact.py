"""Remove personal data before any text leaves the server.

The AI model never needs to know a person's card number, Emirates ID or
phone number to judge whether a message is a scam, so these are replaced by
placeholders such as [CARD] first. Card numbers are only redacted when they
pass the Luhn check, so order numbers and amounts are left alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import normalize_digits

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
EMIRATES_ID = re.compile(r"\b784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")
CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
PHONE = re.compile(
    r"(?<![\w+])(?:"
    r"(?:\+|00)971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}"  # UAE international format
    r"|0\d{1,2}[\s-]?\d{3}[\s-]?\d{4}"  # UAE local format, e.g. 050 123 4567
    r"|(?:\+|00)\d{1,3}[\s-]?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}"  # other countries
    r")(?!\w)"
)


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


@dataclass
class Redaction:
    text: str
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def redact(text: str) -> Redaction:
    text = normalize_digits(text)
    counts: dict[str, int] = {}

    def sub(pattern: re.Pattern, label: str, value: str, check=None) -> str:
        def repl(match: re.Match) -> str:
            if check and not check(match.group(0)):
                return match.group(0)
            counts[label] = counts.get(label, 0) + 1
            return f"[{label}]"

        return pattern.sub(repl, value)

    text = sub(EMAIL, "EMAIL", text)
    text = sub(EMIRATES_ID, "EMIRATES_ID", text)
    text = sub(IBAN, "IBAN", text)
    text = sub(CARD, "CARD", text, check=luhn_valid)
    text = sub(PHONE, "PHONE", text)
    return Redaction(text=text, counts=counts)


def find_identifiers(text: str) -> dict[str, list[str]]:
    """List phone numbers, e-mails and IBANs mentioned in a victim's own account.

    Used by the report builder to pull the scammer's contact details out of the
    description so the victim does not have to type them twice.
    """
    text = normalize_digits(text)
    found = {
        "phones": PHONE.findall(text),
        "emails": EMAIL.findall(text),
        "ibans": IBAN.findall(text),
    }
    return {key: sorted(set(v.strip() for v in values)) for key, values in found.items() if values}
