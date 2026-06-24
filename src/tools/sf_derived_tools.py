"""SpiderFoot-derived tools (free, no key) — capabilities ported from SpiderFoot's
module set (github.com/smicallef/spiderfoot, MIT-licensed) into our declarative
framework. We lift the *technique/endpoint*, not the engine: each tool fetches raw
and the supervisor still tiers + graphs (raw/analysis split preserved).

Tools here:
- certspotter   : domain -> CT-logged certificate ISSUANCE HISTORY + subdomains
                  (Cert Spotter API). Fills the cert-history gap (G2) and adds
                  passive subdomain breadth without the crt.sh timeout.
- robtex_ip     : ip_v4 -> passive-DNS co-hosted domains (Robtex free API). A second
                  reverse-IP source alongside the quota-limited HackerTarget (G1).
- cloud_buckets : domain/company/keyword -> exposed S3 / GCS object-storage buckets
                  (name permutation + existence probe). New attack-surface capability.
- pgp_keyserver : email -> alternate emails / real name on the same PGP key
                  (keys.openpgp.org machine-readable index). Email<->identity pivot (G4).

NOTE: MIT covers SpiderFoot's code; each upstream data source's own ToS still governs use.
"""
import re
import concurrent.futures
from urllib.parse import unquote

import requests

from .base import BaseTool, EntityFound
from .http_tools import HttpTool, _E
from .nethttp import http_get

DEFAULT_UA = "osint-investigator/3.0 (security research tool)"


# ============================ certspotter (HttpTool) ============================
def _ex_certspotter(sel, data):
    """Cert Spotter /v1/issuances returns a LIST of issuance objects. Emit unique
    SAN hostnames as subdomains, plus one seed entity carrying the cert HISTORY
    (issuers, date range, fingerprints) so the supervisor can correlate shared certs."""
    if not isinstance(data, list):
        return []
    seed = (sel or "").strip().lower().lstrip("*.")
    out, seen = [], set()
    issuances = []
    for item in data:
        if not isinstance(item, dict):
            continue
        issr = item.get("issuer")
        issr_name = issr.get("name") if isinstance(issr, dict) else (issr or "")
        issuances.append({
            "not_before": item.get("not_before"), "not_after": item.get("not_after"),
            "issuer": issr_name, "tbs_sha256": item.get("tbs_sha256"),
            "pubkey_sha256": item.get("pubkey_sha256"),
            "dns_names": item.get("dns_names", []),
        })
        for dn in item.get("dns_names", []) or []:
            bare = str(dn).strip().lower().lstrip("*.")
            if not bare or bare == seed or bare in seen:
                continue
            seen.add(bare)
            out.append(_E(bare, "domain", "probable",
                          f"certspotter: CT-logged cert SAN (issuer {issr_name})",
                          {"seed": seed, "san_raw": dn, "wildcard": str(dn).startswith("*.")}))
    if issuances:
        nb = sorted(i["not_before"] for i in issuances if i.get("not_before"))
        na = sorted(i["not_after"] for i in issuances if i.get("not_after"))
        issuers = sorted({i["issuer"] for i in issuances if i.get("issuer")})
        out.append(_E(seed, "domain", "confirmed",
                      f"certspotter: {len(issuances)} CT-logged issuance(s)",
                      {"issuance_count": len(issuances),
                       "first_seen": nb[0] if nb else None,
                       "last_expires": na[-1] if na else None,
                       "issuers": issuers,
                       # recent fingerprints let the supervisor correlate SHARED certs
                       # across domains (cert-history correlation, gap G2)
                       "recent_issuances": issuances[:10]}))
    return out[:300]


certspotter = HttpTool(
    name="certspotter",
    description="Cert Spotter: CT-logged certificate ISSUANCE HISTORY + subdomains for a "
                "domain (free, rate-limited; optional CERTSPOTTER_API_KEY raises the limit). "
                "Cert-history correlation + passive subdomains.",
    input_types=["domain"], output_types=["domain"],
    url="https://api.certspotter.com/v1/issuances?domain={selector}"
        "&include_subdomains=true&expand=dns_names&expand=issuer",
    # B10: free tier is rate-limited; send a Bearer token when one is configured (graceful — works keyless).
    auth_key="CERTSPOTTER_API_KEY", auth_header="Authorization", auth_prefix="Bearer ",
    key_required=False, extract=_ex_certspotter, timeout=30)


# ============================ robtex_ip (HttpTool) ============================
_RBX_HOST_RE = re.compile(r"^(?:[A-Za-z0-9_](?:[A-Za-z0-9_\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")


def _ex_robtex_ip(sel, data):
    """Robtex ipquery returns passive-DNS records under 'pas' (and act/pash/acth).
    Emit each co-hosted host as a domain (reverse-IP / passive DNS)."""
    if not isinstance(data, dict):
        return []
    out, seen = [], set()
    for key in ("pas", "act", "pash", "acth"):
        for rec in data.get(key, []) or []:
            host = (rec.get("o") if isinstance(rec, dict) else None)
            if not host:
                continue
            host = str(host).strip().rstrip(".").lower()
            if host in seen or not _RBX_HOST_RE.match(host):
                continue
            seen.add(host)
            out.append(_E(host, "domain", "probable",
                          f"robtex: passive-DNS host on {sel}",
                          {"shared_ip": sel, "source": key}))
            if len(out) >= 100:
                return out
    return out


robtex_ip = HttpTool(
    name="robtex_ip",
    description="Robtex passive-DNS: domains co-hosted / historically resolved on an IPv4 "
                "(free, no key). Second reverse-IP source alongside HackerTarget.",
    input_types=["ip_v4"], output_types=["domain"],
    url="https://freeapi.robtex.com/ipquery/{selector}", extract=_ex_robtex_ip, timeout=25)


# ============================ cloud_buckets (custom) ============================
class CloudBucketsTool(BaseTool):
    """Permute likely bucket names from a domain/company/keyword and probe AWS S3,
    Google Cloud Storage, Azure Blob, and DigitalOcean Spaces for existence/exposure.
    Path-style S3 is used to avoid the SSL hostname mismatch on dotted bucket names.
    (Ported from SpiderFoot's sfp_s3bucket / sfp_googleobjectstorage /
    sfp_azureblobstorage / sfp_digitaloceanspace technique.)"""
    name = "cloud_buckets"
    description = ("Discover exposed AWS S3 / Google Cloud Storage / Azure Blob / DigitalOcean "
                   "Spaces buckets by permuting names from a domain/company/keyword and probing "
                   "existence (free, no key).")
    input_types = ["domain", "company", "keyword", "url"]
    output_types = ["url"]
    method = "api"

    SUFFIXES = ["", "prod", "production", "dev", "staging", "test", "backup", "backups",
                "assets", "media", "static", "data", "files", "uploads", "public",
                "private", "logs", "cdn", "images", "archive", "storage", "app", "internal"]
    MAX_CANDIDATES = 40
    DO_REGIONS = ["nyc3", "ams3"]   # most common DigitalOcean Spaces regions
    TIMEOUT = 8

    def _bases(self, selector, selector_type):
        s = (selector or "").strip().lower()
        bases = []
        if selector_type in ("domain", "url"):
            host = s.split("://")[-1].split("/")[0].split(":")[0]
            labels = [l for l in host.split(".") if l and l != "www"]
            full = ".".join(labels)
            if full:
                bases.append(full)            # full domain as bucket name (e.g. flaws.cloud)
            if len(labels) >= 2:
                bases.append(labels[-2])      # registrable label (e.g. flaws)
            elif labels:
                bases.append(labels[0])
            bases.append("".join(labels[:-1]) if len(labels) >= 2 else "".join(labels))
        else:
            bases.append(re.sub(r"[^a-z0-9]+", "", s))
            bases.append(re.sub(r"[^a-z0-9]+", "-", s).strip("-"))
        out = []
        for b in bases:
            if b and len(b) >= 3 and b not in out:
                out.append(b)
        return out

    def _candidates(self, bases):
        cands = []
        for base in bases:
            for suf in self.SUFFIXES:
                name = base if not suf else f"{base}-{suf}"
                if name not in cands:
                    cands.append(name)
        return cands[:self.MAX_CANDIDATES]

    PROVIDER_LABELS = {"s3": "AWS S3", "gcs": "Google Cloud Storage",
                       "azure": "Azure Blob", "do": "DigitalOcean Spaces"}

    @staticmethod
    def _s3compat_state(sc, body):
        """Existence state for an S3-compatible endpoint (S3 / GCS / DO Spaces)."""
        if sc == 200:
            return "listable"
        if sc == 403 or "AccessDenied" in body:
            return "exists_private"
        if sc in (301, 307) or "PermanentRedirect" in body:
            return "exists_other_region"
        return None  # 404 NoSuchBucket / 400 invalid = absent

    def _targets(self, candidates, bases):
        """Flat list of (provider, label, url) probes. S3+GCS for every candidate;
        Azure + DigitalOcean bounded to the BASE names (Azure account names can't carry
        hyphens; keeps request count + false-positive noise down)."""
        targets = []
        for name in candidates:
            targets.append(("s3", name, f"https://s3.amazonaws.com/{name}?max-keys=1"))
            targets.append(("gcs", name, f"https://storage.googleapis.com/{name}?max-keys=1"))
        for base in bases:
            alnum = re.sub(r"[^a-z0-9]", "", base)
            if 3 <= len(alnum) <= 24:  # Azure storage-account naming rules
                targets.append(("azure", alnum,
                                f"https://{alnum}.blob.core.windows.net/?comp=list"))
            for region in self.DO_REGIONS:
                targets.append(("do", f"{base} ({region})",
                                f"https://{base}.{region}.digitaloceanspaces.com/?max-keys=1"))
        return targets

    def _probe_target(self, target):
        provider, label, url = target
        try:
            r = requests.get(url, timeout=self.TIMEOUT, headers={"User-Agent": DEFAULT_UA})
        except requests.RequestException:
            return None  # DNS/conn failure (incl. Azure NXDOMAIN) = absent
        sc, body = r.status_code, (r.text or "")[:300]
        if provider == "azure":
            # the host resolving means the storage ACCOUNT exists; 200 = public listing.
            state = "listable" if sc == 200 else (
                "exists_account" if sc in (400, 403, 404, 409) else None)
        else:
            state = self._s3compat_state(sc, body)
        return (provider, label, url.split("?")[0], sc, state) if state else None

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"cloud_buckets doesn't accept {selector_type}")
        bases = self._bases(selector, selector_type)
        if not bases:
            return self.make_result(selector, selector_type, "", [], False,
                                    "could not derive a bucket base name from selector")
        candidates = self._candidates(bases)
        targets = self._targets(candidates, bases)

        hits = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for res in ex.map(self._probe_target, targets):
                if res:
                    hits.append(res)

        entities = []
        for provider, label, url, sc, state in hits:
            conf = "probable" if state == "listable" else "possible"
            entities.append(EntityFound(
                value=url, entity_type="url", confidence=conf,
                source_citation=f"cloud_buckets: {self.PROVIDER_LABELS[provider]} {state} (HTTP {sc})",
                metadata={"provider": provider, "status": sc, "state": state,
                          "listable": state == "listable", "candidate": label, "seed": selector}))

        raw = (f"bases={bases}\ncandidates={len(candidates)} · targets_probed={len(targets)} "
               f"(S3+GCS per candidate; Azure+DO[{','.join(self.DO_REGIONS)}] on bases)\n"
               f"buckets_found={len(hits)}\n" +
               "\n".join(f"  [{st}] HTTP {sc} {self.PROVIDER_LABELS[prov]}: {url}"
                         for prov, lbl, url, sc, st in hits) +
               ("" if hits else "  (no existing buckets matched the permutations)"))
        return self.make_result(selector, selector_type, raw, entities, success=True)


# ============================ pgp_keyserver (custom) ============================
class PgpKeyserverTool(BaseTool):
    """Query keys.openpgp.org's machine-readable index for an email: confirms a PGP
    key exists and surfaces ALTERNATE emails / real name carried by that key's UIDs
    (an email<->identity pivot). (Ported from SpiderFoot's sfp_pgp technique.)"""
    name = "pgp_keyserver"
    description = ("PGP keyserver (keys.openpgp.org): email -> linked alternate emails / real "
                   "name on the same key + key fingerprint (free, no key).")
    input_types = ["email"]
    output_types = ["email", "name"]
    method = "api"
    TIMEOUT = 20

    _UID_RE = re.compile(r"^uid:(.*?):", re.I)
    _PUB_RE = re.compile(r"^pub:([0-9A-Fa-f]+):", re.I)
    _NAME_EMAIL_RE = re.compile(r"^(.*?)\s*<([^>]+)>\s*$")
    _EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

    def query(self, selector, selector_type):
        if selector_type != "email":
            return self.make_result(selector, selector_type, "", [], False,
                                    "pgp_keyserver only accepts email")
        sel = (selector or "").strip().lower()
        url = f"https://keys.openpgp.org/pks/lookup?op=index&options=mr&search={selector}"
        try:
            resp = http_get(url, timeout=self.TIMEOUT, headers={"User-Agent": DEFAULT_UA})
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))

        body = resp.text or ""
        if resp.status_code == 404 or body.lower().startswith("no key found"):
            return self.make_result(selector, selector_type, body[:500], [], True,
                                    "")  # success: a definitive "no PGP key" answer
        if resp.status_code != 200:
            return self.make_result(selector, selector_type, body[:500], [], False,
                                    f"HTTP {resp.status_code}")

        out, seen = [], set()
        fingerprints = [m.group(1) for ln in body.splitlines()
                        for m in [self._PUB_RE.match(ln)] if m]
        for ln in body.splitlines():
            m = self._UID_RE.match(ln)
            if not m:
                continue
            uid = unquote(m.group(1)).strip()
            if not uid:
                continue
            nm = self._NAME_EMAIL_RE.match(uid)
            name = email = None
            if nm:
                name, email = nm.group(1).strip(), nm.group(2).strip().lower()
            else:
                em = self._EMAIL_RE.search(uid)
                if em:
                    email = em.group(0).strip().lower()
                elif len(uid) <= 80:
                    name = uid
            if email and email != sel and ("email", email) not in seen:
                seen.add(("email", email))
                out.append(_E(email, "email", "probable",
                              "pgp_keyserver: alternate email on same PGP key",
                              {"linked_to": sel, "fingerprints": fingerprints}))
            if name and len(name) >= 3 and ("name", name.lower()) not in seen:
                seen.add(("name", name.lower()))
                out.append(_E(name, "name", "probable",
                              "pgp_keyserver: real name on PGP key UID",
                              {"linked_to": sel, "fingerprints": fingerprints}))
        return self.make_result(selector, selector_type, body[:2000], out, success=True)


TOOLS = [certspotter, robtex_ip, CloudBucketsTool(), PgpKeyserverTool()]
