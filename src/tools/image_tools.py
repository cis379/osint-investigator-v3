import json
import os
import platform
import shutil
import tempfile
from pathlib import Path

import requests

from .base import BaseTool, ToolResult, EntityFound

# OS-aware install hint so the "not installed" message + BaseTool.install() are correct
# on whatever platform we're running (macOS: brew, Linux: apt, Windows: winget user-scope).
_SYS = platform.system()
_EXIFTOOL_INSTALL = {
    "Darwin": "brew install exiftool",
    "Linux": "sudo apt-get install -y libimage-exiftool-perl",
}.get(_SYS, "winget install OliverBetz.ExifTool --scope user")  # Windows default


class ExifToolWrapper(BaseTool):
    name = "exiftool"
    description = "Image/file metadata extraction - GPS, camera, timestamps (exiftool)"
    input_types = ["image", "file", "url"]
    output_types = ["coordinates", "date"]
    method = "cli"
    install_command = _EXIFTOOL_INSTALL

    # Windows-only fallback locations so we resolve the binary even when a freshly winget/choco-
    # installed exiftool isn't yet on the *current* process's PATH (G11). Harmless elsewhere:
    # on macOS/Linux brew/apt put exiftool on PATH immediately, so shutil.which() finds it and
    # these paths are simply skipped (isfile == False).
    _CANDIDATE_PATHS = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "ExifTool", "ExifTool.exe"),
        r"C:\ProgramData\chocolatey\bin\exiftool.exe",
    ]

    def _bin(self) -> str:
        found = shutil.which("exiftool")
        if found:
            return found
        for p in self._CANDIDATE_PATHS:
            if p and os.path.isfile(p):
                return p
        return "exiftool"  # last resort; will fail cleanly if truly absent

    def check_installed(self) -> bool:
        stdout, stderr, code = self.run_command([self._bin(), "-ver"])
        return code == 0

    def _resolve_to_path(self, selector: str, selector_type: str):
        """Return (local_path, tempfile_to_cleanup_or_None). Downloads remote URLs."""
        if selector_type == "url" or selector.lower().startswith(("http://", "https://")):
            resp = requests.get(selector, timeout=20, stream=True)
            resp.raise_for_status()
            suffix = Path(selector.split("?")[0]).suffix or ".bin"
            tmp = tempfile.NamedTemporaryFile(prefix="exif_", suffix=suffix, delete=False)
            for chunk in resp.iter_content(8192):
                tmp.write(chunk)
            tmp.close()
            return tmp.name, tmp.name
        return selector, None

    def query(self, selector: str, selector_type: str) -> ToolResult:
        cleanup = None
        try:
            path, cleanup = self._resolve_to_path(selector, selector_type)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, f"Could not fetch URL: {e}")

        try:
            # -j JSON, -n numeric (decimal GPS instead of DMS strings)
            stdout, stderr, code = self.run_command([self._bin(), "-j", "-n", path], timeout=30)
            raw_output = (stdout + stderr)[:8000]
            entities = []

            try:
                meta = json.loads(stdout)[0] if stdout.strip().startswith("[") else {}
            except (json.JSONDecodeError, IndexError):
                meta = {}

            lat = meta.get("GPSLatitude")
            lon = meta.get("GPSLongitude")
            if lat is not None and lon is not None:
                entities.append(EntityFound(
                    value=f"{lat},{lon}",
                    entity_type="coordinates",
                    confidence="confirmed",
                    source_citation=f"exiftool GPSLatitude/GPSLongitude in {Path(path).name}",
                    metadata={"latitude": lat, "longitude": lon},
                ))

            for tkey in ("DateTimeOriginal", "CreateDate", "ModifyDate"):
                if meta.get(tkey):
                    entities.append(EntityFound(
                        value=str(meta[tkey]),
                        entity_type="date",
                        confidence="confirmed",
                        source_citation=f"exiftool {tkey}",
                        metadata={"field": tkey},
                    ))
                    break

            return self.make_result(selector, selector_type, raw_output, entities, success=code == 0)
        finally:
            if cleanup:
                Path(cleanup).unlink(missing_ok=True)


TOOLS = [ExifToolWrapper()]
