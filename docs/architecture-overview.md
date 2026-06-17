# System Architecture Overview

*Baseline 2026-06-12. The top-level plan: four loosely-coupled tools over a shared data/ontology substrate, driven by a command-line AI agent, with view-only visualization. Companions: [tool-a-architecture.md](tool-a-architecture.md), [ontology-spec.md](ontology-spec.md), [data-isolation-budget-deployment.md](data-isolation-budget-deployment.md), [estorides-port-plan.md](estorides-port-plan.md).*

## Interaction model — agent is the control plane, visuals are the view plane

- **Control plane = the command-line AI agent (supervisor).** All investigation is *driven* by conversing with the agent: it plans, dispatches collectors, runs internal queries, surfaces findings, takes vetting + pivots. Each tool exposes capability as agent-callable entrypoints (the `execute.py` + skills pattern), never a web form. This is the PRIMARY and intended way to use the system.
- **View plane = generated, view-only surfaces.** The entity graph, artifact viewer (screenshots/MHTML), bibliography, reports/dossiers are outputs the agent regenerates as a case evolves. You open them to inspect/explore (pan, zoom, filter, click-for-detail) — you do **not** run investigations from them. No stateful web app in the critical path.
- **Interrogation is dual:** conversational (primary — ask the agent, it queries Postgres and answers or regenerates a filtered view) + visual (secondary — eyeball the rendered graph).
- **Deploy benefit:** no web server to secure for the main workflow; visuals are static files; fits the headless "openclaw" autonomous end-state (agent runs, emits artifacts).

## The four tools

```
                       ┌──────────────────────────────────────────┐
                       │  YOU  ·  command-line AI agent            │   PRIMARY interface
                       │  (supervisor: plan · vet · pivot)         │   = CONTROL PLANE
                       └───────────────┬──────────────────────────┘
                                       │ drives
     ┌──────────────┬─────────────────┼──────────────────┬──────────────────┐
     ▼              ▼                 ▼                  ▼                  
 ┌────────┐    ┌────────┐       ┌──────────┐       ┌───────────────┐
 │ TOOL A │    │ TOOL B │       │ TOOL C   │       │ TOOL D        │
 │ OSINT  │    │ AI-CTI │       │ platform │       │ Capability /  │
 │ invest.│    │ intel  │       │ _analyst │       │ Ontology      │
 │external│    │products│       │ INTERNAL │       │ Curator       │
 └───┬────┘    └───┬────┘       │ ISOLATED │       │ self-upgrade  │
     │             │            └────┬─────┘       └──────┬────────┘
     │             │ shared           │ one-way gated      │ proposes
     │        ┌────┴─────┐            │ minimized-selector │ PR (human-merged):
     │        │ ingestion│            │ export (STIX/FtM)  │ new sources, collectors,
     │        │ + corpus │◄───────────┼────────────────────┘ techniques; flags dead ones
     │        │ feeds/   │   D also watches OSINT-tooling
     │        │ newsltrs │   sources (soxoj, cipher387,
     │        └──────────┘   Bellingcat, OSINT Navigator)
     ▼
 ┌──────────────────────────────────────────────────────┐
 │ SHARED SUBSTRATE (design/schema shared; C runs its    │
 │ own isolated instances)                                │
 │ · 8-element core data model (FtM/STIX-aligned)         │
 │ · declarative YAML source/collector layer  (D writes,  │
 │   A consumes)                                          │
 │ · Postgres (structured) + object store (artifacts)     │
 │ · STIX 2.1 / FtM interchange at every seam             │
 └───────────────────────┬──────────────────────────────┘
                         │ agent generates
                         ▼
 ┌──────────────────────────────────────────────────────┐
 │ VIEW PLANE (inspect, don't drive)                      │
 │ · entity graph (pan/zoom/filter/click-for-detail)      │
 │ · artifact viewer · bibliography · reports / dossiers  │
 └──────────────────────────────────────────────────────┘
```

| Tool | Purpose | Data | Notes |
|---|---|---|---|
| **A — OSINT Investigator** | Interactive external/public investigation; produces evidence dossier + CTI report | Public OSINT | Build first, from scratch. CLI-agent-driven. |
| **B — AI-Threat CTI** | Ingest feeds/newsletters/vendor reports → surface how adversaries use AI (6 buckets) → intelligence products | Public feeds | Shares ingestion + corpus with D. OpenCTI core. |
| **C — platform_analyst** | Internal coordination/cluster-hunting over platform data | **Internal (isolated)** | Private repo, own DB/store/runtime + compliant zero-retention LLM; one-way human-gated minimized-selector export to A. Light scaffold only for now. |
| **D — Capability/Ontology Curator** | Continuously watch intel + OSINT-tooling sources → propose ontology/collector upgrades via human-gated PRs; flag dead sources | Public feeds | Self-improvement loop; the "constantly upgrading" engine; built with/after B. |

## Tool D — design notes

- **Shares B's ingestion substrate**; differs in *extractor* (capability/technique discovery vs adversary-AI intel) and *consumer* (your codebase/ontology vs your analyst workflow).
- **Watch sources:** threat-intel + newsletters (shared with B) **plus** OSINT-tooling freshness feeds — soxoj/osint-namecheckers-list, cipher387/API-s-for-OSINT, Bellingcat Toolkit, OSINT Navigator (weekly crawler / MCP), tools.osintnewsletter.com, tool-release feeds.
- **Loop:** monitor → detect candidate source/tool/technique → validate (exists? selectors? free/paid? posture? alive?) → draft ontology entry + declarative YAML collector → open PR with provenance/citations → human review/merge. Also detects + flags dead sources (would auto-catch the Castrick-style shutdowns).
- **Guardrails (non-negotiable — D is itself an adversarial-AI attack surface):** never auto-merge — every change is a human-gated PR; schema-validated; new sources start **passive-only** + domain/sanctions-checked; D has **no write access to live config**; treat all ingested content as untrusted (prompt-injection / source-poisoning defense). Building D defensively is a direct rehearsal of the threats this whole system exists to hunt.

## Shared substrates (the glue)
1. **Ontology / 8-element core data model** — Observable, Entity, reified Assertion, Evidence, Provenance, Cluster/Case, Coordination Signal, Tag; FtM/STIX-aligned. (C uses the same *schema*, its own *instances*.)
2. **Declarative YAML source/collector layer** — D writes proposals, A consumes; code-free source addition.
3. **Storage** — Postgres (structured) + object store (hash-addressed artifacts). Storage is config, so local↔server is free.
4. **Interchange** — STIX 2.1 / FtM at every seam, including C's one-way gated export.
5. **CLI agent harness** — the supervisor/gatherer pattern; each tool has an agent surface, you primarily live in A's.

## Build order
A (from scratch, Phase 0 → roadmap) → light C scaffold (isolation boundary, don't over-invest) → B (with shared ingestion) → D (extractor + PR-writer on B's ingestion). D and B's interrogations are not blockers for A.
