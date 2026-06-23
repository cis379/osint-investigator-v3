# CAPABILITY LOCK — the must-not-regress contract

The System Manager's prime directive is **don't break anything**. This file defines what
"anything" means. Every change must keep `scripts/health_check.py` GREEN and must not
regress the capabilities below. A change that breaks a lock item is reverted, not committed.

## Hard gate (automated — `python scripts/health_check.py`)
- All tools load (registry import clean); **tool count never drops** below the floor.
- `plan_collection` routes; `get_selector_capability` returns runnable tools.
- All 3 regression suites pass (baseline split-invariants, ontology honesty, selector detection).

## Locked architecture (do not remove/regress without USER sign-off)
1. **Raw/analysis split** — collectors (`collect.py`, `web_collect.py`) fetch raw + log;
   they NEVER write the graph. The supervisor tiers + commits via `graph_commit.py`.
2. **Two collection lines** — structured (gatherer) + web-search (web_searcher). Both kept.
3. **Ontology-driven routing** — `plan_collection` + `pivot_map`. No hardcoded routing.
4. **Confidence tiering** — confirmed/probable/possible; supervisor re-grades tool output;
   weak hits kept as `possible`, never dropped.
5. **Honest ontology** — implemented-vs-catalog flags stay consistent (annotate_implemented).
6. **Declarative runners** — HttpTool / CliTool: a new tool is a spec, not bespoke plumbing.
7. **Report last-mile** — graph.json/html + bibliography + report.md/html generate.

## Locked capabilities — the GOLDEN investigations (periodic live re-test)
These must keep working (the deterministic gate is fast; these are the real-world proof,
re-run on the daily audit / before a release):
| Seed | Type | Must recover (golden) |
|---|---|---|
| `example.com` | domain | infra: NS, IPs, certs/subdomains (control case) |
| `Robin Grieff` | name | attorney #5764840, ASU Director, Cornell JD, emails/phones, **family (Marvin+Brianna Grieff) via snippets** |
| `allthespills` | username | identity → Charles "Charley" Smith; Bluesky/Threads/Instagram |
| `viory.video` | domain | Viory↔Ruptly shared infra (AS200350, shared NS/IP), Darpo Vision FZ LLC, RT attribution |

## Locked tools (best-in-class — don't remove without a better replacement)
sherlock, maigret, naminter, linkook, holehe, theharvester, whois/rdap, dns_lookup/dnsrecon,
crtsh, urlscan, shodan_internetdb, ripestat, greynoise, reverse_ip, tls_cert, http_title,
gleif_lei, sec_edgar, hudsonrock_email, xposedornot, blockstream_btc, exiftool, phonenumbers,
email_header_analyzer + the web-search line.

## Change protocol (Manager)
1. health_check GREEN before starting. 2. Work on a branch. 3. Make the scoped change.
4. health_check GREEN after. 5. Commit + update CHANGELOG + BACKLOG. 6. If red → revert.
Architectural changes (touching the locked list above) require USER sign-off first.
