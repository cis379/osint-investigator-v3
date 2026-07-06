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
from .nethttp import http_get

DEFAULT_UA = "osint-investigator/3.0 (security research tool)"


class HttpTool(BaseTool):
    method = "api"  # availability = always "ready" (network checked at call time)

    def __init__(self, *, name, description, input_types, output_types, url,
                 http_method="GET", headers=None, user_agent=DEFAULT_UA,
                 auth_key=None, auth_header=None, auth_prefix="", key_required=False,
                 body=None, derive=None, extract=None, success_codes=(200,),
                 timeout=20):
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
        self._auth_prefix = auth_prefix  # e.g. "Bearer " for Authorization tokens
        self._key_required = key_required
        self._body = body
        self._derive = derive
        self._extract = extract
        self._success_codes = success_codes
        self._timeout = timeout

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
                headers[self._auth_header] = f"{self._auth_prefix}{key}"

        try:
            url = self._url.format(**vars_)
        except (KeyError, IndexError) as e:
            return self.make_result(selector, selector_type, "", [], False, f"url template error: {e}")

        try:
            if self._http_method == "POST":
                resp = requests.post(url, json=self._body, headers=headers, timeout=self._timeout)
            else:
                resp = http_get(url, headers=headers, timeout=self._timeout)  # retries transient failures
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))

        raw = resp.text[:8000]
        ok = resp.status_code in self._success_codes
        entities = []
        # B16 diagnostics: make an empty result honest about WHY it's empty.
        meta = {"http_status": resp.status_code, "response_bytes": len(resp.text)}
        if ok and self._extract:
            data = None
            try:
                data = resp.json()
            except ValueError:
                meta["parse_error"] = "response was not valid JSON"
            if data is not None:
                try:
                    entities = self._extract(selector, data) or []
                except Exception as e:
                    # A crashing extractor is a CODE BUG, not a clean 'no findings'. Surface it
                    # instead of swallowing to [] so it can't masquerade as an authoritative negative.
                    meta["extractor_error"] = f"{type(e).__name__}: {e}"
        meta["entities_extracted"] = len(entities)
        if ok and not entities and "extractor_error" not in meta and "parse_error" not in meta:
            meta["empty_reason"] = "source returned 2xx with no matching data (real negative)"
        return self.make_result(selector, selector_type, raw, entities,
                                success=ok, error="" if ok else f"HTTP {resp.status_code}",
                                metadata=meta)


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


# ---------------- arsenal additions (free) ----------------
def _ex_xposedornot(sel, d):
    out = []
    details = ((d.get("ExposedBreaches") or {}).get("breaches_details")) or []
    seen = set()
    for b in details[:25]:
        name, domain = b.get("breach"), b.get("domain")
        meta = {"breach": name, "breach_date": b.get("xposed_date"),
                "exposed_data": b.get("xposed_data"), "industry": b.get("industry"),
                "records": b.get("xposed_records")}
        cite = f"XposedOrNot breach: {name}"
        if domain and domain not in seen:
            seen.add(domain)
            out.append(_E(domain, "url", "probable", cite, meta))
        elif name:
            out.append(_E(name, "breach", "probable", cite, meta))
    if details:
        out.append(_E(sel, "email", "probable",
                      f"Email exposed in {len(details)} breach(es) per XposedOrNot",
                      {"breach_count": len(details)}))
    return out


_EDGAR_CIK_RE = re.compile(r"\s*\(CIK\s*(\d+)\)\s*$", re.I)
_EDGAR_TICKER_RE = re.compile(r"\s*\(([A-Z0-9.\-]{1,7}(?:,\s*[A-Z0-9.\-]{1,12})*)\)\s*$")


def _ex_edgar(sel, d):
    out, seen = [], set()
    for h in (((d.get("hits") or {}).get("hits")) or [])[:40]:
        s = h.get("_source", {}) or {}
        form, adsh, fdate = s.get("form", ""), s.get("adsh", ""), s.get("file_date", "")
        ciks = s.get("ciks") or []
        for raw in (s.get("display_names") or []):
            m = _EDGAR_CIK_RE.search(raw)
            cik = m.group(1) if m else (ciks[0] if ciks else None)
            name = _EDGAR_CIK_RE.sub("", raw).strip()
            tm = _EDGAR_TICKER_RE.search(name)
            if tm:
                name = _EDGAR_TICKER_RE.sub("", name).strip()
            if not name or (name.lower(), cik) in seen:
                continue
            seen.add((name.lower(), cik))
            out.append(_E(name, "company", "probable",
                          f"SEC EDGAR full-text: {form} {adsh} ({fdate})".strip(),
                          {"cik": cik, "form": form, "accession": adsh}))
    return out


def _ex_aleph(sel, d):
    out = []
    for it in (d.get("results") or [])[:10]:
        schema = it.get("schema") or ""
        props = it.get("properties", {}) or {}
        names = list(props.get("name") or [])
        if it.get("caption"):
            names = [it["caption"]] + [n for n in names if n != it["caption"]]
        etype = "name" if schema in ("Person", "LegalEntity") else "company"
        for nm in names[:3]:
            if nm:
                out.append(_E(nm, etype, "possible", f"OCCRP Aleph {schema} entity",
                              {"schema": schema, "aleph_id": it.get("id")}))
        for em in (props.get("email") or [])[:3]:
            if "@" in str(em):
                out.append(_E(em, "email", "probable", f"OCCRP Aleph {schema} email"))
    return out


def _split_parties(caption):
    if not caption:
        return []
    out = []
    for p in re.split(r"\s+v\.?\s+", caption, flags=re.IGNORECASE):
        p = re.sub(r"^(In re:?|Ex parte|United States ex rel\.)\s+", "", p.strip(" .,"),
                   flags=re.IGNORECASE).strip()
        if 2 <= len(p) <= 80 and not p.lower().startswith(("et al", "et. al")):
            out.append(p)
    return out


_CL_STOP = {"the", "inc", "llc", "ltd", "corp", "co", "company", "group", "and"}


def _cl_tokens(sel):
    """Significant (>=3 char, non-stopword) tokens of the seed for relevance gating."""
    return [t for t in re.split(r"\W+", (sel or "").lower()) if len(t) >= 3 and t not in _CL_STOP]


def _ex_courtlistener(sel, d):
    # B3 precision gate: CourtListener's BM25 is fuzzy and returns unrelated cases for
    # short names ("Robin", "Ruptly"). Only surface a case whose caption/full-name
    # actually contains ALL the seed's significant tokens — otherwise it's a fuzzy
    # false positive. A matched opinion is still only `probable` (could be a namesake),
    # never `confirmed` (we haven't proven it's OUR subject).
    toks = _cl_tokens(sel)
    sel_low = (sel or "").strip().lower()
    out = []
    for r in (d.get("results") or [])[:10]:
        cap = r.get("caseName") or r.get("caseNameFull") or ""
        full_name = (r.get("caseNameFull") or "") + " " + (cap or "")
        hay = full_name.lower()
        relevant = all(t in hay for t in toks) if toks else (sel_low in hay)
        if not relevant:
            continue
        au = r.get("absolute_url")
        if au:
            full = "https://www.courtlistener.com" + au if au.startswith("/") else au
            out.append(_E(full, "url", "probable",
                          f"CourtListener opinion (name-matched): {cap} ({r.get('court','')} {r.get('dateFiled','')})".strip(),
                          {"case_name": cap, "docket": r.get("docketNumber")}))
        for nm in _split_parties(cap):
            if sel_low not in nm.lower():
                out.append(_E(nm, "name", "possible", f"CourtListener case party: {cap}"))
    return out


# ---------------- Tier-1 tool specs (free / no key) ----------------
def _ex_disify(sel, d):
    # Surface the email verdict that was previously buried in raw (extract was None).
    if not isinstance(d, dict) or "format" not in d:
        return []
    disposable = bool(d.get("disposable"))
    cite = (f"disify: {'DISPOSABLE/throwaway address' if disposable else 'not disposable'}; "
            f"format={'valid' if d.get('format') else 'INVALID'}; mx={'yes' if d.get('dns') else 'no'}")
    return [_E(sel, "email", "possible", cite,
               {"disposable": disposable, "valid_format": bool(d.get("format")),
                "has_mx": bool(d.get("dns")), "free_provider": bool(d.get("free"))})]


def _ex_blockstream(sel, d):
    # Surface the BTC address activity verdict (extract was None).
    if not isinstance(d, dict):
        return []
    cs, ms = d.get("chain_stats") or {}, d.get("mempool_stats") or {}
    tx = (cs.get("tx_count") or 0) + (ms.get("tx_count") or 0)
    bal = (cs.get("funded_txo_sum") or 0) - (cs.get("spent_txo_sum") or 0)  # satoshis
    cite = (f"blockstream: {tx} tx, balance {bal/1e8:.8f} BTC" if tx
            else "blockstream: address has NO on-chain activity (0 tx)")
    return [_E(sel, "crypto_btc", "possible", cite,
               {"tx_count": tx, "balance_sat": bal, "balance_btc": bal / 1e8, "active": tx > 0})]


TOOLS = [
    HttpTool(name="rdap", description="RDAP domain registration (structured WHOIS)",
             input_types=["domain"], output_types=["domain", "company", "email"],
             url="https://rdap.org/domain/{selector}", extract=_ex_rdap, timeout=30),

    HttpTool(name="hudsonrock_email", description="Hudson Rock infostealer exposure for an email (free)",
             input_types=["email"], output_types=["email", "url"],
             url="https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={selector}",
             extract=_ex_hudson),

    HttpTool(name="disify", description="Email validity / disposable / MX check (free)",
             input_types=["email"], output_types=["email"],
             url="https://www.disify.com/api/email/{selector}", extract=_ex_disify),

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
             input_types=["crypto_btc"], output_types=["crypto_btc"],
             url="https://blockstream.info/api/address/{selector}", extract=_ex_blockstream),

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

    # --- arsenal additions (free) ---
    HttpTool(name="xposedornot_email", description="XposedOrNot: data breaches an email appears in (free, no key)",
             input_types=["email"], output_types=["url", "breach", "email"],
             url="https://api.xposedornot.com/v1/breach-analytics?email={selector}",
             extract=_ex_xposedornot, success_codes=(200, 404)),

    HttpTool(name="sec_edgar_fts", description="SEC EDGAR full-text search: company name -> filers (CIK/form). Free, needs UA.",
             input_types=["company"], output_types=["company", "name"],
             url='https://efts.sec.gov/LATEST/search-index?q=%22{selector}%22',
             user_agent="osint-investigator research research@example.com", extract=_ex_edgar),

    HttpTool(name="aleph_occrp", description="OCCRP Aleph entity search: name/company -> leaked/corporate records (free public search)",
             input_types=["name", "company"], output_types=["name", "company", "email"],
             url="https://aleph.occrp.org/api/2/entities?q={selector}&limit=10&filter:schemata=Thing",
             auth_key="ALEPH_API_KEY", auth_header="Authorization", key_required=False, extract=_ex_aleph),

    HttpTool(name="courtlistener_search", description="CourtListener: US court opinions mentioning a name/company (free; optional token)",
             input_types=["name", "company"], output_types=["url", "name"],
             url="https://www.courtlistener.com/api/rest/v4/search/?q={selector}&type=o",
             auth_key="COURTLISTENER_API_TOKEN", auth_header="Authorization", key_required=False,
             extract=_ex_courtlistener),
]
