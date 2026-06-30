# OSINT Investigator

Multi-agent OSINT investigation system. Takes a seed selector, pivots through OSINT data sources, builds a graph, and produces a CTI report.

## Project Structure

- `src/core/selector.py` - Selector type detection (email, username, IP, domain, name, etc.)
- `src/core/state.py` - Investigation state management (create, pause, resume, archive)
- `src/ontology/` - Selector types, tools registry, and pivot map JSON files
- `src/tools/` - OSINT tool wrappers (each returns structured ToolResult objects)
- `src/tools/registry.py` - Tool loader and dispatcher
- `src/tools/collect.py` - **Gatherer's tool.** Runs OSINT tool(s), logs raw output, returns JSON. Does NOT touch the graph.
- `src/tools/graph_commit.py` - **Supervisor's tool.** Commits analyzed entities/relationships (with confidence tiers) to the graph; regenerates HTML + bibliography. Runs no tools.
- `src/tools/web_collect.py` - **Web-search collector's logger.** Logs a web-search round (queries/pages/findings) to investigation.md and echoes findings for the supervisor. No graph writes.
- `src/ontology/web_search.json` - The web-search LINE: per-selector-type search profiles (strategy, query templates, fetch priorities, extract targets). Read via `registry.get_web_search_profile(type)`.
- `src/tools/execute.py` - Legacy all-in-one (runs tool + auto-graphs everything as "confirmed"). Superseded by the collect/graph_commit split; kept as a fallback.
- `src/tools/name_tools.py` - Name-specific tools (Wikipedia, Wikidata, Gravatar, GitHub/GitLab username gen)
- `src/graph/database.py` - NetworkX-based investigation graph with JSON persistence
- `src/graph/visualizer.py` - vis.js HTML graph generator
- `src/logger/investigation_log.py` - Markdown investigation logger (full raw output)
- `src/report/cti_report.py` - CTI report generator (markdown)
- `src/report/html_report.py` - Professional HTML report (Google Docs / PDF ready)
- `src/report/bibliography.py` - Clickable bibliography with investigation links per entity
- `.claude/commands/investigate.md` - `/investigate` slash command definition
- `skills/` - Claude Code skill definitions for agents (supervisor, gatherer, report-writer)
- `ontology_viz/ontology.html` - Interactive ontology visualization of the full catalog
- `src/ontology/annotate_implemented.py` - Flags which catalog tools are actually implemented (re-run after wiring tools)

> **Ontology honesty (source of truth = the live registry).** What actually RUNS is the live
> `registry.py` (58 runnable tools) routed by `pivot_map.json` — always query
> `registry.get_selector_capability(type)` / `plan_collection` for the truthful view. The big
> `tools_registry.json` (1,031 entries) is a **roadmap of candidate tools**, NOT the registry of
> what's built: of the 58 runnable tools, ~18 were implemented FROM the roadmap and ~40 were
> **built beyond it** (recorded in `tools_registry.json` → `built_beyond_roadmap` so no live tool
> is invisible to the bookkeeping; `annotate_implemented` keeps it current, the honesty test gates
> it). ~20 of 90 selector types have a dedicated structured tool; the rest are covered by the
> web-search line (the universal fallback) or the general-username fallback, else logged as a GAP.
- `investigations/` - Output directory for investigation cases

## How to Run an Investigation

1. User types `/investigate <selector>` (e.g., `/investigate user@example.com`)
2. System detects selector type and creates investigation workspace
3. Supervisor agent plans investigation using ontology
4. Collection runs on two lines: the **structured** gatherer via `collect.py` (typed tools), and the **web-search** collector via `skills/web_searcher.md` + `web_collect.py` (real searches/fetches). The supervisor routes each selector to the right line(s) — web search is the primary line for `name`/`company`/`telegram_handle`.
5. Supervisor analyzes the raw results from both lines, tiers findings by confidence, and builds the graph via `graph_commit.py`
6. User interacts with supervisor throughout (redirect, inject seeds, ask questions)
7. Report writer produces CTI report + HTML report + bibliography when investigation completes

## Investigation Outputs

Each investigation produces these files in `investigations/INV-YYYYMMDD-NNN/`:

| File | Purpose | When Updated |
|------|---------|-------------|
| `investigation.md` | Full audit log with raw tool output | After every tool execution |
| `graph.json` | Raw graph data (entities + relationships) | After every tool execution |
| `graph.html` | Interactive vis.js entity graph | After every tool execution |
| `bibliography.html` | Clickable investigation links per entity | After every tool execution |
| `state.json` | Investigation status and metadata | After every state change |
| `report.md` | Markdown CTI report | At investigation completion |
| `report.html` | Professional HTML report (Google Docs ready) | At investigation completion |

The graph, bibliography, and log update live — open them in a browser and refresh.

## Running Tools

The collection step and the graph-building step are deliberately separate:
raw tool use (gatherer) is split from analysis/graph-building (supervisor).

### Collection — `collect.py` (gatherer; raw output, no graph):
```bash
# Single tool
python src/tools/collect.py --tool whois_lookup --selector example.com --type domain \
    --log investigations/INV-xxx/investigation.md

# All tools for a selector type
python src/tools/collect.py --run-all --selector example.com --type domain \
    --log investigations/INV-xxx/investigation.md
```

### Graph commit — `graph_commit.py` (supervisor; analyzed findings -> tiered graph):
```bash
python src/tools/graph_commit.py --graph investigations/INV-xxx/graph.json \
    --regen-html investigations/INV-xxx/graph.html --case INV-xxx --input findings.json
# findings.json: {"entities":[{value,type,tool,confidence,citation,depth}], "relationships":[...]}
# confidence is one of: highly_likely | probable | possible  (legacy "confirmed" == highly_likely)
```

### Legacy — `execute.py` (all-in-one; auto-graphs everything as "confirmed"):
Kept as a fallback only. Prefer the collect/graph_commit split above.
```bash
python src/tools/execute.py --run-all --selector example.com --type domain \
    --graph investigations/INV-xxx/graph.json --log investigations/INV-xxx/investigation.md \
    --depth 1 --case INV-xxx --regen-html investigations/INV-xxx/graph.html
```

### Via Python API:
```python
import sys
sys.path.insert(0, 'C:\\Users\\cis37\\osint-investigator-v3')
from src.tools.registry import run_tool, get_tools_for_selector, check_tool_availability

availability = check_tool_availability()
result = run_tool('whois_lookup', 'example.com', 'domain')
tools = get_tools_for_selector('domain')
```

## Key Design Principles

- **No hallucination**: Every finding must trace to specific tool output
- **Supervisor owns analysis**: Gatherer is a dumb data pipe, supervisor does all thinking
- **User in control**: User can talk to supervisor at any time during investigation
- **Full audit trail**: Everything logged to markdown with raw tool output in collapsible blocks
- **Conservative analysis**: Cite exact output, distinguish confirmed vs. inferred
- **Live outputs**: Graph, bibliography, and log update after every tool execution

## Automated Tools by Selector Type

| Type | Tools | What They Do |
|------|-------|-------------|
| **domain** | whois_lookup, dns_lookup, crtsh, wayback, http_headers | WHOIS, DNS records, SSL certs, web archives, headers |
| **ip_v4/v6** | ip_geolocation, reverse_dns, shodan_internetdb, ipinfo | Geolocation, rDNS, open ports, ASN |
| **email** | holehe, user_scanner, disify, hudsonrock, xposedornot | Account enumeration (user_scanner ~100 sites, more reliable than holehe), breach checks |
| **username** | sherlock, maigret, google_dork_generator | Profile discovery across 400+ sites |
| **name** | wikipedia_search, wikidata_search, gravatar_check, hibp_name_search, name_to_username, google_dork_generator | Wikipedia, Wikidata, Gravatar, email generation, GitHub/GitLab username checks |
| **crypto_btc/eth** | blockchain_btc, etherscan | Transaction history, balance |
| **url/domain** | urlscan, threatfox | Scan results, IOC matching |

## Dependencies

Python packages: `networkx`, `python-whois`, `dnspython`, `requests`, `beautifulsoup4`, `mmh3` (favicon hash; optional-degrading)
Optional CLI tools: `sherlock-project`, `maigret`, `holehe` (installed on-demand)

## vis.js Note

The `value` property is reserved by vis.js for numeric node scaling. Entity values are stored as `entityValue` in visualization data to avoid conflicts.
