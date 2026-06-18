"""Log a web-search collection round and pass its findings to the supervisor.

This is the web-search line's analogue of collect.py. The web-search collector
AGENT does the actual searching/fetching with its own WebSearch/WebFetch tools
(judgment-driven discovery). This script handles the two mechanical parts so they
stay consistent with the structured line:

  1. writes the raw search activity + fetched pages + extracted candidate findings
     to investigation.md (the human audit trail), and
  2. prints the findings JSON for the SUPERVISOR to tier and commit via graph_commit.py.

Like collect.py, it does NOT build the graph and does NOT assign final confidence.
Input is a JSON spec via --input FILE or stdin:
{
  "selector": "Robin Grieff",
  "type": "name",
  "searches": [
    {"query": "\"Robin Grieff\" site:linkedin.com",
     "results": [{"url": "...", "title": "...", "snippet": "..."}]}
  ],
  "fetched": [{"url": "...", "summary": "extracted text..."}],
  "findings": [
    {"value": "rgrieff@asu.edu", "type": "email",
     "citation": "ASU directory page lists this address",
     "source_url": "https://...", "confidence_hint": "probable"}
  ]
}
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from src.logger.investigation_log import InvestigationLogger


def log_web_search(spec: dict, log_file: str) -> list:
    selector = spec.get("selector", "")
    stype = spec.get("type", "")
    searches = spec.get("searches", [])
    fetched = spec.get("fetched", [])
    findings = spec.get("findings", [])

    lines = [
        f"- **Selector:** `{selector}` (type: {stype})",
        f"- **Queries run:** {len(searches)} | **Pages fetched:** {len(fetched)} "
        f"| **Candidate findings:** {len(findings)}",
        "",
        "**Searches & results (raw):**",
    ]
    for s in searches:
        lines.append(f"- `{s.get('query', '')}`")
        for r in s.get("results", [])[:10]:
            snippet = (r.get("snippet", "") or "")[:200]
            lines.append(f"    - [{r.get('title', '')}]({r.get('url', '')}) — {snippet}")
    if fetched:
        lines.append("")
        lines.append("**Pages fetched:**")
        for f in fetched:
            lines.append(f"- {f.get('url', '')}: {(f.get('summary', '') or '')[:300]}")
    lines.append("")
    lines.append("**Extracted candidate findings (supervisor will TIER these):**")
    if findings:
        for fd in findings:
            hint = fd.get("confidence_hint", "")
            hint_s = f" _(hint: {hint})_" if hint else ""
            lines.append(
                f"- [{fd.get('type', '?')}] `{fd.get('value', '')}` — "
                f"{fd.get('citation', '')} ({fd.get('source_url', '')}){hint_s}"
            )
    else:
        lines.append("- (none)")

    if log_file:
        InvestigationLogger(log_file).log_step(f"Web Search Collection - {selector}", "\n".join(lines))

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Log a web-search collection round; emit findings for the supervisor (NO graph writes)")
    parser.add_argument("--log", default="", help="investigation.md path for raw audit logging")
    parser.add_argument("--input", help="JSON spec file; if omitted, read stdin")

    args = parser.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        parser.error(f"Input is not valid JSON: {e}")

    findings = log_web_search(spec, args.log)
    print(json.dumps({"findings": findings, "logged": bool(args.log)}, indent=2))


if __name__ == "__main__":
    main()
