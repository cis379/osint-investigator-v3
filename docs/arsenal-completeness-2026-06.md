# Completeness Analysis vs awesome-osint-arsenal (751 tools)

Cross-checked our ontology against rawfilejson/awesome-osint-arsenal. The arsenal is a
broad security mega-list; **~35 of its 50 categories are out of scope** for a
selector-pivot OSINT system (red team, exploitation, password cracking, wireless,
mobile hacking, hardware, OS distros, CTF, learning, Georgian-localized 500+). This
analysis covers the **15 pivot-relevant categories**.

## Verdict: strong on the free-automatable core; the "gaps" are structurally paid/manual

The arsenal **confirms our best-in-class picks** — Sherlock, Maigret, Holehe,
theHarvester, ExifTool, Hudson Rock, GLEIF, Etherscan all appear as the recommended
tools, and we already run them. Most arsenal "extras" are one of: redundant (20
username tools vs our best 5), dead (h8mail, NExfil, OSRFramework, Infoga, EmailRep —
already excluded), paid/manual (facial recognition, people-search, deep breach, threat
-intel platforms), out-of-scope (Nmap/Masscan active scanning, forensic suites), or Go
tools we've deferred (Amass, Subfinder).

## Completeness scorecard by capability
| Capability | Our coverage | Grade | Arsenal-confirmed gap |
|---|---|---|---|
| Username enumeration | sherlock, maigret, naminter, linkook, socid_extractor | **A** | — (we have the best) |
| Email → accounts / verify | holehe, disify, theHarvester | **B+** | email-HEADER analysis (we have eml/email_header types, NO tool); Hunter.io (key) |
| Breach / leak | hudsonrock_email (free) | **B-** | **XposedOrNot (FREE API)**; HIBP/DeHashed/IntelX (paid/key) |
| Domain / DNS / subdomain | whois, rdap, dns_lookup, crtsh, theharvester | **A-** | Amass/Subfinder (Go, deferred); **dnsrecon/Sublist3r (py)** |
| IP / ASN / reputation | ip_geolocation, ipinfo, shodan_internetdb, ripestat, bgpview, greynoise | **A** | AbuseIPDB (key-TODO) |
| Phone | phoneinfoga (unmaintained) | **D** | **Ignorant (free CLI)**, **phonenumbers (free lib)**; carrier = paid |
| Company / corporate | gleif_lei | **C+** | **SEC EDGAR (free)**, **Aleph/OCCRP (free)**, Companies House (key) |
| Crypto | blockchain_btc, blockstream, etherscan | **B** | clustering = paid (Arkham/Chainalysis) |
| Image / metadata | exiftool | **C** | reverse-image (TinEye paid; Yandex/Lens manual) |
| People / identity | (web-search line) | **D** structured | Pipl/BeenVerified/Spokeo/OSINT Industries — all paid; **CourtListener (free legal API)** |
| Geolocation | nominatim_reverse | **C** | rest are manual GEOINT (human-driven), not selector pivots |
| Telegram | (deferred) | **D** | Telethon/Telepathy need an account/session (Tier-4 custom); rest are manual bots |
| Threat intel | threatfox (key-TODO) | **C-** | enterprise platforms (paid); OpenCTI/Yeti self-hosted |

## STATUS: 9 of 10 additions WIRED (2026-06-22)
Wired + validated live: XposedOrNot, Ignorant, phonenumbers, socialscan, SEC EDGAR,
Aleph/OCCRP, dnsrecon, email-header analyzer, CourtListener. Tools 39 → 48.
Deferred: Metagoofil (overlaps theHarvester, low priority). `aleph_occrp` runs but is
sparse without `ALEPH_API_KEY` (anonymous OCCRP access is limited).

## GENUINE free-automatable additions worth wiring (the real output)
These are in the arsenal, free, automatable, and we DON'T have them — true new pivots:
1. **XposedOrNot** — free breach API (email → breaches), no key. Closes part of the breach gap.
2. **Ignorant** — free CLI, phone → account existence (the "holehe for phone"). Best free phone add.
3. **phonenumbers** — free offline lib, phone validation/region/carrier-guess (was in capability map, never wired).
4. **socialscan** — free CLI, email+username existence (fast cross-check).
5. **SEC EDGAR** — free API, company → filings/officers (US).
6. **Aleph (OCCRP)** — free API, name/company → leaks/corporate records aggregator.
7. **dnsrecon** and/or **Sublist3r** — free Python subdomain CLIs (cover the Go-subfinder gap without Go).
8. **Email-header analysis** — parse eml/headers → originating IP/relays/sender (we have the selector types, no tool).
9. **CourtListener** — free API, US legal/court records (people/public-records pivot).
10. **Metagoofil** — domain → public-document metadata (overlaps theHarvester; lower priority).

## Structural gaps that are NOT closeable for free (be honest)
- **Facial recognition / reverse-image** — PimEyes/FaceCheck/TinEye paid; Yandex/Lens manual.
- **People-search identity last-mile** — Pipl/BeenVerified/Spokeo/OSINT Industries all paid.
- **Deep breach** (cracked passwords) — DeHashed/Snusbase/LeakCheck paid.
- **Enterprise threat intel** — Mandiant/CrowdStrike/Flashpoint/Intel471 paid.
- **Telegram deep** — needs an account/session (Tier-4 custom runner).
- **Carrier/owner phone** — paid (Twilio/Trestle).
These are covered partially by the **web-search line** (manual sites via WebFetch) and the
**Tier-2 paid/key TODOs**; they are not a wiring oversight.

## Bottom line on completeness
For **free, automatable, selector-pivot OSINT**, we are ~80-85% of the realistically
achievable surface. The 10 additions above would push the weak rows (phone, breach,
corporate, subdomain-without-Go) up a grade. Everything beyond that is paid, manual,
session-gated, or out of scope — not a gap we can close by wiring a free tool.
