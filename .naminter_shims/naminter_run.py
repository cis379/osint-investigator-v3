"""Windows launcher for naminter: stubs out uvloop (Unix-only) and weasyprint
(PDF, needs native libs) so the CLI runs on Windows for JSON/CSV/HTML output.
Usage: python naminter_run.py <naminter CLI args...>
"""
import sys, types, asyncio

_uv = types.ModuleType("uvloop")
_uv.run = lambda coro, *a, **k: asyncio.run(coro)
_uv.install = lambda *a, **k: None
_uv.new_event_loop = asyncio.new_event_loop
sys.modules["uvloop"] = _uv

_wp = types.ModuleType("weasyprint")
class _HTML:
    def __init__(self, *a, **k):
        raise RuntimeError("weasyprint unavailable on this platform; PDF export disabled")
    def write_pdf(self, *a, **k):
        raise RuntimeError("weasyprint unavailable on this platform; PDF export disabled")
_wp.HTML = _HTML
sys.modules["weasyprint"] = _wp

from naminter.cli.main import entry_point
entry_point()
