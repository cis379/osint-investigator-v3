# CHANGELOG — System Manager decision/change log

One line per change: what + why. The Manager appends here every working session. Newest first.

## 2026-06-24 (RT1 — red-team reviewer agent)
- **RT1 done (architectural, user sign-off):** added `skills/red_team.md`, a READ-ONLY adversarial
  reviewer that hardens the analysis before it ships. Prime directive = break every conclusion;
  default verb = down-tier/relabel, never delete (keep weak-but-real as `possible`, clearly labeled —
  "be clear on what it actually is"). Reviews 5 dimensions, led by OVER-MERGES (co-tenancy ≠ co-
  ownership; every `operated_by` on shared infra alone must show an independent corroborator or be
  relabeled `co_hosted_with` + down-tiered): single-source top-tier, attribution-verb drift, citation
  drift, missed disconfirmers/cluster-splits. Outputs `_redteam.json` (challenges + upheld + missed
  hypotheses) and logs a RED-TEAM REVIEW to investigation.md; it never writes the graph.
- **Wired into supervisor.md as Phase 5.5** — a MANDATORY gate before every report PLUS on-demand
  mid-investigation (human or supervisor). Harden loop: dispatch → supervisor reconciles each
  challenge (apply via graph_commit OR defend with the missed corroborator) → re-run ~2 rounds →
  report. Supervisor briefs the user on what was challenged / down-tiered / upheld.
- Locked as CAPABILITY-LOCK item 8 (process control for the no-over-merge discipline). SYSTEM-SUMMARY
  updated (7 skills; red-team gate in the flow). Health + 3 suites GREEN. Next: G14 (tracker-ID
  extractor) gives the red team a real independent corroborator to test merges against.

## 2026-06-24 (D1 — attribution doctrine + estimative language)
- **D1 done (doctrine):** added an "Attribution discipline — DON'T OVER-MERGE" section to
  `skills/supervisor.md`. Co-tenancy (shared IP/ASN/registrar/NS/template/cert) ≠ co-ownership;
  asserting `operated_by`/`same_operator_as` now REQUIRES an independent corroborator (shared
  registrant identity, a tracker/analytics ID, a unique contact, or an explicit cross-reference);
  co-hosting alone commits as `co_hosted_with` (infra fact), not ownership; supervisor must flag the
  "may be one of N clusters" hypothesis. Grounded in a ground-truth review of INV-20260624-001, which
  over-merged ~20 co-hosted lookalike ticket-scam domains under one company (THE WALKER TOURS LLC) on
  shared IP + shared OVH registrar alone — truth was TWO independent Spanish operators sharing infra,
  and the second (My Top Tour / Al Andalus = MNPQ Gestores Turísticos SL / LA BIBI), linkable only via
  a shared Salesforce/tracker ID, was missed entirely. That miss is the concrete proof-of-need for G14.
- **Estimative language renamed** (operator request — "confirmed" read as certainty and invited
  over-claiming): top tier `confirmed` → **`highly_likely`** across the pipeline; `probable`/`possible`
  unchanged. New `src/graph/confidence.py` is the single source of truth (canonical tiers, legacy
  `confirmed`→`highly_likely` alias, `normalize()`/`humanize()`/`TIER_RANK`). Threaded through
  graph_commit, graph/database, visualizer, cti_report, html_report, bibliography, web_searcher.md,
  and the baseline test. Display shows "Highly likely"; old graphs (INV-20260624-001) still render via
  the alias. Made explicit in supervisor doctrine that raw gatherer/tool `confidence` tags are NOT the
  supervisor's tiers — the supervisor re-classifies every finding into the estimative tiers itself.
  CAPABILITY-LOCK item 4 updated (mechanism locked, labels renamed). Health + 3 suites GREEN.
  RT1 (red-team review agent — the process control for D1) remains open.

## 2026-06-24 (backlog sweep)
- Worked the bug/addressable-gap backlog in 3 health-gated batches (all GREEN):
  - **B8** threatfox: abuse.ch made the API auth-mandatory → it 401'd on every domain/IP run;
    now skips gracefully with a clear "needs free ABUSE_CH_API_KEY" message (live-confirmed by a
    concurrent investigation, GAP-20260624-02). **B1** collect.py CLI → one `{"results":[…]}` schema
    (+`--exclude`). **B9** health gate fast again (baseline excludes cloud_buckets' ~80 probes).
  - **B3** courtlistener name-match gate (BM25 fuzzy FPs gone; matches `probable` not `confirmed`).
    **B2** socid scope narrowed; **B4** holehe → lead-only (positives `probable`, negatives unreliable);
    **B6** whois prefers rdap for new TLDs.
  - **B5** report.md de-lossied (pipe-escape, full values, Citation column, relationship table, no
    dead graph.png) + report-writer passes `relationships`. **B10** certspotter optional Bearer token
    (HttpTool gained `auth_prefix`). **G13** cloud_buckets adds Azure Blob + DigitalOcean Spaces.
  - **G11** exiftool installed via winget user-scope (no elevation); wrapper resolves the binary off
    a stale PATH → all 12/12 CLI tools now READY.
  Note: a concurrent supervisor session (INV-20260624-001) was committing with `git add -A` on the
  shared working tree — it bundled some of this sweep's early changes; nothing lost.

## 2026-06-24
- Intake: **SpiderFoot** (github.com/smicallef/spiderfoot, MIT). Decision: do NOT adopt the
  engine/CLI (a second correlation brain → collides with our raw/analysis split + needs sign-off);
  instead cherry-pick free no-key module *sources* and wire as our own declarative specs. Added
  4 validated tools in `src/tools/sf_derived_tools.py` (51→**55 tools**, +1 runnable type `keyword`):
  - **certspotter** (domain → CT-logged cert ISSUANCE HISTORY + subdomains) — attacks G2
    (cert-history correlation: surfaces issuers/dates/fingerprints) + adds passive subdomain
    breadth (56 subdomains for viory.video). Replaces the AnubisDB/rapiddns idea (both non-viable).
  - **robtex_ip** (ip_v4 → passive-DNS co-hosted domains) — 2nd reverse-IP source vs. quota-dead
    HackerTarget (helps G1).
  - **cloud_buckets** (domain/company/keyword → exposed S3/GCS buckets via name-permutation probe)
    — brand-new attack-surface capability (validated on flaws.cloud).
  - **pgp_keyserver** (email → alternate emails / real name on same PGP key) — email↔identity pivot (G4-adjacent).
  - Rejected: **Ahmia/dark-web** — clearnet search is JS-rendered (no-JS HTML empty); SpiderFoot's
    own dark-web modules need a Tor SOCKS proxy. Logged as new gap G12 (honest, not faked).
  Bumped TOOL_FLOOR 51→55; ran annotate_implemented; health + 3 suites GREEN.

## 2026-06-23
- Phase 1: added the System Manager (`skills/system_manager.md`) + state files
  (`system/VISION.md`, `CHANGELOG.md`, `intake/`). Manager owns vision, ontology, and the
  bug/gap backlog; test-gated autonomy for bugs/wiring, user sign-off for architecture.
- Phase 0: safety net — `scripts/health_check.py` (the gate), `system/CAPABILITY-LOCK.md`
  (must-not-regress contract), `system/BACKLOG.md` (consolidated worklist). Tagged stable
  baseline `v3-baseline-2026-06-23`. Why: make "don't break anything" an enforced mechanism.
- Hardening: HTTP retry/backoff, http_title JS-note, log auto-init, sherlock txt hygiene,
  de-hardcoded paths (`python -m`). Report-writer validated end-to-end.

## Earlier (pre-Manager, summarized)
- 51 tools reached via declarative HTTP/CLI runners + infra tools (reverse_ip/tls_cert/http_title);
  9 arsenal additions; family-recovery snippet fix; ontology honesty pass; web-search line;
  raw/analysis split; pivoting + confidence-tier doctrine. (Full history in git log.)
