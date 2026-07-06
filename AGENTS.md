# AGENTS.md — how any coding agent drives this system

This file is read automatically by **OpenAI Codex** (and other AGENTS.md-aware agents). It is the
**vendor-neutral driver** for OSINT Investigator v3. The analyst logic lives in plain-Markdown
**skills** under `skills/`; this file tells the agent how to launch them. Claude Code users get the
same behavior via `.claude/commands/` and the skills — **the engine is identical across vendors.**

> **You (the agent) are the analyst brain. The Python in `src/` is your hands.** You read a skill,
> then run `python -m src.tools.…` commands and reason over the raw output. Nothing in the engine is
> vendor-specific.

---

## Ground rules (always)
1. **Run every command from the repository root.** Skills use `sys.path.insert(0, '.')` and relative
   paths — they only resolve when the working directory is the repo root.
2. **Use the project virtualenv.** If `.venv/` exists, activate it first
   (`source .venv/bin/activate`; Windows: `.venv\Scripts\Activate.ps1`). If it doesn't exist yet,
   run `./bootstrap.sh` (see `SETUP.md`).
3. **Collect only through the three registered lines** — the structured gatherer (`collect.py`),
   the web-searcher, and the active-collector. Never hand-write bespoke scraping; if a capability is
   missing, check `plan_collection` and log a GAP. This preserves the raw/analysis split and audit trail.
4. **No hallucination.** Every finding traces to specific tool output, cited. Tier by confidence
   (`highly_likely` / `probable` / `possible`); keep weak hits as `possible`, never drop them.

---

## The three things a user asks for → what you do

### 1. "investigate `<selector>`" (run an OSINT investigation)
This is the main workflow. When the user asks to investigate a domain / email / username / name /
IP / phone / crypto address (etc.):
1. **Read `skills/investigate.md`** and follow it — detect the selector type, create the workspace
   (auto-inits the log), load the honest capability view, and **become the Supervisor**.
2. **Then read `skills/supervisor.md`** and run the investigation loop: plan → collect across the
   three lines → analyze & tier → commit the graph (`graph_commit.py`) → brief the user → pivot →
   red-team gate → report. The user can redirect at any time.

Quick capability check for a seed (what will actually run):
```
python -c "import sys,json; sys.path.insert(0,'.'); from src.tools.registry import plan_collection; print(json.dumps(plan_collection('example.com','domain'), indent=2))"
```

### 2. "maintain the system" / "fix a bug" / "intake a tool" (System Manager)
Read **`skills/system_manager.md`** and follow it. This is the meta-role that maintains the system
without breaking it (health-gated changes on a branch). Its durable memory is the files in `system/`
(VISION, CAPABILITY-LOCK, BACKLOG, CHANGELOG). Run it in its own session, separate from investigations.

### 3. "daily review" (read-only audit)
Read **`.claude/commands/osint-daily-review.md`** and follow it — a read-only sweep that surfaces new
bugs/gaps and appends them to `system/BACKLOG.md`. It never edits. (It's a plain Markdown procedure;
any agent can read and follow it.)

---

## The engine, in one screen (so you can drive it directly)
- **Detect a selector:** `python -c "import sys;sys.path.insert(0,'.');from src.core.selector import detect_selector_type as d;print(d('SEED'))"`
- **Plan collection:** `plan_collection(selector, type)` — the ontology router (structured tools +
  web-search availability + general-username fallback). Nothing is hardcoded.
- **Structured collection (raw, no graph):**
  `python -m src.tools.collect --run-all --selector "SEED" --type TYPE --log "CASE_DIR/investigation.md"`
- **Commit analysis to the graph (supervisor only):**
  `python -m src.tools.graph_commit --graph "CASE_DIR/graph.json" --regen-html "CASE_DIR/graph.html" --case CASE_ID --input "CASE_DIR/_commit.json"`
- **Build the report:** `python -m src.report.build …` (see `skills/report-writer.md`).
- **Health gate (after any change to the system):** `python scripts/health_check.py` → must print `=== HEALTHY ===`.

Outputs per case land in `investigations/INV-YYYYMMDD-NNN/` (graph.json/html, bibliography.html,
investigation.md, report.md/html, state.json).

---

## Optional: literal `/investigate` slash command in Codex
Codex custom prompts (`~/.codex/prompts/*.md`) are user-global and now deprecated in favor of Codex
skills, but if you want the exact slash-command feel, copy the ready-made prompt files:
```
cp codex/prompts/*.md ~/.codex/prompts/      # then use /prompts:investigate <selector>
```
Either way, the behavior is identical — they just tell Codex to read the same `skills/*.md`.

---

## Where to read more
- **`SETUP.md`** — build the system on a fresh machine (bootstrap, deps, verify).
- **`MIGRATION.md`** — move it to a new machine.
- **`docs/SYSTEM-SUMMARY.md`** — full architecture. **`system/VISION.md`** — purpose + principles.
- **`system/CAPABILITY-LOCK.md`** — what must not regress (read before changing the system).
