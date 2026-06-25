"""V3 baseline regression suite — the three standing cases.

Verifies the raw/analysis SPLIT holds across all three seed types we test each
iteration:
    domain    : example.com
    name      : Robin Grieff
    username  : allthespills   (Instagram handle; note: the selector auto-detector
                                 mis-types bare "allthespills" as telegram_handle,
                                 which has no tools — so we test it as username)

For each case it checks the invariants:
    1. collection (collect.py) returns results and writes NO graph (separation holds)
    2. the raw output is logged (audit trail)
    3. graph_commit.py builds the graph from supervisor-tiered findings
    4. all stored confidences are valid tiers
Plus one isolated check that all three tiers (highly_likely/probable/possible) render,
and that the legacy "confirmed" label still normalizes to highly_likely (back-compat).

Hermetic: uses temp dirs, does NOT pollute investigations/. Fast: the slow username
CLIs (maigret/sherlock) are validated by the live agent runs, not here — this suite
exercises the username PLUMBING with the quick tool (google_dork_generator) so it
can be run after every change.

Usage:  python tests/replay_baseline.py
Exit code 0 = all checks pass.
"""
import json
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.logger.investigation_log import InvestigationLogger
from src.tools.collect import collect_all, collect_tool
from src.tools import graph_commit

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(cond, msg):
    print(f"  {PASS if cond else FAIL} {msg}")
    if not cond:
        failures.append(msg)


# (label, seed, selector_type, collection strategy, exclude)
#   "all"  -> run every tool for the type (fast for domain/name)
#   "dork" -> run only google_dork_generator (fast username plumbing check)
#   exclude -> tool names skipped in "all" mode; this suite tests the split PLUMBING,
#              not coverage, so network-heavy tools (cloud_buckets fires ~80 probes;
#              web_tech_fingerprint does a passive+live target fetch) are excluded to keep
#              the gate fast. Their plumbing is identical to peers.
CASES = [
    ("domain",   "example.com",  "domain",   "all",  {"cloud_buckets", "web_tech_fingerprint"}),
    ("name",     "Robin Grieff", "name",     "all",  set()),
    ("username", "allthespills", "username", "dork", set()),
]


def run_case(label, seed, stype, strategy, exclude, workdir):
    print(f"\n--- case: {label} ({seed!r} / {stype}) ---")
    log_file = str(workdir / "investigation.md")
    graph_file = str(workdir / "graph.json")
    graph_html = str(workdir / "graph.html")
    InvestigationLogger(log_file).init_log(f"TEST-{label}", seed, stype)

    # Part A: collection writes no graph
    if strategy == "all":
        results = collect_all(seed, stype, log_file, exclude=exclude)
    else:
        results = [{"tool": "google_dork_generator",
                    "result": collect_tool("google_dork_generator", seed, stype, log_file)}]
    n_ok = sum(1 for r in results if r["result"].get("success"))
    n_ent = sum(len(r["result"].get("entities_found", [])) for r in results)
    print(f"  ran {len(results)} tool(s), {n_ok} ok, {n_ent} raw entities")
    check(len(results) > 0, "collection ran at least one tool")
    check(not Path(graph_file).exists(), "collection wrote NO graph (separation holds)")
    check(Path(log_file).exists() and Path(log_file).stat().st_size > 0,
          "raw output logged to investigation.md")

    # Part B: supervisor commits a tiered graph (tier by corroboration; seed = highly_likely)
    source_count, emeta = {}, {}
    for r in results:
        for e in r["result"].get("entities_found", []):
            k = (e["value"], e["entity_type"])
            source_count[k] = source_count.get(k, 0) + 1
            emeta[k] = e
    findings = {"entities": [{"value": seed, "type": stype, "tool": "seed",
                              "confidence": "highly_likely", "citation": "seed", "depth": 0}],
                "relationships": []}
    for (val, et), n in source_count.items():
        conf = "highly_likely" if n >= 2 else "probable"
        findings["entities"].append({"value": val, "type": et,
                                     "tool": emeta[(val, et)].get("source_tool", "collect"),
                                     "confidence": conf,
                                     "citation": emeta[(val, et)].get("source_citation", ""),
                                     "depth": 1})
    out = graph_commit.commit(findings, graph_file, graph_html, f"TEST-{label}")
    print(f"  committed {out['entities_added']} entities")
    check(Path(graph_file).exists(), "graph_commit created graph.json")
    gdata = json.loads(Path(graph_file).read_text(encoding="utf-8"))
    confs = {n.get("confidence") for n in gdata["nodes"]}
    check(confs.issubset({"highly_likely", "probable", "possible"}),
          f"all confidences are valid tiers (saw {sorted(confs)})")


def tier_render_check(workdir):
    print("\n--- 3-tier rendering (isolated) ---")
    g = str(workdir / "tier.json")
    h = str(workdir / "tier.html")
    spec = {"entities": [
        {"value": "strong.x", "type": "domain", "tool": "t", "confidence": "highly_likely"},
        {"value": "likely.x", "type": "domain", "tool": "t", "confidence": "probable"},
        {"value": "weak.x", "type": "domain", "tool": "t", "confidence": "possible"},
        # legacy label must still normalize to highly_likely (back-compat with old graphs)
        {"value": "legacy.x", "type": "domain", "tool": "t", "confidence": "confirmed"},
    ], "relationships": []}
    graph_commit.commit(spec, g, h, "TIER")
    td = json.loads(Path(g).read_text(encoding="utf-8"))
    tiers = {n["confidence"] for n in td["nodes"]}
    check(tiers == {"highly_likely", "probable", "possible"},
          f"all three tiers stored, legacy 'confirmed' -> highly_likely ({sorted(tiers)})")
    html = Path(h).read_text(encoding="utf-8")
    check("borderDashes" in html, "weak/probable nodes render dashed in HTML")
    check("badge-possible" in html, "HTML carries 3-tier badge styling")


def main():
    print("=== V3 baseline regression suite (3 cases) ===")
    with tempfile.TemporaryDirectory(prefix="v3baseline_") as tmp:
        root = Path(tmp)
        for i, (label, seed, stype, strategy, exclude) in enumerate(CASES):
            run_case(label, seed, stype, strategy, exclude, root / f"case{i}_{label}")
        tier_render_check(root / "tier")

    print("\n=== RESULT ===")
    if failures:
        print(f"{FAIL} {len(failures)} check(s) failed:")
        for f in failures:
            print(f"   - {f}")
        return 1
    print(f"{PASS} all baseline checks passed (domain + name + username plumbing).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
