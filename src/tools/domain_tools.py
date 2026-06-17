import json
import socket
import requests
from .base import BaseTool, ToolResult, EntityFound


class WhoisTool(BaseTool):
    name = "whois_lookup"
    description = "WHOIS registration data for domains"
    input_types = ["domain"]
    output_types = ["name", "email", "phone", "company", "domain"]
    method = "library"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "domain":
            return self.make_result(selector, selector_type, "", [], False, "WHOIS only accepts domains")

        try:
            import whois
            w = whois.whois(selector)
            raw_output = str(w)
            entities = []

            if w.registrar:
                entities.append(EntityFound(
                    value=str(w.registrar),
                    entity_type="company",
                    confidence="confirmed",
                    source_citation=f"Registrar: {w.registrar}",
                ))

            if w.emails:
                emails = w.emails if isinstance(w.emails, list) else [w.emails]
                for email in emails:
                    if email:
                        entities.append(EntityFound(
                            value=str(email),
                            entity_type="email",
                            confidence="confirmed",
                            source_citation=f"WHOIS email: {email}",
                        ))

            if w.name:
                names = w.name if isinstance(w.name, list) else [w.name]
                for name in names:
                    if name and name.lower() not in ("redacted", "data protected", "not disclosed"):
                        entities.append(EntityFound(
                            value=str(name),
                            entity_type="name",
                            confidence="confirmed",
                            source_citation=f"WHOIS registrant: {name}",
                        ))

            if w.org:
                orgs = w.org if isinstance(w.org, list) else [w.org]
                for org in orgs:
                    if org and org.lower() not in ("redacted", "data protected"):
                        entities.append(EntityFound(
                            value=str(org),
                            entity_type="company",
                            confidence="confirmed",
                            source_citation=f"WHOIS org: {org}",
                        ))

            if w.name_servers:
                ns_list = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]
                for ns in ns_list:
                    if ns:
                        entities.append(EntityFound(
                            value=str(ns).lower(),
                            entity_type="domain",
                            confidence="confirmed",
                            source_citation=f"Nameserver: {ns}",
                        ))

            metadata = {}
            if w.creation_date:
                cd = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                metadata["creation_date"] = str(cd)
            if w.expiration_date:
                ed = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date
                metadata["expiration_date"] = str(ed)
            if w.updated_date:
                ud = w.updated_date[0] if isinstance(w.updated_date, list) else w.updated_date
                metadata["updated_date"] = str(ud)

            if metadata:
                entities.append(EntityFound(
                    value=selector,
                    entity_type="domain",
                    confidence="confirmed",
                    source_citation="WHOIS registration dates",
                    metadata=metadata,
                ))

            return self.make_result(selector, selector_type, raw_output, entities, success=True)
        except Exception as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class DnsLookupTool(BaseTool):
    name = "dns_lookup"
    description = "DNS record enumeration"
    input_types = ["domain"]
    output_types = ["ip_v4", "ip_v6", "domain"]
    method = "library"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "domain":
            return self.make_result(selector, selector_type, "", [], False, "DNS lookup only accepts domains")

        try:
            import dns.resolver
            raw_lines = []
            entities = []
            record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]

            for rtype in record_types:
                try:
                    answers = dns.resolver.resolve(selector, rtype)
                    for rdata in answers:
                        value = str(rdata).strip('"')
                        line = f"{rtype}: {value}"
                        raw_lines.append(line)

                        if rtype == "A":
                            entities.append(EntityFound(
                                value=value, entity_type="ip_v4",
                                confidence="confirmed", source_citation=line,
                            ))
                        elif rtype == "AAAA":
                            entities.append(EntityFound(
                                value=value, entity_type="ip_v6",
                                confidence="confirmed", source_citation=line,
                            ))
                        elif rtype == "MX":
                            mx_host = value.split()[-1].rstrip(".")
                            if mx_host and "." in mx_host:
                                entities.append(EntityFound(
                                    value=mx_host, entity_type="domain",
                                    confidence="confirmed", source_citation=line,
                                    metadata={"record_type": "MX"},
                                ))
                        elif rtype == "NS":
                            ns_host = value.rstrip(".")
                            if ns_host and "." in ns_host:
                                entities.append(EntityFound(
                                    value=ns_host, entity_type="domain",
                                    confidence="confirmed", source_citation=line,
                                    metadata={"record_type": "NS"},
                                ))
                        elif rtype == "CNAME":
                            cname_host = value.rstrip(".")
                            if cname_host and "." in cname_host:
                                entities.append(EntityFound(
                                    value=cname_host, entity_type="domain",
                                    confidence="confirmed", source_citation=line,
                                    metadata={"record_type": "CNAME"},
                                ))
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    pass

            raw_output = "\n".join(raw_lines)
            return self.make_result(selector, selector_type, raw_output, entities, success=True)
        except Exception as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class CrtShTool(BaseTool):
    name = "crtsh"
    description = "Certificate Transparency log search"
    input_types = ["domain"]
    output_types = ["domain", "email"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "domain":
            return self.make_result(selector, selector_type, "", [], False, "crt.sh only accepts domains")

        try:
            resp = requests.get(
                f"https://crt.sh/?q=%.{selector}&output=json",
                timeout=30,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                certs = resp.json()
                seen_domains = set()
                for cert in certs[:100]:
                    name = cert.get("name_value", "")
                    for domain in name.split("\n"):
                        domain = domain.strip().lstrip("*.")
                        if domain and domain not in seen_domains:
                            seen_domains.add(domain)
                            entities.append(EntityFound(
                                value=domain,
                                entity_type="domain",
                                confidence="confirmed",
                                source_citation=f"crt.sh cert ID {cert.get('id', 'unknown')}: {domain}",
                                metadata={
                                    "issuer": cert.get("issuer_name", ""),
                                    "not_before": cert.get("not_before", ""),
                                    "not_after": cert.get("not_after", ""),
                                },
                            ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class WaybackTool(BaseTool):
    name = "wayback"
    description = "Wayback Machine historical snapshots"
    input_types = ["domain", "url"]
    output_types = ["url"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("domain", "url"):
            return self.make_result(selector, selector_type, "", [], False, "Wayback accepts domains or URLs")

        try:
            resp = requests.get(
                f"https://web.archive.org/cdx/search/cdx?url={selector}&output=json&limit=50&fl=timestamp,original,statuscode,mimetype",
                timeout=30,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                rows = resp.json()
                if len(rows) > 1:
                    for row in rows[1:]:
                        timestamp, original, status, mime = row[0], row[1], row[2], row[3]
                        archive_url = f"https://web.archive.org/web/{timestamp}/{original}"
                        entities.append(EntityFound(
                            value=archive_url,
                            entity_type="url",
                            confidence="confirmed",
                            source_citation=f"Wayback snapshot: {timestamp} - {original}",
                            metadata={
                                "original_url": original,
                                "timestamp": timestamp,
                                "status_code": status,
                                "mime_type": mime,
                            },
                        ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class HttpHeaderTool(BaseTool):
    name = "http_headers"
    description = "HTTP header analysis"
    input_types = ["domain", "url"]
    output_types = ["ip_v4"]
    method = "library"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("domain", "url"):
            return self.make_result(selector, selector_type, "", [], False, "HTTP headers accepts domains or URLs")

        url = selector if selector.startswith("http") else f"https://{selector}"
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            headers_dict = dict(resp.headers)
            raw_output = json.dumps(headers_dict, indent=2)
            entities = []

            try:
                domain = selector if selector_type == "domain" else selector.split("//")[1].split("/")[0]
                ip = socket.gethostbyname(domain)
                entities.append(EntityFound(
                    value=ip,
                    entity_type="ip_v4",
                    confidence="confirmed",
                    source_citation=f"DNS resolution: {domain} -> {ip}",
                ))
            except socket.gaierror:
                pass

            server = headers_dict.get("Server", headers_dict.get("server", ""))
            if server:
                entities.append(EntityFound(
                    value=server,
                    entity_type="domain",
                    confidence="confirmed",
                    source_citation=f"Server header: {server}",
                    metadata={"header_type": "server", "technologies": server},
                ))

            return self.make_result(selector, selector_type, raw_output, entities, success=True)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


TOOLS = [WhoisTool(), DnsLookupTool(), CrtShTool(), WaybackTool(), HttpHeaderTool()]
