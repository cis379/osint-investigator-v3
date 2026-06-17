import json
import requests
from .base import BaseTool, ToolResult, EntityFound


class UrlScanTool(BaseTool):
    name = "urlscan"
    description = "Search urlscan.io for scanned pages"
    input_types = ["domain", "url", "ip_v4"]
    output_types = ["url", "domain", "ip_v4"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("domain", "url", "ip_v4"):
            return self.make_result(selector, selector_type, "", [], False, "urlscan accepts domains, URLs, or IPs")

        try:
            if selector_type == "ip_v4":
                query_param = f"ip:{selector}"
            elif selector_type == "url":
                query_param = f"page.url:{selector}"
            else:
                query_param = f"domain:{selector}"

            resp = requests.get(
                f"https://urlscan.io/api/v1/search/?q={query_param}&size=10",
                timeout=15,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                for result in data.get("results", [])[:10]:
                    page = result.get("page", {})
                    task = result.get("task", {})

                    if page.get("domain"):
                        entities.append(EntityFound(
                            value=page["domain"],
                            entity_type="domain",
                            confidence="confirmed",
                            source_citation=f"urlscan result: {page['domain']} (scanned {task.get('time', '')})",
                            metadata={
                                "scan_url": task.get("url", ""),
                                "server": page.get("server", ""),
                                "status": page.get("status", ""),
                            },
                        ))

                    if page.get("ip"):
                        entities.append(EntityFound(
                            value=page["ip"],
                            entity_type="ip_v4",
                            confidence="confirmed",
                            source_citation=f"urlscan IP: {page['ip']} for {page.get('domain', '')}",
                        ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class ThreatFoxTool(BaseTool):
    name = "threatfox"
    description = "ThreatFox IOC search"
    input_types = ["ip_v4", "domain", "hash_md5", "hash_sha256", "url"]
    output_types = ["ip_v4", "domain", "hash_md5", "hash_sha256"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False, f"ThreatFox doesn't accept {selector_type}")

        try:
            resp = requests.post(
                "https://threatfox-api.abuse.ch/api/v1/",
                json={"query": "search_ioc", "search_term": selector},
                timeout=15,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                if data.get("query_status") == "ok":
                    for ioc in data.get("data", [])[:20]:
                        ioc_value = ioc.get("ioc", "")
                        ioc_type = ioc.get("ioc_type", "")
                        malware = ioc.get("malware", "")
                        threat_type = ioc.get("threat_type", "")

                        entity_type = "domain"
                        if "ip" in ioc_type.lower():
                            entity_type = "ip_v4"
                        elif "md5" in ioc_type.lower():
                            entity_type = "hash_md5"
                        elif "sha256" in ioc_type.lower():
                            entity_type = "hash_sha256"
                        elif "url" in ioc_type.lower():
                            entity_type = "url"

                        entities.append(EntityFound(
                            value=ioc_value,
                            entity_type=entity_type,
                            confidence="confirmed",
                            source_citation=f"ThreatFox: {ioc_value} ({malware} - {threat_type})",
                            metadata={
                                "malware": malware,
                                "threat_type": threat_type,
                                "confidence_level": ioc.get("confidence_level", 0),
                                "first_seen": ioc.get("first_seen_utc", ""),
                                "last_seen": ioc.get("last_seen_utc", ""),
                                "tags": ioc.get("tags", []),
                            },
                        ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class GoogleDorkGenerator(BaseTool):
    name = "google_dork_generator"
    description = "Generate Google dork queries for OSINT discovery"
    input_types = ["username", "email", "domain", "name", "phone", "company", "telegram_handle"]
    output_types = []
    method = "generator"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        dorks = []

        if selector_type == "username":
            dorks = [
                f'"{selector}" site:twitter.com OR site:x.com',
                f'"{selector}" site:github.com',
                f'"{selector}" site:reddit.com',
                f'"{selector}" site:linkedin.com',
                f'"{selector}" site:telegram.me OR site:t.me',
                f'"{selector}" site:discord.com OR site:discord.gg',
                f'"{selector}" site:keybase.io',
                f'"{selector}" site:pastebin.com OR site:paste.ee',
                f'"{selector}" email OR contact',
                f'"{selector}" intext:@gmail.com OR intext:@protonmail.com',
            ]
        elif selector_type == "email":
            local, domain = selector.split("@")
            dorks = [
                f'"{selector}"',
                f'"{selector}" -site:{domain}',
                f'"{selector}" site:pastebin.com',
                f'"{selector}" site:github.com',
                f'"{local}" site:twitter.com OR site:x.com',
                f'"{selector}" filetype:pdf OR filetype:doc OR filetype:xlsx',
                f'"{selector}" "password" OR "leak"',
            ]
        elif selector_type == "domain":
            dorks = [
                f'site:{selector}',
                f'site:{selector} filetype:pdf',
                f'site:{selector} filetype:xlsx OR filetype:csv',
                f'site:{selector} inurl:admin OR inurl:login',
                f'site:{selector} intitle:"index of"',
                f'"{selector}" site:pastebin.com',
                f'"{selector}" site:github.com',
                f'"{selector}" "api key" OR "password" OR "secret"',
                f'inurl:{selector} -site:{selector}',
            ]
        elif selector_type == "phone":
            dorks = [
                f'"{selector}"',
                f'"{selector}" site:facebook.com',
                f'"{selector}" site:linkedin.com',
                f'"{selector}" email OR name',
            ]
        elif selector_type == "name":
            dorks = [
                f'"{selector}" site:linkedin.com',
                f'"{selector}" site:twitter.com OR site:x.com',
                f'"{selector}" site:github.com',
                f'"{selector}" email OR contact',
                f'"{selector}" resume OR CV filetype:pdf',
            ]
        elif selector_type == "company":
            dorks = [
                f'"{selector}" site:linkedin.com',
                f'"{selector}" employees',
                f'"{selector}" @gmail.com OR @outlook.com',
                f'site:*.{selector.lower().replace(" ", "")}.com',
            ]
        elif selector_type == "telegram_handle":
            dorks = [
                f'"{selector}" site:t.me',
                f'"{selector}" site:telegram.me',
                f'"{selector}" telegram',
                f'"{selector}" site:github.com',
                f'"{selector}" site:twitter.com OR site:x.com',
            ]

        raw_output = "Generated Google Dork Queries:\n" + "\n".join(f"  {i+1}. {d}" for i, d in enumerate(dorks))
        entities = []

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=True,
        )


TOOLS = [UrlScanTool(), ThreatFoxTool(), GoogleDorkGenerator()]
