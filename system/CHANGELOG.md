# CHANGELOG — System Manager decision/change log

One line per change: what + why. The Manager appends here every working session. Newest first.

## 2026-06-24 (backlog sweep)
- Worked the bug/addressable-gap backlog in 3 health-gated batches (all GREEN):
  - **B8** threatfox: abuse.ch made the API auth-mandatory → it 401'd on every domain/IP run;
    now skips gracefully with a clear "needs free ABUSE_CH_API_KEY" message (live-confirmed by a
    concurrent investigation, GAP-20260624-02). **B1** collect.py CLI → one `{"results":[…]}` schema
    (+`--exclude`). **B9** health gate fast again (baseline excludes cloud_buckets' ~80 probes).
  - **B3** courtlistener name-match gate (BM25 fuzzy FPs gone; matches `probable` not `confirmed`).
    **B2** socid scope narrowed; **B4** holehe → lead-only (positives `probable`, negatives unreliable);
    **B6** whois prefers rdap for new TLDs.
  - **B5** report.md de-lossied (pipe-escape, full values, Citation column, relationship table, no
    dead graph.png) + report-writer passes `relationships`. **B10** certspotter optional Bearer token
    (HttpTool gained `auth_prefix`). **G13** cloud_buckets adds Azure Blob + DigitalOcean Spaces.
  - **G11** exiftool installed via winget user-scope (no elevation); wrapper resolves the binary off
    a stale PATH → all 12/12 CLI tools now READY.
  Note: a concurrent supervisor session (INV-20260624-001) was committing with `git add -A` on the
  shared working tree — it bundled some of this sweep's early changes; nothing lost.

## 2026-06-24
- Intake: **SpiderFoot** (github.com/smicallef/spiderfoot, MIT). Decision: do NOT adopt the
  engine/CLI (a second correlation brain → collides with our raw/analysis split + needs sign-off);
  instead cherry-pick free no-key module *sources* and wire as our own declarative specs. Added
  4 validated tools in `src/tools/sf_derived_tools.py` (51→**55 tools**, +1 runnable type `keyword`):
  - **certspotter** (domain → CT-logged cert ISSUANCE HISTORY + subdomains) — attacks G2
    (cert-history correlation: surfaces issuers/dates/fingerprints) + adds passive subdomain
    breadth (56 subdomains for viory.video). Replaces the AnubisDB/rapiddns idea (both non-viable).
  - **robtex_ip** (ip_v4 → passive-DNS co-hosted domains) — 2nd reverse-IP source vs. quota-dead
    HackerTarget (helps G1).
  - **cloud_buckets** (domain/company/keyword → exposed S3/GCS buckets via name-permutation probe)
    — brand-new attack-surface capability (validated on flaws.cloud).
  - **pgp_keyserver** (email → alternate emails / real name on same PGP key) — email↔identity pivot (G4-adjacent).
  - Rejected: **Ahmia/dark-web** — clearnet search is JS-rendered (no-JS HTML empty); SpiderFoot's
    own dark-web modules need a Tor SOCKS proxy. Logged as new gap G12 (honest, not faked).
  Bumped TOOL_FLOOR 51→55; ran annotate_implemented; health + 3 suites GREEN.

## 2026-06-23
- Phase 1: added the System Manager (`skills/system_manager.md`) + state files
  (`system/VISION.md`, `CHANGELOG.md`, `intake/`). Manager owns vision, ontology, and the
  bug/gap backlog; test-gated autonomy for bugs/wiring, user sign-off for architecture.
- Phase 0: safety net — `scripts/health_check.py` (the gate), `system/CAPABILITY-LOCK.md`
  (must-not-regress contract), `system/BACKLOG.md` (consolidated worklist). Tagged stable
  baseline `v3-baseline-2026-06-23`. Why: make "don't break anything" an enforced mechanism.
- Hardening: HTTP retry/backoff, http_title JS-note, log auto-init, sherlock txt hygiene,
  de-hardcoded paths (`python -m`). Report-writer validated end-to-end.

## Earlier (pre-Manager, summarized)
- 51 tools reached via declarative HTTP/CLI runners + infra tools (reverse_ip/tls_cert/http_title);
  9 arsenal additions; family-recovery snippet fix; ontology honesty pass; web-search line;
  raw/analysis split; pivoting + confidence-tier doctrine. (Full history in git log.)
