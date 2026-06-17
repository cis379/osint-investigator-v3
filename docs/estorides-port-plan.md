# estorides → osint-investigator Port Plan

*Baseline 2026-06-12. From a close source read of estorides (cloned at `C:\Users\cis37\_scratch_estorides`). **License: estorides is GPL/AGPL copyleft — RE-IMPLEMENT patterns in our own code, never copy.** Every "port" below = adopt the design, expressed against our stack (Postgres + object storage + the 8-element core + the analysis gate).*

## The crown jewel: declarative YAML source schema

`source_loader.py` + `sources/**/*.yaml` — a new collector is **one YAML file**, no central registry edit (the loader `rglob`s the tree). Two fields are pure gold to keep verbatim: **`applies_to`** (which observable types a source accepts → auto-skip, so you don't fire 90 sources blindly) and **`contact`** (`none`/`broker`/`active` safety class, unknown ⇒ treated as active = fail-safe). Request templating substitutes `{query}`/`{api_key}` into url/headers/params/body. See [ontology-spec.md §C](ontology-spec.md) for our extended schema. **This is the highest-leverage thing to adopt.**

## The key divergence to keep front-of-mind

estorides treats **every observation and inferred edge as immediately true** and writes it straight to the graph/case. Our **analysis gate (proposed→confirmed→rejected) has no analog in their code.** It must be inserted at the orchestrator post-process boundary, and **every downstream consumer (graph queries, exports, pivots) must filter on `status='confirmed'`.** Pivots auto-follow only *confirmed* observables; people-type selectors surface as proposed leads for the human.

## Prioritized port plan (top 10, tied to roadmap phases)

| # | What | Source | Phase | Effort |
|---|------|--------|-------|--------|
| 1 | **SSRF guard** — two-layer literal+DNS-resolve blocklist (RFC1918, loopback, 169.254.169.254 cloud IMDS, IPv6 ULA, rebinding/TOCTOU defense); check runs inside fetch | `ssrf_guard.py` | 0 | S |
| 2 | **Input validation front door** — NFC normalize, reject bidi/control chars, length cap, type-gate before dispatch | `validation.py` | 0 | S |
| 3 | **Declarative YAML source schema + loader + `{query}`/`{api_key}` templater** (keep `applies_to`+`contact`) | `source_loader.py`, `orchestrator._safe_format/_execute_source` | 1 | M |
| 4 | **Hardened async HTTP client** — per-host semaphore + backoff ladder (429/5xx retry, 401/403 trip breaker) + circuit breaker; **cache → Postgres/object-store, not SQLite** | `async_client.py` | 1 | M |
| 5 | **Two-pass entity extraction → Observables + Evidence** — regex lexical pass + key-aware human-selector pass; DoS scan caps; corroboration bonus (≥2 sources) | `entity_extraction.py` | 1→2 | M |
| 6 | **Relationship-inferer registry → proposed reified Assertions** + **wire the analysis gate** so inferred edges land `proposed` not fact | `relationship_inference.py`, `orchestrator` | 2 | M |
| 7 | **Postgres graph data model** replacing Kùzu+NetworkX — Observable (`type:value` PK), Evidence/Provenance join (their `OBSERVED_BY`), Assertion table (their typed rels); neighbor queries via recursive CTE (or Apache AGE for Cypher). Their `_DDL` is a useful blueprint | `graph_kuzu.py` (port schema, drop engine) | 3 | L |
| 8 | **Fuzzy clustering + community detection → Cluster element** — `difflib`/`pg_trgm` alias dedup + greedy-modularity communities; **intelligence-tier classifier** (data→information→intelligence→counter-intel) | `entity_extraction.merge`, `knowledge_graph.py` | 3→4 | M |
| 9 | **Cross-feed enrichment + Tags** — resolver (Wikidata/IP-API/RIPE) + **OFAC/OpenSanctions** SDN index + **MITRE ATT&CK** mapper, all emitting proposed Assertions/Tags | `intel_resolver.py`, `ontology.py`, `mitre_attack.py` | 4 | M–L |
| 10 | **STIX 2.1 / MISP export of confirmed elements** — reuse their entity-type→SCO and →attribute mapping tables; Provenance in custom props; Evidence → STIX sightings | `stix.py`, `misp.py` | 4 | M |

**Phase 5–6 also:** the **pivot engine** (`pivot_engine.py` — scored max-heap frontier, `PivotBudget` caps, pivotable-vs-leaf split feeding the gate; the best-engineered file in the repo) for agentic recursion; the **discoverer adapter + SSE event sink** (`discoverer.py`) for background jobs (relevant to the openclaw autonomous deployment).

## Cross-cutting discipline to adopt wholesale
- **Env-overridable typed config with fault-tolerant fallback**, "no literal numbers in logic" (`config.py`).
- **Registry-per-plugin-surface** (`@register` for parsers, inferers, LLM backends, transforms).
- **Parsers/inferers must be total — never raise.**
- **Postgres-backed append-only audit + sliding-window rate limit** (`audit.py`).
- **Multi-LLM backend router** (`manager.py`) — port the priority-list-first-success pattern; **rewrite the prompts ourselves**. (LLM-shaped — consult the claude-api skill for current model IDs when wiring Anthropic.)

## Skip / low priority
`feeds.py` (live-map quake/fire feeds), `report.py` (their human report — we have our own), `scope.py` (bug-bounty scoping — only if we add active-handoff). `encryption.py` (age-encrypt exports) — port only if encrypted-deliverable becomes a requirement.
