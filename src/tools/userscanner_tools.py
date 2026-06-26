"""user_scanner — email account-existence across ~100 third-party platforms (structured line).

Adopted 2026-06-26 after a hands-on validation vs holehe: on the same email, user-scanner
returned a DETERMINATE verdict on ~80% of ~100 sites, where holehe was ~63% rate-limited
(holehe's `[x]` are non-answers — why HoleheTool is lead-only, B4). Different/complementary
site mix (keyless, httpx). A more reliable second email enumerator.

Scope decisions (from the validation):
  - EMAIL ONLY. Its username mode duplicates our best-in-class (sherlock/maigret/naminter/
    linkook) and is noisier — not wired.
  - NO `--hudson` (redundant with our hudsonrock_email, AND it calls input() -> would hang).
  - NO `--allow-loud` (loud sites send a password-reset/notification email to the TARGET — OPSEC).
  - `--no-nsfw` on. Only `Found`/`Registered` statuses are signal; negatives/WAF-errors are
    NOT proof of absence and are discarded. Hits emitted `possible` (tool-self-claimed; the
    supervisor re-tiers).

It is a STRUCTURED-line tool (queries third-party platforms about the selector, like holehe);
it does NOT touch the target's own infrastructure (that's the active-collection line).
"""
import os
import re
import glob
import json
import tempfile

from .base import BaseTool, EntityFound

_OUTDIR = tempfile.gettempdir()


class UserScannerTool(BaseTool):
    name = "user_scanner"
    description = ("Email account-existence across ~100 third-party platforms (keyless). More "
                   "determinate than holehe (which is heavily rate-limited). Only registered-hits "
                   "are signal; negatives/WAF-errors are unreliable. Hits emitted `possible`.")
    input_types = ["email"]
    output_types = ["account", "email"]
    method = "cli"
    install_command = "pip install user-scanner"

    _FOUND = {"found", "registered"}

    def check_installed(self) -> bool:
        out, err, code = self.run_command(["user-scanner", "--version"])
        return code == 0 or "scanner" in (out + err).lower()

    def _outpath(self, selector):
        safe = re.sub(r"[^A-Za-z0-9._@-]", "_", selector or "x")
        return os.path.join(_OUTDIR, f"userscanner_{safe}.json")

    def _load_json(self, out_json):
        for cand in [out_json] + sorted(glob.glob(out_json.replace(".json", "*.json"))):
            try:
                with open(cand, encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                continue
        return None

    def query(self, selector, selector_type):
        if selector_type != "email":
            return self.make_result(selector, selector_type, "", [], False,
                                    "user_scanner is wired for email only")
        if not self.check_installed():
            return self.make_result(selector, selector_type, "", [], False,
                                    f"user_scanner not installed. Install: {self.install_command}")

        out_json = self._outpath(selector)
        # --no-nsfw skips adult sites; NO --allow-loud (OPSEC); NO --hudson (redundant/hangs).
        cmd = ["user-scanner", "-e", selector, "-f", "json", "-o", out_json,
               "--no-nsfw", "--only-found"]
        out, err, code = self.run_command(cmd, timeout=200)
        raw = (out + err)[:8000]

        data = self._load_json(out_json)
        try:
            os.remove(out_json)
        except OSError:
            pass

        entities, seen = [], set()
        if isinstance(data, list):
            for r in data:
                if not isinstance(r, dict):
                    continue
                if str(r.get("status", "")).strip().lower() not in self._FOUND:
                    continue  # negatives / errors / skipped are non-signal
                site = str(r.get("site_name", "")).strip()
                if not site:
                    continue
                url = (r.get("url") or "").strip()
                extra = r.get("extra") if isinstance(r.get("extra"), dict) else {}
                value = url or f"{site} (email registered)"
                key = ("account", value.lower())
                if key in seen:
                    continue
                seen.add(key)
                entities.append(EntityFound(
                    value=value, entity_type="account", confidence="possible",
                    source_citation=f"user_scanner: {selector} registered on {site}",
                    metadata={"platform": site, "category": r.get("category"),
                              "selector": selector, "url": url, "profile": extra}))
                # occasional username->email pivot inside the scraped profile
                pivot = str(extra.get("email") or "").strip()
                if pivot and "@" in pivot and pivot.lower() != selector.lower():
                    pk = ("email", pivot.lower())
                    if pk not in seen:
                        seen.add(pk)
                        entities.append(EntityFound(
                            value=pivot, entity_type="email", confidence="possible",
                            source_citation=f"user_scanner: {site} profile exposed email {pivot}",
                            metadata={"platform": site, "from_selector": selector}))

        success = bool(entities) or isinstance(data, list)
        return self.make_result(selector, selector_type, raw, entities, success=success,
                                error="" if success else (err[:200] or f"exit {code}"))


TOOLS = [UserScannerTool()]
