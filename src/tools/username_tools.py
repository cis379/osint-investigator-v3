import re
import json
from .base import BaseTool, ToolResult, EntityFound


class SherlockTool(BaseTool):
    name = "sherlock"
    description = "Hunt usernames across 400+ social networks"
    input_types = ["username"]
    output_types = ["url"]
    method = "cli"
    install_command = "pip install sherlock-project"

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command(["sherlock", "--version"])
        return code == 0 or "sherlock" in (stdout + stderr).lower()

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "username":
            return self.make_result(selector, selector_type, "", [], False, "Sherlock only accepts usernames")

        stdout, stderr, code = self.run_command(
            ["sherlock", selector, "--print-found", "--no-color", "--timeout", "15"],
            timeout=180,
        )

        raw_output = stdout + stderr
        entities = []

        for line in stdout.splitlines():
            line = line.strip()
            url_match = re.search(r'https?://[^\s]+', line)
            if url_match:
                url = url_match.group(0)
                entities.append(EntityFound(
                    value=url,
                    entity_type="url",
                    confidence="confirmed",
                    source_citation=line,
                ))

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0 or len(entities) > 0,
        )


class MaigretTool(BaseTool):
    name = "maigret"
    description = "Collect information about username from 2500+ sites"
    input_types = ["username"]
    output_types = ["url", "email", "name"]
    method = "cli"
    install_command = "pip install maigret"

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command(["maigret", "--version"])
        return code == 0 or "maigret" in (stdout + stderr).lower()

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "username":
            return self.make_result(selector, selector_type, "", [], False, "Maigret only accepts usernames")

        stdout, stderr, code = self.run_command(
            ["maigret", selector, "--no-color", "--timeout", "10", "--no-progressbar"],
            timeout=300,
        )

        raw_output = stdout + stderr
        entities = []

        for line in stdout.splitlines():
            line = line.strip()
            url_match = re.search(r'https?://[^\s]+', line)
            if url_match:
                url = url_match.group(0)
                entities.append(EntityFound(
                    value=url,
                    entity_type="url",
                    confidence="confirmed",
                    source_citation=line,
                ))

            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
            if email_match:
                entities.append(EntityFound(
                    value=email_match.group(0),
                    entity_type="email",
                    confidence="likely",
                    source_citation=line,
                ))

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0 or len(entities) > 0,
        )


TOOLS = [SherlockTool(), MaigretTool()]
