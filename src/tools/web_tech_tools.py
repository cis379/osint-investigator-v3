"""Web-technology / tracker-ID fingerprinting — the ACTIVE-collection extractor (G14).

`web_tech_fingerprint` fetches a target's page source and extracts embedded third-party
tracker / analytics / ownership IDs (Google Analytics, AdSense, Meta Pixel, Salesforce,
Yandex, etc.) plus a favicon hash. A shared tracker ID is an *independent corroborator* of
common ownership — the thing that shared hosting alone can never prove (see the anti-over-
merge doctrine). The supervisor tiers these; the red team uses them to adjudicate merges.

OPSEC posture (this tool actively touches the TARGET's own infrastructure):
  - **Passive-first, auto-escalate to live.** It first tries a Wayback snapshot (zero touch on
    the live host). Only if passive yields no IDs does it do a single live GET.
  - **Minimal footprint when live:** one GET for HTML (+ at most one for /favicon.ico), a plain
    browser User-Agent (never a tool/org string), short timeout, NO crawling/link-following,
    no retry loop.
  - **Proxy seam:** set env `OSINT_PROXY` (e.g. socks5h://127.0.0.1:9050) to route fetches
    through a proxy; unset today, wired for a future Tor/egress proxy without touching call sites.

It logs raw and returns entities only — it NEVER writes the graph (raw/analysis split).
"""
import os
import re
import base64

import requests
from bs4 import BeautifulSoup

from .base import BaseTool, EntityFound

try:
    import mmh3  # favicon hashing (Shodan/FOFA method); optional — degrade if absent
except ImportError:  # pragma: no cover
    mmh3 = None

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Optional proxy seam (unset by default). socks5h://127.0.0.1:9050 for Tor, etc.
_PROXY = os.environ.get("OSINT_PROXY") or None
_PROXIES = {"http": _PROXY, "https": _PROXY} if _PROXY else None

# (id_kind, compiled regex, capture-group index, ownership_strength, requires-context substring)
# ownership_strength: strong = shared ID ~ common owner; medium = shared ID ~ shared
# account/agency/template (a lead, not proof); weak = copyable/template-level, note-only.
_SIGNATURES = [
    ("ga_universal", re.compile(r"\bUA-\d{4,10}-\d{1,4}\b"), 0, "strong", None),
    ("ga4", re.compile(r"(?:gtag\(\s*['\"]config['\"]\s*,\s*['\"]|googletagmanager\.com/gtag/js\?id=)(G-[A-Z0-9]{6,12})"), 1, "strong", None),
    ("ga4", re.compile(r"\b(G-[A-Z0-9]{8,10})\b"), 1, "medium", None),  # looser fallback
    ("gtm", re.compile(r"\bGTM-[A-Z0-9]{4,9}\b"), 0, "medium", None),
    ("google_ads", re.compile(r"\bAW-\d{9,12}\b"), 0, "medium", None),
    ("adsense", re.compile(r"\bca-pub-\d{16}\b"), 0, "strong", None),
    ("facebook_pixel", re.compile(r"fbq\(\s*['\"]init['\"]\s*,\s*['\"](\d{15,16})['\"]"), 1, "medium", None),
    ("facebook_pixel", re.compile(r"facebook\.com/tr\?id=(\d{15,16})"), 1, "medium", None),
    ("salesforce_org", re.compile(r"\b(00D[A-Za-z0-9]{12,15})\b"), 1, "medium", "salesforce"),
    ("yandex_metrica", re.compile(r"ym\(\s*(\d{6,9})\s*,"), 1, "strong", None),
    ("hotjar", re.compile(r"hjid\s*[:=]\s*['\"]?(\d{6,8})"), 1, "medium", None),
    ("ms_clarity", re.compile(r"clarity\.ms/tag/([a-z0-9]{8,12})"), 1, "medium", None),
    ("matomo", re.compile(r"setSiteId['\"]?\s*,\s*['\"]?(\d{1,6})"), 1, "strong", None),
    ("tiktok_pixel", re.compile(r"ttq\.load\(\s*['\"]([A-Z0-9]{18,24})['\"]"), 1, "medium", None),
    ("brevo", re.compile(r"client_key=([a-z0-9]{20,40})"), 1, "medium", None),
    ("recaptcha", re.compile(r"data-sitekey=['\"]([0-9A-Za-z_\-]{40})['\"]"), 1, "weak", None),
]

# strong/medium/weak -> a CONSERVATIVE raw tag. (Tools never set the final tier; the
# supervisor re-grades. We only hint: a strong shared-ID lead starts at "probable".)
_STRENGTH_TO_RAW = {"strong": "probable", "medium": "possible", "weak": "possible"}


class WebTechFingerprintTool(BaseTool):
    name = "web_tech_fingerprint"
    description = ("Active-collection extractor: fetch a domain/URL's page source and extract embedded "
                   "tracker/analytics/ownership IDs (GA/AdSense/Pixel/Salesforce/Yandex/...) + favicon hash. "
                   "Passive-first (Wayback) then a single minimal live GET. Shared IDs corroborate common ownership.")
    input_types = ["domain", "url"]
    output_types = ["tracker_id", "favicon_hash"]
    method = "library"
    TIMEOUT = 12

    # ---- fetch helpers -------------------------------------------------------
    def _target_url(self, selector, selector_type):
        s = selector.strip()
        if selector_type == "url" or re.match(r"^https?://", s, re.I):
            return s
        return "https://" + s.rstrip("/")

    def _fetch_passive(self, url):
        """Try the closest Wayback snapshot (zero touch on the live host). Returns
        (html, source_url) or (None, reason)."""
        try:
            avail = requests.get("http://archive.org/wayback/available",
                                 params={"url": url}, timeout=self.TIMEOUT,
                                 headers={"User-Agent": BROWSER_UA}, proxies=_PROXIES)
            snap = (avail.json().get("archived_snapshots") or {}).get("closest") or {}
            if not snap.get("available") or not snap.get("url"):
                return None, "no Wayback snapshot"
            # request the RAW archived original (the id_ modifier strips the toolbar)
            raw_url = re.sub(r"(/web/\d+)/", r"\1id_/", snap["url"], count=1)
            r = requests.get(raw_url, timeout=self.TIMEOUT,
                             headers={"User-Agent": BROWSER_UA}, proxies=_PROXIES)
            if r.status_code == 200 and r.text:
                return r.text, snap["url"]
            return None, f"Wayback snapshot HTTP {r.status_code}"
        except (requests.RequestException, ValueError) as e:
            return None, f"Wayback error: {e}"

    def _fetch_live(self, url):
        """A single minimal live GET of the target (footprint-aware). Returns
        (html, final_url) or (None, reason)."""
        try:
            r = requests.get(url, timeout=self.TIMEOUT, allow_redirects=True,
                             headers={"User-Agent": BROWSER_UA,
                                      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
                             proxies=_PROXIES)
            if not r.encoding or r.encoding.lower() == "iso-8859-1":
                r.encoding = r.apparent_encoding or r.encoding
            if r.text:
                return r.text, str(r.url)
            return None, f"live HTTP {r.status_code} (empty body)"
        except requests.RequestException as e:
            return None, f"live fetch error: {e}"

    def _favicon_hash(self, base_url, html):
        """Compute the Shodan/FOFA favicon hash (live fetch of the icon). Best-effort."""
        if mmh3 is None:
            return None, "mmh3 not installed"
        icon = "/favicon.ico"
        try:
            soup = BeautifulSoup(html, "html.parser")
            link = soup.find("link", rel=lambda v: v and "icon" in v.lower())
            if link and link.get("href"):
                icon = link["href"]
        except Exception:
            pass
        if icon.startswith("//"):
            icon_url = "https:" + icon
        elif icon.startswith("http"):
            icon_url = icon
        else:
            root = re.match(r"^(https?://[^/]+)", base_url)
            icon_url = (root.group(1) if root else base_url.rstrip("/")) + "/" + icon.lstrip("/")
        try:
            r = requests.get(icon_url, timeout=self.TIMEOUT,
                             headers={"User-Agent": BROWSER_UA}, proxies=_PROXIES)
            if r.status_code != 200 or not r.content:
                return None, f"favicon HTTP {r.status_code}"
            b64 = base64.encodebytes(r.content)  # RFC2045 newlines every 76 chars (REQUIRED)
            return mmh3.hash(b64), icon_url
        except requests.RequestException as e:
            return None, f"favicon error: {e}"

    # ---- extraction ----------------------------------------------------------
    def _extract_ids(self, html, source_label):
        low = html.lower()
        found, seen = [], set()
        for kind, rx, gi, strength, ctx in _SIGNATURES:
            if ctx and ctx not in low:
                continue
            for m in rx.finditer(html):
                raw_id = m.group(gi) if gi else m.group(0)
                key = (kind, raw_id)
                if not raw_id or key in seen:
                    continue
                seen.add(key)
                found.append(EntityFound(
                    value=raw_id, entity_type="tracker_id",
                    confidence=_STRENGTH_TO_RAW[strength],
                    source_citation=f"web_tech_fingerprint: {kind} {raw_id} in source ({source_label})",
                    metadata={"id_kind": kind, "ownership_strength": strength, "source": source_label}))
        return found

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"web_tech_fingerprint doesn't accept {selector_type}")
        url = self._target_url(selector, selector_type)

        # PASSIVE-FIRST: Wayback (zero live touch)
        html, src = self._fetch_passive(url)
        fetch_mode, source_label, passive_note = "passive_wayback", src, ""
        entities = self._extract_ids(html, f"wayback:{src}") if html else []

        # AUTO-ESCALATE to a single live GET if passive gave us nothing usable
        favicon_hash = favicon_url = None
        if not entities:
            passive_note = f"passive: {src if html else 'no IDs'} -> escalated to live"
            live_html, live_src = self._fetch_live(url)
            if live_html:
                fetch_mode, source_label = "live", live_src
                entities = self._extract_ids(live_html, f"live:{live_src}")
                favicon_hash, favicon_url = self._favicon_hash(live_src, live_html)
            elif not html:
                return self.make_result(selector, selector_type, f"target={url}", [], False,
                                        f"passive ({src}) and live ({live_src}) both failed")

        if favicon_hash is not None:
            entities.append(EntityFound(
                value=str(favicon_hash), entity_type="favicon_hash", confidence="possible",
                source_citation=f"web_tech_fingerprint: favicon mmh3 hash from {favicon_url}",
                metadata={"favicon_url": favicon_url, "source": source_label,
                          "pivot": f"Shodan http.favicon.hash:{favicon_hash} / FOFA icon_hash"}))

        id_lines = [f"  - {e.metadata['id_kind']}: {e.value} [{e.metadata['ownership_strength']}]"
                    for e in entities if e.entity_type == "tracker_id"]
        raw = (f"target={url}\nfetch_mode={fetch_mode}\nsource={source_label}\n"
               + (f"note={passive_note}\n" if passive_note else "")
               + f"tracker_ids_found={len(id_lines)}\n" + ("\n".join(id_lines) if id_lines else "  (none)")
               + (f"\nfavicon_hash={favicon_hash} ({favicon_url})" if favicon_hash is not None else ""))
        ok = bool(entities)
        return self.make_result(selector, selector_type, raw, entities, success=ok,
                                error="" if ok else "no tracker IDs or favicon extracted")


TOOLS = [WebTechFingerprintTool()]
