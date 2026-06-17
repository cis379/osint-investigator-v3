"""Generate a professional HTML CTI report suitable for Google Docs import.

Usage:
    python -m src.report.html_report --case-dir investigations/INV-xxx

Opens in browser. Copy-paste into Google Docs preserves formatting.
Alternatively, print to PDF from the browser.
"""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))


def generate_html_report(case_dir: str) -> str:
    case_dir = Path(case_dir)

    state = json.loads((case_dir / "state.json").read_text(encoding="utf-8"))
    graph_data = json.loads((case_dir / "graph.json").read_text(encoding="utf-8"))
    report_md = (case_dir / "report.md").read_text(encoding="utf-8") if (case_dir / "report.md").exists() else ""
    log_text = (case_dir / "investigation.md").read_text(encoding="utf-8") if (case_dir / "investigation.md").exists() else ""

    case_id = state.get("case_id", "Unknown")
    seed = state.get("seed", {})
    seed_value = seed.get("value", "unknown")
    seed_type = seed.get("type", "unknown")
    created = state.get("created_at", "")[:10]

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    type_colors = {
        "username": "#2e7d32", "email": "#1565c0", "domain": "#e65100",
        "ip_v4": "#c62828", "ip_v6": "#c62828", "phone": "#6a1b9a",
        "crypto_btc": "#bf360c", "crypto_eth": "#37474f", "url": "#00838f",
        "name": "#558b2f", "company": "#283593", "asn": "#9e9d24",
        "telegram_handle": "#00695c", "discord_id": "#5c6bc0",
    }

    confirmed_nodes = [n for n in nodes if n.get("confidence") == "confirmed"]
    probable_nodes = [n for n in nodes if n.get("confidence") == "probable"]
    possible_nodes = [n for n in nodes if n.get("confidence") == "possible"]

    type_counts = {}
    for n in nodes:
        t = n.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    # Parse findings from report markdown
    findings_html = ""
    if "## Significant Findings" in report_md:
        findings_section = report_md.split("## Significant Findings")[1].split("---")[0].strip()
        for line in findings_section.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                parts = line.split("**", 2)
                if len(parts) >= 3:
                    title = parts[1]
                    rest = parts[2].lstrip(" -")
                    findings_html += f'<div class="finding"><div class="finding-title">{title}</div><div class="finding-detail">{rest}</div></div>\n'
                else:
                    findings_html += f'<div class="finding"><div class="finding-detail">{line}</div></div>\n'

    # Parse BLUF
    bluf = ""
    if "## BLUF" in report_md:
        bluf = report_md.split("## BLUF")[1].split("---")[0]
        bluf = bluf.replace("(Bottom Line Up Front)", "").strip()

    # Parse implications
    implications = ""
    if "## Implications" in report_md:
        implications = report_md.split("## Implications")[1].split("---")[0].strip()

    # Build entity table rows
    entity_rows = ""
    for n in sorted(nodes, key=lambda x: (x.get("depth", 0), x.get("type", ""))):
        val = n.get("value", "")
        ntype = n.get("type", "")
        conf = n.get("confidence", "confirmed")
        sources = ", ".join(n.get("source_tools", []))
        depth = n.get("depth", 0)
        citation = n.get("citation", "")
        color = type_colors.get(ntype, "#666")
        conf_class = f"conf-{conf}"

        entity_rows += f"""<tr>
            <td style="max-width:300px;word-break:break-all;">{val}</td>
            <td><span class="type-badge" style="background:{color};">{ntype}</span></td>
            <td>{sources}</td>
            <td><span class="{conf_class}">{conf}</span></td>
            <td>{depth}</td>
            <td class="citation">{citation}</td>
        </tr>\n"""

    # Build relationship rows
    rel_rows = ""
    for e in edges:
        src_node = next((n for n in nodes if n.get("id") == e.get("source")), {})
        tgt_node = next((n for n in nodes if n.get("id") == e.get("target")), {})
        conf = e.get("confidence", "confirmed")
        conf_class = f"conf-{conf}"
        rel_rows += f"""<tr>
            <td>{src_node.get('value', '?')}</td>
            <td class="rel-type">{e.get('relationship', '')}</td>
            <td>{tgt_node.get('value', '?')}</td>
            <td>{e.get('source_tool', '')}</td>
            <td><span class="{conf_class}">{conf}</span></td>
            <td class="citation">{e.get('citation', '')}</td>
        </tr>\n"""

    # Tools used
    all_tools = set()
    for n in nodes:
        all_tools.update(n.get("source_tools", []))
    tools_list = sorted(all_tools - {"seed"})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CTI Report - {case_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: #1a1a2e; background: #ffffff; line-height: 1.6;
            max-width: 900px; margin: 0 auto; padding: 40px 50px;
        }}

        /* Header */
        .report-header {{
            border-bottom: 3px solid #1a1a2e; padding-bottom: 24px; margin-bottom: 32px;
        }}
        .report-header h1 {{
            font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px;
            letter-spacing: -0.5px;
        }}
        .report-header .subtitle {{
            font-size: 14px; color: #666; font-weight: 400;
        }}
        .meta-table {{
            width: 100%; border-collapse: collapse; margin-top: 16px;
            font-size: 13px;
        }}
        .meta-table td {{
            padding: 6px 12px; border: 1px solid #e0e0e0;
        }}
        .meta-table td:first-child {{
            font-weight: 600; background: #f5f5f5; width: 180px; color: #333;
        }}

        /* Sections */
        .section {{
            margin-bottom: 32px;
        }}
        .section h2 {{
            font-size: 18px; font-weight: 700; color: #1a1a2e;
            border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 16px;
            text-transform: uppercase; letter-spacing: 0.5px;
        }}

        /* BLUF box */
        .bluf-box {{
            background: #f0f4ff; border-left: 4px solid #1a56db;
            padding: 16px 20px; border-radius: 0 6px 6px 0;
            font-size: 14px; line-height: 1.7;
        }}

        /* Findings */
        .finding {{
            background: #fafafa; border: 1px solid #e8e8e8; border-radius: 6px;
            padding: 14px 18px; margin-bottom: 10px;
        }}
        .finding-title {{
            font-weight: 600; font-size: 14px; color: #1a1a2e; margin-bottom: 4px;
        }}
        .finding-detail {{
            font-size: 13px; color: #444; line-height: 1.6;
        }}

        /* Tables */
        table {{
            width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px;
        }}
        th {{
            background: #1a1a2e; color: #fff; padding: 8px 10px;
            text-align: left; font-weight: 600; font-size: 11px;
            text-transform: uppercase; letter-spacing: 0.5px;
        }}
        td {{
            padding: 7px 10px; border-bottom: 1px solid #e8e8e8;
            vertical-align: top;
        }}
        tr:nth-child(even) td {{ background: #fafafa; }}
        tr:hover td {{ background: #f0f4ff; }}

        /* Badges */
        .type-badge {{
            display: inline-block; padding: 2px 8px; border-radius: 10px;
            color: #fff; font-size: 11px; font-weight: 600;
        }}
        .conf-confirmed {{ color: #15803d; font-weight: 600; }}
        .conf-probable {{ color: #b45309; font-weight: 600; }}
        .conf-possible {{ color: #9f1239; font-weight: 600; }}
        .rel-type {{ color: #7c3aed; font-weight: 600; }}
        .citation {{ font-size: 11px; color: #888; font-style: italic; }}

        /* Stats grid */
        .stats-grid {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f5f5f5; border-radius: 8px; padding: 16px; text-align: center;
        }}
        .stat-number {{
            font-size: 28px; font-weight: 700; color: #1a1a2e;
        }}
        .stat-label {{
            font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;
        }}

        /* Type breakdown */
        .type-breakdown {{
            display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;
        }}
        .type-chip {{
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 12px; border-radius: 16px; font-size: 12px;
            background: #f0f0f0; font-weight: 500;
        }}
        .type-chip .dot {{
            width: 10px; height: 10px; border-radius: 50%;
        }}

        /* Tools list */
        .tools-list {{
            display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
        }}
        .tool-tag {{
            background: #e8e8e8; padding: 3px 10px; border-radius: 4px;
            font-size: 12px; font-family: 'Courier New', monospace;
        }}

        /* Footer */
        .report-footer {{
            margin-top: 40px; padding-top: 20px; border-top: 2px solid #e0e0e0;
            font-size: 11px; color: #999; text-align: center;
        }}

        /* Print styles */
        @media print {{
            body {{ padding: 20px 30px; }}
            .stat-card {{ break-inside: avoid; }}
            table {{ page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; }}
            .finding {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>

<div class="report-header">
    <h1>Cyber Threat Intelligence Report</h1>
    <div class="subtitle">Open Source Intelligence Assessment</div>
    <table class="meta-table">
        <tr><td>Case ID</td><td>{case_id}</td></tr>
        <tr><td>Classification</td><td>TLP:CLEAR</td></tr>
        <tr><td>Date</td><td>{created}</td></tr>
        <tr><td>Initial Selector</td><td><code>{seed_value}</code> ({seed_type})</td></tr>
        <tr><td>Status</td><td>{state.get('status', 'unknown').replace('_', ' ').title()}</td></tr>
    </table>
</div>

<div class="section">
    <h2>BLUF (Bottom Line Up Front)</h2>
    <div class="bluf-box">{bluf}</div>
</div>

<div class="section">
    <h2>Key Statistics</h2>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{len(nodes)}</div>
            <div class="stat-label">Entities</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(edges)}</div>
            <div class="stat-label">Relationships</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(confirmed_nodes)}</div>
            <div class="stat-label">Confirmed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(probable_nodes)}</div>
            <div class="stat-label">Probable</div>
        </div>
    </div>
    <div class="type-breakdown">
        {"".join(f'<span class="type-chip"><span class="dot" style="background:{type_colors.get(t, "#666")};"></span>{t}: {c}</span>' for t, c in sorted(type_counts.items(), key=lambda x: -x[1]))}
    </div>
</div>

<div class="section">
    <h2>Significant Findings</h2>
    {findings_html if findings_html else '<p style="color:#888;">No significant findings documented.</p>'}
</div>

<div class="section">
    <h2>Entity Inventory</h2>
    <table>
        <thead>
            <tr>
                <th>Entity</th><th>Type</th><th>Source</th>
                <th>Confidence</th><th>Depth</th><th>Citation</th>
            </tr>
        </thead>
        <tbody>
            {entity_rows}
        </tbody>
    </table>
</div>

<div class="section">
    <h2>Relationship Map</h2>
    <table>
        <thead>
            <tr>
                <th>Source</th><th>Relationship</th><th>Target</th>
                <th>Tool</th><th>Confidence</th><th>Citation</th>
            </tr>
        </thead>
        <tbody>
            {rel_rows}
        </tbody>
    </table>
    <p style="font-size:12px;color:#888;margin-top:8px;">
        Interactive graph available: <a href="graph.html">graph.html</a>
    </p>
</div>

<div class="section">
    <h2>Investigation Method</h2>
    <p style="font-size:13px;margin-bottom:12px;">
        <strong>Tools employed:</strong>
    </p>
    <div class="tools-list">
        {"".join(f'<span class="tool-tag">{t}</span>' for t in tools_list)}
    </div>
</div>

<div class="section">
    <h2>Implications &amp; Assessment</h2>
    <div class="bluf-box" style="border-left-color:#b45309;background:#fff8f0;">
        {implications if implications else "No implications assessed."}
    </div>
</div>

<div class="section" style="background:#f0f4ff;padding:20px;border-radius:8px;border:1px solid #d0d7de;">
    <h2 style="border-bottom:none;margin-bottom:8px;">Investigation Resources</h2>
    <p style="font-size:13px;margin-bottom:12px;">Click to open in browser:</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
        <a href="bibliography.html" style="display:inline-block;padding:10px 20px;background:#1a56db;color:#fff;border-radius:6px;font-weight:600;font-size:13px;text-decoration:none;">Clickable Bibliography</a>
        <a href="graph.html" style="display:inline-block;padding:10px 20px;background:#1a56db;color:#fff;border-radius:6px;font-weight:600;font-size:13px;text-decoration:none;">Interactive Graph</a>
        <a href="investigation.md" style="display:inline-block;padding:10px 20px;background:#24292f;color:#fff;border-radius:6px;font-weight:600;font-size:13px;text-decoration:none;">Full Investigation Log</a>
    </div>
</div>

<div class="report-footer">
    Generated by OSINT Investigator | Case: {case_id} | {created}<br>
    This report contains only findings supported by tool output evidence.
</div>

</body>
</html>"""

    output_path = case_dir / "report.html"
    output_path.write_text(html, encoding="utf-8")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate professional HTML CTI report")
    parser.add_argument("--case-dir", required=True, help="Path to investigation case directory")
    args = parser.parse_args()

    output = generate_html_report(args.case_dir)
    print(f"Report generated: {output}")


if __name__ == "__main__":
    main()
