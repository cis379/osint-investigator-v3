# Capability Map — synthesis (structured gatherer line)

Consolidated from the 8 capability-research fragments in this folder. The per-tool
run-metadata lives in each `<bucket>.json`; this is the blueprint + wiring order.

**Totals:** 42 capabilities · 66 best-in-class tools (21 already wired, 45 to wire) · 99 excluded.

## The three runner categories (what the gatherer gets)
| Runner | How it executes | To-wire count | Examples |
|---|---|---|---|
| **HTTP** | declarative `api_url` template + auth + parse JSON | ~33 | RDAP, Hudson Rock, AbuseIPDB, GLEIF, RIPEstat, VirusTotal |
| **CLI** | declarative `install` + `command_template`, shell out (bounded) | ~9 | theHarvester, subfinder, httpx, gau, naminter, linkook |
| **custom** | bespoke (cookies/session/lib) | 5 | GHunt, Instaloader, Telegram, phonenumbers (lib) |

Most to-wire tools are HTTP and many are **free / no key** — a declarative HTTP runner
driven by catalog metadata wires them fast (no per-tool Python class).

## FIX-FIRST — bugs in already-wired tools (the research caught these)
1. **etherscan** — uses v1 keyless endpoint **sunset 2025-05-31**; silently degrading. Migrate to v2 `api.etherscan.io/v2/api?chainid=1&...&apikey=` + free key.
2. **threatfox** — abuse.ch now requires a free **Auth-Key header** (2024 policy); may be silently failing. Verify + add key.
3. **emailrep** — free tier folded into Sublime; effectively **dead**. Remove/replace.
4. **hibp_name_search** — **mislabeled**: does no breach lookup, only email permutation. Rename to reflect reality.
5. **exiftool** — orphaned (in no pivot_map type), binary uninstalled, and mislabels GPS as `name`. Install + switch to `-j -n` JSON, map GPS→`coordinates`, add `image`/`file` inputs.
6. **maigret** — already wired but parses plain stdout; switch run to **`--json ndjson`** to capture the linked emails/display-names socid-extractor already finds. Highest-value cheap fix.

## Wiring priority tiers (free → paid)
**Tier 1 — free, no key, HTTP (fit existing pattern, fastest):**
RDAP, Hudson Rock Cavalier (breach), Disify (email verify), Gravatar-for-email,
GreyNoise Community (IP noise), RIPEstat + BGPView (ASN/BGP), Blockstream Esplora +
mempool.space (BTC), OFAC sanctioned-addresses, etherscan-labels dump, Blockchair
(cross-chain), Nominatim (reverse geocode), GLEIF (LEI), SEC EDGAR, GitHub/Reddit/
Mastodon public JSON (profile extraction). (~17)

**Tier 2 — free key, HTTP:**
AbuseIPDB, VirusTotal v3, AlienVault OTX, Netlas (banners), YouTube Data API,
UK Companies House, IPQualityScore (phone fraud), Etherscan v2 (also fixes the bug).

**Tier 3 — CLI runner (build the runner, then wire):**
theHarvester (org recon), subfinder (subdomains), httpx (tech detect), gau (URL disc.),
naminter (anti-bot username recheck), linkook + socid-extractor (sock-puppet pivot), osgint.

**Tier 4 — custom / cookies / paid (last, with credential vault):**
phonenumbers (free python lib — easy), GHunt (Google cookies), Instaloader (IG cookies),
Telegram (Telethon session), HIBP (paid key), Twilio/Trestle (phone, paid),
TinEye (reverse image, paid), GraphSense/Arkham (chain clustering, gated), Google PSE (legacy key).

## Hard gaps (no free structured tool — honest)
- **Reverse-image / face search** — money-or-manual wall (TinEye paid; Yandex/Lens/PimEyes manual).
- **Structured SERP APIs collapsed (2025–26)** — Bing retired, Brave paid, Google PSE closed to new signups → use the **unstructured web-search line** for general search/dorking.
- **Person identification (non-notable)** — paid/people-search only; structured covers notable people (Wikidata) + the web-search line.
- **Phone → owner name, carrier at volume, SIM-swap** — paid only.
- **Passive/historical DNS, WHOIS history** — paid only.
- **X/Twitter scraping** — dead (API lockdown); web-search best-effort only.
- **Paste/leak search** — no solid free structured API.

## Excluded (99 tools)
Browser extensions, manual-only websites, dead/abandoned tools (SpiderFoot OSS, twint/
snscrape, h8mail/mosint, OXT.me), and paid-with-no-free-tier (OpenCorporates, Censys
Platform, SecurityTrails, Pipl/DeHashed/OSINT Industries). Recorded per-fragment so they
aren't re-evaluated.
