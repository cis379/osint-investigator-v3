from .base import BaseTool, ToolResult, EntityFound


class PhoneInfogaTool(BaseTool):
    name = "phoneinfoga"
    description = "Phone number OSINT - carrier, location, line type"
    input_types = ["phone"]
    output_types = ["company", "name"]
    method = "cli"
    install_command = "pip install phoneinfoga"

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command(["phoneinfoga", "version"])
        return code == 0

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "phone":
            return self.make_result(selector, selector_type, "", [], False, "PhoneInfoga only accepts phone numbers")

        stdout, stderr, code = self.run_command(
            ["phoneinfoga", "scan", "-n", selector],
            timeout=60,
        )

        raw_output = stdout + stderr
        entities = []

        for line in stdout.splitlines():
            line = line.strip()
            if "carrier" in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    entities.append(EntityFound(
                        value=parts[1].strip(),
                        entity_type="company",
                        confidence="confirmed",
                        source_citation=line,
                    ))
            if "country" in line.lower() or "location" in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    entities.append(EntityFound(
                        value=parts[1].strip(),
                        entity_type="name",
                        confidence="confirmed",
                        source_citation=line,
                        metadata={"data_type": "location"},
                    ))

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0 or len(entities) > 0,
        )


TOOLS = [PhoneInfogaTool()]
