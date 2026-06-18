"""Guard selector typing + ontology-driven routing against regressions.

Covers the allthespills misclassification fix: a bare handle must resolve to the
general 'username' bucket (not telegram_handle), and a handle-like type with no
runnable structured tools must fall back to username via plan_collection.

    python tests/test_selector_detection.py
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.core.selector import detect_selector_type
from src.tools.registry import plan_collection

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(cond, msg):
    print(f"  {PASS if cond else FAIL} {msg}")
    if not cond:
        failures.append(msg)


def main():
    print("=== selector detection ===")
    # (input, expected_type, expected_confidence)
    cases = [
        ("allthespills", "username", "inferred"),   # the bug: was telegram_handle/exact
        ("@johndoe", "username", "inferred"),
        ("john_doe_123", "username", "inferred"),
        ("user@example.com", "email", "exact"),
        ("example.com", "domain", "exact"),
        ("192.168.1.1", "ip_v4", "exact"),
        ("123456789012345678", "discord_id", "exact"),
        ("Robin Grieff", "name", "inferred"),
    ]
    for raw, etype, econf in cases:
        r = detect_selector_type(raw)
        check(r.selector_type == etype, f"{raw!r} -> type {r.selector_type} (want {etype})")
        check(r.confidence == econf, f"{raw!r} -> confidence {r.confidence} (want {econf})")
    # telegram_handle must NOT be auto-detected from a bare string anymore
    check(detect_selector_type("allthespills").selector_type != "telegram_handle",
          "bare handle is NOT auto-typed as telegram_handle")

    print("\n=== ontology-driven routing (plan_collection) ===")
    p = plan_collection("allthespills", "username")
    check("sherlock" in p["structured_tools"] and "maigret" in p["structured_tools"],
          "username routes to sherlock+maigret")
    # explicit telegram_handle (no structured tools) must fall back to username
    p2 = plan_collection("allthespills", "telegram_handle")
    check(p2["fallback_applied"] and p2["effective_type"] == "username",
          "telegram_handle falls back to general username")
    check("maigret" in p2["structured_tools"],
          "fallback exposes the username enumerators")
    # a real type with tools must NOT fall back
    p3 = plan_collection("Robin Grieff", "name")
    check(not p3["fallback_applied"] and p3["effective_type"] == "name",
          "name (has tools) does not fall back")

    print("\n=== RESULT ===")
    if failures:
        print(f"{FAIL} {len(failures)} check(s) failed:")
        for f in failures:
            print(f"   - {f}")
        return 1
    print(f"{PASS} selector detection + routing correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
