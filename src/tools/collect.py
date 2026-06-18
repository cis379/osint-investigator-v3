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


def collect_all(selector: str, selector_type: str, log_file: str = "") -> list[dict]:
    """Run every tool registered for the selector type. No graph writes."""
    results = []
    for tool in get_tools_for_selector(selector_type):
        tool_name = tool.name if hasattr(tool, "name") else str(tool)
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

    args = parser.parse_args()

    if args.run_all:
        print(json.dumps(collect_all(args.selector, args.selector_type, args.log), indent=2))
    elif args.tool:
        print(json.dumps(collect_tool(args.tool, args.selector, args.selector_type, args.log), indent=2))
    else:
        parser.error("Either --tool or --run-all is required")


if __name__ == "__main__":
    main()
