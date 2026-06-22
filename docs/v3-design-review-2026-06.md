# V3 System Design Review — 2026-06-22

Written after the 48-tool / pivoting build and a 3-seed full-system test
(viory.video / Robin Grieff / allthespills). All three PASSED; the website seed
reproduced ~6.5 of 7 pillars of a real Bellingcat investigation.

## 1. What V3 is now (the shape)

```
/investigate <seed>
   → selector detection (general-username fallback)
   → workspace (investigations/INV-*/)
   → SUPERVISOR (main thread, analyst brain)
        routes via plan_collection (ONTOLOGY decides what runs)
        ├── STRUCTURED line  → gatherer → collect.py → 48 tools (raw only, logged)
        │     native wrappers (24) + HttpTool runner (15) + CliTool runner (7) + lib (2)
        └── WEB-SEARCH line  → web_searcher → web_collect.py (WebSearch/WebFetch, judgment)
        → analyze + TIER (confirmed/probable/possible) → graph_commit.py
        → PIVOT (ontology-guided, multi-round) → repeat
        → report-writer
```
Spine = the **ontology**: pivot_map (90 types, implemented annotations), tools_registry
(1031 catalog + implemented flags), web_search profiles, tool_buckets (exec classes),
and the `plan_collection`/`get_selector_capability`/`get_web_search_profile` helpers.

**Metrics:** 48 runnable tools · 18/90 selector types runnable · 3/3 system tests PASS.

## 2. What's SOLID (proven across tests — protect these)
- **The raw/analysis split.** Collectors fetch raw; the supervisor tiers + builds the
  graph. Caught tool over-claiming on every run (sherlock/maigret "confirmed", urlscan
  phishing, courtlistener noise). This is the single best decision in V3.
- **Two collection lines, both essential.** viory proved the *structured* line carries
  infrastructure (shared NS + AS200350 linkage, independently); Robin/allthespills proved
  the *web-search* line carries identity/attribution. Neither is supplemental.
- **Ontology-driven routing + pivoting doctrine.** plan_collection + pivot_map yields
  drove real multi-round pivots: the name→email→holehe/xposedornot **verification loop
  fired** (Robin), IP→ASN and domain→related-domain pivots fired (viory). Nothing hardcoded.
- **Confidence tiering.** Honest every run; kept weak hits as `possible` (not dropped),
  caught the `rgrieff`→"Ryan Grieff" username collision.
- **Declarative runners.** Wiring a tool = a spec. Scaled 24→48 in two rounds via parallel
  subagents. This is how coverage grows cheaply.
- **Ontology honesty + test harness.** implemented-vs-catalog flags, 3 regression suites,
  and golden-comparison docs keep the system from lying about coverage or silently regressing.

## 3. What's FRAGILE / technical debt (address these)
1. **`collect.py` output schema is inconsistent** — single-tool returns `{tool,...}`,
   `--run-all` returns `{"results":[...]}`. Real friction for every consumer. **Unify.**
2. **Hardcoded absolute paths everywhere** (`C:\Users\cis37\osint-investigator-v3`). Brittle,
   non-portable, and the source of the recurring `\U` snippet bug. Should come from one config.
3. **Windows shims** (naminter, ignorant) — env-specific launchers stubbing uvloop/updater.
   Work, but fragile; a Linux/cloud move breaks them.
4. **Advertised ≠ real on two tools:** `socid_extractor` is INERT on modern JS/auth-gated
   socials (Bluesky/Threads/X) and extracted 0 even from ASU/Cornell — the url→identity pivot
   it advertises rarely fires. `courtlistener` is LOW-PRECISION on names (false-positive cases
   on both Robin and "Ruptly"). Both need a relevance gate or a narrower advertised scope.
5. **No resilience for flaky externals.** rdap (20s timeout), crt.sh (502/timeout), bgpview
   (refused), reddit (403), holehe (rate-limit → unreliable negatives), whois (no `.video`).
   No retry/backoff/fallback strategy — each just fails. RIPEstat covered for bgpview by luck.
6. **Tool wrappers still self-stamp confidence.** Mitigated by the doctrine, but the wrappers
   lie; a future careless consumer could trust them.
7. **No depth/budget guardrails in the loop** — relies entirely on agent judgment to stop.
8. **Geographic blind spot** — corporate/legal tools (sec_edgar/aleph/courtlistener/gleif) are
   US/EU-centric; the UAE free-zone entity (Darpo Vision) was invisible to the structured line.

## 4. Capability coverage (where we are)
| Strong (A) | Good (B) | Weak (C/D) |
|---|---|---|
| username, domain/DNS/subdomain, IP/ASN | email (+free breach), crypto basics, company (US/EU) | phone (no carrier/owner), people identity last-mile, image/reverse-image, telegram, UAE/non-US corporate, SSL-cert correlation, passive-DNS |

We are ~80-85% of the realistically-achievable **free** pivot surface. The weak rows are
mostly structural (paid/manual/session-gated), not wiring oversights — EXCEPT the four
concrete free gaps below.

## 5. Capability gaps that MATTERED in the test (free, worth building)
1. **Passive-DNS / reverse-IP** — to *prove* IP co-tenancy (the viory shared-hosting claim).
   Free option exists (HackerTarget reverse-IP, etc.).
2. **SSL cert fingerprint/key correlation** — the viory "smoking gun" (shared cert across
   darpo.vision↔ruptly.video) is unreachable; crt.sh gives SANs, not fingerprint reuse.
3. **Subdomain HTTP-title fetcher** — cross-branding detection (frontend.dev.viory.video titled
   "…| Ruptly"). Small custom tool; high signal.
4. **name→relatives / public-records** — family (Marvin/Brianna Grieff) not recovered (clustrmaps blocked).

## 6. The strategic gap: the internal-data bridge is unbuilt
Everything in V3 so far is **OSINT pivoting on external selectors**. But the actual job is
*"take INTERNAL data, pivot on it, and find OSINT."* The `platform_analyst` skill (internal
SQL → flagged accounts/IPs/emails → seed the OSINT graph) was parked on day one and never
integrated. It is the unbuilt half of the mission and arguably the highest-value next build.

## 7. Recommended roadmap (prioritized)
**A — pay down debt (no keys, high leverage):**
- Unify collect.py output schema (one shape).
- Add a relevance gate to courtlistener; narrow socid_extractor's advertised scope (or fix it).
- Add retry/timeout/fallback policy for flaky HTTP tools (bump rdap; per-registry RDAP fallback).
- De-hardcode the base path into one config constant (portability + kills the path-bug class).

**B — new free capability the test proved we need:**
- Reverse-IP / passive-DNS tool; subdomain HTTP-title fetcher; cert-fingerprint correlation.

**C — the mission build:**
- Integrate `platform_analyst` (internal → OSINT bridge) as a first-class collection line.

**D — gated on keys/infra:**
- Tier-2 keyed tools (IOC: VirusTotal/OTX/AbuseIPDB; breach: HIBP) when keys exist.
- Go toolchain → subfinder/amass/httpx/gau; custom/session runner → Telegram/Instagram.

**E — validate the untested:**
- The report-writer skill wasn't exercised end-to-end in these tests — confirm it produces a
  clean CTI product from a committed graph.
