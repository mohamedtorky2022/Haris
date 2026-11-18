"""Offline link analysis.

Each link is scored from what can be seen in the link itself, with no network
call: shorteners, raw IP addresses, look-alike brand names, risky top-level
domains and so on. Links on a known official domain are marked as such.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

URL_PATTERN = re.compile(
    r"(?:https?://[^\s<>\"']+)"
    r"|(?:www\.[^\s<>\"']+)"
    r"|(?:(?<![@\w.])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,12}/[^\s<>\"']*)"
    r"|(?:(?<![@\w.])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:com|net|org|ae|xyz|top|click|live|online|site|info|icu|shop|buzz|vip|cc|tk|ml|ga|cf|gq|link|app|me|co)\b)",
    re.IGNORECASE,
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "is.gd", "shorturl.at",
    "tiny.cc", "ow.ly", "buff.ly", "rebrand.ly", "t.ly", "s.id", "goo.su", "v.gd",
}

RISKY_TLDS = {
    "xyz", "top", "click", "live", "online", "site", "info", "icu", "shop", "buzz",
    "vip", "cc", "tk", "ml", "ga", "cf", "gq", "link", "rest", "cyou", "sbs", "cfd",
}

# Brands scammers impersonate in the UAE, with the domains they really use.
OFFICIAL_BRANDS: dict[str, tuple[str, ...]] = {
    "emiratespost": ("emiratespost.ae",),
    "aramex": ("aramex.com",),
    "dhl": ("dhl.com", "dhl.ae"),
    "fedex": ("fedex.com",),
    "dubaipolice": ("dubaipolice.gov.ae",),
    "adpolice": ("adpolice.gov.ae",),
    "ecrime": ("ecrime.ae", "ecrimehub.gov.ae"),
    "icp": ("icp.gov.ae",),
    "uaepass": ("uaepass.ae",),
    "moi": ("moi.gov.ae",),
    "etisalat": ("etisalat.ae", "eand.com"),
    "salik": ("salik.ae",),
    "rta": ("rta.ae",),
    "dewa": ("dewa.gov.ae",),
    "emiratesnbd": ("emiratesnbd.com",),
    "adcb": ("adcb.com",),
    "bankfab": ("bankfab.com",),
    "mashreq": ("mashreq.com", "mashreqbank.com"),
    "amazon": ("amazon.ae", "amazon.com"),
    "noon": ("noon.com",),
}

OFFICIAL_SUFFIXES = (".gov.ae",)
OFFICIAL_DOMAINS = {"u.ae", "www.u.ae"}  # the UAE government portal

FLAG_WEIGHTS = {
    "brand_lookalike": 40,
    "ip_host": 30,
    "at_symbol": 25,
    "punycode": 25,
    "risky_tld": 20,
    "shortener": 15,
    "many_hyphens": 10,
    "many_subdomains": 10,
    "no_https": 5,
}

_LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "4": "a", "7": "t"})


@dataclass
class LinkReport:
    url: str
    domain: str
    official: bool = False
    flags: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        if self.official:
            return 0
        return sum(FLAG_WEIGHTS[f] for f in self.flags)

    def safe_for_model(self) -> str:
        """The link without its query string, which may carry personal tokens."""
        return f"{self.domain}{urlsplit(self.url if '://' in self.url else 'http://' + self.url).path}"


def extract_urls(text: str) -> list[str]:
    seen: list[str] = []
    for match in URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(".,;:!?)]}،؟")
        if url and url not in seen:
            seen.append(url)
    return seen


def _is_official(domain: str) -> bool:
    if domain in OFFICIAL_DOMAINS or domain.endswith(OFFICIAL_SUFFIXES):
        return True
    return any(
        domain == official or domain.endswith("." + official)
        for officials in OFFICIAL_BRANDS.values()
        for official in officials
    )


def analyze_url(url: str) -> LinkReport:
    raw = url if "://" in url else "http://" + url
    parts = urlsplit(raw)
    domain = (parts.hostname or "").lower().rstrip(".")
    report = LinkReport(url=url, domain=domain)

    if _is_official(domain):
        report.official = True
        if parts.scheme == "http":
            report.flags.append("no_https")
        return report

    try:
        ipaddress.ip_address(domain)
        report.flags.append("ip_host")
    except ValueError:
        pass

    if "@" in (parts.netloc or ""):
        report.flags.append("at_symbol")
    if "xn--" in domain:
        report.flags.append("punycode")
    if domain in SHORTENERS:
        report.flags.append("shortener")

    labels = domain.split(".")
    if labels and labels[-1] in RISKY_TLDS:
        report.flags.append("risky_tld")
    if len(labels) > 4:
        report.flags.append("many_subdomains")
    if domain.count("-") >= 2:
        report.flags.append("many_hyphens")

    squashed = domain.replace("-", "").replace(".", "").translate(_LEET)
    if any(brand in squashed for brand in OFFICIAL_BRANDS):
        report.flags.append("brand_lookalike")

    if parts.scheme == "http" and "://" in url:
        report.flags.append("no_https")
    return report
