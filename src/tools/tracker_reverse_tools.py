"""Tracker-ID REVERSE lookup (G14, second half) — ID -> other domains that embed it.

`tracker_reverse` takes a tracker_id (e.g. UA-12345678-1, ca-pub-..., a GA4 G-..., a Pixel
ID) and finds OTHER domains carrying the SAME id. A shared tracker ID is an *independent
corroborator* of common ownership — the evidence the anti-over-merge doctrine demands before
asserting two co-hosted sites share an operator.

This half cannot be built in-house (it needs a web-wide source-code index), so it WIRES free
external services and degrades gracefully:
  - **PublicWWW** free web results (source-code search; covers ANY id kind) — primary, no key.
  - **SpyOnWeb** API — secondary, only if env `SPYONWEB_API_KEY` is set (the service is also
    intermittently down; wrapped in try/except).
When everything is blocked/empty/keyless, it returns NO results plus a clear pointer to the
operator guide (guides/tracker-id-reverse-lookup.md) — it never fabricates matches.

Like the other collectors it logs raw + returns entities; it NEVER writes the graph.
"""
import os
import re

import requests
from bs4 import BeautifulSoup

from .base import BaseTool, EntityFound

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_PROXY = os.environ.get("OSINT_PROXY") or None
_PROXIES = {"http": _PROXY, "https": _PROXY} if _PROXY else None
_MAX = 100

_DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$", re.I)
# file extensions / non-TLD tokens that the OLD whole-page regex wrongly returned as "domains"
_BAD_TLDS = {"ico", "css", "js", "json", "xml", "html", "htm", "png", "jpg", "jpeg", "gif", "svg",
             "webp", "woff", "woff2", "ttf", "eot", "map", "min", "mp4", "webm", "pdf", "txt", "php"}
_BAD_HOSTS = ("publicwww.com", "w3.org", "googleapis.com", "gstatic.com", "schema.org")
# strong-ownership id kinds -> a shared hit is a probable common-owner lead; others stay weaker
_STRONG_PREFIXES = ("UA-", "ca-pub-", "G-", "AW-")


def _is_result_domain(host: str, seed_host: str | None = None) -> bool:
    """Strict: a real registrable domain, not an asset filename / JS token / page-chrome host."""
    if not host or not _DOMAIN_RE.match(host):
        return False
    if host.rsplit(".", 1)[-1] in _BAD_TLDS:
        return False
    if host.endswith(_BAD_HOSTS) or (seed_host and host == seed_host):
        return False
    return True


def _looks_like_tracker(s: str) -> bool:
    return bool(re.match(r"^(UA-\d|G-[A-Z0-9]|GTM-|AW-\d|ca-pub-\d|\d{15,16}$|00D)", s, re.I))


class TrackerReverseTool(BaseTool):
    name = "tracker_reverse"
    description = ("Reverse-lookup a tracker/analytics ID (GA/AdSense/Pixel/...) to OTHER domains that "
                   "embed the same ID — an independent corroborator of common ownership. NOTE: the free "
                   "PublicWWW path is JavaScript-rendered (no automated results); the working automated "
                   "path is KEYED (SpyOnWeb SPYONWEB_API_KEY). Degrades to the manual guide otherwise.")
    input_types = ["tracker_id"]
    output_types = ["domain"]
    method = "api"
    TIMEOUT = 20

    def _publicwww(self, tracker_id, seed_host=None):
        """PublicWWW source-code search -> co-using domains.

        NOTE: PublicWWW renders its result rows in JavaScript; a no-JS HTTP fetch returns only the
        page chrome (nav/footer/asset refs). So we parse ONLY real result-row domain links and apply
        a strict domain validator — and when no real rows are present (the JS/empty/login-gated case)
        we return CLEAN EMPTY + an honest note, never page-chrome junk. Real automated reverse-lookup
        needs the keyed path (SpyOnWeb / PublicWWW API)."""
        url = f"https://publicwww.com/websites/%22{requests.utils.quote(tracker_id)}%22/"
        try:
            r = requests.get(url, timeout=self.TIMEOUT,
                             headers={"User-Agent": BROWSER_UA}, proxies=_PROXIES)
        except requests.RequestException as e:
            return [], f"PublicWWW error: {e}", ""
        body = r.text or ""
        if r.status_code != 200:
            return [], f"PublicWWW HTTP {r.status_code}", body[:300]
        low = body.lower()
        if "captcha" in low or "are you human" in low:
            return [], "PublicWWW blocked (captcha) — use a keyed source or the manual guide", ""

        # Parse ONLY result-row anchors whose link text is a bare domain (not page chrome / assets).
        hosts, seen = [], set()
        try:
            soup = BeautifulSoup(body, "html.parser")
            for a in soup.select("a[href]"):
                h = (a.get_text() or "").strip().lower().rstrip(".")
                if h in seen or not _is_result_domain(h, seed_host):
                    continue
                seen.add(h)
                hosts.append(h)
                if len(hosts) >= _MAX:
                    break
        except Exception as e:  # parser robustness — never crash the review
            return [], f"PublicWWW parse error: {e}", ""

        if hosts:
            return hosts, "", ""
        js_gated = "enable javascript" in low
        note = ("PublicWWW free results are JavaScript-rendered (no-JS HTTP returns only page chrome) "
                "— no automated domains; use a keyed source (SpyOnWeb/PublicWWW API) or the manual guide"
                if js_gated else
                "PublicWWW returned no parseable result rows (free tier is top-ranked only) — confirm "
                "via the manual guide")
        return [], note, ""

    def _spyonweb(self, tracker_id):
        key = os.environ.get("SPYONWEB_API_KEY")
        if not key:
            return [], "SpyOnWeb skipped (no SPYONWEB_API_KEY)"
        try:
            r = requests.get(f"https://api.spyonweb.com/v1/summary/{requests.utils.quote(tracker_id)}",
                             params={"access_token": key}, timeout=self.TIMEOUT,
                             headers={"User-Agent": BROWSER_UA}, proxies=_PROXIES)
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            return [], f"SpyOnWeb error: {e}"
        if data.get("status") != "found":
            return [], f"SpyOnWeb: {data.get('status', 'no result')}"
        hosts = []
        for section in (data.get("result") or {}).values():
            if isinstance(section, dict):
                hosts.extend((section.get("items") or {}).keys())
        return [h.lower() for h in hosts][:_MAX], ""

    def query(self, selector, selector_type):
        if selector_type != "tracker_id":
            return self.make_result(selector, selector_type, "", [], False,
                                    "tracker_reverse only accepts tracker_id")
        tid = selector.strip()
        if not _looks_like_tracker(tid):
            return self.make_result(selector, selector_type, "", [], False,
                                    f"{tid!r} doesn't look like a known tracker-ID format")

        notes = []
        pw_hosts, pw_note, _ = self._publicwww(tid)
        if pw_note:
            notes.append(pw_note)
        sow_hosts, sow_note = self._spyonweb(tid)
        if sow_note:
            notes.append(sow_note)

        strong = tid.upper().startswith(tuple(p.upper() for p in _STRONG_PREFIXES))
        raw_conf = "probable" if strong else "possible"
        entities, seen = [], set()
        for via, hosts in (("publicwww", pw_hosts), ("spyonweb", sow_hosts)):
            for h in hosts:
                if h in seen:
                    continue
                seen.add(h)
                entities.append(EntityFound(
                    value=h, entity_type="domain", confidence=raw_conf,
                    source_citation=f"tracker_reverse ({via}): embeds shared id {tid}",
                    metadata={"shared_tracker_id": tid, "via": via,
                              "corroborator": "shared_tracker_id"}))

        guide = "guides/tracker-id-reverse-lookup.md"
        raw = (f"tracker_id={tid}\nstrong_ownership_signal={strong}\n"
               f"publicwww_hits={len(pw_hosts)} | spyonweb_hits={len(sow_hosts)}\n"
               + (("notes:\n  - " + "\n  - ".join(notes) + "\n") if notes else "")
               + (f"see {guide} for paid/manual reverse-lookup (BuiltWith/DNSlytics/NerdyData)\n"
                  if not entities else "")
               + "domains:\n" + ("\n".join(f"  - {e.value} (via {e.metadata['via']})" for e in entities)
                                  if entities else "  (none)"))
        ok = bool(entities)
        return self.make_result(selector, selector_type, raw, entities, success=ok,
                                error="" if ok else (notes[0] if notes else "no co-using domains found"))


TOOLS = [TrackerReverseTool()]
