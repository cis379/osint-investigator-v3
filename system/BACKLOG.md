# System Backlog — the Manager's worklist

Single source of truth for **bugs (system — fixable)** and **gaps (intel — capability)**.
The System Manager triages + fixes from here (test-gated). Supervisor sessions APPEND new
`GAP`/`BUG` entries they hit during investigations (see the "Supervisor-logged" section).

Format: `[ID] (type/priority/status) — description — source`. status: open | in-progress | done | wontfix.

## BUGS — system (addressable; Manager can fix test-gated)
- [B1] (bug/med/open) — `collect.py` output schema inconsistent: single-tool returns `{tool,...}`,
  `--run-all` returns `{"results":[...]}`. Unify to one shape. — design review.
- [B2] (bug/med/open) — `socid_extractor` inert on JS/auth-gated socials (Bluesky/Threads/X) and
  on ASU/Cornell page types; the url→identity pivot rarely fires. Narrow advertised scope or fix. — system test.
- [B3] (bug/med/open) — `courtlistener_search` low precision: BM25 fuzzy → unrelated cases for short
  names (Robin, "Ruptly"). Add a relevance/name-match gate. — re-test (2 seeds).
- [B4] (bug/med/open) — `holehe` rate-limited to [x] on ~all sites per run → negatives meaningless,
  name→email→holehe verification can't verify. Add proxy/key or downgrade its role. — re-test.
- [B5] (bug/low/open) — `report.md` lossy vs `report.html`: cti_report.py doesn't escape `|` (breaks
  tables); truncates values to 40 chars; drops citations + the relationship table; dead `graph.png` ref.
  — report-writer validation.
- [B6] (bug/low/open) — `whois_lookup` no `.video`/many-TLD support (rdap covers; prefer rdap). — viory test.
- [B7] (bug/low/wontfix-ish) — maigret/sherlock/name_to_username self-stamp `confidence=confirmed`
  in-wrapper (mitigated by the supervisor tier doctrine; cosmetic). — multiple tests.
- [B8] (bug/HIGH/open) — `threatfox` returns `{"error":"Unauthorized"}` (abuse.ch made the API
  auth-mandatory). It is ROUTED into 4 types (domain, ip_v4, hash_sha256, hash_md5) and silently
  FAILS on every domain/IP investigation — a dead tool burning a slot. Fix: add free `ABUSE_CH_API_KEY`
  (Auth-Key header, graceful degrade) OR drop it from routing until keyed. — review 2026-06-24 (live-confirmed).
- [B9] (bug/med/open) — `cloud_buckets` runs ~80 live HTTP probes inside `replay_baseline` (domain
  run-all on example.com), pushing the health gate past 2 min. The gate tests PLUMBING, not coverage —
  exclude network-heavy tools from the baseline replay, or trim cloud_buckets' probe budget. — review 2026-06-24.
- [B10] (bug/low/open) — `certspotter` free tier is rate-limited (HTTP 429 after a handful of calls/hr).
  Healthy now, but heavy investigations / repeated gate runs will see it degrade. Add a free Cert Spotter
  token to Tier-2 (graceful) or cache per-domain. — review 2026-06-24.

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
- [G11] (gap/low/open) — exiftool binary not installed (wrapper ready; choco needs elevation).
- [G12] (gap/med/open) — dark-web (.onion) search. Ahmia clearnet is JS-rendered (no-JS HTML empty);
  SpiderFoot's own dark-web modules require a Tor SOCKS proxy. **Path: run a local Tor proxy + route
  Ahmia/onionsearchengine through it (custom runner).** Not faked. — SpiderFoot intake 2026-06-24.
- [G13] (gap/low/open) — cloud_buckets covers AWS S3 + GCS; Azure Blob + DigitalOcean Spaces not yet
  probed (different account/container + region model). Extend cloud_buckets when needed. — SpiderFoot intake.

## TIER-2 keyed tools — TODO (need free API keys; user not provisioning now)
threatfox(ABUSE_CH_API_KEY), VirusTotal, AlienVault OTX, AbuseIPDB, Etherscan v2, Netlas,
YouTube Data, Companies House, HIBP(paid). Coded to degrade gracefully; flip on when keyed.

## Supervisor-logged gaps (appended by investigation sessions)
<!-- The supervisor appends `[GAP-<date>-NN] (gap/priority/open) — <what it needed and couldn't do> — INV-<case> -->
- [GAP-20260624-01] (gap/high/open) — reverse-WHOIS: no way to enumerate ALL domains by a registrant org/EIN (e.g. "The Walker Tours LLC" / EIN 37-2091569). Needs paid API (DomainTools/SecurityTrails/WhoisXML reverse-whois). This is the main blocker to mapping a full scam-domain network from its registrant. — INV-20260624-001
- [GAP-20260624-02] (gap/med/open) — threatfox tool returns `{"error":"Unauthorized"}` (needs ABUSE_CH_API_KEY). No IOC-reputation verdict available for domains/IPs. — INV-20260624-001
- [GAP-20260624-03] (gap/low/open) — crt.sh (404) and wayback (503) both failed this run; transient but recurrent. CT-history fell back to certspotter; no archive snapshots retrieved. — INV-20260624-001

## Recently DONE (Manager closes items here)
- SpiderFoot intake: +4 free no-key tools (certspotter, robtex_ip, cloud_buckets, pgp_keyserver)
  in `sf_derived_tools.py`; 51→55 tools, +`keyword` runnable; G1/G2/G10 partly-mitigated; dark-web
  logged as G12 (not faked). Engine/CLI rejected (architecture). — 2026-06-24.
- HTTP retry/backoff (rdap/crt.sh/reverse_ip), http_title JS-note, log auto-init, sherlock txt→temp,
  hardcoded paths → `python -m` — 2026-06-23.
- 9 arsenal additions + 3 infra tools (51 tools); family-recovery snippet fix — 2026-06-22.
