"""System health gate — the System Manager runs this BEFORE and AFTER any change.

PASS (exit 0) = the system's core invariants hold.
FAIL (exit 1) = something regressed — the Manager must revert and not commit.

This is the mechanism behind "don't break anything": every change is validated against
the regression suites + a full tool-registry load + ontology consistency + a tool-count
floor (so functionality can't silently disappear).

    python scripts/health_check.py
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

TOOL_FLOOR = 55  # the Manager bumps this when it deliberately adds tools; it must never DROP.

results = []


def record(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def run_suite(rel_path):
    r = subprocess.run([sys.executable, str(BASE / rel_path)],
                       capture_output=True, text=True, timeout=300)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    return r.returncode == 0, last


def main():
    # 1. registry + all tools load cleanly
    try:
        from src.tools.registry import get_all_tools, plan_collection, get_selector_capability
        tools = get_all_tools()
        record("registry loads all tools", True, f"{len(tools)} tools")
        record(f"tool-count floor (>= {TOOL_FLOOR})", len(tools) >= TOOL_FLOOR,
               f"{len(tools)} tools (floor {TOOL_FLOOR})")
    except Exception as e:
        record("registry loads all tools", False, repr(e))

    # 2. ontology routing works for a known type
    try:
        plan = plan_collection("example.com", "domain")
        record("plan_collection routes", bool(plan.get("structured_tools")),
               f"{len(plan.get('structured_tools', []))} structured tools for domain")
        cap = get_selector_capability("name")
        record("get_selector_capability works", cap.get("implemented_count", 0) > 0,
               f"name -> {cap.get('implemented_count')} runnable")
    except Exception as e:
        record("plan_collection routes", False, repr(e))

    # 3. regression suites (deterministic, fast)
    for name, path in [("baseline suite (split invariants)", "tests/replay_baseline.py"),
                       ("ontology honesty", "tests/test_ontology_honesty.py"),
                       ("selector detection + routing", "tests/test_selector_detection.py")]:
        try:
            ok, last = run_suite(path)
            record(name, ok, last)
        except Exception as e:
            record(name, False, repr(e))

    # report
    print("=== SYSTEM HEALTH CHECK ===")
    healthy = True
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))
        healthy = healthy and ok
    print("=== " + ("HEALTHY" if healthy else "UNHEALTHY - revert, do not commit") + " ===")
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
