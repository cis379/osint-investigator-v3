"""Guard the ontology's HONESTY annotations against drift.

After src/ontology/annotate_implemented.py runs, pivot_map.json carries
"implemented_tools"/"implemented_count" per selector type and tools_registry.json
carries "implemented": bool per tool. This test asserts those annotations still
match what the registry actually loads — so a wired/unwired tool can't leave the
ontology lying about what runs.

Run after wiring tools (re-run annotate_implemented.py first):
    python -m src.ontology.annotate_implemented && python tests/test_ontology_honesty.py
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.tools.registry import get_all_tools, get_tools_for_selector

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  {FAIL} {msg}")


def main():
    print("=== ontology honesty consistency ===")
    impl = set(get_all_tools().keys())
    ONT = BASE / "src" / "ontology"
    pm = json.loads((ONT / "pivot_map.json").read_text(encoding="utf-8"))["pivot_map"]
    tr = json.loads((ONT / "tools_registry.json").read_text(encoding="utf-8"))

    # pivot_map: annotated implemented_tools must equal the loader's view, per type
    type_mismatch = 0
    for stype, entry in pm.items():
        check("implemented_tools" in entry, f"{stype}: missing implemented_tools annotation")
        annotated = sorted(entry.get("implemented_tools", []))
        runtime = sorted(t.name for t in get_tools_for_selector(stype))
        if annotated != runtime:
            type_mismatch += 1
            check(False, f"{stype}: implemented_tools {annotated} != runtime {runtime}")
        check(entry.get("implemented_count") == len(annotated),
              f"{stype}: implemented_count != len(implemented_tools)")

    # tools_registry: implemented flag must match the registry
    flag_mismatch = 0
    for t in tr["tools"]:
        want = t.get("id") in impl
        if t.get("implemented") != want:
            flag_mismatch += 1
    check(flag_mismatch == 0, f"{flag_mismatch} tools_registry entries have a stale 'implemented' flag")

    n_impl_types = sum(1 for e in pm.values() if e.get("implemented_count"))
    print(f"  {len(pm)} selector types checked; {n_impl_types} have >=1 runnable tool")
    print(f"  {sum(t.get('implemented') for t in tr['tools'])}/{len(tr['tools'])} catalog tools flagged implemented")

    print("\n=== RESULT ===")
    if failures:
        print(f"{FAIL} {len(failures)} consistency check(s) failed "
              f"(run `python -m src.ontology.annotate_implemented` to refresh).")
        return 1
    print(f"{PASS} ontology annotations are consistent with the registry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
