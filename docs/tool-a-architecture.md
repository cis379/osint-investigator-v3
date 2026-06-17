# Tool A — OSINT Investigator: Architecture & Requirements Spec

*Baseline 2026-06-12. Captures decisions from the onboarding interrogation. Companion to [landscape-survey-2026.md](landscape-survey-2026.md). This is the design contract for hardening `osint-investigator` into an enterprise-grade, human-in-the-loop investigation system for AI-safety / trust-and-safety work.*

---

## 1. Decision log (locked)

| # | Decision | Choice |
|---|----------|--------|
| Build strategy | How to evolve the foundation | **Extend the existing system**; re-implement (not copy — AGPL) estorides' solved-hard-problems as swappable modules. OpenCTI reserved for Tool B. |
| Ontology | Data-model backbone | **Hybrid**: a lean purpose-built core (the 8 elements below) + FtM/STIX-aligned export + DISARM/ATLAS/ATT&CK as bolt-on tag vocabularies. |
| Integration | How many systems | **Three loosely-coupled tools** (revised 2026-06-12): **A** OSINT investigator (external/public), **B** AI-threat CTI (external feeds), **C** platform_analyst (internal platform data — fully isolated). STIX 2.1 / FtM is the interchange contract at every seam. See [data-isolation-budget-deployment.md](data-isolation-budget-deployment.md). |
| Sequencing | What first | **Tool A (this doc) first.** Tool B (AI-threat CTI) follows. |
| Entry points | What we investigate from | **All four, first-class**: (1) platform-internal signals, (2) external selectors, (3) content/behavioral leads, (4) threat-intel tips. Core must be entry-point-agnostic. |
| Runtime | Where it runs | **Local now, designed for server later** — clean seams, containerizable. |
| Control points | Human-in-the-loop | **Vet at the analysis gate** — collectors run free; nothing becomes a confirmed finding or graph edge, and no pivot fires, without analyst confirmation. |
| Storage | Structured + artifacts | **Postgres + object storage from day one** (locally: Postgres + MinIO/filesystem-S3). Server-grade now, no migration later. |
| Guardrails | Collection posture | **Passive + authenticated collectors** (public sources/APIs + sock/research accounts where legitimately held). No active recon unless explicitly authorized per-target. |
| Deliverable | Primary output | **Both from one case**: enforcement-grade evidence dossier + BLUF CTI report. |

---

## 2. Core data model — the eight elements

Purpose-built for T&S platform-abuse investigation; every type maps cleanly to FtM/STIX for export. Postgres tables; JSONB for flexible sub-structures. **The structural core is fixed early; tag vocabularies hang off it and stay pluggable.**

### 2.1 Observable (atomic selector / indicator)
Immutable fact: a single identifier seen in the world.
- `id`, `type` (enum: `platform_account`, `email`, `username`, `ip`, `domain`, `url`, `phone`, `wallet_btc`/`wallet_eth`, `hash`, `device_id`, `cookie_id`, `session_id`, `payment_hash`, `image`, `coordinate`, …)
- `value` (normalized), `raw_value`
- `identity_strength` (enum: `strong` | `moderate` | `weak` — how uniquely it identifies an operator; shared payment_hash=strong, shared VPN exit=weak). *This field is what your current `selector.py` is missing.*
- `first_seen`, `last_seen`, `generated_by` → Provenance Activity

### 2.2 Entity (resolved real-world thing)
- `id`, `kind` (enum: `person`, `persona`, `organization`, `network`, `asset`)
- `label`, `summary`, `wikidata_qid` (nullable — reconciliation anchor), `created_at`
- Observables attach to Entities via **Assertions** (`attributed_to`), so attribution can sharpen/move as evidence accrues.

### 2.3 Assertion (reified relationship — the heart of the model)
Every edge is a first-class object carrying its own evidence, time, and confidence. Covers both observable→entity attribution and inter-entity links.
- `id`, `subject_ref`, `predicate` (enum: `attributed_to`, `shares_ip`, `co_registered`, `resolves_to`, `operated_by`, `member_of`, `similar_content`, `co_timing`, `transacts_with`, …), `object_ref`
- `valid_from`, `valid_to` (validity window — "A owned B from 2019–2022")
- `evidence_refs` (≥1 Evidence ids)
- `source_reliability` (Admiralty A–F), `info_credibility` (Admiralty 1–6), `analyst_confidence` (low/moderate/high), `probability_term` (WEP: almost-certain / likely / even-chance / unlikely / remote)
- `status` (enum: `proposed` | `confirmed` | `rejected` — **the analysis gate**)
- `generated_by` → Provenance Activity

### 2.4 Evidence / Artifact (the proof — hash-stamped, immutable)
- `id`, `kind` (`screenshot`, `mhtml`, `api_response`, `raw_tool_output`, `document`, `image`)
- `storage_uri` (object-store key), `sha256`, `byte_size`, `mime`
- `source_url`, `captured_at`, `captured_by` (tool/agent id)
- `collection_method` (`passive` | `authenticated` | `active`), `tool_name`, `tool_version`, `request_params` (secrets redacted)

### 2.5 Provenance Activity (PROV: entity–activity–agent)
The audit chain — every Observable/Assertion/Evidence points back to one.
- `id`, `activity_type` (`collection`, `enrichment`, `analyst_edit`, `pivot`, `import`)
- `agent` (tool id or analyst id), `used_refs` (inputs), `generated_refs` (outputs)
- `started_at`, `ended_at`, `params`

### 2.6 Cluster / Case (the unit of work)
- `id`, `name`, `status`, `opened_at`, `assigned_analyst`, `handling` (classification/retention)
- `frame_abcde` (JSONB: actor, behavior[ DISARM ids ], content, degree, effect)
- `frame_diamond` (JSONB: adversary, capability, infrastructure, victim)
- `hypotheses` (JSONB[]: ACH — hypothesis, supporting_refs[], contradicting_refs[], assessment)
- `member_entities[]`, `member_observables[]`

### 2.7 Coordination Signal (first-class — the enforcement basis)
Behavior over content is the defensible line; these are evidenced, not asserted loosely.
- `id`, `signal_type` (`shared_infrastructure`, `synchronized_timing`, `content_similarity`, `shared_selector`, `registration_clustering`)
- `member_refs[]`, `strength_score`, `method` (how computed), `evidence_refs[]`

### 2.8 Tag (bolt-on vocabulary overlay)
- `id`, `namespace` (`disarm` | `atlas` | `attack` | `ofac` | `ai_misuse` | `custom`), `tag_id`, `applied_to_ref`, `applied_by`, `confidence`
- Add/swap/version vocabularies without touching the core schema.

---

## 3. Storage architecture

- **Postgres** = system of record for all eight core types. Recursive CTEs handle graph traversal initially; if traversal/viz load grows, mirror Assertions into an embedded/columnar graph (Kùzu) or Neo4j as a read-optimized layer — the relational store stays authoritative.
- **Object store** = artifact blobs, keyed by `sha256` (content-addressed → natural dedup + integrity). Local: MinIO or a filesystem-S3 shim. Server: swap the endpoint, no code change.
- **Secrets**: API keys in a `.env` / secrets manager, never in evidence `request_params`.
- **Seams for server-later**: DB URL, object-store endpoint, and a job queue are all config — nothing assumes localhost.

---

## 4. Collection layer

- **Collector interface**: `collect(observable) -> CollectionResult { evidence[], observables[], assertions[] }`. Each collector declares: accepted input types, produced output types, `auth` (`none` | `api_key` | `account`), `posture` (`passive` | `authenticated` | `active`), rate limits.
- **Registry**: maps `observable.type → [collectors]`; supersedes the flat tools_registry. The 1,031-entry catalogue becomes a *reference index* (and a candidate for Navigator-MCP lookup), distinct from the live collector set.
- **Four entry points = four seed observable types**: internal `platform_account`/`session` (the `platform_analyst` SQL path), external selectors, content artifacts (image/text → reverse-image, hashing, similarity), CTI indicators (handed from Tool B or a partner).
- **Safety (port estorides patterns, re-implemented)**: SSRF guard (block RFC1918/loopback/cloud-metadata), per-host rate limiting, input validation (control-char/bidi-override), optional Tor/proxy egress, passive-by-default flags.
- **Authenticated collectors**: isolated credential store per platform; provenance records `collection_method=authenticated`; flagged in dossiers so reviewers see how evidence was obtained.
- **Evidence capture**: every collector run produces hash-stamped artifacts (raw API JSON; headless-browser MHTML + screenshot for web pages) before any parsing.

---

## 5. Human-in-the-loop: the analysis gate

1. **Plan** — supervisor proposes a collection plan from the seed + ontology.
2. **Collect (free-running)** — gatherers execute collectors; results land as `proposed` Observables/Assertions + immutable Evidence. No approval needed to *collect*.
3. **Analyze** — supervisor correlates, drafts findings, computes coordination signals, attaches confidence.
4. **Vet (the gate)** — analyst reviews proposed findings: confirm / reject each (status flips); only `confirmed` items enter the findings graph and reports. Rejected items are retained for audit.
5. **Pivot (gated)** — new seeds/pivots require analyst nod before the next collection round.
6. **Interrogate** — analyst can query the case conversationally at any time ("what's the evidence for A↔B?", "show unconfirmed shared-IP links").
7. **Produce** — on close, generate both deliverables.

Everything keeps full provenance regardless of status, so the audit chain is complete even for rejected leads.

---

## 6. Outputs (both from one case)

- **Evidence dossier (enforcement-grade)**: the confirmed cluster; every claim → hashed evidence + provenance + Admiralty/WEP confidence; ACH summary; coordination-signal table. Built to withstand external scrutiny.
- **CTI report (BLUF)**: key judgment + confidence up top, ABCDE/Diamond narrative, entity inventory, link map. Reuses the existing report generator, upgraded to pull only `confirmed` data + confidence fields.
- **Interchange export**: STIX 2.1 bundle (threat-actor/campaign/indicator SDOs + DISARM attack-patterns + confidence/markings) and FtM entities — the contract feeding Tool B and partners.

---

## 7. Standards mapping (hybrid, at a glance)

| Core element | Exports to | Bolt-on overlays |
|---|---|---|
| Observable | STIX SCO / FtM property | identity_strength (custom) |
| Entity | STIX `identity`/`threat-actor` / FtM `Person`/`Organization` | Wikidata QID |
| Assertion | STIX SRO / FtM interval schema | Admiralty + WEP |
| Evidence | STIX `observed-data` + external-ref | PROV-O activity |
| Cluster/Case | STIX `campaign`/`intrusion-set` | ABCDE + Diamond |
| Coordination signal | STIX SRO (relationship) | — |
| Tag | STIX `attack-pattern` ref | DISARM / ATLAS / ATT&CK / OFAC / ai_misuse |

---

## 8. Phased build roadmap

- **Phase 0 — Foundation**: Postgres + object store up locally; core-schema migrations; provenance + content-hashed evidence capture wired through a single write path.
- **Phase 1 — Collector refactor**: new collector interface + registry; port the ~21 working tools onto it; add SSRF/rate-limit/validation safety layer; add MHTML+screenshot capture.
- **Phase 2 — Analysis gate**: proposed/confirmed/rejected status; supervisor vetting loop; gated pivots; conversational case interrogation.
- **Phase 3 — Correlation**: fuzzy entity-resolution + shared-selector clustering; coordination-signal computation; graph persistence + upgraded viz.
- **Phase 4 — Confidence & products**: Admiralty/WEP model; evidence-dossier generator; CTI-report upgrade; STIX/FtM export.
- **Phase 5 — Collector expansion**: priority new sources from the gap list (Spur.us, Netlas, OSINT Industries, GeoSpy, Maigret/Naminter, Telegram CLIs, crypto/Arkham); authenticated-collector framework.
- **Phase 6 — Agentic surface**: expose collectors as MCP tools; integrate OSINT Navigator MCP for tool selection; prep seams for the openclaw autonomous-monitoring deployment.

---

## 9. Open questions / provisioning checklist (your homework)

- **API keys & budget**: which paid sources to provision first — Shodan, Censys, SecurityTrails, HIBP, OSINT Industries, Spur.us, Arkham? Rough monthly budget ceiling?
- **Authenticated accounts**: which platforms will you hold research/sock accounts on (X, Telegram, Reddit, others)?
- **Platform-internal access at the new job**: is the `platform_analyst` schema real (you'll get DB access) or a stand-in to design against? What identifiers will you actually receive?
- **Handling/retention**: employer requirements for PII handling, data retention, and where sensitive case data may live.
- **Local stack preference**: Docker-compose for Postgres+MinIO acceptable? Any constraint on running containers on your workstation?
- **Tool B interrogation** (next session): feeds to subscribe, a dedicated newsletter inbox, confirming the six AI-misuse buckets, OpenCTI deployment, and intelligence-product cadence.
