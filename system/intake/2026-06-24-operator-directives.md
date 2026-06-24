# Operator directives — 2026-06-24 (routed from the analysis session)

**Context.** Ground-truth comparison of `INV-20260624-001` (seed `colosseumdiroma-tickets.com`)
vs the Indicator/Maldita.es "ticket trap" investigation. Our run matched **cluster-1 infrastructure
+ ownership** well (Walker Tours LLC ↔ Feel the City rebrand, contacts, Brevo correlation), but:
(a) **MISSED the 2nd operator cluster** (My Top Tour / Al Andalus / MNPQ Gestores / LA BIBI) — it
runs on *separate* infra and we pivot infra-first; (b) **missed the Google-Ads / demand mechanism**
(the article's headline); and (c) **OVER-MERGED** ~43 domains under one operator on shared-hosting
evidence (co-tenancy ≠ co-ownership).

These are **operator-DIRECTED**. Items marked **[architectural]** need design-confirm with the
operator, but the mandate is given. Every item follows the change protocol (branch + health-gate +
revert-on-red). Suggested sequence at the bottom.

## Priority 1 — ANALYTIC INTEGRITY (the operator's #1 stressed concern: NO over-merging)
- **[D1] (doctrine / CRITICAL)** — STOP OVER-MERGING. With 61 entities / 100 edges on screen, a wrong
  merge is nearly impossible to verify by hand. RULE for `supervisor.md`: do NOT merge entities into
  "one operator" on **shared hosting alone** — co-tenancy ≠ co-ownership. Require an **INDEPENDENT
  corroborator** (shared registrant OR shared tracker/analytics ID OR a shared unique contact) before
  asserting common ownership. When infra-pivoting, FLAG: *"this may be one of N clusters; I only see
  this operator's network."* Tier merges conservatively; a merge asserted on one link is `possible`,
  not `confirmed`.
- **[RT1] (architectural / NEW AGENT)** — RED-TEAM / analytic-challenge skill (`skills/red_team.md`).
  A separate agent that reviews the supervisor's committed findings **adversarially before the report**:
  challenges every merge/inference ("what else explains this? is shared-host the only link? is this
  'confirmed' actually single-source?"), flags over-merges and weak attributions, and returns required
  down-tiers / cluster-splits. This is the *process control* for D1 — the analytic back-and-forth a lone
  analyst skips. The supervisor must run it before finalizing.

## Priority 2 — THE REPORT IS THE PRODUCT (share-with-humans)
- **[R1] (architectural / report overhaul)** — The report-writer currently emits structured text, not a
  WRITE-UP. Rework `report-writer.md` + `cti_report.py` so report.md/html is a **NARRATIVE that tells the
  STORY of the investigation** — *how we got there*, walking through the KEY PIVOTS and the DECISIONS made
  and WHEN (the path), in prose a human reads and shares. Structured data (entity tables, relationships,
  raw) moves to **APPENDICES**. Structure: **BLUF → Narrative (the investigation story) → Key findings →
  Appendices.** Mirrors the supervisor's Decision-Briefing "path so far." (B5's pipe/citation fix is done;
  this is the bigger storyline rework — the share-with-humans artifact.)

## Priority 3 — REUSED-INFRA CORRELATION (also gives D1 its independent corroborator)
- **[G14] (gap / HIGH)** — WEB-TECH / tracker-ID fingerprinting. Build an ACTIVE extractor that fetches a
  site and pulls reusable IDs (Google Analytics `UA-`/`G-`, Tag Manager `GTM-`, AdSense `ca-pub-`, Meta
  Pixel, Salesforce org `00D…`, Yandex Metrica, Brevo, Hotjar/Clarity) → `identifier` entities. Then
  reverse-lookup an ID → other sites using it (PublicWWW / SpyOnWeb / DNSlytics free tiers, or the
  web-search line via `intext:` dorks). Reused analytics/pixel IDs are the **strongest cross-site
  ownership correlator** (networks paste the same snippet everywhere) — and they give D1 the independent
  corroborator it needs. Would have linked cluster-2 via its Salesforce org ID. Build the extractor
  ourselves (active fetch + regex, no key); source the reverse-lookup.
- **[A1] (architectural / NEW AGENT)** — ACTIVE COLLECTION skill (`skills/active_collector.md`), SEPARATE
  from `web_searcher`. It actively touches the TARGET's (potentially malicious) infrastructure — live site
  source, the web-tech extractor (G14), etc. — with bespoke handling and **OPSEC awareness** (it leaves
  logs on the target's server). For scam/fraud now this is fine; build it OPSEC-aware (note the risk; leave
  room for a future proxy/sandbox/routing layer) but do NOT over-engineer OPSEC yet. **NOT for cyber/
  hacking targets.** `web_searcher` stays PASSIVE (search + snippets); the active collector owns "go to the
  live bad site and extract."

## Priority 4 — coverage / standing
- **[G15] (gap / med)** — OUTSIDE-IN TTP playbook in `web_searcher.md`: adversary-pattern checks by suspected
  category — fraud (ad-transparency for the impersonated brand + review sites + "is this the official site?");
  influence (syndication/amplification footprints); phishing (lookalike-domain permutations). Repeatable
  because it's keyed to TRADECRAFT, not one search. (Ad-transparency = one fraud-TTP check, not a whole tool.)
- **[G16] (gap / med)** — traffic/reach analytics (SimilarWeb-style) + app-store scale signals, for harm sizing.
- **[F1] (standing)** — supervisor ANALYSIS-QUALITY evaluation: keep comparing runs to ground truth (operator
  supplies more cases); tighten the merge/precision/tiering doctrine from what we learn.

## Suggested sequence
**D1 + RT1** first (analytic integrity — the stressed concern) → **R1** (the report = the product) →
**G14 + A1** (the correlation tool + its active-collector home, which also strengthens D1) → G15/G16/F1.
