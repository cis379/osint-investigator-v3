"""Commit the SUPERVISOR's analyzed findings to the investigation graph.

This is the *analysis* half of the raw/analysis split. It runs NO OSINT tools.
It takes entities/relationships the supervisor has judged real — each with a
supervisor-assigned confidence tier — writes them to the graph, then regenerates
the graph HTML and bibliography.

Confidence tiers (strong -> weak), rendered distinctly in the graph. These are the
supervisor's ESTIMATIVE likelihood judgments — NOT a collection tool's self-stamp:
    highly_likely  - corroborated by independent evidence / authoritative (strong; solid)
    probable       - likely but single-source or inferred (dashed)
    possible       - weak / likely-noise candidate, KEPT as a pivot, not hidden (faint, dashed)
("confirmed" is still accepted as a legacy alias for "highly_likely".)

Design intent: nothing the tools returned is hidden (the full raw output lives in
investigation.md). The supervisor does not drop data — it *tiers* it, so strong
links stand out while weak candidates remain visible for the human to rule out.

Input: a JSON spec via --input FILE or stdin:
{
  "entities": [
    {"value": "...", "type": "...", "tool": "...",
     "confidence": "highly_likely|probable|possible", "citation": "...",
     "depth": 1, "metadata": {}}
  ],
  "relationships": [
    {"source_value": "...", "source_type": "...",
     "target_value": "...", "target_type": "...",
     "relationship": "...", "tool": "...",
     "confidence": "highly_likely|probable|possible", "citation": "..."}
  ]
}

Usage:
    python -m src.tools.graph_commit --graph investigations/INV-xxx/graph.json \
        --regen-html investigations/INV-xxx/graph.html --case INV-xxx --input findings.json
    # or pipe the spec on stdin:
    echo '{"entities":[...]}' | python -m src.tools.graph_commit --graph ... --case INV-xxx
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.graph.database import InvestigationGraph
from src.graph.visualizer import generate_investigation_html
from src.graph.confidence import normalize as _normalize_conf
from src.report.bibliography import generate_bibliography


def _norm_conf(conf: str, label: str, warnings: list) -> str:
    # Maps the supervisor's tier to canonical form (incl. legacy "confirmed" alias).
    norm = _normalize_conf(conf, default="")
    if not norm:
        warnings.append(f"{label}: unknown confidence {conf!r}; coercing to 'possible' (weakest)")
        return "possible"
    return norm


def commit(spec: dict, graph_file: str, html_file: str = "", case_id: str = "") -> dict:
    graph = InvestigationGraph(graph_file)
    warnings: list[str] = []
    n_ent = n_rel = 0

    for e in spec.get("entities", []):
        conf = _norm_conf(e.get("confidence", "possible"), f"entity {e.get('value')!r}", warnings)
        graph.add_entity(
            e["value"], e["type"], e.get("tool", "supervisor"),
            depth=int(e.get("depth", 1)),
            confidence=conf,
            citation=e.get("citation", ""),
            metadata=e.get("metadata") or {},
        )
        n_ent += 1

    for r in spec.get("relationships", []):
        conf = _norm_conf(r.get("confidence", "possible"),
                          f"relationship {r.get('relationship')!r}", warnings)
        graph.add_relationship(
            r["source_value"], r["source_type"],
            r["target_value"], r["target_type"],
            r.get("relationship", "related_to"),
            r.get("tool", "supervisor"),
            confidence=conf,
            citation=r.get("citation", ""),
        )
        n_rel += 1

    graph.save()

    if html_file:
        generate_investigation_html(graph, html_file, f"Investigation: {case_id}")

    bib = None
    try:
        bib = generate_bibliography(str(Path(graph_file).parent))
    except Exception as e:
        warnings.append(f"bibliography skipped: {e}")

    return {
        "entities_added": n_ent,
        "relationships_added": n_rel,
        "stats": graph.get_stats(),
        "bibliography": bib,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Commit supervisor-analyzed findings to the graph (NO tool execution)")
    parser.add_argument("--graph", required=True, help="Path to graph.json")
    parser.add_argument("--input", help="JSON spec file; if omitted, read stdin")
    parser.add_argument("--regen-html", dest="html", help="Also regenerate graph HTML at this path")
    parser.add_argument("--case", default="", help="Case ID")

    args = parser.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        parser.error(f"Input is not valid JSON: {e}")

    print(json.dumps(commit(spec, args.graph, args.html or "", args.case), indent=2))


if __name__ == "__main__":
    main()
