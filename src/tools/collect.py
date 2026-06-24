"""Collect RAW OSINT tool output. The gatherer's tool — it does NOT touch the graph.

This is the *collection* half of the raw/analysis split. It runs a tool (or every
tool for a selector type), logs the raw output to investigation.md for the human
audit trail, and prints the structured JSON for the SUPERVISOR to analyze.

It deliberately does NOT build the graph or assign confidence. Deciding what is
real, how strong it is, and what enters the graph is the supervisor's job
(see src/tools/graph_commit.py). This preserves the separation:

    gatherer  -> collect.py     (raw tools in, raw JSON out, full audit log)
    supervisor -> graph_commit.py (analyzed findings in, tiered graph out)

Usage:
    python -m src.tools.collect --tool whois_lookup --selector example.com --type domain \
        --log investigations/INV-xxx/investigation.md

    python -m src.tools.collect --run-all --selector example.com --type domain \
        --log investigations/INV-xxx/investigation.md
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.tools.registry import run_tool, get_tools_for_selector
from src.logger.investigation_log import InvestigationLogger


def collect_tool(tool_name: str, selector: str, selector_type: str, log_file: str = "") -> dict:
    """Run one tool, log its raw output, return the structured result dict. No graph writes."""
    result = run_tool(tool_name, selector, selector_type)
    if result is None:
        rd = {"success": False, "tool": tool_name,
              "error": "Tool returned None (not implemented or unavailable)",
              "entities_found": []}
    else:
        rd = result.to_dict()

    # Full raw audit trail — nothing is dropped here; the human can audit everything.
    if log_file:
        InvestigationLogger(log_file).log_tool_execution(tool_name, selector, selector_type, rd)

    return rd


def collect_all(selector: str, selector_type: str, log_file: str = "",
                exclude: set | None = None) -> list[dict]:
    """Run every tool registered for the selector type. No graph writes.

    `exclude` is an optional set of tool names to skip (e.g. network-heavy tools the
    fast regression gate doesn't need to exercise)."""
    exclude = exclude or set()
    results = []
    for tool in get_tools_for_selector(selector_type):
        tool_name = tool.name if hasattr(tool, "name") else str(tool)
        if tool_name in exclude:
            continue
        try:
            rd = collect_tool(tool_name, selector, selector_type, log_file)
        except Exception as e:
            rd = {"success": False, "tool": tool_name, "error": str(e), "entities_found": []}
        results.append({"tool": tool_name, "result": rd})
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Collect raw OSINT tool output (NO graph writes — gatherer use only)")
    parser.add_argument("--tool", help="Specific tool to run")
    parser.add_argument("--run-all", action="store_true", help="Run all tools for the selector type")
    parser.add_argument("--selector", required=True, help="The selector value")
    parser.add_argument("--type", required=True, dest="selector_type", help="Selector type")
    parser.add_argument("--log", default="", help="investigation.md path for raw audit logging")
    parser.add_argument("--exclude", default="", help="Comma-separated tool names to skip (--run-all)")

    args = parser.parse_args()

    # B1: ONE output schema for both modes — {"selector","type","results":[{tool,result}]}.
    # A single-tool run is just a one-element results list, so the supervisor parses
    # the same shape whether one tool or all ran.
    if args.run_all:
        exclude = {t.strip() for t in args.exclude.split(",") if t.strip()}
        results = collect_all(args.selector, args.selector_type, args.log, exclude=exclude)
    elif args.tool:
        rd = collect_tool(args.tool, args.selector, args.selector_type, args.log)
        results = [{"tool": args.tool, "result": rd}]
    else:
        parser.error("Either --tool or --run-all is required")

    print(json.dumps({"selector": args.selector, "type": args.selector_type,
                      "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
