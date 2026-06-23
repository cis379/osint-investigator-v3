# /osint-daily-review

Run the System Manager's READ-ONLY daily audit of osint-investigator-v3. This NEVER edits the
system — it surfaces health + new gaps/bugs and appends them to the backlog for later fixing.

You are acting as the System Manager in review-only mode (see `skills/system_manager.md`, job D).
Do all of this from the project root, and make NO code/skill/ontology changes:

1. **Health:** run `python scripts/health_check.py`. Record GREEN/RED (if RED, that's the headline —
   the system regressed; report exactly which check failed).
2. **New investigations:** list `investigations/INV-*` created since the last review. For each new
   one, skim `investigation.md` for: tool FAILURES, "needs <KEY>" messages, blocked/rate-limited
   sources, over-claiming, or anything the supervisor logged as a gap.
3. **Backlog drift:** re-skim `system/BACKLOG.md` "Supervisor-logged gaps" — anything new since
   last review?
4. **Append (don't fix):** add any NEW bugs/gaps you found to `system/BACKLOG.md` (use Edit/Write),
   with a dated ID and source case. Do NOT change code or close items here.
5. **Report** a short summary to the user: health status, # new investigations reviewed, new
   bugs/gaps logged (with IDs), and the top 3 things worth fixing next.

Then STOP. Fixes happen later, interactively, via the Manager's change protocol (branch + gate +
revert-on-red). This review is read-only on purpose — an unattended agent must never edit the
live system.

---
To automate: schedule this with `/schedule` (cloud routine) or `/loop 1d /osint-daily-review`
(local interval). It needs access to this repo, so run it where the repo lives.
