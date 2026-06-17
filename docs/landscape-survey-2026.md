# OSINT + CTI Landscape Survey & Architecture Reference (2026-06)

*Compiled 2026-06-12 for the osint_ontology_investigator build-out. Four research streams: investigation platforms, source tooling by selector, CTI/AI-threat knowledge management, and frameworks/ontology/tradecraft. Vendor counts (module/source/record totals, pricing) drift — re-verify the few that drive build decisions.*

---

## 0. BLUF on the existing system

`osint-investigator` (repo: github.com/cis379/osint_ontology_investigator) is a **well-architected, correctly-principled multi-agent OSINT skeleton** — further along conceptually than most from-scratch attempts. Strengths: clean supervisor/gatherer/report-writer separation; a "gatherers are dumb pipes, supervisor owns analysis" rule; a hard no-hallucination/cite-everything protocol; live-updating graph + bibliography + audit log; a `platform_analyst` skill that already mirrors real trust-and-safety cluster-hunting (shared-IP/payment/timing SQL pivots).

The honest gap: it is a **strong shell with a thin live core**. The headline "1,031 tools × 114 selectors" is ~21 actually-automated tools plus a large *catalogued-but-manual* registry (the `ext_NNNN_` entries are references, not callable). The ontology is a flat custom JSON taxonomy, not a standards-based entity model, so it has no provenance/chain-of-custody layer, no confidence/source-grading discipline, no entity-resolution/clustering engine, and no persistence across cases. None of that is wrong — it's just the next layer of work, and the survey below says exactly what best-in-class adds.

---

## 1. Investigation platforms

### estorides (grisuno) — closest open-source reference design
`github.com/grisuno/estorides` (AGPL-3.0, active June 2026). A from-scratch OSINT aggregator+correlation engine — essentially the system we're building. Worth studying its source layout before extending ours.
- **Stack:** Python/Flask; async fanout via aiohttp + circuit breakers; SQLite cache; **Kùzu** embedded graph DB (Cypher, persistent across runs) + **NetworkX** (per-run); D3 force-directed graph with **community detection**; Leaflet map + timeline.
- **Selectors:** domain, IPv4/6, email, username, phone, hashes, CVEs, BTC/ETH.
- **Sources:** 99 free public sources across 12 categories (DNS, IP/infra, web, social, threat-intel, breaches, geo, knowledge, wireless, blockchain, pastes, visual).
- **Intel layer:** OFAC/OpenSanctions cross-check, **MITRE ATT&CK auto-tagging**, fuzzy entity clustering (difflib 0.85), multi-backend LLM analyst (Ollama/OpenAI/Anthropic/OpenRouter) producing BLUF reports with confidence grading.
- **Interfaces:** REST API (`/api/intel/resolve`, `/api/intel/graph?q=<cypher>`, per-probe `/api/osiris/*`), CLI (`--passive-only`, Tor/proxy egress).
- **Safety:** append-only JSONL audit log (timestamp/IP/query/latency), SSRF guard (blocks RFC1918/loopback/cloud-metadata), per-IP rate limiting, input validation (control-char/bidi-override), age-encrypted exports.
- **Exports:** STIX 2.1, MISP, GraphML, JSONL.

### OSINT Navigator (navigator.indicator.media) — the catalog/discovery layer
NL tool-discovery engine over **7,500+ tools** aggregated from nine OSINT toolkits, weekly-refreshed. An LLM retrieves only real tools (cannot fabricate). **Queryable via API or MCP** from inside an AI agent (Claude Code / Codex), or locally via a fine-tuned ~2.5 GB model. Full DB open-sourced on Hugging Face. 10 free searches/day. **Directly reusable pattern: our agent can call Navigator (MCP) to pick the right collector per selector.**

### Maltego — the reference entity/transform model
Every node is a typed **Entity**; every edge a **Transform** (`Entity → related Entities`). That input→output entity-type contract *is* an ontology. **Maltego TRX** Python SDK (MIT) for custom transforms; **Machines** for scripted chains; Transform Hub for third-party data. Acquired **Hunchly** (May 2025) for evidence capture. CE free but capped.

### Others
- **SpiderFoot / HX** — 200+ modules over 100+ sources, mostly keyless; HX adds a **correlation engine**. OSS CE (MIT) + paid cloud.
- **Aleph (OCCRP)** — open-source document+entity investigation on **FollowTheMoney** ontology; cross-referencing across hundreds of datasets. Strongest off-the-shelf investigative ontology.
- **Datashare (ICIJ)** — free self-hosted doc search; NER entity extraction; 2024 graph plug-in. Powered Pandora Papers.
- **Hunchly** — silent MHTML capture with SHA-256 + timestamps → tamper-evident chain-of-custody. The evidence layer.
- **Recon-ng / theHarvester / Amass** — OSS collector frameworks (Recon-ng's workspace/marketplace model is a good plug-in template).
- **i2 Analyst's Notebook** (LE standard, desktop) / **Linkurious** (web, multi-user, temporal+geo) / **Gephi** (free, GraphML) / **NodeXL** — the link-analysis/visualization sink.
- **OSINT Industries / Epieos / Intelligence X / Lampyre** — selector-resolution engines, best treated as collectors we call.
- **2025–26 agentic wave:** GeoSeer (multi-agent geoloc), Unifuncs (agent toolkit + MCP), World Monitor (OSS geopolitical dashboard, confidence-scored forecasts), MiroFish (swarm narrative simulation). Signal: **MCP is becoming the integration substrate; confidence-scored multi-agent reasoning over a knowledge graph is the norm.**

### Best-in-class checklist (don't omit)
1. Typed entity ontology with input→output contracts (Maltego / FtM) — adopt, don't invent.
2. Modular collector/transform registry, each `selector→entities`, API-key isolated.
3. Persistent graph store + force-directed viz with clustering; export GraphML/STIX/MISP.
4. Correlation / entity-resolution engine (fuzzy + cross-feed anchors like Wikidata).
5. Enrichment overlay: OFAC/OpenSanctions screening, MITRE ATT&CK/ATLAS tagging.
6. Agentic orchestration via MCP + LLM analyst → BLUF with confidence grading; deterministic fallback.
7. **Court-grade evidence capture & audit trail** (append-only logs + SHA-256/MHTML capture).
8. Passive-by-default safety controls (SSRF guard, rate-limit, Tor egress, input validation).
9. Confidence/provenance on every claim; intelligence tiering (data→information→intelligence).
10. Standards-based interop out: STIX 2.1, MISP, GraphML, FtM.

---

## 2. Source tooling by selector (agent-callable focus)

**[API/CLI] = automatable; [Manual] = human-only.** One correction to bake in: **Castrick Clues shuts down 2026-02-07 — do not register as a live source**; use Epieos + OSINT Industries instead.

- **Username:** Maigret [CLI, 3,100+ sites] is the automation default; WhatsMyName [dataset] is the canonical 700+-site JSON; Naminter [CLI, *new*] adds curl_cffi TLS impersonation to beat Cloudflare; Linkook [CLI, *new*] does recursive linked-account discovery. Sherlock/Blackbird solid. Meta-list: soxoj/osint-namecheckers-list.
- **Email:** Holehe [CLI] (120+ sites), Epieos [API] (140+), OSINT Industries [API] (~200 modules, best single pivot API), GHunt [CLI] (Google account metadata), HIBP [API], Hunter.io [API], EmailRep [API].
- **Phone:** PhoneInfoga [CLI] (best OSS); Twilio Lookup / Trestle / Endato [API] for carrier+identity; Truecaller [Manual, ToS]. 
- **Domain/infra:** SecurityTrails [API] (passive DNS), Censys [API], Shodan [API], **Netlas [API, *new*]** (regex search in response bodies — Shodan/ZoomEye can't), **FOFA/ZoomEye/Hunter.how/Quake** (best non-Western coverage), Criminal IP [API, *new*] (per-host risk history), crt.sh, Amass [CLI], urlscan [API].
- **IP/network:** GreyNoise [API] (scan-noise triage), **Spur.us [API, *new*]** (residential-proxy/VPN attribution — increasingly essential), IPinfo, AbuseIPDB. Wrapper: wtfis [CLI].
- **Face/image:** PimEyes [Manual] (most accurate, no API), FaceCheck.ID [Manual+limited API], search4faces [RU/CIS], **GeoSpy [API, *new*]** (AI photo geolocation), Yandex Images [Manual], TinEye [API] (provenance).
- **Crypto:** Arkham [API] (entity-labeled wallets), Breadcrumbs [API] (flow viz), Etherscan [API], Crystal [API] (AML), Dune/Nansen. ZachXBT's toolkit = Arkham+Etherscan+Breadcrumbs.
- **Social:** Telegram — TGStat/Telemetr [Web] + **Telerecon/TeleTracker/telegram-scraper [CLI]**; Reddit — PRAW [API]; X — paid API; TikTok/Instagram/VK — fragile scrapers.
- **People/records:** OSINT Industries [API], Pipl [API], Endato [API], TLOxp [Manual, gated], ThatsThem [Web], Predicta/UserSearch [API, *new*].
- **Threat IOC:** VirusTotal [API], ThreatFox/MalwareBazaar/URLhaus (abuse.ch) [API, free], AlienVault OTX [API], Pulsedive [API].
- **Geospatial:** Overpass Turbo [API], Bellingcat OSM Search, SunCalc, Sentinel Hub [API], Google Earth [Manual], QGIS [Desktop].

**Newer-than-2023 gaps legacy lists miss:** Naminter, Linkook, Netlas, Hunter.how/Quake/Criminal IP, **Spur.us**, **GeoSpy**, OSINT Industries API, FaceCheck.ID, Endato/Predicta/UserSearch, Telerecon/TeleTracker, wtfis/ioc_analyzer wrappers, threat-intel MCP servers. Freshness meta-resources to track: soxoj/osint-namecheckers-list, cipher387/API-s-for-OSINT, Bellingcat Toolkit, tools.osintnewsletter.com.

---

## 3. CTI ingestion + AI-threat knowledge management

### Knowledge-management core
- **OpenCTI** (Filigran; OSS) — STIX 2.1 knowledge graph + connectors + **TAXII 2.1 server**. The natural system-of-record for an adversarial-AI knowledge graph. **ATLAS ships ready-made OpenCTI bundles.**
- **MISP** (OSS) — Events/Attributes/Objects + **Galaxies** (actor/TTP clusters) + Taxonomies + Warning Lists + server sync. The sharing fabric (ISACs/CERTs). OpenCTI↔MISP connector is standard.
- **STIX 2.1** = language; **TAXII 2.1** = transport (point client at server URL → enumerate collections → poll). Most SIEM/EDR speak TAXII natively.
- Avoid: **MANTIS** (deprecated), MeerCAT (legacy). Lightweight alt: **Yeti**.

### Free feeds to wire in
abuse.ch (ThreatFox/URLhaus/MalwareBazaar) [API, free, some need auth-key], AlienVault OTX [API], **CISA AIS** (bidirectional TAXII 2.1), **CISA KEV** (CSV/JSON, github.com/cisagov/kev-data), Pulsedive (CSV + STIX/TAXII). Master list: github.com/hslatman/awesome-threat-intelligence.

### Newsletter ingestion
- **Risky Business** RSS: flagship `risky.biz/feeds/risky-business`; **Risky Bulletin** (3×/week news) `risky.biz/feeds/risky-business-news`; newsletters-as-text `risky.biz/feeds/newsletters`.
- Others: tl;dr sec, Detection Engineering Weekly (RSS), Daniel Miessler / Unsupervised Learning (AI+sec), SANS ISC (RSS). Directory: github.com/TalEliyahu/awesome-security-newsletters.
- **Technique:** prefer RSS; for email-only → dedicated IMAP inbox → atomail (email→Atom) or LLM-parse HTML body to JSON schema; rule-based parsers break on layout drift, LLM extraction tolerates it.

### Adversarial-AI tracking (the core theme)
- **MITRE ATLAS** — ATT&CK-style matrix for attacks on/via AI. v5.1.0 (Nov 2025) ≈16 tactics/84 techniques/56 sub/32 mitigations/42 case studies (re-verify at build via `github.com/mitre-atlas/atlas-data`). **Consume programmatically:** atlas-data (YAML→STIX/Navigator/Excel) + atlas-navigator-data (pre-built STIX **and OpenCTI bundles**).
- **Incident DBs:** AI Incident Database (AIID, API+export), AIAAIC, OECD AI Incidents Monitor (curated, no submissions).
- **OWASP Top 10 for LLM Apps 2025** — the *defensive* taxonomy (prompt injection, data poisoning, excessive agency, etc.), complements ATLAS.
- **Vendor misuse reporting (richest raw material — PDFs/blogs, must scrape+LLM-extract):** Anthropic threat-intel (Aug 2025 "vibe hacking"/NK remote-worker fraud; Nov 2025 GTG-1002 AI-orchestrated espionage); OpenAI "Disrupting malicious uses of AI" (40+ networks since Feb 2024); Google GTIG/Mandiant; Microsoft MSTIC + Digital Defense Report.
- **Working taxonomy of malicious AI use (build as galaxy/tags):** (1) AI-enabled cyber ops, (2) influence ops/disinformation, (3) deepfakes & impersonation, (4) fraud & scams, (5) CSAM generation, (6) prompt-injection/jailbreak abuse of deployed AI.
- **Hype filter:** Microsoft/OpenAI early assessment = AI used as productivity tool, not yet novel technique. Separate demonstrated capability from vendor marketing; exclude unsourced "89% surge"-type stats.

### NLP pipeline (unstructured → structured)
Ingest→normalize → IOC extraction (regex+NER spaCy/HF) → **TTP extraction & ATT&CK/ATLAS mapping** (TIEF/TechniqueRAG style) → **RAG over report corpus** for grounded summarization → STIX 2.1 normalize/dedupe → publish to MISP/OpenCTI → SIEM/SOAR. Add a thin **"AI-misuse relevance" classifier** scoring each item into the six buckets. **Keep a human-in-the-loop verification gate** — LLMs still err on real-world threat research.

---

## 4. Frameworks, ontology & tradecraft backbone

### Recommended layered stack (mirrors the EU/US-endorsed EEAS counter-FIMI architecture: DISARM + STIX 2.1 + OpenCTI)

1. **Entity & relationship layer → FollowTheMoney (FtM).** Primary graph store. Thing schemata (Person/Company/LegalEntity/Asset/Address/Email) + interval/relationship schemata (Ownership/Membership/Payment) where **the relationship is a first-class entity** carrying source + dates + evidence. Property values reify into nodes (shared phone/address → pivot node) — exactly the OSINT pivot mechanic. Extend with custom platform schemata (account/post/channel/device). Reconcile known real-world entities to **Wikidata QIDs**.
2. **Provenance & chain-of-custody → W3C PROV-O.** Every artifact + analyst action = Entity–Activity–Agent record with source URL, hash, timestamp. Non-negotiable for defensible, DSA-grade enforcement.
3. **Behavior/TTP taxonomy → DISARM (primary) + MITRE ATLAS (AI abuse) + ATT&CK (cyber).** DISARM = "ATT&CK for disinformation" (tactics/techniques/procedures; Red+Blue), used by EU Commission/France; serializes as STIX `attack-pattern`. Tag every observed behavior with a technique ID → comparable cases + actor "procedure" fingerprints for attribution.
4. **Case/analytic schema → ABCDE frame + Diamond Model atom.** Each case = ABCDE record (Actor, Behavior=DISARM, Content, Degree, Effect); each event = Diamond (Adversary–Capability–Infrastructure–Victim). SCOTCH for fast intake triage. Anchor on **Coordinated Inauthentic Behavior** — enforce on *behavior/coordination*, not content (the defensible line). Make coordination signals (shared infra, synchronized timing, near-dup content, shared selectors) first-class evidenced entities.
5. **Evidence grading & confidence → Admiralty (A–F / 1–6) + WEP + analytic confidence, governed by ICD 203/206.** Every evidence item: Admiralty two-char rating + ICD 206 source summary. Every judgment: a Words-of-Estimative-Probability term + a *separate* confidence level with rationale. Run ACH + Key Assumptions Check for any attribution.
6. **Output & interchange → STIX 2.1 bundles + BLUF reports; MISP for federation.** DSA Art. 34/35 expects VLOPs to assess CIB systemic risk — produce structured, behavior-based, provenance-backed, confidence-graded outputs exportable for transparency reporting.

**T&S investigation practice** (Stanford Internet Observatory / Graphika / DFRLab): start from a platform dataset of removed assets → build auditable evidence of coordination that withstands external scrutiny. Model **selectors, pivots, clusters** as native graph operations; log every pivot as a PROV activity.

**Known friction:** DISARM/STIX incident modeling is currently manual/labor-intensive; 2025–26 research shows agentic LLM tagging can automate technique labeling and surface new bot accounts. **Build LLM-assisted DISARM tagging + selector extraction in from day one — that's the AI-safety investigator's tooling advantage.**

---

## 5. Synthesis → implications for our two tools

**Tool A — OSINT investigation system (extend `osint-investigator`):** keep the supervisor/gatherer/no-hallucination spine; add (a) a standards-based entity layer (FtM) replacing the flat custom ontology, (b) a persistent graph store + clustering/entity-resolution engine, (c) a PROV provenance + hash-capture evidence layer, (d) Admiralty/WEP confidence discipline, (e) real automated collectors prioritized by the gap list, (f) MCP-exposed collectors + Navigator MCP for tool selection.

**Tool B — AI-threat knowledge tool:** OpenCTI (with ATLAS+ATT&CK bundles) as system-of-record + free feeds (OTX, abuse.ch, KEV, Pulsedive via TAXII) + RSS/IMAP newsletter ingester (Risky Bulletin first) + vendor-report scraper (Anthropic/OpenAI/Google/MS) + LLM extraction/classification tuned to the six AI-misuse buckets + human verification gate + BLUF product generation.

**Shared spine:** both want a structured data layer (selectors/indicators/entities, FtM-typed) + an artifact store (screenshots/MHTML/PDFs, hash-stamped, PROV-linked) + the same confidence/provenance grammar + STIX/MISP interop. Strong case for one data platform, two front-ends.
