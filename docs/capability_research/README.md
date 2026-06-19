# Capability Research — shared spec

Goal: for the **structured gatherer line only** (NOT web search), pick the BEST tool(s)
per OSINT capability and record how to run them, so we can wire them declaratively.

Each researcher owns a bucket and writes `docs/capability_research/<bucket>.json`.

## Execution categories (the gatherer's runner classes)
- **CLI** — installable command-line tool, run by shelling out (e.g. maigret, holehe, theHarvester).
- **HTTP** — callable via an HTTP/API endpoint that returns parseable data (JSON/XML/HTML).
- **custom** — needs bespoke handling (auth/cookies/session, odd output) — a small custom script.
- **excluded** — browser extension, manual-only website, dead/abandoned, or paid-with-no-free-tier
  that we won't wire now (record it with a reason so we don't re-evaluate it later).

## Per-capability JSON schema
```json
{
  "bucket": "<bucket name>",
  "capabilities": [
    {
      "capability": "username_enumeration",
      "selector_types": ["username"],
      "best": [
        {
          "id": "maigret",
          "name": "Maigret",
          "exec_category": "CLI",
          "install": "pip install maigret",
          "run": "maigret {selector} --json ndjson --no-progressbar --timeout 10",
          "auth": "none",                      // none | api_key | oauth | cookies
          "free": true,                         // free tier usable for automation?
          "maintained": "active (v0.5.0, 2025-08)",
          "outputs": ["url", "email", "name"], // selector types it yields
          "status": "already_implemented",     // already_implemented | to_wire
          "notes": "3000+ sites; extracts linked emails/names; pin version"
        }
      ],
      "runner_up": [ { "id": "naminter", "exec_category": "CLI", "notes": "anti-bot recheck" } ],
      "gaps": "what no good tool covers here"
    }
  ],
  "excluded": [ { "id": "spiderfoot_oss", "reason": "OSS abandoned (Intel 471), 2+ yrs stale" } ]
}
```

## Rules for researchers
1. **Dedup to the best.** Don't list 20 username tools — pick the best 1-3 and a runner-up. Justify.
2. **Lean on the audit first.** Read the reference docs (below) before searching — they already rank
   best-in-class and list dead tools. Only web-search to verify maintained status + exact install/run
   for your picks and to fill gaps.
3. **Accurate run-metadata.** install command, run command (with `{selector}`) OR API URL template,
   auth needs, output format. This becomes the wiring spec — get it right.
4. **Avoid dead tools.** The audit flags abandoned ones (SpiderFoot OSS, twint, h8mail, mosint, etc.).
5. **Structured only.** No web-search/manual tools as "best"; mark manual-only as excluded.
6. **Don't re-research what's wired.** If a pick is already in src/tools/*, mark status=already_implemented.

## Reference docs to read first
- `~/osint_tooling_audit_2026-06.md` — best-tool-per-capability + dead-tool flags (PRIMARY)
- `~/OSINT_Tool_Ontology.md`, `~/OSINT_Tool_Playbook.md` — master input/output reference + playbook
- `~/osint-investigator-v3/docs/landscape-survey-2026.md` — broad survey
- `~/osint-investigator-v3/src/ontology/tool_buckets.json` — candidate tools (filter to your input_types)
- `~/osint-investigator-v3/src/tools/*.py` — already-implemented tools (mark, don't re-research)
