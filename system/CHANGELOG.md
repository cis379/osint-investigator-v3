# CHANGELOG — System Manager decision/change log

One line per change: what + why. The Manager appends here every working session. Newest first.

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
