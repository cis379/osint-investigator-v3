#!/usr/bin/env bash
# ============================================================================
# OSINT Investigator v3 — one-command bootstrap (macOS / Linux)
# ============================================================================
# Rebuilds the whole system from a fresh `git clone` on a new machine:
#   1. checks Python 3.10+
#   2. creates a virtualenv (.venv) and installs the CORE Python deps
#   3. installs the two CLI tools our code imports (naminter, ignorant) INTO the venv
#   4. best-effort installs the standalone OSINT CLI tools via pipx
#   5. best-effort installs exiftool (Homebrew on macOS / apt on Linux)
#   6. scaffolds .env from .env.example
#   7. runs the health check and prints a green/red verdict
#
# The system is designed to DEGRADE GRACEFULLY: the core (steps 1–2) is all that's
# required for health to go green and for every HTTP/API tool to work. Every CLI
# tool that fails to install is reported and skipped — the matching tool just
# reports "not installed" at runtime until you install it.
#
# Usage:   ./bootstrap.sh            (from the repo root)
#          ./bootstrap.sh --core     (skip the optional CLI tools; core only, fastest)
# ============================================================================
set -u
cd "$(dirname "$0")"
ROOT="$(pwd)"
CORE_ONLY=0
[ "${1:-}" = "--core" ] && CORE_ONLY=1

# ---- pretty logging --------------------------------------------------------
c_g="\033[0;32m"; c_r="\033[0;31m"; c_y="\033[0;33m"; c_b="\033[0;34m"; c_0="\033[0m"
say()  { printf "${c_b}==>${c_0} %s\n" "$1"; }
ok()   { printf "  ${c_g}[ok]${c_0} %s\n" "$1"; }
warn() { printf "  ${c_y}[skip]${c_0} %s\n" "$1"; }
die()  { printf "  ${c_r}[FAIL]${c_0} %s\n" "$1"; exit 1; }

OS="$(uname -s)"
say "OSINT Investigator v3 bootstrap  (os=$OS, root=$ROOT)"

# ---- 1. Python -------------------------------------------------------------
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    v="$("$cand" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)"
    maj="${v%%.*}"; min="${v##*.}"
    if [ "${maj:-0}" -eq 3 ] && [ "${min:-0}" -ge 10 ]; then PY="$cand"; PYV="$v"; break; fi
  fi
done
[ -n "$PY" ] || die "Python 3.10+ not found. Install it first (macOS: 'brew install python@3.12')."
ok "Python $PYV ($PY)"

# ---- 2. venv + core deps (REQUIRED) ---------------------------------------
say "Creating virtualenv (.venv) and installing core Python deps"
"$PY" -m venv .venv || die "could not create .venv"
# shellcheck disable=SC1091
. .venv/bin/activate || die "could not activate .venv"
python -m pip install --quiet --upgrade pip || warn "pip self-upgrade failed (continuing)"
python -m pip install --quiet -r requirements.txt || die "core dependency install failed (see requirements.txt)"
ok "core deps installed into .venv"

# naminter + ignorant are launched via the venv's own python (their shims 'import'
# them), so they MUST live in this venv — not pipx. phonenumbers is already core.
python -m pip install --quiet naminter ignorant || warn "naminter/ignorant install failed (those two tools will be unavailable)"
ok "naminter + ignorant installed into .venv"

# ---- 3. standalone OSINT CLI tools (OPTIONAL, best-effort via pipx) --------
if [ "$CORE_ONLY" -eq 1 ]; then
  warn "--core given: skipping optional CLI tools"
else
  say "Installing standalone OSINT CLI tools (best-effort; failures are non-fatal)"
  if ! command -v pipx >/dev/null 2>&1; then
    python -m pip install --quiet --user pipx 2>/dev/null && python -m pipx ensurepath >/dev/null 2>&1 || true
  fi
  PIPX="pipx"; command -v pipx >/dev/null 2>&1 || PIPX="python -m pipx"
  # package name -> what it provides (comment only)
  CLI_PKGS="sherlock-project maigret holehe theHarvester socialscan dnsrecon socid-extractor user-scanner linkook"
  ok_n=0; skip_n=0
  for pkg in $CLI_PKGS; do
    if $PIPX install "$pkg" >/dev/null 2>&1; then ok "$pkg"; ok_n=$((ok_n+1))
    else warn "$pkg (install failed — 'pipx install $pkg' by hand later)"; skip_n=$((skip_n+1)); fi
  done
  say "CLI tools: $ok_n installed, $skip_n skipped"

  # ---- exiftool (image metadata; binary, not pip) -------------------------
  if command -v exiftool >/dev/null 2>&1; then ok "exiftool already present"
  elif [ "$OS" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew install exiftool >/dev/null 2>&1 && ok "exiftool (brew)" || warn "exiftool brew install failed"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y libimage-exiftool-perl >/dev/null 2>&1 && ok "exiftool (apt)" || warn "exiftool apt install failed"
  else
    warn "exiftool not installed (macOS: 'brew install exiftool')"
  fi
fi

# ---- 4. .env scaffold ------------------------------------------------------
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env && ok ".env created from .env.example (add your keys)"
elif [ -f .env ]; then ok ".env already present"
else warn "no .env.example to copy (optional API keys)"; fi

# ---- 5. health check -------------------------------------------------------
say "Running the health gate"
if python scripts/health_check.py; then
  printf "\n${c_g}=== BOOTSTRAP COMPLETE — system is HEALTHY ===${c_0}\n"
  printf "Activate the venv in new shells with:  ${c_b}source .venv/bin/activate${c_0}\n"
  printf "Then drive it with your coding agent (see AGENTS.md) or run tools directly.\n"
else
  printf "\n${c_r}=== health check RED — see output above ===${c_0}\n"
  printf "Core deps are the likely cause; re-run 'python -m pip install -r requirements.txt' inside .venv.\n"
  exit 1
fi
