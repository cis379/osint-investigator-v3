"""Lightweight credential access for tools that need API keys.

Reads keys from the process environment, falling back to a `.env` file at the
project root (gitignored). Tools call get_key("ABUSEIPDB_API_KEY"); when a key is
absent they degrade gracefully (clear "needs key" message) rather than failing
silently. This is the foundation for the keyed (Tier-2+) tools.

.env format (KEY=value per line, # comments allowed):
    ETHERSCAN_API_KEY=abc123
    ABUSE_CH_API_KEY=xyz789
"""
import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
_loaded = False


def _load_env_once():
    global _loaded
    if _loaded:
        return
    _loaded = True
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            # don't clobber a real environment variable
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_key(name: str) -> str | None:
    """Return the credential value, or None if not configured."""
    _load_env_once()
    v = os.environ.get(name)
    return v if v else None


def has_key(name: str) -> bool:
    return get_key(name) is not None
