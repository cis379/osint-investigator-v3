import json
import os
import subprocess
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class EntityFound:
    value: str
    entity_type: str
    confidence: str  # "confirmed" | "likely" | "possible"
    source_citation: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class ToolResult:
    tool_name: str
    query: str
    query_type: str
    timestamp: str
    raw_output: str
    entities_found: list[EntityFound]
    success: bool
    error: str = ""
    # B16: tool-level diagnostics so an EMPTY result is honest about WHY it's empty.
    # success stays transport-level (did the fetch/command work); this channel lets the
    # supervisor tell "source genuinely had nothing" from "rows returned but filtered to
    # zero" from "the extractor crashed" (a code bug that used to read as 'no findings').
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "tool_name": self.tool_name,
            "query": self.query,
            "query_type": self.query_type,
            "timestamp": self.timestamp,
            "raw_output": self.raw_output,
            "entities_found": [e.to_dict() for e in self.entities_found],
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class BaseTool(ABC):
    name: str = "base"
    description: str = ""
    input_types: list[str] = []
    output_types: list[str] = []
    method: str = "cli"  # "cli" | "api" | "library"
    install_command: str = ""

    def check_installed(self) -> bool:
        if self.method == "cli":
            return shutil.which(self.name) is not None
        return True

    def install(self) -> bool:
        if not self.install_command:
            return False
        try:
            subprocess.run(
                self.install_command.split(),
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def run_command(self, cmd: list[str], timeout: int = 120) -> tuple[str, str, int]:
        # Force UTF-8 on both sides: decode our capture as UTF-8 (errors="replace"
        # so odd bytes never crash parsing), and tell the child process (maigret,
        # sherlock, holehe, theHarvester) to emit UTF-8 too. Without this, Windows
        # defaults to cp1252 and Unicode-heavy tools throw 'charmap' encode errors.
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except FileNotFoundError:
            return "", f"Command not found: {cmd[0]}", -1

    def make_result(self, query: str, query_type: str, raw_output: str,
                    entities: list[EntityFound], success: bool, error: str = "",
                    metadata: dict | None = None) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            query=query,
            query_type=query_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_output=raw_output,
            entities_found=entities,
            success=success,
            error=error,
            metadata=metadata or {},
        )

    @abstractmethod
    def query(self, selector: str, selector_type: str) -> ToolResult:
        pass
