"""Make the ontology HONEST about what actually runs.

The ontology is a large CATALOG (1031 tools across 90 selector types), but only
~25 tools are implemented in code. This script flags reality without pruning the
catalog (the catalog is our wiring roadmap):

  - tools_registry.json : adds "implemented": true/false to every tool entry,
                          and an "implemented_total" count.
  - pivot_map.json      : adds, per selector type, "implemented_tools" (the subset
                          of "tools" that actually run) and "implemented_count".

Source of truth = the tools the registry actually loads (src.tools.registry).
Re-run this after wiring new tools to refresh the flags. Idempotent; preserves the
files' existing JSON style (ascii-escaped, indent=2).

    python -m src.ontology.annotate_implemented
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))
from src.tools.registry import get_all_tools

ONT = BASE / "src" / "ontology"


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True)  # match existing style
        f.write("\n")


def main():
    implemented = set(get_all_tools().keys())

    # --- tools_registry.json ---
    tr_path = ONT / "tools_registry.json"
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    n_impl = 0
    for t in tr["tools"]:
        is_impl = t.get("id") in implemented
        t["implemented"] = is_impl
        n_impl += is_impl
    tr["implemented_total"] = n_impl
    # Option B: the live registry is the source of truth; tools_registry is a ROADMAP of candidates.
    # Record tools BUILT BEYOND the roadmap explicitly so the bookkeeping accounts for every live
    # tool (no invisibles) and the "X runnable" framing is honest.
    reg_ids = {t.get("id") for t in tr["tools"]}
    tr["built_beyond_roadmap"] = sorted(implemented - reg_ids)
    tr["built_beyond_roadmap_count"] = len(tr["built_beyond_roadmap"])
    _dump(tr, tr_path)

    # --- pivot_map.json ---
    pm_path = ONT / "pivot_map.json"
    pmwrap = json.loads(pm_path.read_text(encoding="utf-8"))
    pm = pmwrap["pivot_map"]
    for entry in pm.values():
        impl_tools = [tid for tid in entry.get("tools", []) if tid in implemented]
        entry["implemented_tools"] = impl_tools
        entry["implemented_count"] = len(impl_tools)
    _dump(pmwrap, pm_path)

    # --- report ---
    reg_ids = {t.get("id") for t in tr["tools"]}
    in_pivot = {tid for e in pm.values() for tid in e.get("tools", [])}
    print(f"tools_registry: {n_impl}/{len(tr['tools'])} flagged implemented")
    print(f"pivot_map: annotated {len(pm)} selector types")
    print(f"  types with >=1 implemented tool: {sum(1 for e in pm.values() if e['implemented_count'])}/{len(pm)}")
    orphan_pivot = sorted(implemented - in_pivot)
    orphan_cat = sorted(implemented - reg_ids)
    if orphan_pivot:
        print(f"  WARN implemented tools not referenced by ANY pivot_map type: {orphan_pivot}")
    if orphan_cat:
        print(f"  WARN implemented tools missing from tools_registry catalog: {orphan_cat}")


if __name__ == "__main__":
    main()
