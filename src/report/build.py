"""Build the narrative report (R1) from the report-writer's spec + the committed graph.

The report-writer authors `{CASE_DIR}/_report.json` (BLUF, OV-1 spec, story sections with
per-pivot tool-returns + the entity values each pivot introduced, key findings, glossary),
then runs this to render report.md + report.html. Diagrams are generated from graph.json, so
they stay grounded. Run AFTER the red-team grounding pass has signed off the spec.

    python -m src.report.build --case-dir investigations/INV-xxx
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.report.cti_report import generate_cti_report
from src.report.html_report import generate_html_report


def build_reports(case_dir: str) -> dict:
    case_dir = Path(case_dir)
    spec = json.loads((case_dir / "_report.json").read_text(encoding="utf-8"))
    graph_data = json.loads((case_dir / "graph.json").read_text(encoding="utf-8"))
    state = json.loads((case_dir / "state.json").read_text(encoding="utf-8"))

    md = generate_cti_report(spec, graph_data, state, str(case_dir / "report.md"))
    html = generate_html_report(spec, graph_data, state, str(case_dir / "report.html"))
    return {"report_md": md, "report_html": html,
            "sections": len(spec.get("story", [])),
            "entities": len(graph_data.get("nodes", [])),
            "relationships": len(graph_data.get("edges", []))}


def main():
    ap = argparse.ArgumentParser(description="Render report.md + report.html from _report.json + graph.json")
    ap.add_argument("--case-dir", required=True)
    args = ap.parse_args()
    print(json.dumps(build_reports(args.case_dir), indent=2))


if __name__ == "__main__":
    main()
