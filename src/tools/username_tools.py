import re
import json
import glob
import shutil
import tempfile
from pathlib import Path
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

        # Use ndjson output so we capture maigret's socid-extractor metadata (linked
        # emails, display names, locations) — not just the profile URLs. maigret writes
        # the ndjson to a report FOLDER (not stdout), so we point it at a temp folder and
        # read it back. Falls back to stdout parsing if no ndjson is produced.
        outdir = tempfile.mkdtemp(prefix="maigret_")
        try:
            stdout, stderr, code = self.run_command(
                ["maigret", selector, "--no-color", "--timeout", "10", "--no-progressbar",
                 "--json", "ndjson", "--folderoutput", outdir],
                timeout=300,
            )
            ndjson_text = ""
            # maigret names the file "report_<user>_ndjson.json" (note .json extension)
            for fp in glob.glob(str(Path(outdir) / "*ndjson*")):
                try:
                    ndjson_text += Path(fp).read_text(encoding="utf-8", errors="replace") + "\n"
                except OSError:
                    pass
        finally:
            shutil.rmtree(outdir, ignore_errors=True)

        raw_output = (ndjson_text + "\n" + stdout + stderr)[:8000]
        entities = []
        seen = set()

        def add(value, etype, conf, cite):
            key = (etype, value)
            if value and key not in seen:
                seen.add(key)
                entities.append(EntityFound(value=value, entity_type=etype,
                                            confidence=conf, source_citation=cite))

        # Each ndjson line is one found account: {site, url_user, status:{ids:{...}}}
        parsed_ndjson = False
        for line in ndjson_text.splitlines():
            line = line.strip()
            if not (line.startswith("{") and line.endswith("}")):
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            parsed_ndjson = True
            # 'site' is an object; the site NAME is in 'sitename' (or site.source).
            sd = rec.get("site")
            site = rec.get("sitename") or (sd.get("source") if isinstance(sd, dict) else sd) or ""
            url = rec.get("url_user") or rec.get("url") or ""
            if url:
                add(url, "url", "confirmed", f"maigret: account on {site}")
            ids = (rec.get("status") or {}).get("ids") or rec.get("ids") or {}
            for k, v in ids.items():
                vals = v if isinstance(v, list) else [v]
                for val in vals:
                    val = str(val).strip()
                    lk = k.lower()
                    if "email" in lk and "@" in val:
                        add(val, "email", "probable", f"maigret socid-extractor ({site}): {k}")
                    elif lk in ("fullname", "name", "first_name", "last_name", "username"):
                        etype = "username" if lk == "username" else "name"
                        add(val, etype, "probable", f"maigret socid-extractor ({site}): {k}")

        # Fallback: parse plain stdout if no ndjson records were emitted.
        if not parsed_ndjson:
            for line in stdout.splitlines():
                m = re.search(r'https?://[^\s]+', line)
                if m:
                    add(m.group(0), "url", "confirmed", line.strip())
                em = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                if em:
                    add(em.group(0), "email", "probable", line.strip())

        return self.make_result(
            selector, selector_type, raw_output, entities,
            success=code == 0 or len(entities) > 0,
        )


TOOLS = [SherlockTool(), MaigretTool()]
