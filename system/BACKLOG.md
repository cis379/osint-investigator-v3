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

## GAPS — intel (capability; many are structural/paid)
- [G1] (gap/high/open) — reverse_ip free quota (HackerTarget ~2 calls) too small for an investigation.
  Add a key OR auto-fallback to dns co-resolution + spacing. — viory re-test.
- [G2] (gap/med/open) — cert-HISTORY correlation: tls_cert reads live cert; historical shared-cert
  evidence needs crt.sh cert-history (times out). No robust path yet. — viory.
- [G3] (gap/med/open) — JS-rendered branding: http_title can't see SPA `<title>` (now flagged, not solved). — viory.
- [G4] (gap/high/structural) — people identity last-mile (handle/name → verified real person) is paid
  (Pipl/Spokeo/OSINT Industries). Web-search snippets + relatives queries get far but stay `probable`.
- [G5] (gap/med/structural) — phone → owner/carrier/SIM is paid (Twilio/Trestle). Have validation + account-existence only.
- [G6] (gap/med/structural) — reverse-image / face search: paid/manual wall.
- [G7] (gap/med/structural) — deep breach (cracked creds): paid (DeHashed/Snusbase). Have free breach (xposedornot/Hudson Rock).
- [G8] (gap/med/open) — Telegram deep / Instagram content: needs an account/session (custom runner, not built).
- [G9] (gap/med/open) — non-US/UAE corporate registries (a UAE free-zone entity is invisible to sec_edgar/courtlistener).
- [G10] (gap/low/open) — Go toolchain → subfinder/amass/projectdiscovery-httpx/gau (no Go installed).
- [G11] (gap/low/open) — exiftool binary not installed (wrapper ready; choco needs elevation).

## TIER-2 keyed tools — TODO (need free API keys; user not provisioning now)
threatfox(ABUSE_CH_API_KEY), VirusTotal, AlienVault OTX, AbuseIPDB, Etherscan v2, Netlas,
YouTube Data, Companies House, HIBP(paid). Coded to degrade gracefully; flip on when keyed.

## Supervisor-logged gaps (appended by investigation sessions)
<!-- The supervisor appends `[GAP-<date>-NN] (gap/priority/open) — <what it needed and couldn't do> — INV-<case> -->
(none yet)

## Recently DONE (Manager closes items here)
- HTTP retry/backoff (rdap/crt.sh/reverse_ip), http_title JS-note, log auto-init, sherlock txt→temp,
  hardcoded paths → `python -m` — 2026-06-23.
- 9 arsenal additions + 3 infra tools (51 tools); family-recovery snippet fix — 2026-06-22.
