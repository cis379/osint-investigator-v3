"""Passive Telegram OSINT tools (no account, no key) — the PASSIVE tier.

telegram_channel: fetch t.me/s/<channel> — Telegram's OWN server-rendered public preview (no login)
  — and extract posts -> forwarded-from SOURCE channels (the forwarding-graph edges that reveal
  coordination), linked/mentioned channels, and external domains linked from posts (attribution
  pivots that hand off to the domain toolchain). One passive GET, generic UA, OSINT_PROXY seam.

COLLECT ONLY — returns raw output + candidate entities for the SUPERVISOR to tier; never writes the
graph (the raw/analysis split). The ACTIVE tier (session/account-based collection, e.g. Telethon) is
deliberately SEPARATE and deferred to a research account.

telegram_search: search lyzem.com (a server-rendered Telegram search engine) by keyword/phrase ->
  candidate channels with title + description. This is the DISCOVERY entry point — turn a known
  AI-generated phrase or a topic into a channel set to investigate, then read each with
  telegram_channel and walk the forwarding graph.

(Rejected during evaluation: tgramsearch.com hides channels behind an internal /join/<id> redirect
— no clean handle — and xtea.io is JS-walled; both would ship noise. lyzem exposes real channels in
`.search-result-title` anchors, cleanly separable from site chrome. The WEB-SEARCH line's
`site:t.me "phrase"` dorks remain a complementary discovery path.)
"""
import os
import re
import requests
from urllib.parse import urlparse, quote_plus, parse_qs
from bs4 import BeautifulSoup

from .base import BaseTool, EntityFound

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
_PROXY = os.environ.get("OSINT_PROXY") or None            # passive-first OPSEC seam (unset by default)
_PROXIES = {"http": _PROXY, "https": _PROXY} if _PROXY else None

_HANDLE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$")
_SKIP_PATH = {"joinchat", "addstickers", "share", "s", "proxy", "socks", "iv"}
_SKIP_DOMAINS = {"t.me", "telegram.me", "telegram.org"}


def _channel_from_href(href):
    """A t.me/<name> href -> the channel name, or None (skips message-id / joinchat / share links)."""
    if not href or ("t.me/" not in href and "telegram.me/" not in href):
        return None
    parts = [p for p in urlparse(href).path.split("/") if p]
    if parts and parts[0] == "s":
        parts = parts[1:]
    if not parts:
        return None
    name = parts[0].lstrip("@")
    if name.lower() in _SKIP_PATH:
        return None
    return name if _HANDLE_RE.match(name) else None


def _domain_from_href(href):
    """An external http(s) link -> its domain, or None (skips Telegram's own + junk)."""
    if not href or not href.startswith(("http://", "https://")):
        return None
    host = urlparse(href).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if not host or "." not in host or " " in host or host in _SKIP_DOMAINS:
        return None
    return host


def _channel_name(selector, selector_type):
    """Normalize @handle / t.me/x / t.me/s/x / bare handle -> channel name, or None if not a TG channel."""
    s = (selector or "").strip()
    if "t.me/" in s or "telegram.me/" in s:
        parts = [p for p in urlparse(s if "//" in s else "https://" + s).path.split("/") if p]
        if parts and parts[0] == "s":
            parts = parts[1:]
        name = parts[0] if parts else ""
    elif s.startswith("@"):
        name = s[1:]
    elif selector_type == "url":
        return None  # a URL that isn't t.me -> not applicable (clean skip)
    else:
        name = s
    name = name.strip().lstrip("@")
    return name if _HANDLE_RE.match(name) else None


class TelegramChannelTool(BaseTool):
    name = "telegram_channel"
    description = ("Passive Telegram channel reader: fetches t.me/s/<channel> (Telegram's own "
                   "server-rendered public preview; NO account/key) and extracts posts, forwarded-from "
                   "source channels (forwarding-graph edges = coordination signal), linked channels, "
                   "and external domains linked from posts (attribution pivots). Passive: one GET, "
                   "generic UA, OSINT_PROXY seam. Private/empty channels return a clean empty result.")
    input_types = ["telegram_handle", "url"]
    output_types = ["telegram_handle", "url", "domain"]
    method = "api"

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"telegram_channel doesn't accept {selector_type}")
        name = _channel_name(selector, selector_type)
        if not name:
            return self.make_result(selector, selector_type, "", [], False,
                                    "not a Telegram channel (expected @handle or a t.me/ URL)")
        # IN-CHANNEL SEARCH: if the selector carried a ?q=<text>, search WITHIN the channel
        # (Telegram's own t.me/s/<channel>?q=<text> renders only matching posts).
        search_q = None
        if "?" in (selector or ""):
            src = selector if "//" in selector else "https://" + selector
            search_q = (parse_qs(urlparse(src).query).get("q") or [None])[0]
        url = f"https://t.me/s/{name}" + (f"?q={quote_plus(search_q)}" if search_q else "")
        try:
            resp = requests.get(url, headers={"User-Agent": _UA}, proxies=_PROXIES, timeout=20)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))
        raw = resp.text[:8000]
        meta = {"http_status": resp.status_code, "channel": name, "source": url}
        if search_q:
            meta["search_query"] = search_q
        if resp.status_code != 200:
            return self.make_result(selector, selector_type, raw, [], False,
                                    f"HTTP {resp.status_code}", metadata=meta)

        entities, seen, posts = [], set(), 0
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            title_el = soup.select_one(".tgme_channel_info_header_title")
            if title_el:
                meta["title"] = title_el.get_text(strip=True)
            for c in soup.select(".tgme_channel_info_counter"):
                vt, vn = c.select_one(".counter_type"), c.select_one(".counter_value")
                if vt and vn and "subscriber" in vt.get_text(strip=True).lower():
                    meta["subscribers"] = vn.get_text(strip=True)

            for msg in soup.select(".tgme_widget_message"):
                posts += 1
                fwd = msg.select_one("a.tgme_widget_message_forwarded_from_name")
                if fwd and fwd.get("href"):
                    src = _channel_from_href(fwd["href"])
                    if src and ("h", src) not in seen:
                        seen.add(("h", src))
                        entities.append(EntityFound(
                            value="@" + src, entity_type="telegram_handle", confidence="probable",
                            source_citation=f"t.me/s/{name}: post FORWARDED FROM @{src}",
                            metadata={"relationship": "forwarded_from", "from_channel": name}))
                text_el = msg.select_one(".tgme_widget_message_text")
                for a in (text_el.select("a[href]") if text_el else []):
                    href = a.get("href", "")
                    ch = _channel_from_href(href)
                    if ch and ("h", ch) not in seen:
                        seen.add(("h", ch))
                        entities.append(EntityFound(
                            value="@" + ch, entity_type="telegram_handle", confidence="possible",
                            source_citation=f"t.me/s/{name}: links/mentions @{ch}",
                            metadata={"relationship": "links_channel", "from_channel": name}))
                    elif not ch:
                        dom = _domain_from_href(href)
                        if dom and ("d", dom) not in seen:
                            seen.add(("d", dom))
                            entities.append(EntityFound(
                                value=dom, entity_type="domain", confidence="possible",
                                source_citation=f"t.me/s/{name}: post links to {dom}",
                                metadata={"relationship": "links_domain", "from_channel": name}))
        except Exception as e:
            meta["extractor_error"] = f"{type(e).__name__}: {e}"
        meta["posts_parsed"] = posts
        meta["entities_extracted"] = len(entities)
        if posts == 0 and "extractor_error" not in meta:
            meta["empty_reason"] = "no posts on the preview page (private/empty channel or name not found)"
        return self.make_result(selector, selector_type, raw, entities, success=True, metadata=meta)


_LYZEM_CHROME = {"lyzemcom", "lyzembot", "mlyzembot", "editorpost_bot", "lyzem"}


class TelegramSearchTool(BaseTool):
    name = "telegram_search"
    description = ("Passive Telegram DISCOVERY: searches lyzem.com (server-rendered Telegram search "
                   "engine) by keyword/phrase and returns candidate channels with title + description. "
                   "Turns a known phrase/topic into a channel set to investigate (feed results to "
                   "telegram_channel to read + map). No account/key; passive; OSINT_PROXY seam.")
    input_types = ["keyword"]
    output_types = ["telegram_handle"]
    method = "api"

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"telegram_search doesn't accept {selector_type}")
        url = f"https://lyzem.com/search?q={quote_plus(selector)}"
        try:
            resp = requests.get(url, headers={"User-Agent": _UA}, proxies=_PROXIES, timeout=20)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))
        raw = resp.text[:8000]
        meta = {"http_status": resp.status_code, "source": url}
        if resp.status_code != 200:
            return self.make_result(selector, selector_type, raw, [], False,
                                    f"HTTP {resp.status_code}", metadata=meta)
        entities, seen = [], set()
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Real results sit inside a '.search-result-title' container (the t.me anchor is within
            # it); site chrome (bots, promo) is NOT, so this excludes the noise that sank tgramsearch.
            for el in soup.select(".search-result-title"):
                a = el if el.name == "a" else el.find("a", href=True)
                ch = _channel_from_href(a.get("href", "")) if a else None
                if not ch or ch in seen or ch.lower() in _LYZEM_CHROME:
                    continue
                seen.add(ch)
                title = el.get_text(strip=True)
                entities.append(EntityFound(
                    value="@" + ch, entity_type="telegram_handle", confidence="possible",
                    source_citation=f"lyzem search '{selector}': @{ch}" + (f" — {title[:50]}" if title else ""),
                    metadata={"query": selector, "title": title}))
        except Exception as e:
            meta["extractor_error"] = f"{type(e).__name__}: {e}"
        meta["entities_extracted"] = len(entities)
        if not entities and "extractor_error" not in meta:
            meta["empty_reason"] = f"no channel results for '{selector}'"
        return self.make_result(selector, selector_type, raw, entities, success=True, metadata=meta)


TOOLS = [TelegramChannelTool(), TelegramSearchTool()]
