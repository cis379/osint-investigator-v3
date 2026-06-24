# osint-investigator-v3 — Complete System Summary

The definitive "what is this and how does it work" reference. Updated 2026-06-24.
**External OSINT only.** Take a seed selector → pivot through tools → produce a cited,
confidence-tiered intelligence graph + CTI report.

State: **55 runnable tools · 19/90 selector types runnable · 6 skills · 3 system tests PASS.**

---

## 1. The flow (what happens end to end)

```
 USER: /investigate <seed>            e.g. viory.video, "Robin Grieff", allthespills@ig
   │
   ▼
 [skill: investigate.md]  ── detect selector type (core/selector.py, general-username fallback)
   │                      ── create workspace + auto-init log (core/state.py)
   │                      ── BECOME the supervisor
   ▼
 [skill: supervisor.md]  ── the analyst brain; runs in the MAIN thread (user can interrupt)
   │
   │  ROUTE via the ONTOLOGY:  registry.plan_collection(selector, type)
   │     → which structured tools run? is it web-searchable? general-username fallback?
   │
   ├─────────────── dispatches TWO COLLECTION LINES (background agents) ───────────────┐
   │                                                                                    │
   ▼ STRUCTURED LINE                                          ▼ WEB-SEARCH LINE          │
 [skill: gatherer.md]                                     [skill: web_searcher.md]      │
   runs  python -m src.tools.collect                        uses WebSearch + WebFetch   │
   → registry runs the typed tools (51)                     → snippet IS evidence;      │
   → logs RAW output to investigation.md                      runs relatives/public-    │
   → returns raw JSON (NO graph, NO analysis)                 records queries; extracts │
                                                              CITED findings            │
   slow tools run individually; flaky HTTP retries            → python -m src.tools.    │
   (nethttp.http_get); operator judgment                       web_collect (logs + echo)│
   │                                                                    │               │
   └──────────────────────────► raw findings ◄─────────────────────────┘               │
                                     │                                                  │
                                     ▼                                                  │
   SUPERVISOR ANALYZES + TIERS  (confidence: confirmed | probable | possible)          │
     - re-grades tool self-"confirmed" (tools over-claim); corroboration upgrades       │
     - keeps weak hits as `possible` (never drops them)                                 │
                                     │                                                  │
                                     ▼                                                  │
   COMMIT  python -m src.tools.graph_commit  (graph/database.py NetworkX)               │
     → writes entities/relationships at the supervisor's tier                           │
     → regenerates graph.html (graph/visualizer.py) + bibliography.html                 │
                                     │                                                  │
                                     ▼                                                  │
   PIVOT (supervisor.md doctrine, ontology-guided) ───────────────────────────────────┘
     for each NEW entity: plan_collection(it) → worth a pivot? (confidence-gate,
     high-yield types, verify-the-leads loop: name→email→holehe/xposedornot,
     domain→ip→reverse_ip/ripestat, username→linked email→verify). Loop until dry.
                                     │
                                     ▼
 [skill: report-writer.md]  → report.md (report/cti_report.py)
                              + report.html (report/html_report.py)
                              + bibliography.html (report/bibliography.py)

 OUTPUTS per case in investigations/INV-YYYYMMDD-NNN/:
   investigation.md (raw audit) · graph.json/.html · bibliography.html · state.json · report.md/.html
```

**The spine is the ontology.** Every routing/pivot decision is `registry.plan_collection`
+ `pivot_map` yields — nothing is hardcoded.

---

## 2. SCRIPTS — where they are + key functions

### Core (`src/core/`)
- **selector.py** — `detect_selector_type(raw)`: regex-based type detection; bare handles →
  general `username` (inferred). `Selector` dataclass.
- **state.py** — `create_investigation(seed, type)` (creates the INV dir, state.json, AND
  auto-inits the log), `load/save/pause/resume/complete_investigation`, `add_pivot`.

### Ontology (`src/ontology/`) — the routing brain (data + helpers in registry)
- **pivot_map.json** — 90 selector types → `tools`, `yields`, `implemented_tools`, `implemented_count`.
- **tools_registry.json** — 1031-tool catalog (metadata: method, command_template, install,
  in/out types) + per-tool `implemented` flag. Mostly a reference/roadmap.
- **web_search.json** — per-type web-search profiles (strategy, query templates, fetch_priority,
  extract targets) for the web-search line.
- **selector_types.json**, **tool_buckets.json** (execution-class buckets).
- **annotate_implemented.py** — re-flags implemented-vs-catalog (run after wiring tools).
- **bucket_catalog.py** — buckets the catalog by execution class (CLI/HTTP/custom).

### Tools (`src/tools/`)
- **registry.py** — loads all `TOOLS`; `get_all_tools`, `get_tools_for_selector`,
  `get_selector_capability` (honest runnable view), `get_web_search_profile`,
  **`plan_collection`** (the router + general-username fallback), `run_tool`.
- **base.py** — `BaseTool` (query/make_result/run_command — UTF-8, env), `ToolResult`, `EntityFound`.
- **collect.py** — the GATHERER'S script: runs tool(s), logs raw, prints JSON. **No graph.**
- **graph_commit.py** — the SUPERVISOR'S script: commits tiered entities/rels → graph + HTML + bib.
- **web_collect.py** — the WEB-SEARCH collector's logger (logs a search round + echoes findings).
- **credentials.py** — `.env`/env API-key access (graceful when absent).
- **nethttp.py** — `http_get` with retry/backoff (transient HTTP resilience).
- **execute.py** — LEGACY all-in-one (auto-graphs everything "confirmed"); superseded.
- Tool modules (51 tools): `username_tools`(2) `email_tools`(1) `domain_tools`(5) `ip_tools`(4)
  `phone_tools`(1) `crypto_tools`(2) `social_tools`(3) `image_tools`(1) `name_tools`(5) +
  the **declarative runners**: `http_tools`(15, `HttpTool` specs) `cli_tools`(7, `CliTool` specs)
  `extra_tools`(2, library) `infra_tools`(3, reverse_ip/tls_cert/http_title) +
  `sf_derived_tools`(4, SpiderFoot-derived, MIT: certspotter/robtex_ip/cloud_buckets/pgp_keyserver).

### Graph / Logger / Report
- **graph/database.py** — `InvestigationGraph` (NetworkX, add_entity/relationship, save/load,
  `export_for_visualization` with tier styling). **graph/visualizer.py** — vis.js HTML.
- **logger/investigation_log.py** — `InvestigationLogger` (init_log, log_step, log_tool_execution,
  log_analysis) — the markdown audit trail.
- **report/cti_report.py** (`generate_cti_report` → report.md), **html_report.py**
  (`generate_html_report` → report.html), **bibliography.py** (`generate_bibliography`).

### Tests (`tests/`)
- **replay_baseline.py** (split invariants across domain/name/username), **test_ontology_honesty.py**
  (annotations match registry), **test_selector_detection.py** (typing + plan_collection fallback).

---

## 3. SKILLS — where they are + key components

| Skill (`skills/`) | Role | Key components |
|---|---|---|
| **investigate.md** | Launcher (`/investigate`) | parse seed → detect type → `create_investigation` (auto-inits log) → become supervisor |
| **supervisor.md** | Analyst brain (main thread) | route via `plan_collection`; dispatch both lines; analyze; **Confidence-Tier doctrine** (re-grade, never drop, corroboration upgrades); commit via graph_commit; **Pivoting doctrine** (ontology-guided, verify-the-leads loop); launch report-writer |
| **gatherer.md** | Structured collector | skilled OPERATOR: run `collect.py` with judgment (pick tools, slow→individual, retry-once transient), return raw; NO analysis/graph |
| **web_searcher.md** | Web-search collector | WebSearch/WebFetch; **snippet IS evidence** (blocked page ≠ missing finding); relatives/public-records queries; cite everything; log via web_collect; NO graph |
| **report-writer.md** | CTI product | read graph+log → report.md/html + bibliography; evidence-based, BLUF-first |

(`.claude/commands/investigate.md` is the slash-command entry that mirrors investigate.md.)

---

## 4. Tool coverage (19 runnable selector types)
| Strong | Tools |
|---|---|
| **domain** (15) | whois, rdap, dns_lookup, dnsrecon, crtsh, **certspotter** (cert history+subdomains), wayback, http_headers, theharvester, tls_cert, http_title, urlscan, threatfox, google_dork, **cloud_buckets** (S3/GCS) |
| **ip_v4** (11) | ip_geolocation, ipinfo, shodan_internetdb, reverse_dns, ripestat, bgpview, greynoise, reverse_ip, **robtex_ip** (passive DNS), urlscan, threatfox |
| **company** (11) | gleif_lei, sec_edgar, aleph, courtlistener, wikipedia, wikidata, theharvester(via domain), **cloud_buckets**… |
| **username** (8) | sherlock, maigret, naminter, linkook, socialscan, github_user, reddit_about, google_dork |
| **name** (8) | web-search-primary + gravatar, hibp_name_search(gen), wikipedia, wikidata, name_to_username, aleph, courtlistener |
| **email** (7) | holehe, disify, hudsonrock, xposedornot, socialscan, gravatar, **pgp_keyserver** (alt emails/name) |
| **keyword** (1) | **cloud_buckets** (S3/GCS bucket discovery) — first runnable tool for this type |
| also | url, ip_v6, phone (phonenumbers/ignorant/phoneinfoga), crypto_btc/eth, hashes, coordinates, image/file, email_header/eml |

---

## 5. GAPS — INTEL (capabilities we lack; mostly structural)
- **Reverse-IP at scale** — reverse_ip + now **robtex_ip** (2nd free passive-DNS source, 2026-06-24);
  for true scale a key/auto-fallback to dns co-resolution is still the long-term fix.
- **Cert-history correlation** — tls_cert reads the LIVE cert; **certspotter** (2026-06-24) now
  retrieves CT issuance history (issuers/dates + tbs/pubkey fingerprints), so shared-cert evidence
  is recoverable; cross-domain correlation is supervisor-side (compare fingerprints across runs).
- **Dark-web (.onion) search** — Ahmia clearnet is JS-rendered (no-JS HTML empty); SpiderFoot's own
  dark-web modules need a Tor SOCKS proxy. Path: local Tor proxy + Ahmia/onionsearchengine runner (G12).
- **JS-rendered branding** — http_title can't see SPA titles (flagged, not solved).
- **People identity last-mile** — handle/name → verified real person is paid/manual (Pipl/Spokeo/
  OSINT Industries). Web-search snippets + relatives queries get far but stay `probable`.
- **Phone → owner/carrier** — paid (Twilio/Trestle); we have validation + account-existence only.
- **Reverse-image / face search** — paid/manual wall.
- **Deep breach (cracked creds)** — paid (DeHashed/Snusbase); we have free breach (xposedornot/Hudson Rock).
- **Telegram deep / Instagram content** — needs account/session (custom runner, not built).
- **Non-US/UAE corporate registries** — sec_edgar/companies-house/courtlistener are US/UK; a UAE
  free-zone entity (Darpo Vision) is invisible to the structured line.
- **Enterprise threat-intel + UAE registries + Go tools (subfinder/amass/httpx/gau)** — keys/Go toolchain.

## 6. BUGS — SYSTEM (things we can address)
- **collect.py output schema inconsistency** — single-tool returns `{tool,...}`, `--run-all`
  returns `{"results":[...]}`. Consumers must handle both. (Unify — open.)
- **socid_extractor under-delivers** — inert on JS/auth-gated socials (Bluesky/Threads/X) and on
  ASU/Cornell page types; the url→identity pivot it advertises rarely fires. (Narrow scope or fix.)
- **courtlistener low precision** — BM25 fuzzy → unrelated cases for short names (Robin, "Ruptly").
  Needs a relevance gate. (Open.)
- **holehe rate-limited to uselessness** — [x] on ~all sites per run; negatives meaningless, so the
  name→email→holehe verification can't verify. Needs proxy/key or role downgrade. (Open.)
- **maigret self-stamps "confirmed"** on collision sites (mitigated by tier doctrine; wrapper still lies).
- **whois_lookup** has no `.video`/many-TLD support (rdap covers it — prefer rdap).
- **aleph/sec_edgar** sparse/500 without keys/UAE coverage (expected; keys are TODO).
- **report.md is lossy vs report.html** (report-writer validated 2026-06-23, works end-to-end but):
  (a) `cti_report.py` doesn't escape `|` in entity values → a value like `Trending News | Viory`
  breaks the markdown table; (b) entity values truncated to 40 chars in report.md (full in HTML);
  (c) **citations + the relationship table never reach report.md** (only report.html) and report.md
  references a `graph.png` that is never generated (dead image link). report.html is the complete,
  citation-rich product; report.md needs the pipe-escape + relationship/citation surfacing.
- FIXED this round: HTTP retry/backoff (rdap/crt.sh/reverse_ip), http_title JS-note, log auto-init
  (init_log header swap), sherlock `<user>.txt` → temp (root hygiene), hardcoded paths → `python -m`.

## 8. Maintenance layer — the System Manager (runs in its own session)
A second agent maintains the system without breaking it (`skills/system_manager.md`, launch
`/system-manager`). Its durable memory is files in `system/` (VISION, CAPABILITY-LOCK, BACKLOG,
CHANGELOG, intake/). Every change is health-gated by `scripts/health_check.py` (registry load +
tool-count floor + 3 suites), done on a branch, reverted on red; bugs/wiring are autonomous,
architecture needs user sign-off. It triages the BACKLOG, intakes new OSINT resources (classify →
wire/backlog/manual-guide/reject), owns the ontology, and runs a READ-ONLY daily audit
(`/osint-daily-review`). The supervisor feeds it: it logs gaps it hits to BACKLOG and writes
operator **manual guides** (`guides/`) for key-gated/manual capabilities. Skills are now 6
(+ system_manager). Stable baseline tag: `v3-baseline-2026-06-23`.

## 7. What's solid (protect)
The raw/analysis split (collectors fetch, supervisor tiers+graphs); two collection lines (both
proven essential); ontology-driven routing + pivoting; confidence tiering (catches FPs every run);
the declarative runners (a new tool = a spec; 24→51 fast); ontology honesty + 3 regression suites.
