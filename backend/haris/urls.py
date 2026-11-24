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
    "bitly.com", "bit.do", "cutt.us", "shorte.st", "adf.ly", "short.gy", "t2m.io", "qrco.de",
}

# Haris's own demo server, on a free host: its training page must look clean until it is visited.
OWN_HOSTS = {"haris-uae.onrender.com"}

# Free website builders, app hosts and public file storage: a scam page costs nothing there and is
# gone by the time anyone reports it. A page on one is not a scam by itself, so this weighs little.
FREE_HOSTS = (
    "square.site", "netlify.app", "vercel.app", "pages.dev", "workers.dev", "github.io", "gitlab.io",
    "web.app", "firebaseapp.com", "glitch.me", "replit.app", "repl.co", "onrender.com", "herokuapp.com",
    "wixsite.com", "weebly.com", "weeblysite.com", "webflow.io", "framer.website", "framer.app", "typedream.app",
    "godaddysites.com", "carrd.co", "blogspot.com", "sites.google.com", "notion.site", "gitbook.io",
    "000webhostapp.com", "wordpress.com", "ukit.me", "tilda.ws", "mystrikingly.com", "jimdosite.com",
    "r2.dev", "storage.googleapis.com", "firebasestorage.googleapis.com", "s3.amazonaws.com",
    "blob.core.windows.net", "web.core.windows.net", "ipfs.io", "dweb.link", "surge.sh", "fly.dev",
    "infinityfreeapp.com", "rf.gd", "epizy.com", "great-site.net", "kesug.com", "wuaze.com", "free.nf",
)

RISKY_TLDS = {
    "xyz", "top", "click", "live", "online", "site", "info", "icu", "shop", "buzz",
    "vip", "cc", "tk", "ml", "ga", "cf", "gq", "link", "rest", "cyou", "sbs", "cfd",
    # also among the most abused endings in Spamhaus's and Interisle's phishing reports
    "bond", "lat", "pw", "work", "fun", "qpon", "autos", "boats", "cam", "mov", "zip", "monster", "beauty", "mom", "lol",
}

_MS = ("microsoft.com", "microsoftonline.com", "live.com", "outlook.com", "office.com", "office365.com", "sharepoint.com",
       "onmicrosoft.com", "msn.com", "bing.com", "azure.com", "windows.net", "skype.com", "xbox.com", "hotmail.com")

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
    "etisalat": ("etisalat.ae", "eand.ae", "eand.com"),  # e& moved its UAE site to eand.ae
    "salik": ("salik.ae",),
    "rta": ("rta.ae",),
    "dewa": ("dewa.gov.ae",),
    "tamm": ("tamm.abudhabi",),  # Abu Dhabi's government services portal, where fines and fees are paid
    "emiratesnbd": ("emiratesnbd.com",),
    "adcb": ("adcb.com",),
    "bankfab": ("bankfab.com",),
    "mashreq": ("mashreq.com", "mashreqbank.com"),
    "amazon": ("amazon.ae", "amazon.com"),
    "noon": ("noon.com",),
    # Global brands phished everywhere, the UAE included.
    "paypal": ("paypal.com", "paypal.me", "paypalobjects.com"),
    "microsoft": _MS, "outlook": _MS, "office365": _MS, "hotmail": _MS,
    "apple": ("apple.com", "icloud.com", "apple.co"), "icloud": ("icloud.com", "apple.com"),
    "netflix": ("netflix.com", "netflix.net"),
    "facebook": ("facebook.com", "fb.com", "fbcdn.net", "meta.com", "messenger.com"),
    "instagram": ("instagram.com", "cdninstagram.com"),
    "whatsapp": ("whatsapp.com", "whatsapp.net", "wa.me"),
    "binance": ("binance.com",), "coinbase": ("coinbase.com",), "metamask": ("metamask.io",),
    # A fictional bank, used only by the training page /demo/falcon-bank.html. Its "official"
    # domain uses the reserved .example ending, so no real site can ever match it.
    "falconbank": ("falconbank.example",),
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
    "free_host": 20,
    "random_label": 10,
    "no_https": 5,
}

# Words glued to a short brand name in scam domains: «rtafines», «payicp», «dhlupdate».
_BAIT_WORDS = {"fine", "fines", "pay", "payment", "uae", "ae", "login", "secure", "update", "verify", "online",
               "portal", "service", "services", "app", "gov", "track", "tracking", "delivery", "redelivery", "bill",
               "id", "account", "accounts", "support", "signin", "help", "security", "alert", "wallet", "verification"}

# Brand names that are also everyday words or inside them (pineapple, outlookindia): matched only as a
# whole part of the name, or joined to a bait word, like the short ones.
_WORD_BRANDS = {"apple", "outlook", "hotmail", "icloud"}  # icloud: also inside hicloud (Huawei)

# The global brands' own infrastructure, which their apps and pages load from.
BRAND_INFRA = {
    "amazonaws.com", "amazonaws.com.cn", "media-amazon.com", "ssl-images-amazon.com", "amazon-adsystem.com",
    "amazontrust.com", "amazonvideo.com", "amazonalexa.com", "amazon.dev", "cloudfront.net",
    "apple-dns.net", "apple-dns.cn", "cdn-apple.com", "apple-cloudkit.com", "icloud-content.com", "apple.news",
    "microsoftpersonalcontent.com", "microsoftazuread-sso.com", "msftauth.net", "msauth.net", "office.net",
    "facebook.net", "fbsbx.com", "whatsapp.com", "paypal-objects.com",
}

# Brands that own their top-level domain (.apple, .microsoft, .amazon).
BRAND_TLDS = {"apple", "microsoft", "amazon", "google", "netflix"}

# Storage hosts that serve files straight from their own name (storage.googleapis.com/<bucket>/page.html).
STORAGE_HOSTS = {"storage.googleapis.com", "firebasestorage.googleapis.com", "s3.amazonaws.com", "ipfs.io", "dweb.link"}

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


def _own_country_site(domain: str) -> bool:
    """The brand's own site in another country: amazon.de, amazon.co.uk, icloud.com.cn, microsoft.us."""
    labels = domain.split(".")
    for n in (2, 3):
        if len(labels) >= n:
            name, rest = labels[-n], labels[-n + 1:]
            country = len(rest[-1]) == 2 and (len(rest) == 1 or rest[0] in {"co", "com"})
            if country and name in OFFICIAL_BRANDS and len(name) >= 5 and name not in ("emiratespost", "falconbank"):
                return True
    return False


def _is_official(domain: str) -> bool:
    if domain in OFFICIAL_DOMAINS or domain.endswith(OFFICIAL_SUFFIXES):
        return True
    labels = domain.split(".")
    if labels[-1] in BRAND_TLDS or any(domain == d or domain.endswith("." + d) for d in BRAND_INFRA):
        return True
    if _own_country_site(domain):
        return True
    return any(
        domain == official or domain.endswith("." + official)
        for officials in OFFICIAL_BRANDS.values()
        for official in officials
    )


def _looks_like_brand(domain: str) -> bool:
    """A brand name hidden in a domain that is not the brand's own.

    Long names (adcb, emiratespost, uaepass...) count anywhere in the squashed domain. Short ones
    (rta, icp, moi, dhl, noon, tamm) count only at the start or end of a label or hyphen-separated
    part, so «portal» or «tammy» is not read as RTA or TAMM.
    """
    leet = domain.translate(_LEET)
    squashed = leet.replace("-", "").replace(".", "")
    tokens = [t for t in re.split(r"[.\-]", leet) if t]
    for brand in OFFICIAL_BRANDS:
        if len(brand) >= 5 and brand not in _WORD_BRANDS:
            if brand in squashed:
                return True
        elif any(t == brand
                 or t.startswith(brand) and (not t[len(brand)].isalpha() or t[len(brand):] in _BAIT_WORDS)
                 or t.endswith(brand) and (not t[-len(brand) - 1].isalpha() or t[:-len(brand)] in _BAIT_WORDS)
                 for t in tokens):
            return True
    return False


def _homograph(domain: str) -> bool:
    """A look-alike Unicode name: Latin mixed with other letters, or Cyrillic/Greek letters that pass for Latin.

    A name written wholly in its own script (Arabic, Thai, Chinese) is an ordinary local domain.
    """
    for label in domain.split("."):
        if not label.startswith("xn--"):
            continue
        try:
            text = label.encode("ascii").decode("idna")
        except (UnicodeError, ValueError):
            return True
        letters = [c for c in text if c.isalpha()]
        latin = any(c.isascii() for c in letters)
        other = [c for c in letters if not c.isascii()]
        if latin and other:
            return True
        if other and all("\u0370" <= c <= "\u04ff" for c in other):  # Greek and Cyrillic
            return True
    return False


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
    if "xn--" in domain and _homograph(domain):
        report.flags.append("punycode")
    if domain in SHORTENERS:
        report.flags.append("shortener")

    labels = domain.split(".")
    if labels and labels[-1] in RISKY_TLDS:
        report.flags.append("risky_tld")
    if len(labels) > 4:
        report.flags.append("many_subdomains")
    if domain.replace("xn--", "").count("-") >= 2:
        report.flags.append("many_hyphens")

    if _looks_like_brand(domain):
        report.flags.append("brand_lookalike")
    if domain not in OWN_HOSTS and (domain in STORAGE_HOSTS or any(domain.endswith("." + h) for h in FREE_HOSTS)):
        report.flags.append("free_host")
    # A machine-made label (a storage bucket id, a throwaway name with many digits).
    if any(len(t) >= 16 and sum(c.isdigit() for c in t) >= 6 and not t.startswith("xn--") for t in labels[:-1]):
        report.flags.append("random_label")

    if parts.scheme == "http" and "://" in url:
        report.flags.append("no_https")
    return report
