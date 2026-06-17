"""Execute OSINT tools and persist results to graph + log in a single call.

Usage:
    python -m src.tools.execute --tool whois_lookup --selector example.com --type domain \
        --graph investigations/INV-xxx/graph.json --log investigations/INV-xxx/investigation.md \
        --depth 1 --case INV-xxx

    python -m src.tools.execute --run-all --selector example.com --type domain \
        --graph investigations/INV-xxx/graph.json --log investigations/INV-xxx/investigation.md \
        --depth 1 --case INV-xxx

This replaces error-prone inline Python commands with a single reliable entry point.
Results are printed as JSON and simultaneously written to graph + log.
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.tools.registry import run_tool, get_tools_for_selector
from src.graph.database import InvestigationGraph
from src.graph.visualizer import generate_investigation_html
from src.logger.investigation_log import InvestigationLogger
from src.report.bibliography import generate_bibliography


def execute_tool(tool_name: str, selector: str, selector_type: str,
                 graph_file: str, log_file: str, depth: int = 1,
                 case_id: str = "") -> dict:
    result = run_tool(tool_name, selector, selector_type)
    if result is None:
        rd = {"success": False, "tool": tool_name, "error": "Tool returned None (not implemented or unavailable)"}
    else:
        rd = result.to_dict()

    if log_file:
        logger = InvestigationLogger(log_file)
        logger.log_tool_execution(tool_name, selector, selector_type, rd)

    if graph_file and rd.get("success"):
        graph = InvestigationGraph(graph_file)
        graph.add_entity(selector, selector_type, tool_name, depth=max(0, depth - 1),
                         confidence="confirmed", citation="Investigation seed/pivot")
        for entity in rd.get("entities_found", []):
            eid = graph.add_entity(
                entity["value"], entity["entity_type"], tool_name,
                depth=depth,
                confidence=entity.get("confidence", "confirmed"),
                citation=entity.get("source_citation", ""),
                metadata=entity.get("metadata", {}),
            )
            graph.add_relationship(
                selector, selector_type,
                entity["value"], entity["entity_type"],
                f"found_by_{tool_name}",
                tool_name,
                confidence=entity.get("confidence", "confirmed"),
                citation=entity.get("source_citation", ""),
            )
        graph.save()

    return rd


def execute_all_for_selector(selector: str, selector_type: str,
                             graph_file: str, log_file: str, depth: int = 1,
                             case_id: str = "") -> list[dict]:
    tools = get_tools_for_selector(selector_type)
    results = []
    for tool in tools:
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        try:
            rd = execute_tool(tool_name, selector, selector_type,
                              graph_file, log_file, depth, case_id)
        except Exception as e:
            rd = {"success": False, "tool": tool_name, "error": str(e)}
        results.append({"tool": tool_name, "result": rd})
    return results


def regenerate_graph_html(graph_file: str, output_html: str, title: str = "Investigation Graph"):
    graph = InvestigationGraph(graph_file)
    generate_investigation_html(graph, output_html, title)
    stats = graph.get_stats()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Execute OSINT tools with auto-persistence")
    parser.add_argument("--tool", help="Specific tool to run")
    parser.add_argument("--run-all", action="store_true", help="Run all tools for the selector type")
    parser.add_argument("--selector", required=True, help="The selector value")
    parser.add_argument("--type", required=True, dest="selector_type", help="Selector type")
    parser.add_argument("--graph", required=True, help="Path to graph.json")
    parser.add_argument("--log", required=True, help="Path to investigation.md")
    parser.add_argument("--depth", type=int, default=1, help="Depth from seed")
    parser.add_argument("--case", default="", help="Case ID")
    parser.add_argument("--regen-html", help="Also regenerate graph HTML at this path")

    args = parser.parse_args()

    if args.run_all:
        results = execute_all_for_selector(
            args.selector, args.selector_type,
            args.graph, args.log, args.depth, args.case
        )
        print(json.dumps(results, indent=2))
    elif args.tool:
        result = execute_tool(
            args.tool, args.selector, args.selector_type,
            args.graph, args.log, args.depth, args.case
        )
        print(json.dumps(result, indent=2))
    else:
        parser.error("Either --tool or --run-all is required")

    if args.regen_html:
        stats = regenerate_graph_html(args.graph, args.regen_html,
                                      f"Investigation: {args.case}")
        print(f"\nGraph HTML regenerated: {json.dumps(stats)}", file=sys.stderr)

    # Auto-regenerate bibliography from the case directory
    case_dir = str(Path(args.graph).parent)
    try:
        bib_path = generate_bibliography(case_dir)
        print(f"Bibliography updated: {bib_path}", file=sys.stderr)
    except Exception as e:
        print(f"Bibliography generation skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
