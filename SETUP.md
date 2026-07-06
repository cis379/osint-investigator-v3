# SETUP — build this system from scratch on a new machine

This is the complete, assume-nothing guide to stand up **OSINT Investigator v3** on a
fresh machine (macOS, Linux, or Windows). If you have never seen this project before,
follow this top to bottom and you will end with a working, health-checked system.

> **What this is (30-second version).** A multi-agent OSINT investigation system. You
> give it a *seed* (a domain, email, username, name, IP, phone, crypto address, …); an
> **AI coding agent** (Claude Code *or* OpenAI Codex — your choice) reads the analyst
> "skills" in `skills/*.md` and drives a **Python engine** (58 OSINT tools, an ontology
> router, a graph, a report generator). The AI is the brain; the Python is the hands.
> **The AI vendor is swappable** — see "Drive it" below.

---

## 0. Prerequisites

| Need | Why | Install |
|---|---|---|
| **Python 3.10+** | the engine | macOS: `brew install python@3.12` · Linux: system pkg · Windows: python.org |
| **Git** | clone the repo | preinstalled on macOS/Linux; git-scm.com on Windows |
| **A coding agent** | drives the system | **Claude Code** *or* **OpenAI Codex CLI** (either works — see §6) |
| Homebrew (macOS only) | installs `exiftool` | https://brew.sh (optional but recommended) |

Nothing else is mandatory. Every OSINT *CLI* tool and every API key is **optional** —
the system is built to **degrade gracefully** (a missing tool just reports "not installed";
a missing key makes that one tool skip with a clear message).

---

## 1. The fast path (macOS / Linux) — one command

```bash
git clone <your-repo-url> osint-investigator-v3
cd osint-investigator-v3
./bootstrap.sh
```

`bootstrap.sh` does everything and ends by running the health gate. When you see
**`=== BOOTSTRAP COMPLETE — system is HEALTHY ===`**, you're done.

Want the fastest possible core-only setup (skip the optional CLI tools)?
```bash
./bootstrap.sh --core
```

### What bootstrap.sh does (so there's no magic)
1. Verifies Python 3.10+.
2. Creates a virtualenv `.venv/` and installs the **core** Python deps (`requirements.txt`).
3. Installs `naminter` + `ignorant` **into the venv** (our code launches them via the venv's Python).
4. Best-effort installs the standalone OSINT CLI tools via **pipx** (failures are non-fatal).
5. Best-effort installs `exiftool` (Homebrew on macOS, apt on Linux).
6. Copies `.env.example` → `.env` (for optional API keys).
7. Runs `scripts/health_check.py` and prints GREEN/RED.

Every new shell: `source .venv/bin/activate` before you use the system.

---

## 2. Manual path (or Windows, or if bootstrap fails)

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install naminter ignorant      # launched via our venv python — must be in the venv
cp .env.example .env                 # optional keys; Windows: copy .env.example .env
python scripts/health_check.py       # must print "=== HEALTHY ==="
```

That is the **required** minimum: with just the core deps, the health gate goes green and
**every HTTP/API tool works** (whois/rdap, dns, crt.sh, wayback, urlscan, shodan, ripestat,
geolocation, breach checks, tracker fingerprinting, web search, …). The CLI tools in §3 are
enrichment on top.

---

## 3. External OSINT CLI tools (optional enrichment)

These are separate programs the engine shells out to. Install any/all; skip the rest.
`pipx` is preferred for the standalone ones (isolated envs, put on PATH). The two marked
**venv** must go in the project venv because our code imports/launches them via its Python.

| Tool | Install | Selector | What it adds |
|---|---|---|---|
| sherlock | `pipx install sherlock-project` | username | profiles across 400+ sites |
| maigret | `pipx install maigret` | username | extended username enumeration |
| naminter | `pip install naminter` **(venv)** | username | WhatsMyName (~700 sites), beats Cloudflare |
| linkook | `pipx install linkook` | username | connected accounts / linked emails |
| holehe | `pipx install holehe` | email | account existence (lead-only; rate-limited) |
| socialscan | `pipx install socialscan` | email/username | registered-platform check |
| user-scanner | `pipx install user-scanner` | email | ~100 sites, more reliable than holehe |
| theHarvester | `pipx install theHarvester` | domain | emails/subdomains/hosts |
| dnsrecon | `pipx install dnsrecon` | domain | DNS enumeration |
| socid_extractor | `pipx install socid-extractor` | url | identity record from server-rendered profiles |
| ignorant | `pip install ignorant` **(venv)** | phone | account existence by phone ("holehe for phone") |
| exiftool | `brew install exiftool` (macOS) | image/file | media metadata (EXIF/GPS) |

After installing more tools, re-run `python scripts/health_check.py` — it should stay green
(the gate tests plumbing, not tool presence; tools degrade gracefully).

---

## 4. API keys (all optional)

Copy `.env.example` to `.env` and fill any you have. **Everything works without them** —
each keyed tool degrades to a clear "needs KEY" skip. The two worth having first:

- `OSINT_NAVIGATOR_API_KEY` — used by the red-team gate for coverage-gap checks (subscription).
- `SPYONWEB_API_KEY` — free key; makes the reverse-tracker (anti-over-merge) chain self-serve.

`.env` is **gitignored** — it never travels in the repo. Move it to the new machine by hand
(see MIGRATION.md).

---

## 5. Verify

```bash
python scripts/health_check.py
```
Expected tail:
```
=== HEALTHY ===
```
That confirms: the registry loads all 58 tools, the ontology router works, and all 3
regression suites pass (split-invariants, ontology honesty, selector detection).

---

## 6. Drive it — with Claude Code **or** Codex (vendor-agnostic)

The analyst logic lives in plain-Markdown **skills** (`skills/*.md`) that any capable coding
agent can read. Only the thin *entry layer* differs per vendor:

- **Claude Code** — open the repo in Claude Code and run the slash command:
  ```
  /investigate example.com
  ```
  (defined in `.claude/commands/investigate.md`; also `/system-manager`, `/osint-daily-review`.)

- **OpenAI Codex** — open the repo in Codex. It reads **`AGENTS.md`** at the repo root, which
  tells it how to launch an investigation and points at the same `skills/*.md`. Start with:
  ```
  investigate example.com
  ```
  See **AGENTS.md** for the exact Codex commands and conventions.

Under the hood both agents do the identical thing: read the skills, run
`python -m src.tools.collect …` / `graph_commit.py`, and produce the same outputs. **No engine
behavior changes between vendors.**

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `health_check` RED on import | core deps missing — `pip install -r requirements.txt` inside `.venv` |
| a CLI tool reports "not installed" | install it from §3 (optional) |
| `naminter`/`ignorant` never run | they must be in the **project venv**, not pipx — `pip install naminter ignorant` with `.venv` active |
| `exiftool` not found (macOS) | `brew install exiftool` |
| keyed tool says "needs KEY" | expected without the key — add it to `.env` or ignore |
| Windows PowerShell blocks the venv activate | `Set-ExecutionPolicy -Scope Process RemoteSigned` then re-activate |

For the meaning of the system, its architecture, and how to maintain it, read
`docs/SYSTEM-SUMMARY.md` and `system/VISION.md`. For moving it to a new machine, read
`MIGRATION.md`.
