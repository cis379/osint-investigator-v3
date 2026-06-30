"""Infrastructure / hosting-pivot tools (free, no key) — the gaps the viory.video test exposed.

- reverse_ip : reverse-IP / passive-DNS (HackerTarget) -> other domains co-hosted on an IP.
- tls_cert   : live TLS cert -> co-hosted domains (subjectAltName) + issuer + SHA-256 fingerprint.
- http_title : fetch a domain/URL -> page TITLE + Server + branding meta (cross-branding detection).
"""
import re
import ssl
import socket
import hashlib

import requests
from bs4 import BeautifulSoup

from .base import BaseTool, EntityFound
from .nethttp import http_get

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_DOMAIN_RE = re.compile(r"^(?:[A-Za-z0-9_](?:[A-Za-z0-9_\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")


class ReverseIpTool(BaseTool):
    name = "reverse_ip"
    description = "Reverse-IP / passive-DNS: other domains co-hosted on an IPv4 (HackerTarget, free no-key)"
    input_types = ["ip_v4"]
    output_types = ["domain"]
    method = "api"
    _RATE_LIMIT_HINTS = ("api count exceeded", "api limit", "rate limit", "too many requests")
    _MAX_DOMAINS = 100

    def query(self, selector, selector_type):
        if selector_type != "ip_v4":
            return self.make_result(selector, selector_type, "", [], False,
                                    "reverse_ip only accepts ip_v4 (free reverse-IP has no IPv6)")
        url = f"https://api.hackertarget.com/reverseiplookup/?q={selector}"
        try:
            resp = http_get(url, timeout=20, retries=1, headers={"User-Agent": "osint-investigator/1.0"})
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))

        raw_output = resp.text or ""
        text = raw_output.strip()
        low = text.lower()
        if resp.status_code != 200:
            return self.make_result(selector, selector_type, raw_output, [], False,
                                    f"HTTP {resp.status_code}: {text[:200]}")
        if any(h in low for h in self._RATE_LIMIT_HINTS):
            return self.make_result(selector, selector_type, raw_output, [], False, text[:200])
        if low.startswith("error") or "no dns" in low or "no records" in low:
            return self.make_result(selector, selector_type, raw_output, [], False, text[:200] or "no results")

        seed = selector.lower()
        entities, seen = [], set()
        for line in text.splitlines():
            host = line.strip().rstrip(".").lower()
            if not host or host in seen or host == seed or not _DOMAIN_RE.match(host):
                continue
            seen.add(host)
            entities.append(EntityFound(
                value=host, entity_type="domain", confidence="probable",
                source_citation=f"reverse_ip (HackerTarget): co-hosted on {selector}",
                metadata={"shared_ip": selector}))
            if len(entities) >= self._MAX_DOMAINS:
                break
        if not entities:
            return self.make_result(selector, selector_type, raw_output, [], False,
                                    "no co-hosted domains parsed from response")
        return self.make_result(selector, selector_type, raw_output, entities, success=True)


class TlsCertTool(BaseTool):
    name = "tls_cert"
    description = ("Fetch a domain's live TLS certificate; extract co-hosted domains (subjectAltName), "
                  "issuer, validity, and SHA-256 fingerprint")
    input_types = ["domain"]
    output_types = ["domain"]
    method = "library"
    TIMEOUT = 10

    def query(self, selector, selector_type):
        if selector_type != "domain":
            return self.make_result(selector, selector_type, "", [], False, "tls_cert only accepts domains")
        host = selector.strip().lower()
        if "://" in host:
            host = host.split("://", 1)[1]
        host = host.split("/", 1)[0].split(":", 1)[0]
        if not host:
            return self.make_result(selector, selector_type, "", [], False, "empty hostname")

        ctx = ssl.create_default_context()
        verify_note = ""
        try:
            with socket.create_connection((host, 443), timeout=self.TIMEOUT) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    der = ssock.getpeercert(binary_form=True)
                    tls_version = ssock.version()
        except ssl.SSLCertVerificationError as e:
            try:
                pem = ssl.get_server_certificate((host, 443), timeout=self.TIMEOUT)
                der = ssl.PEM_cert_to_DER_cert(pem)
                cert, tls_version = {}, None
                verify_note = f" (cert did NOT verify: {e})"
            except Exception as e2:
                return self.make_result(selector, selector_type, "", [], False,
                                        f"SSL verification failed and un-verified read failed: {e2}")
        except (socket.timeout, TimeoutError):
            return self.make_result(selector, selector_type, "", [], False,
                                    f"connection to {host}:443 timed out after {self.TIMEOUT}s")
        except (socket.gaierror, ConnectionRefusedError, OSError) as e:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"connection to {host}:443 failed: {e}")
        except ssl.SSLError as e:
            return self.make_result(selector, selector_type, "", [], False, f"SSL error: {e}")

        fingerprint = hashlib.sha256(der).hexdigest()
        fp_colon = ":".join(fingerprint[i:i + 2] for i in range(0, len(fingerprint), 2)).upper()
        san_dns = [v for (k, v) in cert.get("subjectAltName", ()) if k.lower() == "dns"]

        def _flatten(rdn_seq):
            return ", ".join(f"{k}={v}" for rdn in (rdn_seq or ()) for (k, v) in rdn)

        issuer = _flatten(cert.get("issuer"))
        not_before, not_after = cert.get("notBefore", ""), cert.get("notAfter", "")
        meta = {"issuer": issuer, "fingerprint_sha256": fp_colon,
                "not_before": not_before, "not_after": not_after, "seed_domain": host}

        entities, seen = [], set()
        for name in san_dns:
            bare = name.lstrip("*.").lower()
            if not bare or bare == host or bare in seen:
                continue
            seen.add(bare)
            entities.append(EntityFound(
                value=bare, entity_type="domain", confidence="probable",
                source_citation=f"tls_cert: shared SAN on {host} certificate",
                metadata={**meta, "san_raw": name, "wildcard": name.startswith("*.")}))
        entities.append(EntityFound(
            value=host, entity_type="domain", confidence="confirmed",
            source_citation=f"tls_cert: live certificate served by {host}:443",
            metadata={**meta, "tls_version": tls_version, "san_count": len(san_dns), "san_dns": san_dns}))

        raw_lines = [f"host: {host}:443{verify_note}", f"tls_version: {tls_version}",
                     f"issuer: {issuer or '-'}", f"not_before: {not_before or '-'}",
                     f"not_after: {not_after or '-'}", f"sha256_fingerprint: {fp_colon}",
                     f"san_count: {len(san_dns)}", "subjectAltName (DNS):"]
        raw_lines += [f"  - {n}" for n in san_dns]
        return self.make_result(selector, selector_type, "\n".join(raw_lines), entities, success=True)


class HttpTitleTool(BaseTool):
    name = "http_title"
    description = ("Fetch a domain/URL over HTTP(S) and extract page TITLE + Server header + branding "
                  "meta (og:site_name/generator) for cross-branding detection")
    input_types = ["domain", "url"]
    output_types = ["company", "keyword"]
    method = "library"

    def _candidate_urls(self, selector, selector_type):
        s = selector.strip()
        if selector_type == "url" or re.match(r"^https?://", s, re.I):
            return [s]
        s = s.rstrip("/")
        return [f"https://{s}", f"http://{s}"]

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"http_title doesn't accept {selector_type}")
        headers = {"User-Agent": BROWSER_UA,
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        last_err, resp, tried = "", None, []
        for url in self._candidate_urls(selector, selector_type):
            tried.append(url)
            try:
                resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                break
            except requests.RequestException as e:
                last_err = f"{type(e).__name__} on {url}: {e}"
                resp = None
        if resp is None:
            return self.make_result(selector, selector_type, f"tried={tried}", [], False,
                                    last_err or "could not connect")

        final_url, status = resp.url, resp.status_code
        server = resp.headers.get("Server", "")
        powered_by = resp.headers.get("X-Powered-By", "")
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding or resp.encoding

        title = og_site = generator = app_name = ""
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            for m in soup.find_all("meta"):
                prop = (m.get("property") or m.get("name") or "").lower()
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                if prop == "og:site_name":
                    og_site = content
                elif prop == "generator":
                    generator = content
                elif prop == "application-name":
                    app_name = content
        except Exception:
            pass

        # Only treat branding as REAL on a 2xx success page. A 4xx/5xx page often still has a
        # <title> ("404 Not Found", "Error") — emitting that as the site's brand is a false
        # finding, so we suppress branding entities on non-2xx (the status stays in raw).
        is_2xx = 200 <= status < 300
        entities = []
        if is_2xx and title:
            entities.append(EntityFound(value=title, entity_type="keyword", confidence="possible",
                                        source_citation=f"http_title: {title} at {final_url}",
                                        metadata={"final_url": final_url, "status": status, "server": server}))
        if is_2xx and og_site:
            entities.append(EntityFound(value=og_site, entity_type="company", confidence="possible",
                                        source_citation=f"http_title og:site_name: {og_site} at {final_url}",
                                        metadata={"final_url": final_url}))
        if is_2xx and app_name and app_name.lower() != (og_site or "").lower():
            entities.append(EntityFound(value=app_name, entity_type="company", confidence="possible",
                                        source_citation=f"http_title application-name: {app_name} at {final_url}",
                                        metadata={"final_url": final_url}))
        if is_2xx and generator:
            entities.append(EntityFound(value=generator, entity_type="keyword", confidence="possible",
                                        source_citation=f"http_title generator: {generator} at {final_url}",
                                        metadata={"final_url": final_url}))

        # A 200 with no <title> usually means a JS-rendered SPA (BeautifulSoup sees no
        # static title) — flag it so the supervisor doesn't read "no title" as "no brand".
        js_note = ""
        if not title and is_2xx:
            js_note = "\nnote=title empty at status 200; likely JS-rendered (SPA) — branding not in static HTML"
        elif not is_2xx:
            js_note = f"\nnote=HTTP {status} (non-2xx) — branding NOT extracted (error/redirect page, not the site)"
        raw = (f"final_url={final_url}\nstatus={status}\nserver={server or '-'}\n"
               f"x_powered_by={powered_by or '-'}\ntitle={title or '-'}\n"
               f"og:site_name={og_site or '-'}\napplication-name={app_name or '-'}\ngenerator={generator or '-'}{js_note}")
        # Honest success: a real page (2xx). A 4xx/5xx is a response, not a usable branding result.
        ok = is_2xx
        return self.make_result(selector, selector_type, raw, entities, success=ok,
                                error="" if ok else f"HTTP {status} (non-2xx)")


TOOLS = [ReverseIpTool(), TlsCertTool(), HttpTitleTool()]
