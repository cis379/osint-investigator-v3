---
description: Launch an OSINT investigation from a seed selector
argument-hint: <selector> (domain, email, username, name, IP, phone, crypto address, ...)
---
You are launching an OSINT investigation. The user provided this selector: $ARGUMENTS

Run everything from the repository root, with the project virtualenv active
(`source .venv/bin/activate`; if there is no venv yet, run `./bootstrap.sh` first — see SETUP.md).

1. Read `skills/investigate.md` and follow it exactly: detect the selector type, create the
   investigation workspace (it auto-inits the log), load the honest capability view
   (`plan_collection` / `get_selector_capability`), and BECOME the Supervisor.
2. Then read `skills/supervisor.md` and run the investigation loop from there — plan, collect across
   the three lines, analyze and tier, commit the graph via `graph_commit.py`, brief the user, pivot,
   red-team, report.

Non-negotiable: no hallucinated findings (cite tool output), tier by confidence, keep weak hits as
`possible`, log everything to `investigation.md`, and let the user redirect at any time.
