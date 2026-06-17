"""Generate a clickable bibliography / lead tracker for an investigation.

Produces an interactive HTML file with every discovered entity as a clickable
link, grouped by type and sortable by confidence. Updated live during
investigation — just refresh the browser.

Usage:
    from src.report.bibliography import generate_bibliography
    generate_bibliography("investigations/INV-xxx")
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus


# For each entity type, generate actionable investigation URLs
def _investigation_links(value: str, entity_type: str) -> list[dict]:
    links = []
    v = quote_plus(value)

    if entity_type == "username":
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
            {"label": "Twitter/X", "url": f"https://x.com/{value}"},
            {"label": "GitHub", "url": f"https://github.com/{value}"},
            {"label": "Reddit", "url": f"https://www.reddit.com/user/{value}"},
            {"label": "Instagram", "url": f"https://www.instagram.com/{value}"},
            {"label": "Keybase", "url": f"https://keybase.io/{value}"},
            {"label": "Telegram", "url": f"https://t.me/{value}"},
            {"label": "NameCheckr", "url": f"https://www.namecheckr.com/search?q={v}"},
        ]
    elif entity_type == "email":
        local = value.split("@")[0] if "@" in value else value
        domain = value.split("@")[1] if "@" in value else ""
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
            {"label": "HIBP", "url": f"https://haveibeenpwned.com/account/{v}"},
            {"label": "Gravatar", "url": f"https://en.gravatar.com/{value}"},
            {"label": "Hunter.io", "url": f"https://hunter.io/verify/{v}"},
            {"label": "EmailRep", "url": f"https://emailrep.io/{v}"},
            {"label": "Google (username)", "url": f"https://www.google.com/search?q=%22{quote_plus(local)}%22"},
        ]
    elif entity_type == "domain":
        links = [
            {"label": "WHOIS", "url": f"https://who.is/whois/{value}"},
            {"label": "crt.sh", "url": f"https://crt.sh/?q=%25.{value}"},
            {"label": "Shodan", "url": f"https://www.shodan.io/search?query={v}"},
            {"label": "VirusTotal", "url": f"https://www.virustotal.com/gui/domain/{value}"},
            {"label": "Wayback", "url": f"https://web.archive.org/web/*/{value}"},
            {"label": "SecurityTrails", "url": f"https://securitytrails.com/domain/{value}"},
            {"label": "DNSDumpster", "url": f"https://dnsdumpster.com/?q={value}"},
            {"label": "URLScan", "url": f"https://urlscan.io/search/#{v}"},
        ]
    elif entity_type in ("ip_v4", "ip_v6"):
        links = [
            {"label": "Shodan", "url": f"https://www.shodan.io/host/{value}"},
            {"label": "VirusTotal", "url": f"https://www.virustotal.com/gui/ip-address/{value}"},
            {"label": "AbuseIPDB", "url": f"https://www.abuseipdb.com/check/{value}"},
            {"label": "Censys", "url": f"https://search.censys.io/hosts/{value}"},
            {"label": "IPInfo", "url": f"https://ipinfo.io/{value}"},
            {"label": "GreyNoise", "url": f"https://viz.greynoise.io/ip/{value}"},
        ]
    elif entity_type == "url":
        links = [
            {"label": "Open", "url": value},
            {"label": "Wayback", "url": f"https://web.archive.org/web/*/{value}"},
            {"label": "URLScan", "url": f"https://urlscan.io/search/#{v}"},
            {"label": "Google Cache", "url": f"https://webcache.googleusercontent.com/search?q=cache:{v}"},
        ]
    elif entity_type == "phone":
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
            {"label": "TrueCaller", "url": f"https://www.truecaller.com/search/{value}"},
            {"label": "SpyDialer", "url": f"https://www.spydialer.com/results.aspx?rid={v}"},
        ]
    elif entity_type == "name":
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
            {"label": "LinkedIn", "url": f"https://www.linkedin.com/search/results/people/?keywords={v}"},
            {"label": "Twitter/X", "url": f"https://x.com/search?q=%22{v}%22&f=user"},
            {"label": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{v}"},
            {"label": "Pipl", "url": f"https://pipl.com/search/?q={v}"},
            {"label": "OpenSanctions", "url": f"https://www.opensanctions.org/search/?q={v}"},
        ]
    elif entity_type == "company":
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
            {"label": "LinkedIn", "url": f"https://www.linkedin.com/search/results/companies/?keywords={v}"},
            {"label": "OpenCorporates", "url": f"https://opencorporates.com/companies?q={v}"},
            {"label": "Crunchbase", "url": f"https://www.crunchbase.com/textsearch?q={v}"},
            {"label": "OpenSanctions", "url": f"https://www.opensanctions.org/search/?q={v}"},
        ]
    elif entity_type in ("crypto_btc",):
        links = [
            {"label": "Blockchain.com", "url": f"https://www.blockchain.com/btc/address/{value}"},
            {"label": "BlockCypher", "url": f"https://live.blockcypher.com/btc/address/{value}/"},
            {"label": "WalletExplorer", "url": f"https://www.walletexplorer.com/address/{value}"},
        ]
    elif entity_type in ("crypto_eth",):
        links = [
            {"label": "Etherscan", "url": f"https://etherscan.io/address/{value}"},
            {"label": "DeBank", "url": f"https://debank.com/profile/{value}"},
        ]
    elif entity_type in ("hash_md5", "hash_sha1", "hash_sha256"):
        links = [
            {"label": "VirusTotal", "url": f"https://www.virustotal.com/gui/search/{value}"},
            {"label": "MalwareBazaar", "url": f"https://bazaar.abuse.ch/browse.php?search=sha256:{value}"},
            {"label": "ThreatFox", "url": f"https://threatfox.abuse.ch/browse/?search=ioc:{value}"},
        ]
    else:
        links = [
            {"label": "Google", "url": f"https://www.google.com/search?q=%22{v}%22"},
        ]

    return links


TYPE_COLORS = {
    "username": "#2e7d32", "email": "#1565c0", "domain": "#e65100",
    "ip_v4": "#c62828", "ip_v6": "#c62828", "phone": "#6a1b9a",
    "crypto_btc": "#bf360c", "crypto_eth": "#37474f", "url": "#00838f",
    "name": "#558b2f", "company": "#283593", "asn": "#9e9d24",
    "telegram_handle": "#00695c", "discord_id": "#5c6bc0",
}

CONF_PRIORITY = {"confirmed": 0, "probable": 1, "possible": 2}


def generate_bibliography(case_dir: str) -> str:
    case_dir = Path(case_dir)
    graph_data = json.loads((case_dir / "graph.json").read_text(encoding="utf-8"))
    state = json.loads((case_dir / "state.json").read_text(encoding="utf-8"))

    case_id = state.get("case_id", "Unknown")
    seed = state.get("seed", {})
    nodes = graph_data.get("nodes", [])

    nodes_sorted = sorted(nodes, key=lambda n: (
        CONF_PRIORITY.get(n.get("confidence", "confirmed"), 9),
        n.get("depth", 0),
        n.get("type", ""),
    ))

    # Group by type
    by_type = {}
    for n in nodes_sorted:
        t = n.get("type", "unknown")
        by_type.setdefault(t, []).append(n)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build entity cards
    cards_html = ""
    for entity_type in sorted(by_type.keys(), key=lambda t: -len(by_type[t])):
        entities = by_type[entity_type]
        color = TYPE_COLORS.get(entity_type, "#666")
        cards_html += f'<div class="type-group" data-type="{entity_type}">\n'
        cards_html += f'<h2 class="type-header" style="border-left:4px solid {color};padding-left:12px;">'
        cards_html += f'{entity_type} <span class="count">({len(entities)})</span></h2>\n'

        for n in entities:
            value = n.get("value", "")
            conf = n.get("confidence", "confirmed")
            depth = n.get("depth", 0)
            sources = ", ".join(n.get("source_tools", []))
            citation = n.get("citation", "")
            links = _investigation_links(value, entity_type)

            conf_class = f"conf-{conf}"
            links_html = " ".join(
                f'<a href="{lk["url"]}" target="_blank" rel="noopener" class="inv-link">{lk["label"]}</a>'
                for lk in links
            )

            cards_html += f"""<div class="entity-card" data-type="{entity_type}" data-conf="{conf}" data-depth="{depth}">
    <div class="entity-header">
        <span class="entity-value">{value}</span>
        <span class="badge {conf_class}">{conf}</span>
    </div>
    <div class="entity-meta">
        <span>Source: {sources}</span> | <span>Depth: {depth}</span>
    </div>
    <div class="entity-citation">{citation}</div>
    <div class="entity-links">Investigate: {links_html}</div>
</div>\n"""
        cards_html += "</div>\n"

    # Count stats
    total = len(nodes)
    confirmed = sum(1 for n in nodes if n.get("confidence") == "confirmed")
    probable = sum(1 for n in nodes if n.get("confidence") == "probable")
    possible = sum(1 for n in nodes if n.get("confidence") == "possible")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bibliography - {case_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family:'Inter',system-ui,sans-serif; background:#0d1117; color:#c9d1d9;
            max-width:1100px; margin:0 auto; padding:24px 32px;
        }}
        a {{ color:#58a6ff; text-decoration:none; }}
        a:hover {{ text-decoration:underline; }}

        .header {{
            border-bottom:2px solid #30363d; padding-bottom:20px; margin-bottom:24px;
        }}
        .header h1 {{ font-size:22px; color:#58a6ff; font-weight:700; margin-bottom:4px; }}
        .header .meta {{ font-size:13px; color:#8b949e; }}

        .controls {{
            display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px;
            padding:12px; background:#161b22; border-radius:8px; border:1px solid #30363d;
        }}
        .controls label {{ font-size:12px; color:#8b949e; margin-right:4px; }}
        .filter-btn {{
            padding:4px 12px; border-radius:14px; font-size:12px; cursor:pointer;
            border:1px solid #30363d; background:#21262d; color:#c9d1d9; transition:all 0.15s;
        }}
        .filter-btn.active {{ border-color:#58a6ff; background:#1f3a5f; color:#79c0ff; }}
        .filter-btn:hover {{ border-color:#58a6ff; }}
        #search {{
            flex:1; min-width:200px; padding:6px 12px; background:#0d1117;
            border:1px solid #30363d; border-radius:6px; color:#c9d1d9; font-size:13px;
        }}
        #search:focus {{ border-color:#58a6ff; outline:none; }}

        .stats {{
            display:flex; gap:16px; margin-bottom:20px; font-size:13px;
        }}
        .stat {{ padding:8px 16px; background:#161b22; border-radius:6px; border:1px solid #30363d; }}
        .stat .num {{ font-size:20px; font-weight:700; color:#e6edf3; }}
        .stat .lbl {{ color:#8b949e; font-size:11px; text-transform:uppercase; }}

        .type-group {{ margin-bottom:24px; }}
        .type-header {{
            font-size:15px; font-weight:600; color:#e6edf3; margin-bottom:10px;
            padding:8px 0;
        }}
        .type-header .count {{ color:#8b949e; font-weight:400; font-size:13px; }}

        .entity-card {{
            background:#161b22; border:1px solid #30363d; border-radius:8px;
            padding:14px 18px; margin-bottom:8px; transition:border-color 0.15s;
        }}
        .entity-card:hover {{ border-color:#58a6ff; }}
        .entity-header {{
            display:flex; align-items:center; justify-content:space-between;
            margin-bottom:6px;
        }}
        .entity-value {{
            font-size:14px; font-weight:600; color:#e6edf3;
            word-break:break-all; flex:1; margin-right:12px;
        }}
        .entity-meta {{ font-size:11px; color:#8b949e; margin-bottom:4px; }}
        .entity-citation {{ font-size:12px; color:#7d8590; font-style:italic; margin-bottom:8px; }}
        .entity-links {{ display:flex; flex-wrap:wrap; gap:6px; }}
        .inv-link {{
            display:inline-block; padding:3px 10px; border-radius:4px;
            font-size:11px; font-weight:500; background:#21262d; border:1px solid #30363d;
            color:#79c0ff; transition:all 0.15s;
        }}
        .inv-link:hover {{
            background:#1f3a5f; border-color:#58a6ff; text-decoration:none;
        }}

        .badge {{
            padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600;
            white-space:nowrap;
        }}
        .conf-confirmed {{ background:#238636; color:#fff; }}
        .conf-probable {{ background:#9e6a03; color:#fff; }}
        .conf-possible {{ background:#6e4014; color:#fff; }}

        .hidden {{ display:none !important; }}

        .footer {{
            margin-top:32px; padding-top:16px; border-top:1px solid #30363d;
            font-size:11px; color:#484f58; text-align:center;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>Investigation Bibliography</h1>
    <div class="meta">{case_id} | Seed: <code>{seed.get('value','')}</code> ({seed.get('type','')}) | Generated: {now}</div>
</div>

<div class="stats">
    <div class="stat"><div class="num">{total}</div><div class="lbl">Entities</div></div>
    <div class="stat"><div class="num">{confirmed}</div><div class="lbl">Confirmed</div></div>
    <div class="stat"><div class="num">{probable}</div><div class="lbl">Probable</div></div>
    <div class="stat"><div class="num">{possible}</div><div class="lbl">Possible</div></div>
</div>

<div class="controls">
    <input type="text" id="search" placeholder="Filter entities..." />
    <label>Confidence:</label>
    <span class="filter-btn active" data-filter="conf" data-val="all">All</span>
    <span class="filter-btn" data-filter="conf" data-val="confirmed">Confirmed</span>
    <span class="filter-btn" data-filter="conf" data-val="probable">Probable</span>
    <span class="filter-btn" data-filter="conf" data-val="possible">Possible</span>
</div>

<div id="content">
{cards_html}
</div>

<div class="footer">
    OSINT Investigator | {case_id} | This bibliography is auto-generated from investigation data.
    <br>Click any link to investigate further in your browser.
</div>

<script>
    const cards = document.querySelectorAll('.entity-card');
    const groups = document.querySelectorAll('.type-group');
    let activeConf = 'all';

    // Confidence filter
    document.querySelectorAll('.filter-btn[data-filter="conf"]').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.filter-btn[data-filter="conf"]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeConf = btn.dataset.val;
            applyFilters();
        }});
    }});

    // Search
    document.getElementById('search').addEventListener('input', () => applyFilters());

    function applyFilters() {{
        const query = document.getElementById('search').value.toLowerCase();
        cards.forEach(card => {{
            const val = card.querySelector('.entity-value').textContent.toLowerCase();
            const citation = card.querySelector('.entity-citation').textContent.toLowerCase();
            const conf = card.dataset.conf;
            const matchesSearch = !query || val.includes(query) || citation.includes(query);
            const matchesConf = activeConf === 'all' || conf === activeConf;
            card.classList.toggle('hidden', !(matchesSearch && matchesConf));
        }});
        // Hide empty groups
        groups.forEach(g => {{
            const visible = g.querySelectorAll('.entity-card:not(.hidden)').length;
            g.classList.toggle('hidden', visible === 0);
        }});
    }}
</script>
</body>
</html>"""

    output_path = case_dir / "bibliography.html"
    output_path.write_text(html, encoding="utf-8")
    return str(output_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    args = parser.parse_args()
    print(f"Generated: {generate_bibliography(args.case_dir)}")
