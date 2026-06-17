from .base import BaseTool, ToolResult, EntityFound


class ExifToolWrapper(BaseTool):
    name = "exiftool"
    description = "Image metadata extraction - GPS, camera, timestamps"
    input_types = ["url"]
    output_types = []
    method = "cli"

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command(["exiftool", "-ver"])
        return code == 0

    def query(self, selector: str, selector_type: str) -> ToolResult:
        stdout, stderr, code = self.run_command(
            ["exiftool", selector],
            timeout=30,
        )
        raw_output = stdout + stderr
        entities = []

        for line in stdout.splitlines():
            line = line.strip()
            if "GPS" in line and ":" in line:
                entities.append(EntityFound(
                    value=line.split(":", 1)[1].strip(),
                    entity_type="name",
                    confidence="confirmed",
                    source_citation=line,
                    metadata={"data_type": "gps_coordinate"},
                ))

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0,
        )


TOOLS = [ExifToolWrapper()]
