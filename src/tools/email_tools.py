import re
import json
import requests
from .base import BaseTool, ToolResult, EntityFound


class HoleheTool(BaseTool):
    name = "holehe"
    description = "Check if email is registered on various sites"
    input_types = ["email"]
    output_types = ["url", "username"]
    method = "cli"
    install_command = "pip install holehe"

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command(["holehe", "--version"])
        return code == 0 or "holehe" in (stdout + stderr).lower()

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "email":
            return self.make_result(selector, selector_type, "", [], False, "Holehe only accepts emails")

        stdout, stderr, code = self.run_command(
            ["holehe", selector, "--no-color"],
            timeout=120,
        )

        raw_output = stdout + stderr
        entities = []

        for line in stdout.splitlines():
            line = line.strip()
            if "[+]" in line or "exists" in line.lower() or "registered" in line.lower():
                site_match = re.search(r'(\w+\.(?:com|org|net|io|co|me))', line, re.IGNORECASE)
                if site_match:
                    entities.append(EntityFound(
                        value=site_match.group(0),
                        entity_type="domain",
                        confidence="confirmed",
                        source_citation=line,
                        metadata={"registration_status": "registered"},
                    ))

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0 or len(entities) > 0,
        )


class EmailRepTool(BaseTool):
    name = "emailrep"
    description = "Email reputation and activity data"
    input_types = ["email"]
    output_types = []
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "email":
            return self.make_result(selector, selector_type, "", [], False, "EmailRep only accepts emails")

        try:
            resp = requests.get(
                f"https://emailrep.io/{selector}",
                headers={"User-Agent": "OSINT-Investigator", "Accept": "application/json"},
                timeout=15,
            )
            raw_output = resp.text
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                entities.append(EntityFound(
                    value=selector,
                    entity_type="email",
                    confidence="confirmed",
                    source_citation=f"EmailRep reputation: {data.get('reputation', 'unknown')}",
                    metadata={
                        "reputation": data.get("reputation"),
                        "suspicious": data.get("suspicious"),
                        "references": data.get("references", 0),
                        "details": data.get("details", {}),
                    },
                ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
                error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


TOOLS = [HoleheTool(), EmailRepTool()]
