"""Bucket the full tool catalog by HOW each tool is executed.

This is the analysis step before wiring: every catalog entry is assigned an
execution class and a proposed gatherer category, so we can build one runner per
category (CLI / HTTP / custom) and see what needs per-tool research. STRUCTURED
line only — this does not touch the web-search line.

Writes src/ontology/tool_buckets.json (the categorized index) and prints a summary.

    python -m src.ontology.bucket_catalog
"""
import json
import sys
import collections
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))
ONT = BASE / "src" / "ontology"

# exec_class -> proposed gatherer category + whether it's automatable by a generic runner
EXEC_META = {
    "implemented":   ("already-wired",        True),
    "cli_ready":     ("CLI",                  True),   # has command_template + install
    "cli_research":  ("CLI",                  False),  # method=cli but no run metadata yet
    "api_ready":     ("HTTP",                 True),   # has api_url template
    "api_research":  ("HTTP",                 False),  # method=api but no endpoint yet
    "library":       ("CLI",                  False),  # python lib -> thin wrapper
    "web_interface": ("HTTP",                 False),  # website w/ url -> test if queryable
    "generator":     ("special",              True),   # dork generator
    "extension":     ("EXCLUDED:extension",   False),  # browser extension, not automatable
    "framework":     ("custom",               False),  # orchestrator (spiderfoot etc.)
    "other":         ("custom",               False),
}


def exec_class(t: dict) -> str:
    if t.get("implemented"):
        return "implemented"
    m = t.get("method")
    if m == "cli":
        return "cli_ready" if t.get("command_template") and t.get("install") else "cli_research"
    if m == "api":
        return "api_ready" if t.get("api_url") else "api_research"
    if m in ("library", "generator", "website", "extension", "framework"):
        return {"website": "web_interface"}.get(m, m)
    return "other"


def main():
    tr = json.loads((ONT / "tools_registry.json").read_text(encoding="utf-8"))["tools"]

    buckets = collections.defaultdict(list)
    for t in tr:
        ec = exec_class(t)
        t2 = {k: t.get(k) for k in ("id", "name", "category", "method", "input_types",
                                    "output_types", "command_template", "install",
                                    "api_url", "url", "free", "reliability")}
        t2["exec_class"] = ec
        t2["gatherer_category"] = EXEC_META[ec][0]
        t2["automatable_now"] = EXEC_META[ec][1]
        buckets[ec].append(t2)

    # --- summary ---
    print(f"=== {len(tr)} catalog tools bucketed by execution class ===")
    print(f"{'exec_class':16s} {'gatherer_cat':22s} {'auto':5s} count")
    order = ["implemented", "cli_ready", "cli_research", "api_ready", "api_research",
             "library", "web_interface", "generator", "framework", "extension", "other"]
    for ec in order:
        if ec in buckets:
            cat, auto = EXEC_META[ec]
            print(f"  {ec:14s} {cat:22s} {str(auto):5s} {len(buckets[ec])}")

    auto_now = [t for b in buckets.values() for t in b if t["automatable_now"] and t["exec_class"] != "implemented"]
    print(f"\nAutomatable NOW (have run-metadata, not yet wired): {len(auto_now)}")
    for t in auto_now:
        run = t.get("command_template") or t.get("api_url") or "(lib)"
        print(f"  [{t['exec_class']:10s}] {t['id']:28s} key={t.get('free')} :: {run}")

    # --- capability coverage: tools per input selector type (automatable candidates) ---
    print("\n=== candidate tools per input selector type (cli/api/library/website only) ===")
    cand_classes = {"cli_ready", "cli_research", "api_ready", "api_research", "library", "web_interface"}
    by_input = collections.Counter()
    for b in buckets.values():
        for t in b:
            if t["exec_class"] in cand_classes:
                for it in (t.get("input_types") or ["?"]):
                    by_input[it] += 1
    for it, n in by_input.most_common(20):
        print(f"  {it:18s} {n}")

    # --- dedup view: capability category -> how many candidate tools (pick best later) ---
    print("\n=== top capability categories (candidate tools; dedup target) ===")
    by_cat = collections.Counter()
    for b in buckets.values():
        for t in b:
            if t["exec_class"] in cand_classes:
                by_cat[t.get("category", "?")] += 1
    for c, n in by_cat.most_common(15):
        print(f"  {n:4d}  {c}")

    out = {"_doc": "Catalog bucketed by execution class for the structured/gatherer line. "
                   "Built by bucket_catalog.py. gatherer_category groups runners (CLI/HTTP/custom).",
           "exec_meta": {k: {"gatherer_category": v[0], "automatable": v[1]} for k, v in EXEC_META.items()},
           "buckets": dict(buckets)}
    (ONT / "tool_buckets.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote src/ontology/tool_buckets.json ({sum(len(v) for v in buckets.values())} tools)")


if __name__ == "__main__":
    main()
