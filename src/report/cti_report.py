"""report.md — the narrative CTI report (R1).

Consumes a report SPEC authored by the report-writer (`_report.json`) + the committed
graph (`graph.json`) + `state.json`. Structure:
    BLUF (+ OV-1 mermaid)  ->  The Investigation Story (per-pivot: teaching, what each
    tool returned, a grounded subgraph, what it revealed)  ->  Key Findings  ->
    Appendices (full entity table, relationship table, raw-output pointer, glossary).

The diagrams are generated from graph.json (see diagram.py), so a picture can't depict a
link the data lacks. Tier words are humanized (highly likely / probable / possible).
"""
from datetime import datetime, timezone
from pathlib import Path

from src.graph.confidence import humanize as _conf_human, normalize as _conf_norm
from src.report import diagram


def _md_cell(value, width: int = 200) -> str:
    s = str(value if value is not None else "").replace("|", "\\|")
    s = s.replace("\r", " ").replace("\n", " ").strip()
    if width and len(s) > width:
        s = s[:width - 1] + "…"
    return s


def _tool_returns_md(tr) -> str:
    """A section's 'what each tool returned' block (list of {tool,returned[,query]} or str)."""
    if not tr:
        return ""
    if isinstance(tr, str):
        return tr.strip() + "\n"
    lines = []
    for item in tr:
        if isinstance(item, dict):
            tool = item.get("tool", "?")
            q = f" `{item['query']}`" if item.get("query") else ""
            lines.append(f"- **`{tool}`**{q} → {item.get('returned', '').strip()}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _mermaid_block(code: str) -> str:
    return f"```mermaid\n{code.strip()}\n```\n" if code and code.strip() else ""


def generate_cti_report(spec: dict, graph_data: dict, state: dict, output_path: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seed = state.get("seed", {})
    case_id = state.get("case_id", spec.get("case_id", "INV"))
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    nid = {n.get("id"): n for n in nodes}

    # --- BLUF + OV-1 ---
    ov1 = spec.get("ov1_mermaid") or (diagram.overview_ov1(spec["ov1"]) if spec.get("ov1") else "")
    out = [
        f"# Cyber Threat Intelligence Report — {case_id}", "",
        "| Field | Value |", "|-------|-------|",
        f"| **Case ID** | {case_id} |",
        "| **Classification** | TLP:CLEAR |",
        f"| **Date** | {now} |",
        f"| **Initial Seed** | `{seed.get('value','')}` ({seed.get('type','')}) |", "",
        "---", "", "## BLUF (Bottom Line Up Front)", "", spec.get("bluf", "").strip(), "",
    ]
    if ov1:
        out += ["**Investigation at a glance (OV-1):**", "", _mermaid_block(ov1)]
    out += ["---", "", "## The Investigation Story", "",
            "*How we went from the initial seed to the findings — each step explains the pivot "
            "(for readers new to that technique), shows what the tools returned, and graphs what it "
            "added. Diagram legend: solid = highly likely, dashed = probable, faint = possible.*", ""]

    for i, sec in enumerate(spec.get("story", []), 1):
        out += [f"### {i}. {sec.get('title','Pivot')}", "", sec.get("teaching", "").strip(), ""]
        tr = _tool_returns_md(sec.get("tools_returned"))
        if tr:
            out += ["**What we ran & what it returned**", "", tr]
        sub = sec.get("mermaid") or diagram.subgraph_for_values(graph_data, sec.get("entity_values", []))
        if sub:
            out += [_mermaid_block(sub)]
        if sec.get("revealed"):
            out += [f"**What it revealed:** {sec['revealed'].strip()}", ""]

    # --- Key Findings ---
    out += ["---", "", "## Key Findings", ""]
    kf = spec.get("key_findings", [])
    if kf:
        for j, f in enumerate(kf, 1):
            tier = f" _[{_conf_human(f['tier'])}]_" if f.get("tier") else ""
            cite = f" — {f['citation']}" if f.get("citation") else ""
            out.append(f"{j}. **{f.get('title','Finding')}** — {f.get('description','').strip()}{tier}{cite}")
        out.append("")
    else:
        out += ["_No findings recorded._", ""]

    # --- Appendices (grounded in graph.json) ---
    out += ["---", "", "## Appendix A — Entities (full)", "",
            "| Entity | Type | Confidence | Depth | Source | Citation |",
            "|--------|------|------------|-------|--------|----------|"]
    for n in sorted(nodes, key=lambda x: (x.get("depth", 0), x.get("type", ""))):
        out.append(f"| `{_md_cell(n.get('value',''))}` | {_md_cell(n.get('type',''))} "
                   f"| {_conf_human(n.get('confidence')) if n.get('confidence') else ''} "
                   f"| {_md_cell(n.get('depth',''))} | {_md_cell(', '.join(n.get('source_tools',[])))} "
                   f"| {_md_cell(n.get('citation',''))} |")

    out += ["", "## Appendix B — Relationships (full)", "",
            "| Source | Relationship | Target | Confidence | Tool | Citation |",
            "|--------|--------------|--------|------------|------|----------|"]
    for e in edges:
        s = nid.get(e.get("source"), {}).get("value", "?")
        t = nid.get(e.get("target"), {}).get("value", "?")
        out.append(f"| {_md_cell(s)} | {_md_cell(e.get('relationship',''))} | {_md_cell(t)} "
                   f"| {_conf_human(e.get('confidence')) if e.get('confidence') else ''} "
                   f"| {_md_cell(e.get('source_tool',''))} | {_md_cell(e.get('citation',''))} |")

    out += ["", "## Appendix C — Raw tool output", "",
            "Full raw output for every tool execution is preserved in the investigation audit log "
            "(`investigation.md`) and the interactive graph (`graph.html`). Each finding above traces "
            "to a specific entry there.", "",
            "[Open interactive graph](./graph.html) · [Open bibliography](./bibliography.html)", ""]

    gloss = spec.get("glossary", [])
    if gloss:
        out += ["## Appendix D — Methodology & glossary", ""]
        for g in gloss:
            if isinstance(g, dict):
                out.append(f"- **{g.get('term','')}** — {g.get('plain_explanation','').strip()}")
            else:
                out.append(f"- {g}")
        out.append("")

    out += ["---", f"*Generated by OSINT Investigator | Case: {case_id} | {now}*",
            "*Every claim traces to tool output or a cited source (red-team grounding-checked). "
            "No speculative analysis.*"]

    text = "\n".join(out) + "\n"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(text, encoding="utf-8")
    return output_path
