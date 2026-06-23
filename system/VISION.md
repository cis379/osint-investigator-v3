# VISION — osint-investigator-v3

The stable north star. Detailed current state lives in `docs/SYSTEM-SUMMARY.md`; this is
the purpose + principles that don't change run-to-run.

## Purpose
Take an investigation **seed** (a selector: domain, name, username, email, IP, phone, etc.),
**pivot** through OSINT sources guided by an ontology, and produce a **cited, confidence-tiered
intelligence graph + CTI report**. The job is to make the operator THE expert at external OSINT,
at scale, without ever fabricating a finding.

Scope: **EXTERNAL OSINT only.** Internal-data analysis is a separate system.

## Who runs it
- **Supervisor sessions** run investigations (per-seed; fast; user-interactive).
- **System Manager session** builds + maintains the system (meta; careful; conservative).
They share this repo; the interface between them is `system/BACKLOG.md`.

## Principles (the things that make it trustworthy)
1. **No hallucination.** Every finding traces to a specific tool output or source URL.
2. **Raw/analysis split.** Collectors fetch raw; the supervisor decides what's real, tiers it,
   and builds the graph. Tools are not trusted to grade themselves.
3. **Tier, don't drop.** confirmed / probable / possible. Weak hits stay visible as pivots.
4. **The ontology is the spine.** Routing + pivoting are ontology-driven, never hardcoded.
5. **Two lines.** Structured tools (deterministic) + web-search (judgment) — both essential.
6. **Don't break anything.** A running system that never loses key functionality. Changes are
   health-gated and reversible. (See `CAPABILITY-LOCK.md`.)
7. **Declarative growth.** A new tool is a spec (HttpTool/CliTool), not bespoke plumbing.
8. **Honest about limits.** Gaps are documented (BACKLOG); key-gated/manual capabilities get
   manual guides for the operator, not silent failures.

## Success looks like
The 4 golden investigations keep passing; the health gate stays green; coverage grows
tool-by-tool; gaps shrink or are honestly documented; the operator can always ask the Manager
"what is the system, what's broken, what's missing" and get a grounded answer.
