"""Mermaid diagram generation for the narrative report (R1).

Two kinds of picture, both GROUNDED in graph.json so a diagram can never depict a link
the data doesn't contain:
  - `subgraph_for_values` : a per-pivot subgraph — the entities a pivot introduced + the
    real edges among them (from the committed graph), tier-styled.
  - `overview_ov1`        : the BLUF OV-1 — an editorial one-glance schematic the report
    writer supplies as a node/edge spec (validated by the red-team grounding pass).

Tier styling mirrors the graph/report: highly_likely = solid, probable = dashed,
possible = faint dotted. Legacy `confirmed` normalizes to highly_likely.
"""
from src.graph.confidence import normalize as _norm

_TIER_CLASS = {"highly_likely": "hl", "probable": "pr", "possible": "po"}

_CLASSDEFS = (
    "classDef hl fill:#0f2e1a,stroke:#3fb950,color:#e6edf3,stroke-width:2px;\n"
    "classDef pr fill:#3a2d0b,stroke:#d29922,color:#e6edf3,stroke-width:1px,stroke-dasharray:5 3;\n"
    "classDef po fill:#2d1e0f,stroke:#bb8009,color:#b9b9b9,stroke-width:1px,stroke-dasharray:2 4;\n"
    "classDef seed fill:#16324f,stroke:#58a6ff,color:#ffffff,stroke-width:3px;\n"
    "classDef finding fill:#3d1f3a,stroke:#bc8cff,color:#ffffff,stroke-width:2px;\n"
    "classDef cluster fill:#1d2b22,stroke:#3fb950,color:#e6edf3,stroke-width:2px;\n"
)


def _san(text, maxlen=46):
    """Make a string safe for a mermaid node/edge label."""
    s = str(text if text is not None else "")
    for a, b in (('"', "'"), ("\n", " "), ("|", "/"), ("[", "("), ("]", ")"),
                 ("{", "("), ("}", ")"), ("<", "("), (">", ")")):
        s = s.replace(a, b)
    s = s.strip()
    if maxlen and len(s) > maxlen:
        s = s[:maxlen - 1] + "…"
    return s


def _safe_id(raw, used):
    """A mermaid-safe node id (alnum/underscore), unique within the diagram."""
    base = "".join(c if c.isalnum() else "_" for c in str(raw))[:24] or "n"
    if base[0].isdigit():
        base = "n" + base
    nid, i = base, 1
    while nid in used:
        nid, i = f"{base}_{i}", i + 1
    used.add(nid)
    return nid


def _node_label(node):
    return f"{_san(node.get('value'))}<br/>({_san(node.get('type'), 22)})"


def subgraph_for_values(graph_data, values, direction="LR"):
    """Mermaid subgraph of the graph nodes whose `value` is in `values`, plus the real
    edges among them. `values` is the list of entity values a pivot section introduced."""
    want = {str(v) for v in (values or [])}
    nodes = [n for n in graph_data.get("nodes", []) if str(n.get("value")) in want]
    if not nodes:
        return ""
    by_gid, used = {}, set()
    lines = [f"flowchart {direction}"]
    for n in nodes:
        mid = _safe_id(n.get("value"), used)
        by_gid[n.get("id")] = mid
        cls = _TIER_CLASS.get(_norm(n.get("confidence"), default="highly_likely"), "po")
        lines.append(f'    {mid}["{_node_label(n)}"]:::{cls}')
    for e in graph_data.get("edges", []):
        a, b = by_gid.get(e.get("source")), by_gid.get(e.get("target"))
        if a and b:
            lines.append(f'    {a} -->|"{_san(e.get("relationship", "related"), 26)}"| {b}')
    return "\n".join(lines) + "\n" + _CLASSDEFS


def overview_ov1(ov1_spec, direction="TD"):
    """The BLUF OV-1 from an editorial spec:
        {"nodes":[{"id","label","kind"}], "edges":[{"from","to","label"}]}
    kind in: seed | cluster | finding | entity (+ a tier: hl/pr/po for `entity`).
    The report writer authors this; the red-team grounding pass checks each edge/claim
    against the graph before the report ships."""
    if not ov1_spec or not ov1_spec.get("nodes"):
        return ""
    shape = {  # (open, close) wrappers per kind
        "seed": ('["', '"]'), "cluster": ('(("', '"))'),
        "finding": ('(["', '"])'), "entity": ('["', '"]'),
    }
    cls_for = {"seed": "seed", "cluster": "cluster", "finding": "finding"}
    idmap, used = {}, set()
    lines = [f"flowchart {direction}"]
    for nd in ov1_spec["nodes"]:
        mid = _safe_id(nd.get("id") or nd.get("label"), used)
        idmap[nd.get("id")] = mid
        kind = (nd.get("kind") or "entity").lower()
        opn, cls = shape.get(kind, ('["', '"]'))
        klass = cls_for.get(kind) or _TIER_CLASS.get(_norm(nd.get("tier"), "highly_likely"), "hl")
        lines.append(f'    {mid}{opn}{_san(nd.get("label"), 54)}{cls}:::{klass}')
    for e in ov1_spec.get("edges", []):
        a, b = idmap.get(e.get("from")), idmap.get(e.get("to"))
        if a and b:
            lbl = _san(e.get("label", ""), 30)
            lines.append(f'    {a} -->|"{lbl}"| {b}' if lbl else f"    {a} --> {b}")
    return "\n".join(lines) + "\n" + _CLASSDEFS
