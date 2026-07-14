"""Passive Telegram OSINT tools (no account, no key) — the PASSIVE tier.

telegram_channel: fetch t.me/s/<channel> — Telegram's OWN server-rendered public preview (no login)
  — and extract posts -> forwarded-from SOURCE channels (the forwarding-graph edges that reveal
  coordination), linked/mentioned channels, and external domains linked from posts (attribution
  pivots that hand off to the domain toolchain). One passive GET, generic UA, OSINT_PROXY seam.

COLLECT ONLY — returns raw output + candidate entities for the SUPERVISOR to tier; never writes the
graph (the raw/analysis split). The ACTIVE tier (session/account-based collection, e.g. Telethon) is
deliberately SEPARATE and deferred to a research account.

DISCOVERY (keyword/phrase -> channels) is handled by the WEB-SEARCH line (`site:t.me "phrase"` dorks +
google_dork_generator), NOT here: the third-party index tgramsearch.com was evaluated and rejected —
its result cards hide the real channel behind an internal /join/<id> redirect (no @handle / t.me link),
so clean passive extraction isn't possible (would ship display-name noise). See BACKLOG intake note.
"""
import os
import re
import requests
from urllib.parse import urlparse
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
        url = f"https://t.me/s/{name}"
        try:
            resp = requests.get(url, headers={"User-Agent": _UA}, proxies=_PROXIES, timeout=20)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))
        raw = resp.text[:8000]
        meta = {"http_status": resp.status_code, "channel": name, "source": url}
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


TOOLS = [TelegramChannelTool()]
