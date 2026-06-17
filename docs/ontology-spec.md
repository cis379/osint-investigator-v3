# OSINT Ontology + Source Catalog — Authoritative Spec

*Baseline 2026-06-12. Reconciles three artifacts — the repo's `src/ontology/*.json` (114 selector types, ~1,031 tools), the standalone `~/OSINT_Tool_Ontology.md`, and estorides' declarative source model — against [landscape-survey-2026.md](landscape-survey-2026.md). This is the authoritative ontology layer for Tool A.*

## Headline finding

The current taxonomy is **inflated**: the 114 "selector types" mix true observables with output field-names, file formats, and aspirational stubs (24 have zero tools); the "1,031 tools" are mostly manual catalog entries (~21 are live). estorides is the disciplined opposite — a tight ~17-type canonical observable set with ~99 genuinely-callable declarative sources. **We collapse 114 → ~55 canonical observables** while keeping coverage intent, and adopt a declarative source model.

---

## A. Reconciled observable taxonomy (→ `Observable.type` enum)

`identity_strength`: strong = near-unique anchor, moderate = narrows but collides, weak = contextual/pivot-only.

**IDENTITY** — `email` (strong), `username` (moderate), `person_name` (weak, rename from `name`), `phone` (strong, E.164), `org_name` (weak, → Wikidata QID/LEI), `pgp_key` (strong, wire to keyserver), **`platform_account{platform,handle}`** (strong, NEW — *replaces 21 redundant per-platform handle stubs*). Keep numeric internal IDs `facebook_id`/`twitter_id`/`discord_id`/`vk_id` distinct (they pivot differently).

**INFRASTRUCTURE** — `domain`, `ipv4`, `ipv6`, `url`, `asn`, `certificate` (merge serial+fingerprint), `favicon_hash` (Shodan/FOFA pivot — wire it), `mac_address{is_bssid}` (merge bssid), `ssid` (WiGLE geo pivot), `port`/`cpe` (infra outputs).

**FINANCIAL** — `btc_address`, `eth_address`, `crypto_tx` (wire to explorers), `nft_token`, `lei`, `iban`, `bin`, **`payment_hash`** (strong, NEW — T&S shared-payment pivot). Drop generic `crypto_wallet` (resolve to btc/eth at detection). `credit_card_number` → keep only as redacted BIN (handling/legal).

**CONTENT/MEDIA** — `image` (pHash+SHA-256), `media{kind}` (collapse video/audio/document), `keyword{is_hashtag}`.

**GEOSPATIAL** — `coordinates` (merge `geolocation`), `street_address`, `cell_tower_id`.

**DEVICE** — `imei` (Luhn), `fcc_id`, `device{model,serial}`, **`device_id`** (NEW, T&S), **`session_id`** + **`cookie_id`** (NEW, T&S coordination), **`user_agent`** (NEW, weak fingerprint).

**MALWARE/THREAT** — `hash_md5`/`hash_sha1`/`hash_sha256`, `cve_id` (wire NVD/CIRCL), **`ghsa_id`** (NEW), `ioc` (composite tagged union).

**NICHE (keep, don't prioritize)** — transport/records: `license_plate`, `vin`, `vessel_mmsi`, `flight_number`, `container_number`, `ssn`/`national_id`/`document_id`.

### Hygiene actions
- **Collapse:** 21 platform handles → `platform_account`; `crypto_wallet`→drop; `geolocation`→`coordinates`; media trio→`media{kind}`; `bssid`→`mac_address`.
- **Demote (not observables):** 8 file formats (`eml/mbox/har/warc/twitter_archive/whatsapp_export/telegram_export/gpx`) → `Artifact.format`; output field-names that leaked in (`whois`, `dns`, `exif`, `metadata`, `transcript`, `code`, `regex`, `http_status_code`, `google_dork`, `app_id`) → output/evidence, not types.
- **Add 7+ for T&S:** `platform_account`, `payment_hash`, `device_id`, `session_id`, `cookie_id`, `user_agent`, `ghsa_id` (+`ioc`/`cpe`/`port`). The five T&S types become **first-class evidenced graph entities** so a pivot on a shared `device_id`/`session_id` is a logged PROV activity, not a hidden join (survey §4.4).

---

## B. Source/collector catalog — tiered

Full per-source table (input/output/access/posture/automation) is maintained as the YAML source set; tier guidance lives in [data-isolation-budget-deployment.md §2](data-isolation-budget-deployment.md). Provisioning highlights by observable:

- **domain/infra:** crt.sh, CertSpotter, DoH DNS, RDAP, Wayback, HackerTarget, urlscan (T1); SecurityTrails, Shodan, Censys, **Netlas**, **Criminal IP**, FOFA/Quake/Hunter.how (T2); Amass (CLI).
- **ip:** GreyNoise, AbuseIPDB, IPinfo, RIPEstat (T1); **Spur.us** (T2, essential — proxy/VPN attribution), wtfis wrapper.
- **email:** Holehe, EmailRep, XposedOrNot (T1); HIBP, Hunter.io, GHunt, Epieos, **OSINT Industries** (T2 flagship), DeHashed.
- **phone:** PhoneInfoga, libphonenumber (T1); Twilio Lookup/Trestle/Endato (T2).
- **username:** Maigret, Sherlock, WhatsMyName, **Naminter**, **Linkook**, GitHub/Reddit/Keybase/Mastodon (T1).
- **face/image:** EXIF, Yandex (T1); TinEye, **GeoSpy** (T2); PimEyes, FaceCheck.ID (T3).
- **crypto:** Blockchain.com, Etherscan (T1); **Arkham**, **Breadcrumbs** (T2); Crystal (T3).
- **social:** Reddit PRAW (T1); **Telerecon/TeleTracker/telegram-scraper** CLIs (T1), TGStat/Telemetr (T2).
- **threat IOC:** abuse.ch family, OTX, CISA KEV, Pulsedive (T1); VirusTotal (T2).
- **geo/records/sanctions:** Nominatim/Overpass, OpenSanctions/OFAC, Wikidata (T1); Sentinel Hub, WiGLE (T2); Pipl/Endato/Predicta/UserSearch (T2/T3).

**REMOVE:** **Castrick Clues** (`ext_0423_castrickclues`, shut down 2026-02-07) — delete from `pivot_map.json` under `username`/`email`/`phone`; substitute Epieos + OSINT Industries.

---

## C. Declarative source-definition schema (YAML)

Adopt estorides' code-free loader (drop a YAML in `sources/<NN_category>/`, no central registry edit) and **extend it** with typed observables, assertions, and evidence capture for the provenance layer.

```yaml
name:            # unique snake_case id
enabled:         # bool
category:        # "01. DNS Intelligence"
description:     # one line
tier:            # 1 | 2 | 3   (drives provisioning + cost gating)
input:
  observable_types: [domain, ip_v4]      # canonical enum (was estorides `applies_to`)
auth:
  required:      # bool
  type:          # none | api_key | basic | bearer | account_cookie
  key_env:       # env var name
posture:         # passive | broker | active | authenticated   (was `contact`)
rate_limit:      # "5/min" | "free:100/day"
logs_queries:    # bool — does provider log our lookups (OPSEC)
request:                                  # was estorides `tool`
  method: GET|POST
  url:           # {query} + {api_key} templating
  headers: {}
  params: {}
  body: {}
parser:          # named parser, OR inline extraction below
extraction:                               # NEW — structured output mapping
  observables:
    - { path: "$.subdomains[*]", type: domain }
  assertions:                             # NEW — typed reified edges + provenance
    - { subject: "{query}", predicate: resolves_to, object_path: "$.ip", confidence: 0.95 }
evidence:                                 # NEW — chain-of-custody directive
  capture: response_json                  # response_json | screenshot | mhtml
  hash: sha256
  retain: raw
```

Migration from estorides is mechanical: `requires_key`→`auth.required`, `key_env`→`auth.key_env`, `applies_to`→`input.observable_types`, `contact`→`posture`, `tool`→`request`; the flat `entity_hints` is **upgraded** to the structured `extraction` block (the missing provenance piece). Worked examples (crt.sh T1, Shodan T2) are in the source agent's output and should seed `sources/`.

### Parser/inferer contract (port from estorides)
Parsers and relationship-inferers **must be total — never raise, return empty container on junk.** Each source registers via `@register_parser`/`@register_inferer`. Each emitted edge becomes a **proposed** reified Assertion (gated, not fact).
