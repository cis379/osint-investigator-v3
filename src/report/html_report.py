"""report.html — the professional narrative CTI report (R1), the share-with-humans product.

Same spec as report.md (BLUF + OV-1 -> investigation story -> key findings -> appendices) but
rendered as a styled, Google-Docs / PDF-ready HTML page with mermaid.js diagrams. Diagrams are
generated from graph.json (diagram.py) so they cannot depict a link the data lacks.

    python -m src.report.html_report --case-dir investigations/INV-xxx   (via build.py)
"""
import html
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.graph.confidence import humanize as _conf_human  # noqa: E402
from src.report import diagram  # noqa: E402

esc = html.escape


def _mermaid(code: str) -> str:
    # Escape so the browser hands mermaid the literal source (incl. <br/>) via textContent.
    return f'<pre class="mermaid">{esc(code.strip())}</pre>' if code and code.strip() else ""


def _tool_returns_html(tr) -> str:
    if not tr:
        return ""
    if isinstance(tr, str):
        return f"<p>{esc(tr)}</p>"
    rows = []
    for item in tr:
        if isinstance(item, dict):
            q = f' <code>{esc(str(item["query"]))}</code>' if item.get("query") else ""
            rows.append(f'<li><code class="tool">{esc(item.get("tool","?"))}</code>{q} '
                        f'&rarr; {esc(item.get("returned",""))}</li>')
        else:
            rows.append(f"<li>{esc(str(item))}</li>")
    return '<ul class="tool-returns">' + "".join(rows) + "</ul>"


def generate_html_report(spec: dict, graph_data: dict, state: dict, output_path: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = state.get("seed", {})
    case_id = state.get("case_id", spec.get("case_id", "INV"))
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    nid = {n.get("id"): n for n in nodes}

    ov1 = spec.get("ov1_mermaid") or (diagram.overview_ov1(spec["ov1"]) if spec.get("ov1") else "")

    # story sections
    story_html = ""
    for i, sec in enumerate(spec.get("story", []), 1):
        sub = sec.get("mermaid") or diagram.subgraph_for_values(graph_data, sec.get("entity_values", []))
        tr = _tool_returns_html(sec.get("tools_returned"))
        story_html += f"""<section class="pivot">
  <h3><span class="step">{i}</span> {esc(sec.get('title','Pivot'))}</h3>
  <div class="teaching">{esc(sec.get('teaching','')).replace(chr(10),'<br>')}</div>
  {('<h4>What we ran &amp; what it returned</h4>' + tr) if tr else ''}
  {_mermaid(sub)}
  {('<p class="revealed"><strong>What it revealed:</strong> ' + esc(sec['revealed']) + '</p>') if sec.get('revealed') else ''}
</section>"""

    # key findings
    kf_html = ""
    for f in spec.get("key_findings", []):
        tier = f'<span class="tier tier-{f.get("tier","")}">{_conf_human(f["tier"])}</span>' if f.get("tier") else ""
        cite = f'<div class="cite">{esc(f["citation"])}</div>' if f.get("citation") else ""
        kf_html += (f'<div class="finding"><div class="finding-h">{esc(f.get("title","Finding"))} {tier}</div>'
                    f'<div class="finding-d">{esc(f.get("description",""))}</div>{cite}</div>')

    # appendix tables
    ent_rows = ""
    for n in sorted(nodes, key=lambda x: (x.get("depth", 0), x.get("type", ""))):
        conf = n.get("confidence")
        ent_rows += (f"<tr><td><code>{esc(str(n.get('value','')))}</code></td><td>{esc(str(n.get('type','')))}</td>"
                     f"<td><span class='tier tier-{conf}'>{_conf_human(conf) if conf else ''}</span></td>"
                     f"<td>{esc(str(n.get('depth','')))}</td><td>{esc(', '.join(n.get('source_tools',[])))}</td>"
                     f"<td class='cite'>{esc(str(n.get('citation','')))}</td></tr>")
    rel_rows = ""
    for e in edges:
        s = nid.get(e.get("source"), {}).get("value", "?")
        t = nid.get(e.get("target"), {}).get("value", "?")
        conf = e.get("confidence")
        rel_rows += (f"<tr><td>{esc(str(s))}</td><td class='rel'>{esc(str(e.get('relationship','')))}</td>"
                     f"<td>{esc(str(t))}</td><td><span class='tier tier-{conf}'>{_conf_human(conf) if conf else ''}</span></td>"
                     f"<td>{esc(str(e.get('source_tool','')))}</td><td class='cite'>{esc(str(e.get('citation','')))}</td></tr>")

    gloss_html = ""
    for g in spec.get("glossary", []):
        if isinstance(g, dict):
            gloss_html += f"<li><strong>{esc(g.get('term',''))}</strong> — {esc(g.get('plain_explanation',''))}</li>"
        else:
            gloss_html += f"<li>{esc(str(g))}</li>"

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CTI Report — {esc(case_id)}</title>
<style>
  body{{font-family:'Segoe UI',system-ui,sans-serif;max-width:960px;margin:0 auto;padding:32px 40px;color:#1a1a2e;line-height:1.6;background:#fff;}}
  h1{{font-size:26px;border-bottom:3px solid #16324f;padding-bottom:10px;}}
  h2{{font-size:20px;color:#16324f;border-bottom:1px solid #ddd;padding-bottom:6px;margin-top:36px;}}
  h3{{font-size:17px;color:#1f3a5f;margin-top:28px;}}
  h4{{font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:#666;margin:14px 0 6px;}}
  .meta{{border-collapse:collapse;margin:12px 0;font-size:13px;}} .meta td{{border:1px solid #ddd;padding:5px 12px;}} .meta td:first-child{{background:#f4f6fb;font-weight:600;}}
  .bluf{{background:#f4f6fb;border-left:4px solid #16324f;padding:14px 18px;border-radius:4px;font-size:15px;}}
  .pivot{{border-left:3px solid #e0e6f0;padding-left:18px;margin:22px 0;}}
  .step{{display:inline-block;background:#16324f;color:#fff;width:26px;height:26px;border-radius:50%;text-align:center;line-height:26px;font-size:14px;margin-right:6px;}}
  .teaching{{color:#333;}} .revealed{{background:#eef6ef;border-left:3px solid #3fb950;padding:8px 12px;border-radius:3px;}}
  ul.tool-returns{{font-size:14px;}} code.tool{{background:#16324f;color:#fff;padding:1px 6px;border-radius:3px;font-size:12px;}}
  code{{background:#f0f0f4;padding:1px 5px;border-radius:3px;font-size:13px;}}
  .finding{{border:1px solid #e0e0e8;border-radius:6px;padding:12px 16px;margin:10px 0;}}
  .finding-h{{font-weight:700;color:#16324f;}} .cite{{font-size:11px;color:#888;font-style:italic;margin-top:4px;}}
  .tier{{font-size:11px;font-weight:700;padding:1px 8px;border-radius:10px;color:#fff;}}
  .tier-highly_likely,.tier-confirmed{{background:#238636;}} .tier-probable{{background:#9e6a03;}} .tier-possible{{background:#b06a2c;}}
  table.appx{{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0;}} table.appx th,table.appx td{{border:1px solid #e0e0e8;padding:4px 8px;text-align:left;vertical-align:top;}}
  table.appx th{{background:#16324f;color:#fff;}} td.cite{{font-size:11px;color:#777;font-style:italic;}} td.rel{{color:#7c3aed;font-weight:600;}}
  pre.mermaid{{background:#0d1117;border-radius:8px;padding:14px;margin:12px 0;text-align:center;}}
  .legend{{font-size:12px;color:#666;}} .foot{{margin-top:40px;border-top:2px solid #e0e0e0;padding-top:14px;font-size:11px;color:#999;text-align:center;}}
  @media print{{.pivot{{break-inside:avoid;}} tr{{break-inside:avoid;}}}}
</style></head><body>

<h1>Cyber Threat Intelligence Report</h1>
<table class="meta">
  <tr><td>Case ID</td><td>{esc(case_id)}</td></tr>
  <tr><td>Classification</td><td>TLP:CLEAR</td></tr>
  <tr><td>Date</td><td>{now}</td></tr>
  <tr><td>Initial Seed</td><td><code>{esc(str(seed.get('value','')))}</code> ({esc(str(seed.get('type','')))})</td></tr>
</table>

<h2>BLUF — Bottom Line Up Front</h2>
<div class="bluf">{esc(spec.get('bluf','')).replace(chr(10),'<br>')}</div>
{('<h4>Investigation at a glance (OV-1)</h4>' + _mermaid(ov1)) if ov1 else ''}

<h2>The Investigation Story</h2>
<p class="legend"><em>How we went from the initial seed to the findings — each step explains the pivot,
shows what the tools returned, and graphs what it added. Legend: solid = highly likely, dashed = probable,
faint = possible.</em></p>
{story_html}

<h2>Key Findings</h2>
{kf_html or '<p><em>No findings recorded.</em></p>'}

<h2>Appendix A — Entities (full)</h2>
<table class="appx"><tr><th>Entity</th><th>Type</th><th>Confidence</th><th>Depth</th><th>Source</th><th>Citation</th></tr>{ent_rows}</table>

<h2>Appendix B — Relationships (full)</h2>
<table class="appx"><tr><th>Source</th><th>Relationship</th><th>Target</th><th>Confidence</th><th>Tool</th><th>Citation</th></tr>{rel_rows}</table>

<h2>Appendix C — Raw tool output</h2>
<p>Full raw output for every tool execution is preserved in the investigation audit log
(<code>investigation.md</code>) and the interactive graph. Each finding traces to a specific entry there.</p>
<p><a href="./graph.html">Open interactive graph</a> &middot; <a href="./bibliography.html">Open bibliography</a></p>

{('<h2>Appendix D — Methodology &amp; glossary</h2><ul>' + gloss_html + '</ul>') if gloss_html else ''}

<div class="foot">OSINT Investigator | Case {esc(case_id)} | {now}<br>
Every claim traces to tool output or a cited source (red-team grounding-checked). No speculative analysis.</div>

<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
</script>
</body></html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(page, encoding="utf-8")
    return output_path
