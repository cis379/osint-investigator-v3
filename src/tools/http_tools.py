"""Declarative HTTP tools — one generic runner, many tools defined as specs.

Each tool is an HttpTool(spec): a URL template (with {selector} and optional derived
vars), optional auth header (from credentials), and a small extractor that pulls
entities from the JSON response. The raw response is always logged for the supervisor;
extraction is best-effort (the supervisor re-analyzes raw per the doctrine). Wiring a
new HTTP tool = adding a spec here, no new class.

This is the Tier-1 batch (free / no key). Tier-2 (keyed) tools slot in the same way
with auth_key/auth_header set.
"""
import re
import requests

from .base import BaseTool, EntityFound
from .credentials import get_key

DEFAULT_UA = "osint-investigator/3.0 (security research tool)"


class HttpTool(BaseTool):
    method = "api"  # availability = always "ready" (network checked at call time)

    def __init__(self, *, name, description, input_types, output_types, url,
                 http_method="GET", headers=None, user_agent=DEFAULT_UA,
                 auth_key=None, auth_header=None, key_required=False,
                 body=None, derive=None, extract=None, success_codes=(200,)):
        self.name = name
        self.description = description
        self.input_types = input_types
        self.output_types = output_types
        self._url = url
        self._http_method = http_method
        self._headers = headers or {}
        self._user_agent = user_agent
        self._auth_key = auth_key
        self._auth_header = auth_header
        self._key_required = key_required
        self._body = body
        self._derive = derive
        self._extract = extract
        self._success_codes = success_codes

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"{self.name} doesn't accept {selector_type}")

        vars_ = {"selector": selector}
        if self._derive:
            try:
                vars_.update(self._derive(selector, selector_type) or {})
            except Exception as e:
                return self.make_result(selector, selector_type, "", [], False, f"input error: {e}")

        headers = dict(self._headers)
        if self._user_agent:
            headers.setdefault("User-Agent", self._user_agent)
        if self._auth_key:
            key = get_key(self._auth_key)
            if not key and self._key_required:
                return self.make_result(selector, selector_type, "", [], False,
                                        f"{self.name} needs {self._auth_key} in .env")
            if key and self._auth_header:
                headers[self._auth_header] = key

        try:
            url = self._url.format(**vars_)
        except (KeyError, IndexError) as e:
            return self.make_result(selector, selector_type, "", [], False, f"url template error: {e}")

        try:
            if self._http_method == "POST":
                resp = requests.post(url, json=self._body, headers=headers, timeout=20)
            else:
                resp = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))

        raw = resp.text[:8000]
        ok = resp.status_code in self._success_codes
        entities = []
        if ok and self._extract:
            try:
                data = resp.json()
            except ValueError:
                data = None
            if data is not None:
                try:
                    entities = self._extract(selector, data) or []
                except Exception:
                    entities = []  # extraction is best-effort; raw is always logged
        return self.make_result(selector, selector_type, raw, entities,
                                success=ok, error="" if ok else f"HTTP {resp.status_code}")


def _E(value, etype, conf, cite, meta=None):
    return EntityFound(value=str(value), entity_type=etype, confidence=conf,
                       source_citation=cite, metadata=meta or {})


# ---------------- extractors (best-effort, defensive) ----------------
def _ex_rdap(sel, d):
    out = []
    for ns in d.get("nameservers", []) or []:
        n = ns.get("ldhName")
        if n:
            out.append(_E(n.lower(), "domain", "confirmed", "RDAP nameserver"))
    for ent in d.get("entities", []) or []:
        roles = ent.get("roles", []) or []
        name = email = None
        v = ent.get("vcardArray")
        if v and len(v) > 1:
            for item in v[1]:
                if item and item[0] == "fn":
                    name = item[3]
                elif item and item[0] == "email":
                    email = item[3]
        if name and "registrar" in roles:
            out.append(_E(name, "company", "confirmed", "RDAP registrar"))
        if email:
            out.append(_E(email, "email", "probable", f"RDAP {','.join(roles)} email"))
    return out


def _ex_hudson(sel, d):
    out = []
    stealers = d.get("stealers", []) or []
    for s in stealers[:25]:
        for u in (s.get("top_logins") or [])[:10]:
            if "@" in str(u):
                out.append(_E(u, "email", "possible", "Hudson Rock stealer-log login"))
        for url in (s.get("top_passwords") or [])[:0]:  # don't surface passwords as entities
            pass
    return out


def _ex_greynoise(sel, d):
    out = []
    if d.get("name") and d.get("name") not in ("unknown", None):
        out.append(_E(d["name"], "company", "possible", f"GreyNoise actor/org ({d.get('classification','')})"))
    return out


def _ex_ripestat(sel, d):
    out = []
    data = d.get("data", {}) or {}
    for asn in data.get("asns", []) or []:
        out.append(_E(f"AS{asn}", "asn", "confirmed", "RIPEstat network-info"))
    return out


def _ex_bgpview(sel, d):
    out = []
    for p in (d.get("data", {}) or {}).get("prefixes", []) or []:
        asn = p.get("asn", {}) or {}
        if asn.get("asn"):
            out.append(_E(f"AS{asn['asn']}", "asn", "confirmed",
                          f"BGPView: {asn.get('name','')} - {asn.get('description','')}"))
    return out


def _ex_gleif(sel, d):
    out = []
    for rec in (d.get("data") or [])[:5]:
        lei = rec.get("id")
        ent = (rec.get("attributes", {}) or {}).get("entity", {}) or {}
        nm = (ent.get("legalName") or {}).get("name")
        if lei:
            out.append(_E(lei, "lei", "confirmed", "GLEIF LEI record", {"legal_name": nm}))
        if nm:
            out.append(_E(nm, "company", "confirmed", "GLEIF legal name"))
    return out


def _ex_github(sel, d):
    out = []
    if d.get("name"):
        out.append(_E(d["name"], "name", "probable", "GitHub profile display name"))
    if d.get("email"):
        out.append(_E(d["email"], "email", "confirmed", "GitHub public email"))
    if d.get("blog"):
        out.append(_E(d["blog"], "url", "probable", "GitHub profile blog/url"))
    if d.get("company"):
        out.append(_E(d["company"], "company", "possible", "GitHub profile company"))
    if d.get("html_url"):
        out.append(_E(d["html_url"], "url", "confirmed", "GitHub profile URL"))
    return out


def _ex_reddit(sel, d):
    data = d.get("data", {}) or {}
    nm = data.get("name")
    return [_E(f"https://www.reddit.com/user/{nm}", "url", "confirmed", "Reddit profile")] if nm else []


def _ex_nominatim(sel, d):
    dn = d.get("display_name")
    return [_E(dn, "location", "confirmed", "Nominatim reverse geocode")] if dn else []


def _derive_coords(sel, stype):
    parts = re.split(r"[,\s]+", sel.strip())
    if len(parts) < 2:
        raise ValueError("coordinates must be 'lat,lon'")
    return {"lat": parts[0], "lon": parts[1]}


# ---------------- Tier-1 tool specs (free / no key) ----------------
TOOLS = [
    HttpTool(name="rdap", description="RDAP domain registration (structured WHOIS)",
             input_types=["domain"], output_types=["domain", "company", "email"],
             url="https://rdap.org/domain/{selector}", extract=_ex_rdap),

    HttpTool(name="hudsonrock_email", description="Hudson Rock infostealer exposure for an email (free)",
             input_types=["email"], output_types=["email", "url"],
             url="https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={selector}",
             extract=_ex_hudson),

    HttpTool(name="disify", description="Email validity / disposable / MX check (free)",
             input_types=["email"], output_types=[],
             url="https://www.disify.com/api/email/{selector}", extract=None),

    HttpTool(name="greynoise_community", description="GreyNoise scanner-noise classification (free, low quota)",
             input_types=["ip_v4"], output_types=["company"],
             url="https://api.greynoise.io/v3/community/{selector}",
             extract=_ex_greynoise, success_codes=(200, 404)),

    HttpTool(name="ripestat_network", description="RIPEstat network-info: ASN(s) for an IP (free)",
             input_types=["ip_v4", "ip_v6"], output_types=["asn"],
             url="https://stat.ripe.net/data/network-info/data.json?resource={selector}",
             extract=_ex_ripestat),

    HttpTool(name="bgpview_ip", description="BGPView: prefixes/ASN for an IP (free)",
             input_types=["ip_v4"], output_types=["asn"],
             url="https://api.bgpview.io/ip/{selector}", extract=_ex_bgpview),

    HttpTool(name="blockstream_btc", description="Blockstream Esplora BTC address stats (free, no key)",
             input_types=["crypto_btc"], output_types=[],
             url="https://blockstream.info/api/address/{selector}", extract=None),

    HttpTool(name="gleif_lei", description="GLEIF: company legal entity (LEI) lookup (free)",
             input_types=["company"], output_types=["lei", "company"],
             url="https://api.gleif.org/api/v1/lei-records?filter%5Bentity.legalName%5D={selector}",
             extract=_ex_gleif),

    HttpTool(name="github_user", description="GitHub public profile (name/email/blog/company)",
             input_types=["username"], output_types=["name", "email", "url", "company"],
             url="https://api.github.com/users/{selector}", extract=_ex_github,
             success_codes=(200, 404)),

    HttpTool(name="reddit_about", description="Reddit public profile",
             input_types=["username"], output_types=["url"],
             url="https://www.reddit.com/user/{selector}/about.json",
             user_agent="osint-investigator/3 by u/researcher", extract=_ex_reddit,
             success_codes=(200, 404)),

    HttpTool(name="nominatim_reverse", description="Reverse geocode coordinates -> place (OpenStreetMap)",
             input_types=["coordinates"], output_types=["location"],
             url="https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
             derive=_derive_coords, extract=_ex_nominatim),
]
