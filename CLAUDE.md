# OSINT Investigator

Multi-agent OSINT investigation system. Takes a seed selector, pivots through OSINT data sources, builds a graph, and produces a CTI report.

## Project Structure

- `src/core/selector.py` - Selector type detection (email, username, IP, domain, name, etc.)
- `src/core/state.py` - Investigation state management (create, pause, resume, archive)
- `src/ontology/` - Selector types, tools registry, and pivot map JSON files
- `src/tools/` - OSINT tool wrappers (each returns structured ToolResult objects)
- `src/tools/registry.py` - Tool loader and dispatcher
- `src/tools/execute.py` - Unified tool execution with auto graph/log/bibliography persistence
- `src/tools/name_tools.py` - Name-specific tools (Wikipedia, Wikidata, Gravatar, GitHub/GitLab username gen)
- `src/graph/database.py` - NetworkX-based investigation graph with JSON persistence
- `src/graph/visualizer.py` - vis.js HTML graph generator
- `src/logger/investigation_log.py` - Markdown investigation logger (full raw output)
- `src/report/cti_report.py` - CTI report generator (markdown)
- `src/report/html_report.py` - Professional HTML report (Google Docs / PDF ready)
- `src/report/bibliography.py` - Clickable bibliography with investigation links per entity
- `.claude/commands/investigate.md` - `/investigate` slash command definition
- `skills/` - Claude Code skill definitions for agents (supervisor, gatherer, report-writer)
- `ontology_viz/ontology.html` - Interactive ontology visualization (1031 tools, 114 selector types)
- `investigations/` - Output directory for investigation cases

## How to Run an Investigation

1. User types `/investigate <selector>` (e.g., `/investigate user@example.com`)
2. System detects selector type and creates investigation workspace
3. Supervisor agent plans investigation using ontology
4. Gatherer agents execute OSINT tools via `execute.py` (auto-logs, auto-graphs, auto-bibliography)
5. Supervisor analyzes results, identifies connections, plans pivots
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

### Via execute.py (recommended — handles logging, graph, bibliography automatically):
```bash
# Single tool
python src/tools/execute.py --tool whois_lookup --selector example.com --type domain \
    --graph investigations/INV-xxx/graph.json --log investigations/INV-xxx/investigation.md \
    --depth 1 --case INV-xxx --regen-html investigations/INV-xxx/graph.html

# All tools for a selector type
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
| **email** | holehe, emailrep | Account enumeration, reputation |
| **username** | sherlock, maigret, google_dork_generator | Profile discovery across 400+ sites |
| **name** | wikipedia_search, wikidata_search, gravatar_check, hibp_name_search, name_to_username, google_dork_generator | Wikipedia, Wikidata, Gravatar, email generation, GitHub/GitLab username checks |
| **crypto_btc/eth** | blockchain_btc, etherscan | Transaction history, balance |
| **url/domain** | urlscan, threatfox | Scan results, IOC matching |

## Dependencies

Python packages: `networkx`, `python-whois`, `dnspython`, `requests`, `beautifulsoup4`
Optional CLI tools: `sherlock-project`, `maigret`, `holehe` (installed on-demand)

## vis.js Note

The `value` property is reserved by vis.js for numeric node scaling. Entity values are stored as `entityValue` in visualization data to avoid conflicts.
