# OSINT Investigator — Briefing Deck (content + speaker notes)

> Audience: analytically-minded, OSINT-focused, semi-technical leadership.
> Purpose: (1) show what the system is / does / how it works, (2) justify IT approval.
> Every number here is pulled from the live system and a real completed case (INV-20260626-001).
> Source of truth checked 2026-07-14: 58 runnable tools · 92 selector types · 8 skills · health GREEN.

---

## Slide 1 — Title

# OSINT Investigator
### Automated external-OSINT investigation — from one seed to a cited intelligence graph

- Multi-agent system: give it a **seed** (domain, email, username, name, IP, phone, crypto address…),
  it **pivots** through open sources, **builds a confidence-tiered entity graph**, and produces a
  **cited CTI report**.
- **External OSINT only. Runs locally. Never fabricates a finding.**
- Open source (MIT) · agent-vendor-agnostic (Claude Code or OpenAI Codex).

**Speaker note:** "This is a force-multiplier for an OSINT analyst. It doesn't replace judgment — it
does the tedious collection and first-pass link analysis at machine speed, and it shows its work so
you can trust or challenge every line. I'll show you a real case at the end where it mapped a
criminal ticket-fraud network from a single scam URL."

---

## Slide 2 — What it is (BLUF)

**The problem:** an analyst handed one selector (a suspicious domain, an email, a handle) faces hours
of manual lookups across dozens of tools, then has to keep the links straight by hand.

**What this does:**
- Runs the right tools automatically (**ontology-driven**, not hardcoded).
- Analyzes the raw output, **grades each finding by confidence**, and builds the graph.
- **Pivots on its own findings** — new entity → what can I run on it? → loop until dry.
- **Red-teams itself** before producing a report (challenges its own conclusions).
- Ships a narrative report a human can read, with **every finding cited to tool output**.

**Three properties that make it trustworthy** (and IT-friendly):
1. **No hallucination** — every claim traces to a specific tool output or source URL.
2. **Full audit trail** — every tool run is logged raw; the graph is reproducible.
3. **Honest about limits** — gaps are documented, never faked.

**Speaker note:** "The headline for an analyst is the pivoting and the confidence tiering. The
headline for IT is the next three lines — local, auditable, external-only."

---

## Slide 3 — OV-1 (Operational Concept)

**One seed in → cited intelligence graph + report out.** (Diagram: horizontal flow.)

```
  SEED                SUPERVISOR (analyst brain)            GATES              PRODUCT
 selector  ──►  route via ONTOLOGY (plan_collection)                                    
                        │                                                               
                        ├─► STRUCTURED line  (58 typed tools)                           
                        ├─► WEB-SEARCH line   (real searches + fetches)   ─┐            
                        └─► ACTIVE line       (tracker/analytics IDs)      │            
                                   │  raw output, logged, NEVER graphs     │            
                                   ▼                                       │            
                        ANALYZE + TIER  (highly likely / probable / possible)          
                                   │  supervisor re-grades; corroboration upgrades      
                                   ▼                                       │            
                        COMMIT to graph  ──►  PIVOT on each new entity ────┘  (loop)    
                                   │                                                    
                                   ▼                                                    
                        RED-TEAM GATE (adversarial, read-only) ──► reconcile            
                                   ▼                                                    
                        REPORT-WRITER ──► GROUNDING GATE ──► report.md / .html          
```

- **Three collection lines**, each a separate agent; all fetch raw and **never write the graph**.
- **The supervisor is the only brain** — it decides what's real and tiers it (the *raw/analysis split*).
- **Two adversarial gates** — one on the analysis, one on the drafted report — before anything ships.

**Speaker note:** "The key architectural idea is separation of powers. Collectors are dumb pipes.
One supervisor does all the analysis. An independent red-team agent tries to break the conclusions
before they reach you. That's what keeps a big auto-generated graph honest."

---

## Slide 4 — The Ontology → Tools (the routing brain)

**Nothing is hardcoded. A knowledge base decides what runs.**

| The ontology knows… | Numbers (live) |
|---|---|
| **Selector types** it can reason about | **92** |
| Types with a dedicated structured tool | **20** (rest covered by the web-search line or logged as a gap) |
| **Runnable tools** wired into the engine | **58** |
| Candidate-tool **roadmap** (catalog of what *could* be built) | 1,031 |

**How routing works:** `plan_collection(selector, type)` → returns the exact tools to run + whether
it's web-searchable + a fallback for bare handles. **How pivoting works:** each type declares what it
*yields* (domain → IPs, certs, subdomains; name → emails, usernames), so the system plans chains
several hops ahead.

**Honesty is enforced by a test.** The catalog is a *roadmap*, not a claim of what's built. A
regression test asserts every runnable tool is accounted for — the ontology can't lie about what runs.

**Speaker note:** "This is why adding coverage is cheap and safe: a new tool is a spec the ontology
routes to, not bespoke plumbing. And the honesty test means the system's self-description is always
true — important when you're briefing findings up the chain."

---

## Slide 5 — Software Laydown

**Small, auditable, standard.** Pure-Python engine; no exotic runtime.

**Core dependencies (7, pinned in `requirements.txt`):**
| Package | Purpose |
|---|---|
| `requests` | HTTP client for all API tools |
| `networkx` | the investigation graph |
| `python-whois` | WHOIS lookups |
| `dnspython` | DNS records |
| `beautifulsoup4` | HTML parsing |
| `mmh3` | favicon hashing (ownership corroborator) |
| `phonenumbers` | phone parsing/validation |

**What we built (the engine — ~48 Python modules under `src/`):**
- `core/` — selector detection + investigation state
- `ontology/` — the routing brain (`pivot_map.json`, honesty annotator)
- `tools/` — **58 tools** via declarative runners (`HttpTool` / `CliTool`) + a registry/dispatcher
- `graph/` — NetworkX graph + interactive vis.js visualizer
- `report/` — narrative CTI report (Markdown + HTML + Mermaid diagrams)
- `logger/` — the raw audit trail
- `scripts/health_check.py` — the safety gate (registry loads + tool floor + 3 regression suites)

**Optional external OSINT CLIs** (installed on demand, degrade gracefully if absent): sherlock,
maigret, naminter, holehe, theHarvester, exiftool, etc. **Keyed APIs** (optional, off by default):
Shodan, DNSlytics, Flare, etc. — the system runs fully without any key.

**Speaker note:** "Seven well-known open-source packages, everything pinned, one command to build and
self-verify. There's no black box — an IT reviewer can read the whole dependency list on one slide."

---

## Slide 6 — Use Case (1/2): one scam URL → a mapped network

**Seed:** `colosseumdiroma-tickets.com` — a fake Colosseum ticket-resale site.
**Result (auto-generated):** a **119-node / 170-edge** intelligence graph.

**What the pivots built, automatically:**
- **Registration** — WHOIS/RDAP: registrar OVH; registrant org *The Walker Tours LLC* survived the
  privacy redaction; created 2024-01-16.
- **Hosting estate** — domain → IPs (AWS us-east-2) → co-hosted lookalike domains → back through the
  domain pivots. This is the engine that turns **one** scam site into the **network**.
- **Content identifiers (active line)** — extracted **15 tracker/analytics IDs** (Google Ads `AW-…`,
  GA4 `G-…`, Universal Analytics `UA-…`) embedded across the sites — the independent corroborators
  that tie sites to a common owner.

**The graph, tiered honestly:** 75 domains, 15 tracker IDs, 7 companies, 5 IPs, phones, emails —
**96 highly-likely · 14 probable · 9 possible.** Weak leads are kept visible, not dropped; the count
is *not* over-sold as a "75-site scam estate" (it includes AWS nameservers, a CMS host, and the
legitimate origin-brand domains — called out explicitly).

**Speaker note:** "Start at one URL. The system expands the hosting neighborhood, fingerprints the
sites, and clusters them by shared analytics IDs — the same technique investigative journalists use
by hand. Here it did it automatically and kept a running, tiered graph."

---

## Slide 7 — Use Case (2/2): the system corrects itself (the trust story)

**This is the part that should earn an analyst's trust.**

1. An early pass read the estate as **two operators**.
2. The **red-team gate** challenged the merge — "shared hosting ≠ shared ownership; show me an
   independent corroborator."
3. A deeper pivot found the **gold-standard evidence**: the seed itself ran a **strong `UA-131208121-1`
   analytics property in its 2024 Wayback snapshot — the same property as `sevillafreetour.com`.**
4. On **six independent corroborators**, red-team round 3 **revised the conclusion to ONE operator
   group**: *Grupo Feel The City S.L.* (Seville), fronted by two US shells (*Walker Tours Corp.* FL +
   *LLC* DE) sharing federal **EIN 37-2091569**.
5. **Critical nuance the system preserved:** it distinguished the **legitimate 2010 origin tour
   business** (Pancho Tours / real Seville tours) from the **2024–26 monument-ticket scam build-out** —
   and flagged that the legit brand must NOT be labelled a scam in any takedown referral.

**Why it matters:** the system didn't just *find* links — it **pressure-tested its own conclusion,
changed its mind on evidence, and refused to over-claim.** That is exactly the discipline that makes
machine-assisted attribution safe to brief.

**Speaker note:** "If a tool only ever confirms what it first guessed, you can't trust it. This one
argued with itself on the record, upgraded its conclusion when the evidence justified it, and drew a
clean line around the innocent business. Every step is in the audit log."

---

## Slide 8 — Why IT should approve (1/2): where the data goes

**Concern: data egress / data handling.**

- **Runs entirely on the local machine.** No server, no cloud service, no account required to operate.
- **External OSINT only — by design and by scope.** It never ingests internal/corporate data; the
  vision statement and scope explicitly exclude internal-data analysis.
- **What leaves the machine is only the selector**, sent to *public* OSINT sources (WHOIS/DNS/CT logs,
  search engines, public APIs) — the same requests an analyst makes by hand in a browser.
- **Results stay on disk**, under `investigations/`, which is **git-ignored** — case data is never
  committed or pushed. API keys live in a **git-ignored `.env`** — never in the repo.
- **Passive-first OPSEC posture:** the active line prefers archived (Wayback) copies before any live
  request, uses a generic user-agent, no crawling, and has a proxy seam for attribution control.

**Net:** the tool's network behavior is a subset of normal analyst browsing, from the local machine,
against public sources only.

**Speaker note:** "Nothing internal goes in. What goes out is the same public lookups an analyst would
run manually. Results and keys never leave the box and are never committed to git."

---

## Slide 9 — Why IT should approve (2/2): provenance & safeguards

**Concern: dependency & tool provenance (supply chain).**

- **Seven pinned, mainstream open-source packages** — the entire core dependency list fits on a slide
  (`requirements.txt`). No obscure or unvetted runtime.
- **Declarative tool registry** — every one of the 58 tools is a small, readable spec (endpoint +
  parser). What each tool touches is auditable at a glance; there's no hidden collection.
- **No bespoke scraping allowed** — collection only goes through registered, reviewed tools; the
  doctrine explicitly forbids ad-hoc scripts (keeps behavior auditable and within policy).
- **Optional external CLIs and keyed APIs are opt-in** and **degrade gracefully** — the system is
  fully functional with zero keys and zero extra installs.
- **MIT-licensed**, open for review/download.

**Built-in safety governance (bonus):**
- A **health gate** (`health_check.py`) + 3 regression suites gate every change; a **capability-lock**
  defines what must never regress; a separate **System Manager** role maintains it conservatively.

**Speaker note:** "Everything a supply-chain reviewer wants: short pinned dependency list, every tool
is a readable spec, no hidden network calls, opt-in extras, permissive license, and an automated gate
that proves the system still works after any change."

---

## Slide 10 — Close

**What this gives the team:**
- An OSINT analyst force-multiplier: **seed → cited, confidence-tiered intelligence graph + report**,
  automatically, with a full audit trail.
- Proven on a **real ticket-fraud network** — mapped, attributed, and self-corrected without over-claiming.
- **Safe by construction:** local, external-only, auditable, honest about limits.

**Available now:**
- Open-source, MIT: **github.com/cis379/osint-investigator-v3** (public)
- One command to stand up (`./bootstrap.sh`), health-gated, runs on Mac/Linux/Windows.
- Vendor-neutral — drive it with Claude Code or Codex.

**The ask:** approval to run it (locally, external-OSINT only) as an analyst tool.

**Speaker note:** "It's ready, it's open, and it's built to be trusted. I'm asking for the green light
to use it as a local analyst tool — and I'm happy to walk IT through the code and the audit trail."

---

### Appendix (optional back-up slides)
- **A1 — Confidence tiers:** highly likely / probable / possible; supervisor re-grades tool output;
  weak hits kept as pivots, never dropped.
- **A2 — The three lines in detail:** structured (typed tools), web-search (snippet-as-evidence),
  active (tracker-ID ownership corroborator, passive-first OPSEC).
- **A3 — Coverage & honest gaps:** strong on domain/IP/email/username/name; documented structural gaps
  (paid/keyed): reverse-image, deep breach, phone→owner, non-US registries — with candidate sources
  (Shodan / DNSlytics / Flare) identified.
- **A4 — Outputs:** investigation.md (audit), graph.json/html, bibliography.html, report.md/html.
