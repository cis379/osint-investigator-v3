You are launching an OSINT investigation. The user provided this selector: $ARGUMENTS

This slash command is a thin, portable entry point. The canonical launch procedure lives in
the vendor-neutral skill **`skills/investigate.md`** (which then hands off to
`skills/supervisor.md`). Follow it exactly.

## Do this now
1. **Read `skills/investigate.md`** and follow its steps to:
   - detect the selector type,
   - create the investigation workspace (auto-inits the log),
   - load the honest capability view (`plan_collection` / `get_selector_capability`),
   - and **become the Supervisor**.
2. **Then read `skills/supervisor.md`** and run the investigation loop from there.

## Conventions (both apply on macOS, Linux, and Windows)
- **Run every command from the repository root.** The skills use `sys.path.insert(0, '.')`
  and relative paths — they resolve correctly only when the working directory is the repo root.
- Activate the project virtualenv first if you created one: `source .venv/bin/activate`
  (Windows: `.venv\Scripts\Activate.ps1`).
- Collection goes through the three lines only (`collect.py` / web-searcher / active-collector);
  the supervisor tiers findings and commits the graph via `graph_commit.py`. Never hand-write
  bespoke collection.

## Non-negotiable rules (from the skills)
- NEVER hallucinate findings — every finding traces to specific tool output, cited.
- Distinguish confirmed vs. inferred; tier by confidence; keep weak hits as `possible`.
- The user is in control and can redirect at any time.
- Log everything to `investigation.md`.
