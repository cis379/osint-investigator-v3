# Full-System Test — 2026-06-21 (post HTTP-runner round)

Three autonomous supervisor runs, full system (both collection lines, 35 tools).
**Verdict: PASS end-to-end on all three.** Routing, both lines, tiering doctrine,
graph_commit, HTML/bibliography regen all functioned. New tools `rdap` + `github_user`
work. maigret `--json ndjson` upgrade is mechanically working (reads report file,
parses ids).

| Seed | Case | Entities (C/P/Po) | Outcome |
|---|---|---|---|
| example.com (domain) | INV-20260621-001 | 16 (12/0/4) | Infra from structured (rdap+whois+dns agree), governance from web search |
| Robin Grieff (name) | INV-20260621-002 | 22 (12/5/5) | **Every V1 golden item recovered**; structured thin, web-search carried it |
| allthespills (username) | INV-20260621-003 | 17 (4/5/8) | Instagram confirmed + identity recovered (self-stated→probable); missed JHU APL |

## BUGS to fix (data-quality / skill-doc) — prioritized
1. **[HIGH] urlscan wrapper returns the GLOBAL recent-scan timeline, not query-scoped.**
   Injected unrelated phishing domains (e.g. `proton-pass-...pages.dev`) as `confirmed`.
   Also mislabels **IPv6 as `ip_v4`**. Fix: filter results to those whose page/task
   domain contains the query; correct IPv6 typing.
2. **[HIGH] supervisor.md `log_analysis` snippet uses a non-raw `'C:\Users\...'` path**
   → `SyntaxError: unicodeescape`. Hit by 2 of 3 agents. Sweep ALL skill `python -c`
   snippets for backslash paths → use raw strings or forward slashes.
3. **[MED] crt.sh wrapper emits non-domains as `type:domain`** — emails
   (`user@example.com`) and CN-description strings tagged domain/confirmed. Filter.
4. **[MED] maigret trusts "Claimed" even when `http_status:404`** (Roblox, opensea
   returned 404 yet committed as accounts); OP.GG explodes one account into ~18 regional
   URL entities. Fix: drop 404s; dedupe OP.GG-style region dupes.
5. **[MED] threatfox = "Unauthorized"** without `ABUSE_CH_API_KEY` — currently dead
   weight on every domain/url run. Wire the key (Tier-2) or gate it.

## CAPABILITY GAPS (need wiring) — prioritized
1. **IOC / threat-intel: none functional.** threatfox keyless is dead. → VirusTotal v3,
   AlienVault OTX, AbuseIPDB (Tier-2, free keys).
2. **Reverse-IP / co-hosted domains** — absent (can't pivot IP→other domains).
3. **ASN/netblock on the domain line** — urlscan exposes ASN in raw JSON but the
   wrapper drops it; ripestat is IP-only. Extract ASN from urlscan, or add an IP→ASN
   step in the domain pivot.
4. **name→email→account verification pivot not closed** — `hibp_name_search` generates
   email candidates but nothing verifies them; the supervisor should chain them into
   `holehe`. Orchestration gap, not a tool gap.
5. **Deeper identity corroboration** — allthespills' JHU APL (and non-self-stated name
   confirmation) needs LinkedIn/paid or deeper web-search; structured can't reach it.

## DESIGN WINS (working as intended)
- **Tiering doctrine earns its keep every run** — re-graded tool self-"confirmed",
  excluded urlscan phishing, kept maigret FPs visible as `possible` (not dropped).
- **Web-search line is the identity MVP** for name + username seeds.
- Structured line is correctly strong on infrastructure (domain/ip) and thin on names —
  exactly the documented design.
