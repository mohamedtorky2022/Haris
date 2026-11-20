"""Step-by-step emergency plans for victims, and official reporting channels.

Contacts were checked against Abu Dhabi Police and Dubai Police announcements
(November 2026). The partner authority should confirm them before launch.
The plans' titles and steps are in `locales/<lang>.json` under "playbooks",
and the contact labels under "contacts".
"""

from __future__ import annotations

from .text import SUPPORTED_LANGS
from .translations import section, table

CONTACT_VALUES = [
    ("emergency", "999"),
    ("aman", "8002626"),
    ("aman_sms", "2828"),
    ("aman_email", "aman@adpolice.gov.ae"),
    ("ecrime", "https://www.ecrime.ae"),
    ("dubai_police", "901"),
]

# For tourists and other visitors (u.ae and Dubai Police, November 2026). Dubai's Tourism Police follows a
# visitor's case even after they have left the country.
VISITOR_CONTACT_VALUES = [
    ("tourist_police_dubai", "+971 50 453 8107"),
    ("tourist_police_dubai_email", "TouristPolice@dubaipolice.gov.ae"),
    ("tourist_police_abu_dhabi", "+971 2 512 7777"),
]

_labels = table("contacts")
CONTACTS = [{"id": cid, "value": value, "label": _labels[cid]} for cid, value in CONTACT_VALUES]
VISITOR_CONTACTS = [{"id": cid, "value": value, "label": _labels[cid]} for cid, value in VISITOR_CONTACT_VALUES]

PLAYBOOKS: dict[str, dict] = {
    key: {
        "title": {lang: section(lang, "playbooks")[key]["title"] for lang in SUPPORTED_LANGS},
        "steps": {lang: section(lang, "playbooks")[key]["steps"] for lang in SUPPORTED_LANGS},
    }
    for key in section("ar", "playbooks")
}


def contacts(lang: str) -> list[dict]:
    return [{"id": c["id"], "value": c["value"], "label": c["label"][lang]} for c in CONTACTS]


def visitor_help(lang: str) -> dict:
    """What changes for a tourist: a card from a bank abroad, the embassy, travel insurance, the Tourism Police."""
    return {"title": section(lang, "visitor")["title"], "tips": section(lang, "visitor")["tips"],
            "contacts": [{"id": c["id"], "value": c["value"], "label": c["label"][lang]} for c in VISITOR_CONTACTS]}


def list_playbooks(lang: str) -> list[dict]:
    return [{"id": key, "title": pb["title"][lang]} for key, pb in PLAYBOOKS.items()]


def get_playbook(playbook_id: str, lang: str) -> dict | None:
    pb = PLAYBOOKS.get(playbook_id)
    if not pb:
        return None
    return {"id": playbook_id, "title": pb["title"][lang], "steps": pb["steps"][lang], "contacts": contacts(lang),
            "visitor": visitor_help(lang)}
