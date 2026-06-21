"""Declarative CLI tools — one generic runner, many tools defined as specs.

Mirror of http_tools.py for command-line OSINT tools (theHarvester, linkook,
naminter, socid_extractor, ...). Each tool is a CliTool(spec): a binary +
install command + an argv template (with {selector}) + a small extractor that
pulls entities from stdout. Execution is timeout-bounded (collectors must not hang).
Raw stdout is always logged for the supervisor; extraction is best-effort.

Wiring a new CLI tool = adding a spec to TOOLS, no new class. All four specs below
were install-and-run validated by per-tool research agents (see docs/capability_research).
"""
import re
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


# =================== socid_extractor (url -> identity record) ===================
_SOCID_NAME_FIELDS = {"name", "fullname", "full_name", "real_name", "realname"}
_SOCID_USER_FIELDS = {"username", "uid", "user_id", "id", "gravatar_username",
                      "nickname", "login", "screen_name"}
_SOCID_EMAIL_FIELDS = {"email", "gravatar_email"}


def _socid_extract(selector, stdout):
    """Parse socid_extractor 'key: value' lines into entities (defensive)."""
    entities, seen = [], set()
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line or ":" not in line or line.startswith("Analyzing URL"):
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if not key or not val:
            continue
        if key in _SOCID_NAME_FIELDS:
            etype, conf = "name", "probable"
        elif key in _SOCID_EMAIL_FIELDS:
            etype, conf = "email", "probable"
        elif key in _SOCID_USER_FIELDS:
            etype, conf = "username", "probable"
        elif val.startswith(("http://", "https://")):
            etype, conf = "url", "possible"
        else:
            continue
        dedup = (etype, val.lower())
        if dedup in seen:
            continue
        seen.add(dedup)
        entities.append(_E(val, etype, conf, f"socid_extractor: {key}"))
    return entities


# =================== linkook (username -> linked accounts) ===================
_LINKOOK_URL_LINE = re.compile(r"^\s*(?:\[\+\]\s*)?([^:\n]+?):\s*(https?://\S+)\s*$")
_LINKOOK_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _extract_linkook(selector, stdout):
    """Profile URLs -> url (confirmed); linked emails -> email; related usernames -> username."""
    out, seen = [], set()
    sel = (selector or "").strip().lower()

    def add(value, etype, conf, cite):
        v = str(value).strip()
        key = (etype, v.lower())
        if not v or key in seen:
            return
        seen.add(key)
        out.append(_E(v, etype, conf, cite))

    for line in stdout.splitlines():
        m = _LINKOOK_URL_LINE.match(line)
        if m:
            platform = m.group(1).strip().lstrip("[+] ").strip()
            url = m.group(2).strip().rstrip(".,")
            add(url, "url", "confirmed", f"linkook: {platform} profile")
    for line in stdout.splitlines():
        if "email" in line.lower() and "@" in line:
            for em in _LINKOOK_EMAIL.findall(line):
                add(em, "email", "probable", "linkook: linked email")
    for line in stdout.splitlines():
        m = re.match(r"^\s*Related Usernames:\s*(.+)$", line)
        if m:
            for u in re.split(r"[,\s]+", m.group(1).strip()):
                u = u.strip().strip(".,")
                if u and u.lower() != sel:
                    add(u, "username", "probable", "linkook: related username")
    return out


# =================== theHarvester (domain -> emails/hosts/ips) ===================
import os as _os, re as _re, glob as _glob, json as _json, tempfile as _tempfile

_TH_OUTDIR = _tempfile.gettempdir()


def _th_outbase(selector):
    safe = _re.sub(r"[^A-Za-z0-9._-]", "_", selector or "x")
    return _os.path.join(_TH_OUTDIR, f"theharvester_{safe}")


def _theharvester_extract(selector, stdout):
    """Read the JSON report theHarvester wrote to <outbase>.json (stdout isn't parseable)."""
    base = _th_outbase(selector)
    path = base + ".json"
    data = None
    try:
        with open(path, encoding="utf-8") as fh:
            data = _json.load(fh)
    except Exception:
        for cand in sorted(_glob.glob(base + "*.json")):
            try:
                with open(cand, encoding="utf-8") as fh:
                    data = _json.load(fh)
                break
            except Exception:
                continue
    if not isinstance(data, dict):
        return []

    out, seen = [], set()
    ip_re = _re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^[0-9A-Fa-f:]+:[0-9A-Fa-f:]+$")
    host_re = _re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    def add(value, etype, cite):
        value = (value or "").strip().rstrip(".")
        if not value:
            return
        key = (etype, value.lower())
        if key in seen:
            return
        seen.add(key)
        conf = "probable" if etype == "email" else "possible"
        out.append(_E(value, etype, conf, cite, {"selector": selector}))

    for em in data.get("emails", []) or []:
        if isinstance(em, str) and "@" in em:
            add(em, "email", "theHarvester emails")
    for ip in data.get("ips", []) or []:
        if isinstance(ip, str) and ip_re.match(ip.strip()):
            add(ip, "ip_v6" if ":" in ip else "ip_v4", "theHarvester dns")
    for key, cite in (("hosts", "theHarvester hosts"), ("vhosts", "theHarvester vhosts")):
        for entry in data.get(key, []) or []:
            if not isinstance(entry, str):
                continue
            entry = entry.strip()
            if ":" in entry and not entry.lower().startswith(("http", "[")):
                host, _, ip = entry.partition(":")
                host, ip = host.strip(), ip.strip()
                if host_re.match(host):
                    add(host, "domain", cite)
                if ip_re.match(ip):
                    add(ip, "ip_v6" if ":" in ip else "ip_v4", cite)
                elif host_re.match(ip):
                    add(ip, "domain", cite)
            else:
                if host_re.match(entry):
                    add(entry, "domain", cite)
    # cap noise (wildcard-cert domains can explode into 1000s)
    return out[:300]


# =================== naminter (username -> profile URLs, anti-bot) ===================
NAMINTER_LAUNCHER = r"C:\Users\cis37\osint-investigator-v3\.naminter_shims\naminter_run.py"
_NAMINTER_LINE = re.compile(r"^\+\s*\[(?P<site>[^\]]+)\]\s+(?P<url>https?://\S+)")


def _extract_naminter(selector, stdout):
    """Found profile URLs from naminter console output -> url entities."""
    out, seen = [], set()
    for line in (stdout or "").splitlines():
        m = _NAMINTER_LINE.match(line.strip())
        if not m:
            continue
        url = m.group("url").rstrip(".,)")
        site = m.group("site").strip()
        if url in seen:
            continue
        seen.add(url)
        out.append(_E(url, "url", "probable", f"naminter: {site}",
                      {"site": site, "username": selector}))
    return out


TOOLS = [
    CliTool(
        name="theharvester",
        description="Domain/org recon: emails, subdomains/hosts, IPs from keyless free "
                    "OSINT sources (crtsh, duckduckgo, otx, rapiddns, hackertarget, certspotter).",
        input_types=["domain"], output_types=["email", "domain", "ip_v4"],
        binary="theHarvester", install_command="pipx install theHarvester",
        command=["theHarvester", "-d", "{selector}",
                 "-b", "crtsh,duckduckgo,otx,rapiddns,hackertarget,certspotter",
                 "-l", "200", "-n",
                 "-f", _os.path.join(_TH_OUTDIR, "theharvester_{selector}.thv")],
        timeout=180, extract=_theharvester_extract),

    CliTool(
        name="linkook",
        description="Scan a username for connected social accounts, linked emails, and "
                    "related usernames across platforms (sock-puppet pivoting).",
        input_types=["username"], output_types=["url", "email", "username"],
        binary="linkook", install_command="pip install linkook",
        command=["linkook", "{selector}", "--show-summary", "--no-color", "--concise"],
        timeout=180, extract=_extract_linkook, success_substrings=["Scan Summary", "Found"]),

    CliTool(
        name="naminter",
        description="Username enumeration via WhatsMyName (~700 sites) with curl-cffi browser "
                    "impersonation to beat Cloudflare; complements sherlock/maigret.",
        input_types=["username"], output_types=["url"],
        binary="naminter", install_command="pip install naminter",
        command=["python", NAMINTER_LAUNCHER, "-u", "{selector}", "--skip-validation",
                 "--no-color", "--no-progressbar", "--filter-exists", "--timeout", "15",
                 "--max-tasks", "50"],
        timeout=240, extract=_extract_naminter, success_substrings=["+ ["]),

    CliTool(
        name="socid_extractor",
        description="Extract a structured identity record (name, username, email, ids) from a "
                    "social/profile URL. Key url->identity pivot tool; 100+ sites.",
        input_types=["url"], output_types=["name", "email", "username", "url"],
        binary="socid_extractor", install_command="pip install socid-extractor",
        command=["socid_extractor", "--url", "{selector}"], timeout=60, extract=_socid_extract),
]
