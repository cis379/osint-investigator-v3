# OSINT Investigator v3

A multi-agent **external-OSINT** investigation system. You give it a seed *selector* — a domain,
email, username, real name, IP, phone, crypto address, and more — and an **AI coding agent** pivots
through OSINT sources, builds a **confidence-tiered entity graph**, and produces a **cited CTI
report**. Every finding traces to specific tool output; nothing is fabricated.

The AI is the **analyst brain**; the Python in `src/` is its **hands**. The system is
**agent-vendor-agnostic** — drive it with **Claude Code** *or* **OpenAI Codex** (see `AGENTS.md`).

---

## Quickstart (fresh machine, ~15 min)

```bash
# prerequisites (macOS example): brew install git python@3.12 pipx exiftool && pipx ensurepath
git clone https://github.com/cis379/osint-investigator-v3.git
cd osint-investigator-v3
./bootstrap.sh          # venv + deps + OSINT CLI tools + .env scaffold + health gate
```
When you see **`=== BOOTSTRAP COMPLETE — system is HEALTHY ===`**, you're ready. Then, from your
coding agent in this folder:

- **Codex** — it reads `AGENTS.md` automatically; say `investigate example.com`.
- **Claude Code** — run `/investigate example.com`.

> **Setting this up with an agent?** Point it at the repo and tell it to "get the system running."
> It should read **`AGENTS.md`** (or `CLAUDE.md`), run `./bootstrap.sh`, confirm the health gate is
> green, and it's ready. Full detail in **`SETUP.md`**; moving machines is in **`MIGRATION.md`**.

---

## How it works

```
/investigate <seed>
   │
   ▼
[investigate skill] → detect selector type → create workspace → BECOME the Supervisor
   │
[supervisor skill]  → the analyst brain (main thread; you can interrupt anytime)
   │  routes via the ONTOLOGY (registry.plan_collection — nothing hardcoded)
   │
   ├── THREE COLLECTION LINES (dispatched as background agents) ──────────────┐
   │   • STRUCTURED  (gatherer → collect.py)        typed tools, raw output    │
   │   • WEB-SEARCH  (web_searcher)                 real searches + fetches    │
   │   • ACTIVE      (active_collector)             tracker/analytics IDs =    │
   │                                                independent ownership proof │
   │                        (all three log raw + NEVER write the graph) ◄──────┘
   ▼
SUPERVISOR analyzes + TIERS every finding (highly_likely / probable / possible)
   │  re-grades tool self-claims; corroboration upgrades; weak hits kept, never dropped
   ▼
COMMIT to the graph (graph_commit.py) → graph.json/html + bibliography (live)
   │
   ▼  PIVOT on each new entity (ontology-guided) — loop until dry
   │
[red_team skill]  → MANDATORY adversarial gate before any report (and on demand):
   │  challenges over-merges / single-source top-tier / attribution drift → supervisor reconciles
   ▼
[report-writer]   → narrative CTI report (BLUF + OV-1 → pivot-by-pivot story → appendices)
   │  → red_team MODE 2 grounding loop: checks the draft vs graph+log until 100% grounded
   ▼
report.md / report.html   (ships only when grounded)
```

**The spine is the ontology.** Every routing and pivot decision comes from
`registry.plan_collection` + `pivot_map` — never hardcoded.

---

## The agents (skills)

Eight vendor-neutral skills in `skills/` (plus the `.claude/commands/` and `codex/prompts/` entry
points):

| Skill | Role |
|---|---|
| **investigate** | Launcher: detect selector, create workspace, become the supervisor |
| **supervisor** | The analyst brain — plan, dispatch the 3 lines, analyze, **tier by confidence**, commit the graph, pivot, run the gates |
| **gatherer** | Structured collector — runs `collect.py` (typed tools), returns raw, never analyzes |
| **web_searcher** | Web-search collector — real WebSearch/WebFetch; snippet-as-evidence; cites everything |
| **active_collector** | Active line — touches the target's own infra for tracker/analytics IDs + favicon hash (the **independent ownership corroborator**); OPSEC-aware, passive-first |
| **red_team** | Adversarial gate (READ-ONLY). **Mode 1:** challenges the analysis before any report. **Mode 2:** grounds the drafted report against graph+log until 100% grounded |
| **report-writer** | Authors the narrative CTI report (story + grounded diagrams) |
| **system_manager** | Maintains/extends the system without breaking it (health-gated); its own session |

---

## What it can run (honest view)

**58 runnable tools** routed by the ontology across **20 of 92 selector types** with a dedicated
structured tool; the rest are covered by the web-search line (the universal fallback) or the
general-username fallback, else logged as a GAP.

> **Ontology honesty.** The live `registry.py` is the source of truth for what RUNS. The big
> `tools_registry.json` (1,031 entries) is a **roadmap of candidate tools**, not a claim of what's
> built: of the 58 runnable tools, ~18 were implemented from that roadmap and ~40 were built beyond
> it (all ledgered). Query `registry.get_selector_capability(type)` / `plan_collection` for the truth.

Strong coverage: **domain** (16 tools incl. whois/rdap, dns/dnsrecon, crtsh/certspotter, wayback,
tls_cert, urlscan, cloud_buckets, **web_tech_fingerprint**), **ip_v4** (11 incl. shodan_internetdb,
ripestat, greynoise, reverse_ip/robtex), **username** (sherlock, maigret, naminter, linkook,
socialscan…), **email** (holehe, **user_scanner**, hudsonrock, xposedornot, pgp_keyserver…),
**name/company** (web-search-primary + wikipedia/wikidata, gleif_lei, sec_edgar, courtlistener),
plus crypto, phone, image/EXIF, and the **tracker_id** ownership-corroborator line.

Some capabilities are structural gaps (paid/manual/keyed) and are **documented honestly** rather than
faked — reverse-WHOIS at scale, people-identity last-mile, phone→owner, reverse-image, deep breach,
session-gated social, non-US registries, dark-web. See `system/BACKLOG.md`.

---

## Outputs (per case, in `investigations/INV-YYYYMMDD-NNN/`)

| File | What |
|---|---|
| `investigation.md` | Full audit trail — every tool's raw output |
| `graph.json` / `graph.html` | Entity graph (vis.js), tier-styled — refresh live |
| `bibliography.html` | Clickable investigation links per entity |
| `report.md` / `report.html` | Narrative CTI report (BLUF + OV-1 → story → appendices) |
| `state.json` | Investigation status/metadata |

---

## Design principles

1. **No hallucination** — every finding traces to a specific tool output or source URL.
2. **Raw/analysis split** — collectors fetch raw and log; the supervisor decides what's real, tiers
   it, and builds the graph. Tools never grade themselves into the graph.
3. **Tier, don't drop** — `highly_likely` / `probable` / `possible`; weak hits stay visible as pivots.
4. **The ontology is the spine** — routing and pivoting are ontology-driven, never hardcoded.
5. **Three collection lines** — structured + web-search + active, all essential.
6. **Adversarial gate** — the red team challenges every merge/inference before anything ships.
7. **Don't break anything** — health-gated (`scripts/health_check.py`), reversible changes.
8. **Honest about limits** — gaps are documented, not faked.

---

## Documentation map

- **`SETUP.md`** — build it on a fresh machine (assume-nothing).
- **`AGENTS.md`** — how any coding agent (Codex/Claude Code) drives it.
- **`MIGRATION.md`** — move it to a new machine.
- **`CLAUDE.md`** — project instructions (Claude Code).
- **`docs/SYSTEM-SUMMARY.md`** — full architecture reference.
- **`system/VISION.md`** — purpose + principles · **`system/CAPABILITY-LOCK.md`** — what must not regress.

## License
MIT

## Acknowledgments
- Tool-catalog roadmap seeded from [cipher387/osint_stuff_tool_collection](https://github.com/cipher387/osint_stuff_tool_collection)
- Graph visualization via [vis.js](https://visjs.org/); report diagrams via Mermaid
