"""Takedown evidence for a fake website: who registered it, who hosts it, what it does, and draft requests.

For one address, the authority gets everything needed to have the site taken down or blocked:

  what Haris found    the live inspection from sitecheck.py: final address, redirects, what the page asks
                      for, the brand it imitates, the AI's reading, and a SHA-256 of the page as it was seen
  the registrar       from the domain's RDAP record: registrar name, IANA id, abuse e-mail and phone,
                      registration and expiry dates, name servers, status
  the host            the server's address, and from that address's RDAP record the network, its owner,
                      country and abuse e-mail; and the platform when the page sits on a free website builder
  draft requests      to the registrar's abuse desk and to the host's (in English, as most are abroad), and
                      a request to block the site inside the UAE (in Arabic)

Every contact comes from the registries' own records, never from a list written by hand, and a contact that
could not be found is left empty rather than guessed. Nothing is sent: the drafts are for an officer to
check, complete with the authority's details, and send. The query string is dropped from the address, as
in sitecheck.py, so no victim identifier appears in the evidence.
"""

from __future__ import annotations

import json
import logging
import socket
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlsplit

from . import sitecheck
from .i18n import SITE_FLAGS, t

log = logging.getLogger("haris.evidence")

HIGH, MEDIUM = 55, 25  # the same thresholds as the message check (detector.py)


def _rdap(path: str) -> dict | None:
    """One RDAP record from rdap.org, which forwards to the registry that holds it."""
    try:
        req = urllib.request.Request(f"https://rdap.org/{path}",
                                     headers={"Accept": "application/rdap+json", "User-Agent": "Haris/1.0"})
        with urllib.request.urlopen(req, timeout=sitecheck.TIMEOUT) as resp:
            return json.loads(resp.read(300_000))
    except (OSError, ValueError) as exc:
        log.info("RDAP %s failed: %s", path.split("/")[0], type(exc).__name__)
        return None


def _vcard(entity: dict) -> dict:
    """Name, e-mail and phone from an RDAP entity's vCard."""
    out: dict[str, str] = {}
    try:
        for item in entity.get("vcardArray", [None, []])[1]:
            kind, value = item[0], item[3]
            if kind == "fn" and value:
                out.setdefault("name", str(value).strip())
            elif kind == "email" and value:
                out.setdefault("email", str(value).strip())
            elif kind == "tel" and value:
                out.setdefault("phone", str(value).replace("tel:", "").strip())
    except (IndexError, TypeError, AttributeError):
        pass
    return out


def _entities(record: dict, role: str) -> list[dict]:
    """Every entity with this role, at any depth (registries nest the abuse contact inside the registrar)."""
    found = []
    for entity in record.get("entities", []) or []:
        if role in (entity.get("roles") or []):
            found.append(entity)
        found += _entities(entity, role)
    return found


def _event(record: dict, action: str) -> str | None:
    for event in record.get("events", []) or []:
        if event.get("eventAction") == action and event.get("eventDate"):
            return str(event["eventDate"])[:10]
    return None


def registrar_facts(record: dict | None) -> dict:
    if not record:
        return {}
    facts: dict = {"registered": _event(record, "registration"), "expires": _event(record, "expiration"),
                   "nameservers": sorted({str(ns.get("ldhName", "")).lower() for ns in record.get("nameservers", []) or []
                                          if ns.get("ldhName")}),
                   "status": list(record.get("status", []) or [])[:6]}
    registrars = _entities(record, "registrar")
    if registrars:
        reg = registrars[0]
        facts["registrar"] = _vcard(reg).get("name")
        for pid in reg.get("publicIds", []) or []:
            if "IANA" in str(pid.get("type", "")):
                facts["iana_id"] = str(pid.get("identifier"))
        abuse = _entities(reg, "abuse")
        contact = _vcard(abuse[0]) if abuse else {}
        facts["abuse_email"], facts["abuse_phone"] = contact.get("email"), contact.get("phone")
    if not facts.get("abuse_email"):  # some registries list the abuse contact at the top level
        top = _entities(record, "abuse")
        if top:
            contact = _vcard(top[0])
            facts["abuse_email"] = contact.get("email")
            facts["abuse_phone"] = facts.get("abuse_phone") or contact.get("phone")
    return {k: v for k, v in facts.items() if v not in (None, [], "")}


def network_facts(record: dict | None) -> dict:
    if not record:
        return {}
    facts: dict = {"network": record.get("name"), "country": record.get("country"),
                   "range": " – ".join(x for x in (record.get("startAddress"), record.get("endAddress")) if x) or None}
    owners = _entities(record, "registrant") or _entities(record, "administrative")
    if owners:
        facts["organisation"] = _vcard(owners[0]).get("name")
    abuse = _entities(record, "abuse")
    if abuse:
        contact = _vcard(abuse[0])
        facts["abuse_email"], facts["abuse_phone"] = contact.get("email"), contact.get("phone")
    return {k: v for k, v in facts.items() if v not in (None, [], "")}


def _ip(host: str) -> str | None:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        return None
    v4 = [i for i in infos if i[0] == socket.AF_INET]
    return (v4 or infos)[0][4][0] if infos else None


def _risk(score: int) -> str:
    return "high" if score >= HIGH else "medium" if score >= MEDIUM else "low"


# --- Draft requests ------------------------------------------------------------------------------

_FINDING_EN = {
    "threat_list": "it is listed by Google Safe Browsing",
    "brand_on_page": "the page presents itself as {brand} on a domain that is not theirs",
    "brand_with_form": "it asks for personal or payment details under {brand}'s name",
    "new_domain": "the domain was registered {age} days ago",
    "young_domain": "the domain was registered {age} days ago",
    "card_form": "it asks for a card number and security code",
    "otp_form": "it asks for the one-time verification code sent to the victim's phone",
    "password_form": "it asks for a password",
    "offsite_form": "its form sends what is typed to another domain",
    "bad_certificate": "its TLS certificate is invalid",
    "cross_domain_redirect": "the link redirects to a different domain",
    "free_host": "it is hosted on a free website builder",
    "ai_high": "an AI reading of the page judged it a phishing site",
    "ai_medium": "an AI reading of the page found it suspicious",
}


# English names for the brand keys in urls.py and sitecheck.py, for the letters.
BRAND_EN = {
    "emiratespost": "Emirates Post", "aramex": "Aramex", "dhl": "DHL", "fedex": "FedEx", "dubaipolice": "Dubai Police",
    "adpolice": "Abu Dhabi Police", "ecrime": "the UAE eCrime platform", "icp": "the Federal Authority for Identity (ICP)",
    "uaepass": "UAE PASS", "moi": "the UAE Ministry of Interior", "etisalat": "e& (Etisalat)", "salik": "Salik",
    "rta": "Dubai RTA", "dewa": "DEWA", "emiratesnbd": "Emirates NBD", "adcb": "ADCB (Abu Dhabi Commercial Bank)",
    "bankfab": "First Abu Dhabi Bank", "mashreq": "Mashreq Bank", "amazon": "Amazon", "noon": "noon",
    "microsoft": "Microsoft", "apple": "Apple", "paypal": "PayPal", "netflix": "Netflix", "att": "AT&T",
    "docusign": "DocuSign", "adobe": "Adobe", "google": "Google",
    "falconbank": "Falcon National Bank (a fictional bank used in Haris's demo)",
}


def _brand_en(site: dict) -> str:
    names = [BRAND_EN.get(b, b) for b in site.get("brands", [])]
    if not names and (site.get("ai") or {}).get("impersonates"):
        names = [site["ai"]["impersonates"]]
    return ", ".join(names) or "a known organisation"


def _iso(text) -> str:
    """Keep a Latin value (address, date, hash) in one left-to-right piece inside Arabic text."""
    return f"\u2066{text}\u2069"


def _findings_en(site: dict) -> list[str]:
    brand = _brand_en(site)
    age = site.get("domain_age_days")
    out = []
    for flag in site.get("flags", []):
        if flag in _FINDING_EN:
            out.append(_FINDING_EN[flag].format(brand=brand, age=age if age is not None else "few"))
    return out


def drafts(ev: dict) -> dict:
    site, dom, net = ev["site"], ev["domain"], ev["hosting"]
    when = ev["checked_at"].replace("T", " ")[:16] + " UTC"
    facts = "\n".join(f"  - {f}" for f in _findings_en(site)) or "  - (see the attached findings)"
    chain = " -> ".join([ev["url"]] + [f"https://{h}" for h in site.get("redirects", []) if h]) if site.get("redirects") else ev["url"]
    common = (f"Address: {ev['url']}\n"
              + (f"Ends at: {site['final_url']}\nRedirect chain: {chain}\n" if site.get("final_url") != ev["url"] else "")
              + f"Checked: {when}, by Haris, an automated fraud-check assistant\n"
              + (f"Server address: {net['ip']}\n" if net.get("ip") else "")
              + (f"Page SHA-256 at the time of the check: {site['sha256']}\n" if site.get("sha256") else "")
              + f"\nWhat the check found:\n{facts}\n")
    sign = "\n[Officer's name]\n[Authority's name]\n[Phone and e-mail for follow-up]\n"
    out = {}
    if dom.get("abuse_email") or dom.get("registrar"):
        out["registrar"] = {
            "to": dom.get("abuse_email"),
            "subject": f"Phishing site on {ev['registrable']}: request to suspend the domain",
            "body": (f"Dear {dom.get('registrar') or 'registrar'} abuse team,\n\n"
                     f"The domain {ev['registrable']}, registered through you, is being used for a phishing site "
                     "that targets people in the United Arab Emirates. We ask you to suspend it under your "
                     "abuse policy.\n\n" + common + sign),
        }
    if net.get("abuse_email") or net.get("organisation") or ev.get("free_host"):
        provider = ev.get("free_host") or net.get("organisation") or net.get("network") or "hosting provider"
        out["hosting"] = {
            "to": net.get("abuse_email"),
            "subject": f"Phishing page hosted on your service: {site.get('final_domain') or ev['registrable']}",
            "body": (f"Dear {provider} abuse team,\n\n"
                     "A page on your service is being used for phishing that targets people in the United Arab "
                     "Emirates. We ask you to take it down.\n\n" + common + sign),
        }
    labels_ar = "\n".join(f"  - {x}" for x in site.get("flag_labels", [])) or "  - (انظر النتائج المرفقة)"
    out["block_ar"] = {
        "to": None,
        "subject": f"طلب حجب موقع احتيالي داخل الدولة: {_iso(site.get('final_domain') or ev['registrable'])}",
        "body": ("إلى: الجهة المختصة بحجب المواقع داخل الدولة (هيئة تنظيم الاتصالات والحكومة الرقمية)\n\n"
                 "نرجو حجب الموقع التالي لدى مزوّدي خدمة الإنترنت في الدولة، لاستخدامه في الاحتيال على الجمهور.\n\n"
                 f"العنوان: {_iso(ev['url'])}\n"
                 + (f"ينتهي إلى: {_iso(site['final_url'])}\n" if site.get("final_url") != ev["url"] else "")
                 + f"وقت الفحص: {_iso(when)}\n"
                 + (f"عنوان الخادم: {_iso(net['ip'])}\n" if net.get("ip") else "")
                 + (f"بصمة الصفحة (SHA-256): {_iso(site['sha256'])}\n" if site.get("sha256") else "")
                 + f"\nما وجده الفحص:\n{labels_ar}\n\n[اسم الضابط]\n[اسم الجهة]\n[رقم المتابعة]\n"),
    }
    return out


# --- Putting it together -----------------------------------------------------------------------------

def build(url: str) -> dict:
    """The whole evidence file for one address. Visits the site (or reuses a visit from the last hour)."""
    site = sitecheck.inspect(url, "ar")
    site = dict(site, flag_labels=[t(SITE_FLAGS, f, "ar") for f in site["flags"]])
    host = site.get("final_domain") or (urlsplit(site["url"]).hostname or "")
    registrable = sitecheck.registrable(host) if host else ""
    refused = (site.get("error") or "").startswith("refused")
    free = next((h for h in sitecheck.FREE_HOSTS if host.endswith("." + h)), None)

    dom = {} if refused or not registrable or sitecheck._is_ip(host) else registrar_facts(_rdap(f"domain/{registrable}"))
    ip = None if refused else (host if sitecheck._is_ip(host) else _ip(host))
    net = network_facts(_rdap(f"ip/{ip}")) if ip else {}
    if ip:
        net["ip"] = ip

    notes = []
    if not site.get("reachable"):
        notes.append("الموقع لا يستجيب الآن. قد يكون أُزيل، أو يحجب الزيارات من خوادم السحابة. بيانات التسجيل والاستضافة ما زالت صالحة لطلب الإزالة.")
    if free:
        notes.append(f"الصفحة على منصة مجانية ({free}): مالك النطاق هو المنصة نفسها، فطلب الإزالة يُوجَّه إلى المنصة عبر نموذج الإبلاغ عن الإساءة لديها، لا إلى مسجّل النطاق.")
    if host.endswith(".ae"):
        notes.append("نطاق إماراتي (.ae): يمكن طلب تعليقه أيضاً عبر إدارة نطاق .ae لدى هيئة تنظيم الاتصالات والحكومة الرقمية.")
    if not dom.get("abuse_email"):
        notes.append("لم يُعثر على بريد الإبلاغ لدى المسجّل في سجل RDAP؛ يُترك فارغاً ولا يُخمَّن.")
    if "falconbank" in site.get("brands", []):
        notes.append("هذا موقع التدريب في «حارس» (بنك خيالي). لا تُرسَل هذه المسودات.")

    ev = {
        "url": site["url"],
        "registrable": registrable,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "risk": _risk(site.get("score", 0)),
        "site": {k: site.get(k) for k in ("final_url", "final_domain", "reachable", "status", "redirects", "title",
                                         "domain_age_days", "cert_age_days", "flags", "flag_labels", "brands", "ai",
                                         "score", "sha256", "error")},
        "domain": dom,
        "hosting": net,
        "free_host": free,
        "notes": notes,
    }
    ev["drafts"] = drafts(ev)
    return ev
