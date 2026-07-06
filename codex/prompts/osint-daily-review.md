---
description: Run the read-only OSINT daily review (surfaces bugs/gaps; never edits)
---
Run from the repository root. Read `.claude/commands/osint-daily-review.md` and follow it exactly.

It is a READ-ONLY audit: run `python scripts/health_check.py`, scan recent `investigations/INV-*/`
for tool failures / "needs key" / repeated gaps / over-claims, re-skim the supervisor-logged section
of `system/BACKLOG.md`, then APPEND any new bugs/gaps to the backlog and report a short summary.
Do not fix anything in the review — fixes happen later via the System Manager's change protocol.
