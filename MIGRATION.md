# MIGRATION — move this system to a new machine (Windows → Mac)

Two parts: **(A)** what you do on the current Windows machine *before you leave*, and **(B)** what you
do on the new Mac to be *usable on day one*. The engine is already portable and agent-agnostic
(see `SETUP.md` / `AGENTS.md`); this doc is just the transport + first-run.

A clean fresh-clone rebuild has been verified: a bare clone + `requirements.txt` + health gate goes
green with current dependency wheels. So if you follow this, it will come up working.

---

## Part A — before you leave (on the Windows machine, ~10 min)

### A1. Put the repo on a private remote (so the Mac can `git clone` it)
You have no git remote yet. Easiest path (no extra tooling):

1. On github.com, create a **new EMPTY private repo** (no README/.gitignore) — e.g. `osint-investigator-v3`.
2. In this repo folder, wire it up and push **the branch and the tags**:
   ```bash
   git remote add origin https://github.com/<you>/osint-investigator-v3.git
   git push -u origin master
   git push origin --tags        # carries v3-windows-final-2026-07-06 (your preserved V3 baseline)
   ```
   (Prefer the `gh` CLI? `winget install GitHub.cli`, `gh auth login`, then
   `gh repo create osint-investigator-v3 --private --source=. --push` and `git push origin --tags`.)

### A2. Carry the things git does NOT track (they're gitignored on purpose)
These never go in the repo — move them out-of-band (USB, encrypted drive, password manager, etc.):

| Item | Why it's not in git | Carry it? |
|---|---|---|
| **`.env`** | contains API keys (e.g. `OSINT_NAVIGATOR_API_KEY`) | **Yes** — copy the file securely; you'll drop it into the Mac clone. |
| **`investigations/`** | real casework, can be sensitive | Only if you want your case history on the new machine. |
| `.venv/` | machine-specific | **No** — rebuilt by `bootstrap.sh` on the Mac. |
| `.claude/settings.local.json` | local Claude Code settings | Optional; re-create as needed. |

### A3. Sanity check before you push
```bash
python scripts/health_check.py      # expect: === HEALTHY ===
git status                          # expect: clean
```

---

## Part B — on the Mac (day one, ~15–20 min incl. installs)

### B1. Install prerequisites
```bash
# Homebrew (if not present): https://brew.sh
brew install git python@3.12 pipx exiftool
pipx ensurepath
```

### B2. Clone and build
```bash
git clone https://github.com/<you>/osint-investigator-v3.git
cd osint-investigator-v3
./bootstrap.sh                      # venv + core deps + CLI tools + .env scaffold + health gate
```
When you see **`=== BOOTSTRAP COMPLETE — system is HEALTHY ===`**, the engine is up.
(If a few optional CLI tools fail to install, that's fine — they degrade gracefully. Re-run any by
hand from `SETUP.md §3`.)

### B3. Restore your keys and (optionally) casework
```bash
cp /path/to/your/carried/.env  ./.env         # from step A2
cp -R /path/to/your/investigations  ./         # optional, only if you carried it
```

### B4. Install your coding agent and drive it
- **Codex:** install the Codex CLI, open this folder — it reads `AGENTS.md` automatically. Say
  `investigate example.com` (or copy `codex/prompts/*.md` to `~/.codex/prompts/` for a literal
  `/prompts:investigate` slash command).
- **Claude Code:** open this folder; run `/investigate example.com` (or `/system-manager`).

Either agent runs the identical engine. See `AGENTS.md` for the full command map.

### B5. Verify end-to-end
```bash
source .venv/bin/activate
python scripts/health_check.py                 # === HEALTHY ===
python -c "import sys;sys.path.insert(0,'.');from src.tools.registry import plan_collection,get_all_tools;print(len(get_all_tools()),'tools'); import json;print(json.dumps(plan_collection('example.com','domain')['effective_type']))"
```
Then run a real smoke investigation on `example.com` (the domain control case) and confirm you get a
graph + report under `investigations/`.

---

## First-run checklist
- [ ] `git clone` succeeded; `git tag -l` shows `v3-windows-final-2026-07-06`.
- [ ] `./bootstrap.sh` ended HEALTHY.
- [ ] `.env` copied in (keyed tools stop saying "needs KEY").
- [ ] Your agent (Codex/Claude Code) launches an investigation via `AGENTS.md` / the skills.
- [ ] A smoke run on `example.com` produces a graph + report.

## If something's off
- **`bash\r` / bad interpreter on `bootstrap.sh`** — line-ending issue; `.gitattributes` forces LF, but
  if needed: `sed -i '' 's/\r$//' bootstrap.sh` then re-run.
- **health RED on import** — core deps; `source .venv/bin/activate && pip install -r requirements.txt`.
- **a CLI tool missing** — optional; install from `SETUP.md §3` (`pipx install <tool>`), or ignore.
- **`naminter`/`ignorant` don't run** — they must be in the **project venv**: `pip install naminter ignorant` with `.venv` active.

To preserve/return to the exact Windows-era baseline at any time: `git checkout v3-windows-final-2026-07-06`.
