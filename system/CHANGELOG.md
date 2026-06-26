# CHANGELOG — System Manager decision/change log

One line per change: what + why. The Manager appends here every working session. Newest first.

## 2026-06-26 (D2 refine — analytic principles over source mandates + coverage check; OV-1 tweak)
- The completed INV-20260626-001 (re-run of the INV-001 seed) VALIDATED D1+RT1+R1 end-to-end: 81 nodes/51
  domains (after the operator's IP prompt), NO over-merge (split Walker vs a separate "Operator-2" on per-site
  GA4/UA properties; correctly graded shared Google Ads `AW-` as medium→caps at probable vs GA4/UA property
  as strong/ownership-grade), and BOTH red-team gates fired — analysis (×2 rounds, down-tiered museivaticani/
  notredame) AND report-grounding Mode 2 (`_report_review.json` caught 2 over-claims — "shell company"→
  "Delaware LLC" + a tier mismatch — writer fixed → `grounded` before ship). The narrative report is strong.
- BUT it OVER-INVESTED in website-kit fingerprinting (web_tech_fingerprint 132×, tracker_reverse 86×, plus
  bespoke `_arch_*` JS/asset scrapers) — the tunnel-vision failure, inverted (last time it skipped infra; this
  time it skipped breadth for kits). Per operator guidance, REFINED D2 in supervisor.md: replaced the HARD
  source-specific mandates ("never leave an IP un-reversed", non-skippable named-tool list) with FLEXIBLE
  ANALYTIC PRINCIPLES — (a) confidence comes from CONVERGENCE of multiple INDEPENDENT source-types, a single
  signal (tracker/kit/host) is a lead not a conclusion, don't over-invest in one technique; (b) cover the
  evidence CATEGORIES the seed affords (registration / hosting-estate / content-identifiers / reputation) via
  whatever registered tools fit; (c) a **coverage check** before concluding — don't finish while
  `plan_collection` offers unrun tools on real entities. Kept no-bespoke-collection + no-anchoring.
- Refined `report-writer.md`: the BLUF OV-1 must center the KEY FINDINGS (a conclusions diagram, ~5-8 nodes,
  edges labeled with the evidence) — not the pivot plumbing. Health + 3 suites GREEN.

## 2026-06-26 (doctrine D2 — flexible seed-driven pivoting; infra-first; no anchoring; no bespoke collection)
- Watching INV-20260626-001 (a re-run of the INV-001 scam seed) exposed a decision-logic failure: the
  supervisor OVER-INDEXED on the prior case — it tunneled on the new tracker-ID tooling (`tracker_reverse` 84×,
  `web_tech_fingerprint` 22×, plus a hand-written urlscan scraper `_arch_step1.py`) and **never ran
  `reverse_ip`/`robtex`**, so the IP→co-hosted-domain estate engine (which produced ~21 siblings in INV-001)
  was skipped → 32 nodes/15 domains vs INV-001's 79/40+.
- Fixed `supervisor.md` pivot doctrine (D2): (1) **EXHAUST the seed's options** — run all `plan_collection`
  pivots, no cherry-picking; (2) **every investigation is INDEPENDENT** — don't anchor on a prior case's
  framing/conclusion; (3) **INFRA-FIRST** — build the network (domain→IP→`reverse_ip`/`robtex` co-hosts→
  subdomains) THEN attribute (trackers/registrant are corroborators, not the map); non-skippable IP→reverse_ip;
  (4) **collect ONLY through the three lines — no bespoke collection scripts/sub-agents** (bypasses the
  raw/analysis split, audit log, OPSEC, typed output — if a tool seems missing, check plan_collection then log
  a GAP); (5) brief the path as a coherent **seed→infra→estate→attribution ARC**. Health + 3 suites GREEN.

## 2026-06-26 (intake: user_scanner — better email enumerator)
- Intake **user-scanner** (kaifcodec, PyPI, free/no-key). Validated hands-on in an isolated venv via a
  sub-agent: on the same email it returned a determinate verdict on ~80% of ~100 sites vs **holehe's ~37%
  (holehe ~63% rate-limited)** — materially more reliable, complementary site mix. **Adopted EMAIL-ONLY** as
  `user_scanner` (new `src/tools/userscanner_tools.py`), a STRUCTURED-line tool (queries third-party
  platforms about the selector like holehe; does NOT touch the target's infra, so NOT the active line —
  resolved the operator's categorization question). Mitigates **B4** (holehe lead-only). NOT wired: username
  mode (duplicates sherlock/maigret/naminter/linkook), `--hudson` (redundant + calls input() → hangs),
  `--allow-loud` (OPSEC: emails the target). Wrapper: --no-nsfw, positives-only, conservative `possible`,
  graceful degrade. Wired into pivot_map `email`; TOOL_FLOOR 57→58; annotate refreshed; live-tested; health
  + 3 suites GREEN.

## 2026-06-26 (R1 — narrative report overhaul + report-grounding gate)
- **R1 done (architectural, user sign-off):** rebuilt the report last-mile as the share-with-humans
  NARRATIVE product. Flow: report-writer authors `_report.json` -> `python -m src.report.build` renders
  `report.md` + styled `report.html`. Structure: **BLUF (+ an OV-1 overview diagram) -> the Investigation
  STORY** (one section per pivot, semi-instructional tone for non-experts, showing **what each tool
  returned** + a graph of what the pivot added) **-> Key Findings -> Appendices** (full entity + relationship
  tables, raw-output pointer, glossary).
- **Visuals = Mermaid, generated FROM graph.json** (`src/report/diagram.py`): `subgraph_for_values` draws
  only the real edges among a pivot's entities (a picture can't depict a link the data lacks);
  `overview_ov1` renders the editorial BLUF schematic. Tier-styled (solid/dashed/faint). Renders in
  report.html via mermaid.js (CDN), degrades to code-fence in report.md, prints to PDF. No Node/browser/
  graphviz dependency. `cti_report.py`/`html_report.py` rewritten to consume the spec + graph; `build.py`
  orchestrates. Smoke-tested on INV-001's real 79-node graph.
- **Red-team gains Mode 2 (report grounding)** in `skills/red_team.md`: checks the DRAFT report against
  graph.json + investigation.md for hallucinations / over-claims-vs-tier / phantom data / citation drift /
  diagram mismatch, writes `_report_review.json`, and loops with the report-writer until `verdict: grounded`.
  The report ships ONLY when 100% grounded — the report-stage mirror of the Phase 5.5 analysis gate.
  Wired into report-writer.md + supervisor.md Phase 6. Locked as CAPABILITY-LOCK item 7. Health GREEN.
- Logged the **INV-001 G14/A1 validation** as an F1 data point: web_tech_fingerprint recovered the shared
  Google Ads (C1) and Salesforce org (C2) IDs and showed the two clusters share none — the new toolchain
  reaches the correct two-operator answer the original run missed.

## 2026-06-25 (A1 + G14 — active collection + tracker-ID fingerprinting)
- Preceded by an off-the-shelf survey (build vs buy): off-the-shelf fingerprinters (Wappalyzer family,
  webanalyze) throw away the RAW id and/or need Go/Node; maintained reverse-lookup is paid/flaky.
  Decision: **BUILD extraction in-house, WIRE free reverse-lookup with graceful degradation.**
- **G14 done — two tools (+2 -> 57; floor 57):** `web_tech_fingerprint` (domain/url -> tracker_id +
  favicon_hash): fetches page source PASSIVE-FIRST (Wayback) and auto-escalates to one minimal live GET;
  extracts 15 id kinds (GA UA-/G-, GTM, AdSense ca-pub-, Meta Pixel, Salesforce, Yandex, Hotjar, Clarity,
  Matomo, TikTok, reCAPTCHA, ...) each tagged id_kind + ownership_strength, + favicon mmh3 hash; proxy seam
  `OSINT_PROXY`. `tracker_reverse` (tracker_id -> domains): PublicWWW free + optional SpyOnWeb key, degrades
  to guides/tracker-id-reverse-lookup.md, never fabricates. Ontology: umbrella type `tracker_id` (id_kind in
  metadata) + `favicon_hash`; domain/url yield+route into the extractor; selector.py detects UA-/G-/GTM-/AW-/
  ca-pub-. Dep mmh3 (optional-degrading). Extractor+reverse excluded from baseline replay (network-heavy).
- **A1 done (architectural, user sign-off) — `skills/active_collector.md`, the THIRD collection line.**
  Actively touches the target's own infra to recover the INDEPENDENT ownership corroborator a shared host
  can't prove. OPSEC: passive-first auto-escalate, generic UA, no crawl, proxy seam, fraud/scam scope-guard.
  Keeps the raw/analysis split (collects+logs via collect.py, never graphs). Wired into supervisor.md: 3rd
  line; the domain/url -> web_tech_fingerprint -> tracker_id -> tracker_reverse ownership-corroborator chain;
  shared strong id upgrades co_hosted_with -> same_operator_as, different ids SPLIT a cluster; red-team
  `demand_corroborator` now triggers an active-collection pass. Locked as CAPABILITY-LOCK item 9. Health GREEN.
  This is the capability that would have separated the two operators in INV-20260624-001 (the Salesforce org id).

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
