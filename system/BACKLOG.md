# System Backlog — the Manager's worklist

Single source of truth for **bugs (system — fixable)** and **gaps (intel — capability)**.
The System Manager triages + fixes from here (test-gated). Supervisor sessions APPEND new
`GAP`/`BUG` entries they hit during investigations (see the "Supervisor-logged" section).

Format: `[ID] (type/priority/status) — description — source`. status: open | in-progress | done | wontfix.

## CURRENT STATUS (as of 2026-07-06) — where to pick up
- **MIGRATION PREP COMPLETE (2026-07-06):** system is now Mac-portable + agent-agnostic (Codex or Claude
  Code) + self-rebuilding, WITHOUT engine changes. New files: `requirements.txt`, `bootstrap.sh`,
  `SETUP.md`, `AGENTS.md`, `MIGRATION.md`, `.gitattributes`, `codex/prompts/*`. V3 frozen as tag
  `v3-windows-final-2026-07-06`. Verified by a clean fresh-clone rebuild (health GREEN). **PUSHED
  2026-07-06 to private remote `https://github.com/cis379/osint-investigator-v3` (master + all tags;
  origin/master in sync).** Repo strategy: SEPARATE repo per tool (osint vs PRIZICONU) — prizy is being
  prepped by another agent. **On the Mac (day one): clone → `./bootstrap.sh` → copy `.env` back** (see
  MIGRATION.md Part B). `.env` is gitignored so it did NOT travel — carry it by hand.
- **Bugs: ALL closed (B1–B16).** B16 (honest empty results) closed 2026-07-06.
- **No `main` branch** — `master` is the working baseline; all migration work merged there.
- Health: GREEN · 58 tools · 8 skills. Baseline tags: v3-baseline-2026-06-26, **v3-windows-final-2026-07-06**.
- Still-open worklist below is unchanged (G15/G16/F1 buildable; structural gaps need keys/$; Bucket-2
  items still need operator sign-off before action).

## CURRENT STATUS (as of 2026-06-26) — historical
- **Bugs:** all closed (B1–B6, B8–B10 done; B7 wontfix-ish). No open bugs.
- **Operator brief (2026-06-24): COMPLETE** — D1 ✅ · RT1 ✅ · G14 ✅ · A1 ✅ · R1 ✅.
- **Open worklist (free, buildable next):** G15 (TTP playbook in web_searcher), G16 (traffic/reach +
  app-store harm-sizing), F1 (standing supervisor-quality eval), G8 (Telegram/Instagram session runner),
  G12 (dark-web via local Tor proxy). **G3** partly eased by `web_tech_fingerprint` (reads full JS source).
- **Open (structural / need keys or $, document don't fake):** G4 people last-mile · G5 phone→owner ·
  G6 reverse-image · G7 deep breach · G9 non-US/UAE registries · GAP-20260624-01 reverse-WHOIS (the big
  one; G14 partly routes around it via shared tracker IDs) · the Tier-2 keyed tools.
- **Unproven / to test:** end-to-end report-writer + red-team grounding loop (live); `tracker_reverse`
  live PublicWWW/SpyOnWeb lookup. Health: GREEN · 58 tools · 8 skills. Baseline tag: v3-baseline-2026-06-26.
- **Recent intake:** `user_scanner` wired (email-only, structured) 2026-06-26 — better email enumerator than
  holehe (mitigates B4). **Queued (approved, not yet wired):** OSINT Navigator → Manager-discovery + Red-Team
  gap-covering (subscription key in `.env`); Spotlight → borrow methodology only. See INTAKE QUEUE.

## BUGS — system (addressable; Manager can fix test-gated)
- [B1] (bug/med/done) — `collect.py` output schema inconsistent: single-tool returns `{tool,...}`,
  `--run-all` returns `{"results":[...]}`. Unify to one shape. — design review.
- [B2] (bug/med/done) — `socid_extractor` inert on JS/auth-gated socials (Bluesky/Threads/X) and
  on ASU/Cornell page types; the url→identity pivot rarely fires. Narrow advertised scope or fix. — system test.
- [B3] (bug/med/done) — `courtlistener_search` low precision: BM25 fuzzy → unrelated cases for short
  names (Robin, "Ruptly"). Add a relevance/name-match gate. — re-test (2 seeds).
- [B4] (bug/med/done) — `holehe` rate-limited to [x] on ~all sites per run → negatives meaningless,
  name→email→holehe verification can't verify. Add proxy/key or downgrade its role. — re-test.
- [B5] (bug/low/done) — `report.md` lossy vs `report.html`: cti_report.py doesn't escape `|` (breaks
  tables); truncates values to 40 chars; drops citations + the relationship table; dead `graph.png` ref.
  — report-writer validation.
- [B6] (bug/low/done) — `whois_lookup` no `.video`/many-TLD support (rdap covers; prefer rdap). — viory test.
- [B7] (bug/low/wontfix-ish) — maigret/sherlock/name_to_username self-stamp `confidence=confirmed`
  in-wrapper (mitigated by the supervisor tier doctrine; cosmetic). — multiple tests.
- [B8] (bug/HIGH/done) — `threatfox` returns `{"error":"Unauthorized"}` (abuse.ch made the API
  auth-mandatory). It is ROUTED into 4 types (domain, ip_v4, hash_sha256, hash_md5) and silently
  FAILS on every domain/IP investigation — a dead tool burning a slot. Fix: add free `ABUSE_CH_API_KEY`
  (Auth-Key header, graceful degrade) OR drop it from routing until keyed. — review 2026-06-24 (live-confirmed).
- [B9] (bug/med/done) — `cloud_buckets` runs ~80 live HTTP probes inside `replay_baseline` (domain
  run-all on example.com), pushing the health gate past 2 min. The gate tests PLUMBING, not coverage —
  exclude network-heavy tools from the baseline replay, or trim cloud_buckets' probe budget. — review 2026-06-24.
- [B10] (bug/low/done) — `certspotter` free tier is rate-limited (HTTP 429 after a handful of calls/hr).
  Healthy now, but heavy investigations / repeated gate runs will see it degrade. Add a free Cert Spotter
  token to Tier-2 (graceful) or cache per-domain. — review 2026-06-24.

## SYSTEM AUDIT 2026-06-30 (adversarial self-audit sub-agent + tool-scout + doctrine review)
Three sub-agents audited the system. The core is sound (raw/analysis split structurally enforced;
noise filters + no-key degradation good). Findings:
> **Bucket-2 items below are QUEUED FOR DEEPER EXPLORATION** (operator 2026-06-30): `DOCTRINE-TRIM`,
> `GATE-STAKES`, and `TOOL-CANDS-20260630` each need a fuller design/explanation pass before any action —
> do NOT execute them off this summary; scope each properly first.
- [B11] (bug/HIGH/**DONE 2026-06-30**) — RE-TIER NO-OP: `add_entity` short-circuited on existing nodes,
  never updating confidence — so red-team down-tiers AND corroboration upgrades were SILENT no-ops at the
  graph level (defeated CAPABILITY-LOCK #4/#8 + the whole G14/A1 corroborator chain). Fixed: re-commit now
  honors the supervisor's re-grade; added `retier_check` regression. Verified by repro.
- [B12] (bug/med/**DONE 2026-06-30**) — graph_commit defaulted missing-confidence to `probable` (one notch
  too strong); changed to conservative `possible`. (entity + relationship)
- [B13] (bug/med/**DONE 2026-06-30**) — tools that dress EMPTY/garbage as `success=True` with no signal: `disify` +
  `blockstream_btc` (any HTTP 200=success, no verdict surfaced), `cloud_buckets` (unconditional success even
  on total network failure), `http_title` (404 page with a `<title>` emits branding), `pgp_keyserver` (404
  same shape as hit). Fix: parse the key verdict into metadata; gate http_title branding on 2xx; cloud_buckets
  track probe failures. — self-audit M2.
- [B14] (bug/med/**DONE 2026-06-30**) — `theharvester`/`dnsrecon` write temp JSON keyed only on selector + extractor globs
  first match and does NOT delete it → same-selector RERUNS (re-investigations, golden re-tests) can silently
  read the PREVIOUS run's stale JSON. Fix: delete before+after (as socialscan does) or namespace per-run. — self-audit M4.
- [B15] (bug/med/**DONE 2026-06-30**, Option B) — ONTOLOGY HONESTY blind spot: `test_ontology_honesty` only checks catalog entries'
  flags, never asserts every implemented tool IS catalogued; 40/58 implemented tools are absent from the
  1031-catalog (so "58 of 1031" framing is untrue + the WARN is not a gate). Fix: add reverse assertion +
  reframe/catalog. — self-audit H2.
- [B16] (bug/low/**DONE 2026-07-06**) — `crtsh`/`wayback`/`urlscan` 200-but-empty = success (can't tell "source empty" from
  "filtered to nothing"); HttpTool/CliTool swallow extractor exceptions to `entities=[]` (broken extractor ==
  "no findings"). **Fixed:** added `ToolResult.metadata` diagnostic channel (transport `success` unchanged);
  HttpTool/CliTool now SURFACE the extractor exception (`extractor_error`) instead of swallowing it, and record
  `entities_extracted` + an `empty_reason`; crtsh/wayback/urlscan record `rows_returned`/`snapshots_returned`/
  `results_returned` so "filtered to zero" is distinguishable from "source empty". — self-audit M5/L2.
- [AUDIT-L] (low/open) — health gate runs only 3 selector types + excludes network tools → tool-rot invisible
  between manual golden audits (add a periodic non-blocking live-smoke); phone-regex national-format edge (L3);
  no concurrency lock on multi-commit (latent — single-committer invariant, L4).
- [DOCTRINE-TRIM] (doctrine/med/open — **needs operator approach-nod**) — doctrine review: the analytic
  principles are right but the same few are restated 5-6× across files (over-prescription). CONSOLIDATE: one
  canonical anti-over-merge block + pointers (O1); collapse the convergence/coverage/exhaust cluster to 2
  principles (O2); make "no bespoke collection" a MECHANICAL bright-line not a self-granted exception (C1 — the
  failure that already happened); state honest-crediting ONCE + conditional calibration note (O4); demote the
  45-line Navigator dim-6 mechanics to a helper/docstring, keep the 4-line principle (O5). Cheap ADDS:
  evidence-preservation (snapshot+date for load-bearing findings — active line already fetches Wayback; G1);
  fold person-merges into the anti-merge rule (G7); one-line ACH framing; source-reliability qualifier in
  citations (NOT a 6×6 matrix); temporal category. NET = shorter, sharper doctrine.
- [GATE-STAKES] (architectural/open — **needs operator sign-off**) — scale the MANDATORY red-team gate to
  stakes (lightweight grounding-only pass for small, no-attribution graphs). Touches CAPABILITY-LOCK's
  "mandatory gate" — sign-off required. — doctrine review C3/O4.
- [TOOL-CANDS-20260630] (candidate/open) — tool scout (Navigator + web), free/no-Go/non-loud net-new:
  **BlockCypher** (multichain crypto, no-key HTTP, 200/hr) + **Orbit** (BTC wallet clustering, Python) = the
  top crypto net-new (but crypto seeds haven't appeared in casework — wire only if crypto becomes in-scope);
  **OnionSearch** (Tor dark-web, Python — needs the G12 Tor proxy first); verify-first: EU e-Justice/BRIS +
  OpenOwnership (G9, may be web-line/dataset not API), LeakCheck public (G7 free metadata?). CONFIRMED PAID
  WALLS (no free fill): G5 phone→owner, G7 deep cracked-creds. Adds to CAND-gitrecon/blockchair/phunter.

## ARCHITECTURE — queued for deeper exploration
- [ARCH-collection-mode] (architectural/open — **needs operator sign-off; deeper exploration**) — PASSIVE vs
  ACTIVE separation is enforced at the AGENT/skill level (active_collector has the OPSEC posture: passive-first,
  proxy seam, scope-guard) but "active vs passive" is really a property of the TOOL. So the structured/gatherer
  line (conceptually passive third-party collection) can fire ACTIVE target-touching tools with NONE of the
  active line's OPSEC: **`http_title`** (live GET of the target home page), **`tls_cert`** (live TLS handshake
  to target :443), **`cloud_buckets`** (probes the target's own S3/GCS/Azure assets). Proposed direction: tag
  every tool with `collection_mode` (passive|active); make the OPSEC posture (passive-first via Wayback/urlscan,
  `OSINT_PROXY` seam) apply to ANY active tool regardless of which line runs it; gatherer = passive-only; active
  touches routed/flagged to the active line. A full pass must enumerate ALL active-touching tools (start:
  http_title, tls_cert, cloud_buckets, web_tech_fingerprint[already active], http_headers?). Touches the locked
  3-line model + pivot_map routing → design + sign-off first. — operator 2026-06-30.

## GAPS — intel (capability; many are structural/paid)
- [G1] (gap/high/partly-mitigated) — reverse_ip free quota (HackerTarget ~2 calls) too small.
  **2026-06-24: added `robtex_ip` as a 2nd free passive-DNS/reverse-IP source.** Still no key;
  for scale a key/auto-fallback is the long-term fix. — viory re-test.
- [G2] (gap/med/partly-mitigated) — cert-HISTORY correlation. **2026-06-24: added `certspotter`
  (CT issuance history: issuers/dates + tbs/pubkey fingerprints in metadata).** History is now
  retrievable; cross-domain shared-cert correlation is supervisor-side (compare fingerprints). — viory.
- [G3] (gap/med/open) — JS-rendered branding: http_title can't see SPA `<title>` (now flagged, not solved). — viory.
- [G4] (gap/high/structural) — people identity last-mile (handle/name → verified real person) is paid
  (Pipl/Spokeo/OSINT Industries). Web-search snippets + relatives queries get far but stay `probable`.
- [G5] (gap/med/structural) — phone → owner/carrier/SIM is paid (Twilio/Trestle). Have validation + account-existence only.
- [G6] (gap/med/structural) — reverse-image / face search: paid/manual wall.
- [G7] (gap/med/structural) — deep breach (cracked creds): paid (DeHashed/Snusbase). Have free breach (xposedornot/Hudson Rock).
- [G8] (gap/med/open) — Telegram deep / Instagram content: needs an account/session (custom runner, not built).
- [G9] (gap/med/open) — non-US/UAE corporate registries (a UAE free-zone entity is invisible to sec_edgar/courtlistener).
- [G10] (gap/low/partly-mitigated) — Go toolchain → subfinder/amass/httpx/gau (no Go). **2026-06-24:
  `certspotter` adds CT-based passive subdomain breadth (Python/HTTP, no Go); crt.sh+certspotter
  now cover much of what subfinder's CT sources do.** Non-CT passive sources (AnubisDB/rapiddns)
  were non-viable (Cloudflare 403 / sparse). — design.
- [G11] (gap/low/done) — exiftool binary not installed (wrapper ready; choco needs elevation).
- [G12] (gap/med/open) — dark-web (.onion) search. Ahmia clearnet is JS-rendered (no-JS HTML empty);
  SpiderFoot's own dark-web modules require a Tor SOCKS proxy. **Path: run a local Tor proxy + route
  Ahmia/onionsearchengine through it (custom runner).** Not faked. — SpiderFoot intake 2026-06-24.
- [G13] (gap/low/done) — cloud_buckets covers AWS S3 + GCS; Azure Blob + DigitalOcean Spaces not yet
  probed (different account/container + region model). Extend cloud_buckets when needed. — SpiderFoot intake.

## DIRECTED INITIATIVES — operator 2026-07-14 (Telegram AI-content / foreign-influence)
- [INIT-TELEGRAM-AICONTENT] (initiative/high/open — PLAN produced, not yet executed) — Operator's new
  role problem: adversaries generating lots of AI-generated content on **Telegram**; operator knows some
  of the TEXT (and sometimes channels) but little else. GOAL: find that content and SHOW it is part of a
  coordinated deception / **foreign-influence** network. Deliverable requested = a PLAN, not an
  investigation. **Initial plan report written to `planning/telegram-ai-influence-plan.md` (LOCAL/
  gitignored — NOT public).** Core reframe: AI-detection alone is weak/unreliable → the provable signal is
  COORDINATION (same/near-duplicate text across many channels + forwarding graphs + timing). Arc:
  content(seed) → discovery → near-dup clustering → network(forwarding) → coordination/attribution → tiered
  report. Uses our web_searcher line + graph/tiering/red-team; the DEEP-Telegram collection is the **G8
  gap** (needs a session/API runner — e.g. Telethon/TeleGraphite/Telepathy). Navigator-surfaced tools:
  TgramSearch, TeleGraphite, Telepathy, TOsint, telegram-archive (IA); AI-detectors Copyleaks/Originality/
  Hive (Navigator noted NONE do near-dup clustering — that's a small BUILD). Flare (intake above) indexes
  illicit Telegram = relevant.
  **STEP 1 DONE 2026-07-14 (passive tools; operator-approved "tools now, agent next, active later"):**
  wired **`telegram_channel`** (`src/tools/telegram_tools.py`) — passive fetch of Telegram's OWN
  server-rendered `t.me/s/<channel>` (no account/key): extracts posts + **forwarded-from source channels
  (forwarding-graph edges)** + linked channels + **external domains** in posts (attribution pivots →
  domain toolchain). Routes on `telegram_handle` (+ accepts t.me `url`); passive-first + OSINT_PROXY seam
  + B16 empty-honesty. TOOL_FLOOR 58→59; live-validated (@durov: 20 posts). Clean type split:
  `username`=cross-platform enumeration vs `telegram_handle`=Telegram-specific (test updated; general
  fallback invariant preserved via discord_id). **`tgramsearch` EVALUATED & REJECTED** — cards hide the
  channel behind an internal `/join/<id>` redirect (no @handle/t.me link) → no clean passive extraction
  (would ship display-name noise, cf. GAP-20260626-01); DISCOVERY stays on the WEB-SEARCH line
  (`site:t.me` dorks). xtea.io also rejected (JS-walled). **NEXT (Step 2, needs sign-off):** dedicated
  `telegram_collector.md` skill (discover→fetch→walk-forwards→pivot); then Step 3 active tier (research acct).

## DIRECTED INITIATIVES — operator 2026-06-24 (full brief: intake/2026-06-24-operator-directives.md)
Source: ground-truth comparison of INV-20260624-001 vs the Indicator/Maldita "ticket trap"
investigation. Suggested sequence: D1+RT1 → R1 → G14+A1 → G15/G16/F1. [architectural] = design-confirm
with operator first; mandate given.
- [D1] (doctrine/CRITICAL/done) — STOP OVER-MERGING. Co-tenancy ≠ co-ownership: never merge entities
  into "one operator" on shared-hosting alone; require an INDEPENDENT corroborator (shared registrant
  OR tracker/analytics ID OR unique contact) first; flag "may be one of N clusters." Operator's #1
  concern (61 entities/100 edges = a wrong merge can't be hand-verified). **DONE 2026-06-24:** added
  "Attribution discipline — DON'T OVER-MERGE" section to supervisor.md (infra-fact vs ownership-claim,
  independent-corroborator rule, cluster-hypothesis flag). Confirmed against ground truth: INV-20260624-001
  merged ~20 co-hosted lookalikes under THE WALKER TOURS LLC on shared-IP + shared-registrar alone; truth
  = TWO operators sharing infra, and the 2nd (My Top Tour / Al Andalus = MNPQ Gestores / LA BIBI, findable
  only via a shared Salesforce/tracker ID) was missed — the proof-of-need for G14. Also renamed the
  estimative tiers confirmed→**highly_likely** (probable/possible unchanged) and made "raw tool tags are
  not your tiers" explicit. RT1 (red-team agent) is the process control for this and remains open.
- [RT1] (architectural/new-agent/done) — RED-TEAM skill (skills/red_team.md): adversarially reviews the
  supervisor's findings before the report; challenges every merge/inference, flags over-merges + weak
  single-source "highly likely"s, returns down-tiers/splits. The process control for D1. **DONE
  2026-06-24 (user sign-off):** read-only reviewer; MANDATORY pre-report gate + on-demand mid-
  investigation (human or supervisor); 5 review dimensions (over-merge, single-source top-tier,
  attribution-verb drift, citation drift, missed disconfirmers/cluster-splits); writes `_redteam.json`,
  supervisor reconciles via graph_commit (relabel/down-tier/split, KEEP-don't-drop) over ~2 rounds.
  Wired into supervisor.md Phase 5.5; locked in CAPABILITY-LOCK. Next: G14 gives it a real tracker-ID
  corroborator to test merges against.
- [R1] (architectural/report/done) — Report-writer overhaul: report.md/html must be a NARRATIVE STORY
  of the investigation (how we got there; key pivots + decisions + when), structured data -> APPENDICES.
  BLUF -> Narrative -> Key findings -> Appendices. The share-with-humans product. **DONE 2026-06-26
  (user sign-off):** new flow — report-writer authors `_report.json`; `src/report/build.py` renders
  report.md + styled report.html (mermaid.js). BLUF carries an **OV-1** diagram; each pivot section is
  semi-instructional (teaches the technique), shows **what each tool returned**, and a **grounded
  Mermaid subgraph** (src/report/diagram.py — drawn from graph.json, can't depict an absent link); all
  data -> appendices. **Red-team Mode 2 (report grounding)** checks the draft vs graph+log for
  hallucinations/over-claims/phantom-data/citation-drift and loops with the writer until `grounded`.
  Visuals = Mermaid (no Node/browser/graphviz dep). Locked in CAPABILITY-LOCK item 7.
- [G14] (gap/HIGH/done) — WEB-TECH tracker-ID fingerprinting: active extractor (GA/AdSense/Pixel/Salesforce/
  Brevo/Yandex IDs -> identifier entities) + reverse-lookup (PublicWWW/SpyOnWeb/web-search). The reused-infra
  unlock; ALSO gives D1 its independent corroborator. Would have linked cluster-2 via its Salesforce org ID.
  **DONE 2026-06-25 (with A1):** built `web_tech_fingerprint` (in-house extractor; 15 id kinds + favicon
  mmh3) + `tracker_reverse` (PublicWWW free + optional SpyOnWeb key, degrades to guide). New umbrella type
  `tracker_id` (id_kind in metadata) + `favicon_hash`; survey said BUILD extraction / WIRE reverse. mmh3 dep;
  TOOL_FLOOR 55->57. Guide: guides/tracker-id-reverse-lookup.md.
- [A1] (architectural/new-agent/done) — ACTIVE COLLECTION skill (skills/active_collector.md), SEPARATE from
  web_searcher: actively touches the target's (potentially malicious) infra (live source, web-tech extractor);
  bespoke + OPSEC-aware (leaves logs on target; build room for future proxy/sandbox; NOT cyber/hacking; scams ok now).
  **DONE 2026-06-25 (user sign-off, built with G14):** the THIRD collection line. OPSEC posture: passive-first
  (Wayback) auto-escalating to a single minimal live GET, generic UA, no crawl, `OSINT_PROXY` seam (unset),
  fraud/scam scope-guard. Runs web_tech_fingerprint + tracker_reverse via collect.py (raw/analysis split — no
  graph). Wired into supervisor.md (3rd line, the ownership-corroborator pivot chain, and the red-team
  `demand_corroborator` -> go-get-the-tracker loop). Locked in CAPABILITY-LOCK.
- [D2] (doctrine/HIGH/done) — FLEXIBLE SEED-DRIVEN PIVOTING. Triggered by watching INV-20260626-001 (re-run
  of the INV-001 scam seed): the supervisor OVER-INDEXED on the prior case — it tunneled on the new tracker-ID
  tooling (tracker_reverse 84×, web_tech_fingerprint 22× + a hand-written urlscan scraper `_arch_step1.py`) and
  NEVER ran reverse_ip/robtex, skipping the IP→co-hosted-domain estate engine that built ~21 siblings last time
  → 32 nodes/15 domains vs INV-001's 79/40+. **DONE 2026-06-26:** supervisor.md pivot doctrine now mandates
  (1) EXHAUST the seed's options via plan_collection (no cherry-picking); (2) every investigation is
  INDEPENDENT — no anchoring on a prior case's framing/conclusion; (3) INFRA-FIRST (build the network:
  domain→IP→**reverse_ip/robtex** co-hosts→subdomains, THEN attribute; trackers are corroborators not the map;
  never leave a discovered IP un-reversed); (4) COLLECT ONLY through the 3 lines — **no bespoke collection
  scripts/sub-agents** (bypasses raw/analysis split + audit + OPSEC); (5) brief the path as a coherent
  seed→infra→estate→attribution ARC. — operator observation 2026-06-26.
  **REFINED 2026-06-26 (full INV-20260626-001 result):** the completed run VALIDATED D1+RT1+R1 — 81 nodes/51
  domains (after the IP prompt), it did NOT over-merge (split Walker vs a separate "Operator-2" on per-site
  GA4/UA; calibrated Ads `AW-`=medium→probable vs GA4/UA property=strong), and BOTH red-team gates ran
  (analysis ×2 + report-grounding Mode 2 caught 2 over-claims → fixed → `grounded` before ship). BUT it
  OVER-INVESTED in website-kit fingerprinting (web_tech 132×, tracker_reverse 86×, bespoke `_arch_*` JS/asset
  scrapers) — same tunnel-vision failure, inverted. Per operator: replaced D2's HARD source-specific mandates
  with FLEXIBLE ANALYTIC PRINCIPLES — confidence from CONVERGENCE of multiple INDEPENDENT sources (no single
  signal dominates); cover evidence CATEGORIES (registration/hosting/content/reputation) via whatever
  registered tools fit, not named-tool mandates; + a **coverage check** (don't conclude while plan_collection
  offers unrun tools on real entities). Kept no-bespoke + no-anchoring. Also refined report-writer OV-1: the
  BLUF graphic must center KEY FINDINGS (a conclusions diagram, ~5-8 nodes), not the pivot plumbing.
- [G15] (gap/med/open) — outside-in TTP playbook in web_searcher.md (adversary-pattern checks by category:
  fraud=ad-transparency+reviews+is-it-official; influence=syndication; phishing=lookalikes). TTP-keyed, repeatable.
- [G16] (gap/med/open) — traffic/reach analytics (SimilarWeb-style) + app-store scale signals (harm sizing).
- [F1] (standing/open) — supervisor analysis-quality evaluation: compare more runs to ground truth; tighten
  merge/precision/tiering doctrine from findings.
  **Data point 2026-06-26 (G14/A1 validation vs INV-20260624-001 ground truth):** ran `web_tech_fingerprint`
  on 4 real ticket-scam domains. Cluster 1 (Walker/Feel-the-City) sites share **Google Ads `AW-16724105870`**;
  Cluster 2 (My Top Tour/Al Andalus) sites share **Salesforce org `00D8b000001358R`** (the exact corroborator
  the Indicator/Maldita journalists used); the two clusters share NO IDs → the tool would have SPLIT them into
  two operators, refuting INV-001's over-merge. Confirms D1+RT1+A1/G14 reach the correct two-operator answer.
  Passive-first worked (C1 from Wayback, zero live touch; only live C2 sites escalated). tracker_reverse's live
  PublicWWW/SpyOnWeb lookup still unproven against the network.

## INTAKE QUEUE (resources to assess — Manager classifies: wire / backlog / guide / reject)
- [INTAKE-20260714-shodan] (intake/**wire-now**, operator has key) — full **Shodan API** (keyed). Upgrade
  over our free `shodan_internetdb`: full host detail (banners/certs/HTTP), and the killer feature —
  fingerprint SEARCH/pivot (favicon hash, TLS cert, JARM, HTTP title) to find OTHER hosts sharing a
  fingerprint + host HISTORY. Infra estate-expansion + the reverse-fingerprint corroborator. Wire as
  HttpTool on ip_v4/domain; add SHODAN_API_KEY (graceful degrade). Ranked #2 of the 3 CTI sources.
- [INTAKE-20260714-dnslytics] (intake/**wire-now / #1**, operator/team has key) — **DNSlytics**: reverse
  DNS/NS/MX + **reverse-WHOIS** (all domains by registrant) + **reverse-Analytics** (domains sharing a
  GA/AdSense ID) + domain/IP history. Directly fills **GAP-20260624-01 (reverse-WHOIS — the top blocker)**
  and eases **G1** (reverse-IP at scale) and gives a 2nd source for the tracker corroborator (vs SpyOnWeb).
  Highest-value of the 3 for domain/IP network mapping. Wire as HttpTool (reverse endpoints) on domain/ip_v4.
- [INTAKE-20260714-flare] (intake/**wire-now**, operator has key) — **Flare**: threat-exposure aggregator
  over dark-web / illicit Telegram+forums / stealer-logs / leaked creds / paste+bucket+git leaks. Net-new
  THREAT-INTEL line; fills **G7 (deep breach)** + **G12 (dark-web)** and pushes toward ATTRIBUTION. Wire as
  HttpTool on domain/ip_v4/email; treat hits as LEADS (`possible`/`probable`) per tiering doctrine.
  Note: Flare indexes illicit Telegram — RELEVANT to the new Telegram initiative below.


- [INTAKE-20260626-user-scanner] (intake/**WIRED 2026-06-26**) — github.com/kaifcodec/user-scanner.
  **Validated hands-on (isolated venv) + adopted EMAIL-ONLY as `user_scanner` (structured line).**
  Benchmark vs holehe on the same email: user-scanner ~80% determinate over ~100 sites vs holehe ~37%
  (holehe ~63% rate-limited) — a materially more reliable email enumerator with a complementary site mix;
  **mitigates B4** (holehe lead-only). Categorization: STRUCTURED line (queries third-party platforms about
  the selector, like holehe; does NOT touch the target's infra → not active-line). NOT wired: username mode
  (duplicates sherlock/maigret/naminter/linkook), `--hudson` (redundant with hudsonrock_email + it calls
  input() → would hang), `--allow-loud` (OPSEC: emails the target). Wrapper `src/tools/userscanner_tools.py`
  (email-only, --no-nsfw, positives-only, `possible`). Dep: pip `user-scanner` (httpx, light). TOOL_FLOOR
  57→58. Live-tested. — user 2026-06-26.

- [INTAKE-20260626-osint-navigator] (intake/**approved — design+wire next**) — OSINT Navigator (Indicator
  Media / Tom Vaillant): a RAG tool-DISCOVERY engine over ~7,500 OSINT tools (9 toolkits, weekly-refreshed,
  deprecated-flagged; LLM recommends ONLY tools in the DB — no hallucinated tools). MCP supports Claude Code;
  API/MCP for members (~50 queries/day). **Operator has a subscription; key stored in `.env` as
  `OSINT_NAVIGATOR_API_KEY` (gitignored, NOT committed).** Underlying dataset:
  https://huggingface.co/datasets/tomvaillant/osint-tool-database. **Decision: integrate at TWO targets
  (NOT the supervisor — keep it on our own ontology):**
  (1) **MANAGER / intake-discovery** — I use Navigator to find new best-in-class tools to wire + keep our
      ontology honest/fresh (flag deprecated, surface per-selector gaps). Best impl: pull the **HF dataset
      locally** (free, no rate-limit, bulk) and diff against our `tools_registry`/`pivot_map`; refresh periodically.
  (2) **RED TEAM (gap-covering)** — the red team queries Navigator for tools/angles/CATEGORIES the
      investigation didn't cover and raises them as INDEPENDENT completeness challenges ("you didn't check
      category X"). Best impl: the **live MCP/API** (per-case, low volume — fits the 50/day budget; query once
      by category, not per-entity). Findings → coverage challenges + Manager GAP log (most surfaced tools won't
      be wired — that's fine, they become manual leads / wiring candidates).
  Caveats: 50/day rate limit (red team must query sparingly); external dependency on an agent that's currently
  self-contained; recommends tools, doesn't pull data (strengthens COMPLETENESS challenges, not factual
  refutation). — operator 2026-06-26.
  **WIRED 2026-06-29 (red team):** verified the live REST API (`POST navigator.indicator.media/api/query`,
  Bearer auth) — chose it over the MCP (red team needs ONE structured headless query/case, not a conversational
  session; MCP URL is login-gated). New `src/tools/navigator.py` (`query_navigator()` — keyed via
  `OSINT_NAVIGATOR_API_KEY`, graceful degrade, NOT registered/routed so the supervisor can't reach it). Added
  red_team.md **dimension 6 (COVERAGE GAPS)**: one query/case by seed-type, diff recommended categories vs the
  graph's `source_tools`+`plan_collection`, emit `coverage_gap` challenges + `missed_hypotheses` +
  `MANAGER-GAP` wiring candidates; Navigator output is a completeness signal, NEVER a finding. Self-throttles on
  `rate_limit.queries_remaining`. Manager-discovery via the same module. Health GREEN. (MCP path optional, not wired.)
- [INTAKE-20260629-breadth-diff] (analysis/done) — Manager-side diff of our 58 tools vs the Navigator dataset
  (`tomvaillant/osint-tool-database`, 11,345 rows / 21 categories; mostly a web-only link directory — only
  ~10-20% automatable). **Verdict: our BREADTH is appropriate for the core selectors** (domain/ip/email/
  username/company — we run best-in-class; do NOT add more there). **Confirmed real gaps** (specific tools exist):
  dark-web/breach (=G7/G12), platform-specific social TikTok/IG/Telegram (session-gated =G8), crypto multichain
  (BTC+ETH only), email→phone + Google-account cross-pivots, aggregated subdomain enum. **Top FREE candidates
  that fit our stack (Manager-filtered):** `gitrecon`/GitSome (username→email+name from git commits), `Blockchair`
  (multichain crypto, free-tier HTTP API), `Phunter` (phone carrier/line-type, Python). **Rejected on our
  constraints:** Subfinder/mosint (Go — we have no Go toolchain, G10; certspotter+crtsh already cover CT
  subdomains), email2phonenumber (LOUD — pings target reset oracles, OPSEC), GHunt/Instagrapi/Telethon
  (session/cookie-gated = G8). — agent diff 2026-06-29.
- [INTAKE-20260626-spotlight] (intake/**borrow-methodology, reject code**) — buriedsignals/spotlight: a
  journalist editorial case-management system (Python multi-agent CLI, skills/agents/AGENTS.md). Overlaps us
  heavily (confidence grounding ≈ our tiering; independent fact-check ≈ our red team; report gen). Tools are
  keyed/newsroom (Firecrawl/Mycroft/Junkipedia) — not for us. **NO explicit OSS license stated → do NOT copy
  files/code; LEARN from the methodology only.** Borrow these IDEAS into our red-team/report gates: (a) a
  READINESS CHECKLIST before shipping (their 6 editorial checks — esp. "≥2 independent sources", "no
  unresolved disputes", "known gaps explicitly stated", "primary documents cited"); (b) CYCLE-TARGETING (a
  failed check makes the NEXT round target that specific gap — complements our coverage check); (c) PROVENANCE
  discipline (cite only locally-traceable material + source hashes — hardens grounding). Reject the
  workflow/tooling. Effort: small doctrine edits to red_team.md (Mode 2) + supervisor coverage loop. — operator 2026-06-26.

## WIRING CANDIDATES — validated free, ready to wire (from breadth diff 2026-06-29)
Net-new, free, no-key (or free-tier), fit our Python/HTTP stack, fill a real gap, don't duplicate locked tools.
- [CAND-gitrecon] (candidate/med/open) — `gitrecon` (or GitSome/gitcolombo): mine a GitHub/GitLab user's COMMIT
  HISTORY for exposed emails + real names. Selector: username (→ email/name). Free, Python CLI. Net-new
  username→identity pivot beyond `github_user` (which only reads the profile). Wire as a CliTool; positives
  `possible` (supervisor re-tiers). High value for the people/identity last-mile (G4-adjacent).
- [CAND-blockchair] (candidate/med/open) — Blockchair multichain API: one free-tier HTTP endpoint covering
  BTC/ETH/LTC/BCH/DOGE/+ address lookups (balance, tx history). Selector: crypto_btc/eth (+ new chains). Fills
  the crypto-multichain gap (we have BTC+ETH only). Wire as an HttpTool (graceful degrade past the free tier).
- [CAND-phunter] (candidate/low/open) — `Phunter`: phone validity + carrier + line-type + light footprint.
  Selector: phone. Free, Python CLI. Modest enrichment beyond `phonenumbers`/`phoneinfoga` (carrier/line-type);
  partial relief for G5 (the owner/SIM half stays paid). Lower priority than the two above.
- REJECTED from the breadth diff (don't wire): Subfinder/mosint (Go — no toolchain, G10; certspotter+crtsh cover
  CT subdomains); email2phonenumber (LOUD — pings target reset oracles, OPSEC); GHunt/Instagrapi/Telethon/
  TikTokApi (session/cookie-gated — that's the G8 wall, not a quick wire).

## TIER-2 keyed tools — TODO (need free API keys; user not provisioning now)
threatfox(ABUSE_CH_API_KEY), VirusTotal, AlienVault OTX, AbuseIPDB, Etherscan v2, Netlas,
YouTube Data, Companies House, HIBP(paid). Coded to degrade gracefully; flip on when keyed.
- **SpyOnWeb (`SPYONWEB_API_KEY`, FREE key)** — the real automated reverse-tracker path (the free
  PublicWWW HTTP path is JS-rendered → unusable; confirmed 2026-06-30). `tracker_reverse` already has the
  SpyOnWeb adapter; provisioning the free key makes the anti-over-merge corroborator chain self-serve.
  **High value — recommend provisioning this one** (like the OSINT Navigator key).
- PublicWWW API (PAID) — full source-code reverse-search; the paid alternative to SpyOnWeb.

## Supervisor-logged gaps (appended by investigation sessions)
<!-- The supervisor appends `[GAP-<date>-NN] (gap/priority/open) — <what it needed and couldn't do> — INV-<case> -->
- [GAP-20260624-01] (gap/high/open) — reverse-WHOIS: no way to enumerate ALL domains by a registrant org/EIN (e.g. "The Walker Tours LLC" / EIN 37-2091569). Needs paid API (DomainTools/SecurityTrails/WhoisXML reverse-whois). This is the main blocker to mapping a full scam-domain network from its registrant. — INV-20260624-001
- [GAP-20260624-02] (gap/med/open) — threatfox tool returns `{"error":"Unauthorized"}` (needs ABUSE_CH_API_KEY). No IOC-reputation verdict available for domains/IPs. — INV-20260624-001
- [GAP-20260624-03] (gap/low/open) — crt.sh (404) and wayback (503) both failed this run; transient but recurrent. CT-history fell back to certspotter; no archive snapshots retrieved. — INV-20260624-001
- [GAP-20260624-04] (gap/med/open) — `reverse_ip` (HackerTarget) quota exhausted after ~2 IPs; the 3rd/4th network IPs (18.190.207.230, 143.47.57.203) had NO co-host enumeration except robtex+urlscan (incomplete). Reinforces G1 — a keyed/rotating reverse-IP source is needed to fully enumerate multi-IP scam estates. — INV-20260624-001
- [GAP-20260626-01] (gap/high/**FIXED 2026-06-30** — see note below) — `tracker_reverse` PublicWWW path returns PARSER-ARTIFACT NOISE (asset filenames + JS tokens like `favicon.ico`, `bootstrap.min.css`, `document.cookie`, `math.random` returned as "domains") instead of real co-using domains, even when it reports `publicwww_hits>0` / `strong_ownership_signal=True`. SpyOnWeb path needs SPYONWEB_API_KEY (skipped). Net: reverse-tracker enumeration is effectively non-functional automatically — could not enumerate other domains carrying GA4 G-6PLNK76P14 / Ads AW-16724105870. Needs (a) a real domain-extraction parser for PublicWWW results, and/or (b) a keyed source. This is the automation of the anti-over-merge corroborator chain — high value. Note: this case re-hit the SAME operator as INV-20260624-001 (Walker Tours, EIN 37-2091569). — INV-20260626-001
  **FIX NOTE 2026-06-30:** root cause was deeper than parsing — PublicWWW results are JS-RENDERED, so a no-JS
  HTTP fetch returns only page chrome; the old whole-page regex scraped PublicWWW's own nav/footer/asset refs as
  "domains." Now: scope-parse only real result-row anchors + a strict domain validator (reject file-ext "TLDs");
  on the JS/empty page return CLEAN-EMPTY + an honest note (no junk). The FREE path can't deliver automated
  results; the WORKING path is keyed SpyOnWeb (Tier-2, recommend provisioning). Verified 0 junk on G-/AW- ids.
- [IDEA-20260630-corroboration-loop] (doctrine/note/open) — operator idea: when reverse_ip (or any pivot)
  surfaces NEW co-hosted domains, fingerprint THEIR trackers too (active line) and compare → shared id corroborates
  same-operator, different ids split. **Largely ALREADY covered** by D2 "exhaust the seed's options / pivot every
  new entity" (a co-hosted domain is a new entity; plan_collection offers web_tech_fingerprint for it). Keep it
  PRINCIPLE-based (gather corroboration on new entities), NOT a hardcoded "fingerprint all co-hosts" rule. Consider
  one explicit example in the DOCTRINE-TRIM pass. — operator 2026-06-30.
- [GAP-20260624-05] (gap/low/open) — `shodan_internetdb` returned "No information available" for all three AWS EC2 IPs (only the Oracle IP had data) — AWS-hosted hosts give no port/service fingerprint via InternetDB. — INV-20260624-001
- [GAP-20260624-06] (gap/low/open) — `bgpview_ip` DNS resolution failed ("getaddrinfo failed" for api.bgpview.io) on this run; ASN data came from urlscan/robtex instead. Transient network/DNS issue. — INV-20260624-001

## Recently DONE (Manager closes items here)
- Backlog sweep (3 batches, all health-gated GREEN): B8 threatfox auth-skip, B1 collect schema,
  B9 gate speed, B3 courtlistener name-gate, B2 socid scope, B4 holehe lead-only, B6 whois->rdap,
  B5 report.md de-lossied, B10 certspotter token, G13 cloud_buckets Azure/DO, G11 exiftool installed
  (winget user-scope; 12/12 CLI tools READY). — 2026-06-24.
- SpiderFoot intake: +4 free no-key tools (certspotter, robtex_ip, cloud_buckets, pgp_keyserver)
  in `sf_derived_tools.py`; 51→55 tools, +`keyword` runnable; G1/G2/G10 partly-mitigated; dark-web
  logged as G12 (not faked). Engine/CLI rejected (architecture). — 2026-06-24.
- HTTP retry/backoff (rdap/crt.sh/reverse_ip), http_title JS-note, log auto-init, sherlock txt→temp,
  hardcoded paths → `python -m` — 2026-06-23.
- 9 arsenal additions + 3 infra tools (51 tools); family-recovery snippet fix — 2026-06-22.
