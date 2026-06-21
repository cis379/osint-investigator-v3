# Known Gaps — come back to these

Living list of deferred work and capability gaps. Updated as we go.

## Deferred tooling
- **exiftool binary not installed** — wrapper + ontology wiring are DONE
  (`src/tools/image_tools.py`), but the binary isn't installed (choco needs
  elevation in this environment). To finish: `choco install exiftool -y` from an
  elevated shell, OR drop the portable Windows exe into `tools_installed/` and add
  it to PATH. Until then, `image`/`file`/`url` EXIF extraction is unavailable.

## Hard capability gaps (no free structured tool — from the capability research)
- **Reverse-image / face search** — money-or-manual (TinEye paid; Yandex/Lens/PimEyes manual).
- **Structured SERP / dorking APIs** — collapsed 2025–26 (Bing retired, Brave paid,
  Google PSE closed to new signups). Use the unstructured web-search line instead.
- **Non-notable person identification** — paid people-search only; structured covers
  notable people (Wikidata) + the web-search line.
- **Phone → owner name / live carrier / SIM-swap** — paid only (Twilio/Trestle).
- **Passive/historical DNS, WHOIS history** — paid only.
- **X / Twitter** — scraping dead (API lockdown); web-search best-effort only.
- **Paste / leak search** — no solid free structured API.
- **Free spam-caller reputation API** — none agent-callable (Truecaller/Hiya gated).

## Wired but environment-blocked (tool code is fine)
- **reddit_about** — Reddit returns HTTP 403 to datacenter IPs / non-OAuth clients.
  Tool is correct; needs a residential IP or Reddit OAuth to work. Username coverage
  meanwhile comes from maigret/sherlock + the web-search line.
- **bgpview_ip** — `api.bgpview.io` was unreachable from this environment (connection
  refused). Redundant with `ripestat_network` (works), kept as a fallback.

## To revisit later (lower priority)
- theHarvester needs the CLI runner (Tier-3) before company recon is wired.
- Instagram/Telegram profile extraction need the custom/session runner (Tier-4).
- GraphSense (crypto clustering) is free-but-gated (email request).
