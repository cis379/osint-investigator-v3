"""Declarative CLI tools — one generic runner, many tools defined as specs.

Mirror of http_tools.py for command-line OSINT tools (theHarvester, linkook,
naminter, socid_extractor, ...). Each tool is a CliTool(spec): a binary +
install command + an argv template (with {selector}) + a small extractor that
pulls entities from stdout. Execution is timeout-bounded (collectors must not hang).
Raw stdout is always logged for the supervisor; extraction is best-effort.

Wiring a new CLI tool = adding a spec to TOOLS, no new class.
"""
import shutil

from .base import BaseTool, EntityFound


class CliTool(BaseTool):
    method = "cli"

    def __init__(self, *, name, description, input_types, output_types, binary,
                 install_command, command, timeout=180, extract=None,
                 success_substrings=None):
        self.name = name
        self.description = description
        self.input_types = input_types
        self.output_types = output_types
        self._binary = binary
        self.install_command = install_command
        self._command = command          # list of argv tokens; {selector} is substituted
        self._timeout = timeout
        self._extract = extract
        self._success_substrings = success_substrings

    def check_installed(self) -> bool:
        if shutil.which(self._binary):
            return True
        out, err, code = self.run_command([self._binary, "--version"])
        return code == 0

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"{self.name} doesn't accept {selector_type}")
        if not self.check_installed():
            return self.make_result(selector, selector_type, "", [], False,
                                    f"{self.name} not installed. Install: {self.install_command}")

        cmd = [tok.replace("{selector}", selector) for tok in self._command]
        out, err, code = self.run_command(cmd, timeout=self._timeout)
        raw = (out + err)[:8000]

        entities = []
        if self._extract:
            try:
                entities = self._extract(selector, out) or []
            except Exception:
                entities = []  # best-effort; raw is always logged

        if self._success_substrings:
            success = any(s in raw for s in self._success_substrings) or bool(entities)
        else:
            success = code == 0 or bool(entities)

        return self.make_result(selector, selector_type, raw, entities,
                                success=success,
                                error="" if success else (err[:200] or f"exit {code}"))


def _E(value, etype, conf, cite, meta=None):
    return EntityFound(value=str(value), entity_type=etype, confidence=conf,
                       source_citation=cite, metadata=meta or {})


# Specs are added here as the per-tool subagents validate install + command + parsing.
TOOLS = []
