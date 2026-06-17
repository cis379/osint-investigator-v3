import json
import requests
from .base import BaseTool, ToolResult, EntityFound


class IpGeoTool(BaseTool):
    name = "ip_geolocation"
    description = "IP geolocation - city, country, ASN, ISP"
    input_types = ["ip_v4", "ip_v6"]
    output_types = ["asn", "company"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("ip_v4", "ip_v6"):
            return self.make_result(selector, selector_type, "", [], False, "IP geolocation only accepts IPs")

        try:
            resp = requests.get(
                f"http://ip-api.com/json/{selector}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,query",
                timeout=10,
            )
            raw_output = resp.text
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    if data.get("as"):
                        entities.append(EntityFound(
                            value=data["as"].split()[0] if data["as"] else "",
                            entity_type="asn",
                            confidence="confirmed",
                            source_citation=f"ASN: {data['as']}",
                            metadata={"asn_name": data.get("asname", "")},
                        ))
                    if data.get("org"):
                        entities.append(EntityFound(
                            value=data["org"],
                            entity_type="company",
                            confidence="confirmed",
                            source_citation=f"Organization: {data['org']}",
                        ))
                    if data.get("isp"):
                        entities.append(EntityFound(
                            value=data["isp"],
                            entity_type="company",
                            confidence="confirmed",
                            source_citation=f"ISP: {data['isp']}",
                        ))

                    entities.append(EntityFound(
                        value=selector,
                        entity_type=selector_type,
                        confidence="confirmed",
                        source_citation=f"Geolocation: {data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}",
                        metadata={
                            "country": data.get("country"),
                            "region": data.get("regionName"),
                            "city": data.get("city"),
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "timezone": data.get("timezone"),
                        },
                    ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class ReverseDnsTool(BaseTool):
    name = "reverse_dns"
    description = "Reverse DNS lookup"
    input_types = ["ip_v4", "ip_v6"]
    output_types = ["domain"]
    method = "library"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("ip_v4", "ip_v6"):
            return self.make_result(selector, selector_type, "", [], False, "Reverse DNS only accepts IPs")

        try:
            import dns.resolver
            import dns.reversename
            rev_name = dns.reversename.from_address(selector)
            answers = dns.resolver.resolve(rev_name, "PTR")
            raw_lines = []
            entities = []

            for rdata in answers:
                hostname = str(rdata).rstrip(".")
                line = f"PTR: {selector} -> {hostname}"
                raw_lines.append(line)
                entities.append(EntityFound(
                    value=hostname,
                    entity_type="domain",
                    confidence="confirmed",
                    source_citation=line,
                ))

            return self.make_result(
                selector, selector_type, "\n".join(raw_lines), entities, success=True,
            )
        except Exception as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class ShodanInternetDBTool(BaseTool):
    name = "shodan_internetdb"
    description = "Shodan InternetDB - free open ports and hostnames"
    input_types = ["ip_v4"]
    output_types = ["domain"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "ip_v4":
            return self.make_result(selector, selector_type, "", [], False, "Shodan InternetDB only accepts IPv4")

        try:
            resp = requests.get(f"https://internetdb.shodan.io/{selector}", timeout=10)
            raw_output = resp.text
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                for hostname in data.get("hostnames", []):
                    entities.append(EntityFound(
                        value=hostname,
                        entity_type="domain",
                        confidence="confirmed",
                        source_citation=f"Shodan hostname: {hostname}",
                    ))

                if data.get("ports"):
                    entities.append(EntityFound(
                        value=selector,
                        entity_type="ip_v4",
                        confidence="confirmed",
                        source_citation=f"Open ports: {data['ports']}",
                        metadata={
                            "ports": data.get("ports", []),
                            "vulns": data.get("vulns", []),
                            "cpes": data.get("cpes", []),
                            "tags": data.get("tags", []),
                        },
                    ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class IpInfoTool(BaseTool):
    name = "ipinfo"
    description = "IPinfo.io - geolocation, ASN, company, hostname"
    input_types = ["ip_v4", "ip_v6"]
    output_types = ["domain", "asn", "company"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type not in ("ip_v4", "ip_v6"):
            return self.make_result(selector, selector_type, "", [], False, "IPinfo only accepts IPs")

        try:
            resp = requests.get(f"https://ipinfo.io/{selector}/json", timeout=10)
            raw_output = resp.text
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                if data.get("hostname"):
                    entities.append(EntityFound(
                        value=data["hostname"],
                        entity_type="domain",
                        confidence="confirmed",
                        source_citation=f"IPinfo hostname: {data['hostname']}",
                    ))
                if data.get("org"):
                    parts = data["org"].split(" ", 1)
                    if len(parts) == 2 and parts[0].startswith("AS"):
                        entities.append(EntityFound(
                            value=parts[0],
                            entity_type="asn",
                            confidence="confirmed",
                            source_citation=f"IPinfo ASN: {data['org']}",
                        ))
                        entities.append(EntityFound(
                            value=parts[1],
                            entity_type="company",
                            confidence="confirmed",
                            source_citation=f"IPinfo org: {data['org']}",
                        ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


TOOLS = [IpGeoTool(), ReverseDnsTool(), ShodanInternetDBTool(), IpInfoTool()]
