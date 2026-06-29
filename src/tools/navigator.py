"""OSINT Navigator (Indicator Media) — RAG tool-DISCOVERY client.

A keyed helper used by the RED TEAM (per-investigation coverage-gap check) and the
SYSTEM MANAGER (tool discovery / ontology freshness). It RECOMMENDS tools from a
natural-language query — it does NOT collect data, so its output is a COMPLETENESS
SIGNAL, never a finding/entity.

Deliberately NOT registered in the registry / pivot_map: it is not a collection tool and
the supervisor must not route to it. The red team / Manager call `query_navigator()`
directly. Reads `OSINT_NAVIGATOR_API_KEY` from `.env` via credentials.get_key and degrades
gracefully when the key is unset, the service errors, or the daily budget is spent.

Budget: ~50 queries/day (member). Query SPARINGLY — at most once per investigation.
Verified endpoint: POST https://navigator.indicator.media/api/query  (Bearer auth).
"""
import requests

from .credentials import get_key

_ENDPOINT = "https://navigator.indicator.media/api/query"
_TIMEOUT = 30


def query_navigator(question: str) -> dict:
    """Ask Navigator which tools/categories fit a task.

    Returns a dict: {ok, answer, tools:[{tool_name,category,tool_url,...}], categories:[...],
    rate_limit:{queries_remaining,limit,...}, error}. On any failure ok=False with a clear
    `error` and empty tools — callers skip gracefully (never hard-fail a review over this)."""
    key = get_key("OSINT_NAVIGATOR_API_KEY")
    if not key:
        return {"ok": False, "error": "OSINT_NAVIGATOR_API_KEY not configured (.env)",
                "answer": "", "tools": [], "categories": [], "rate_limit": {}}
    try:
        r = requests.post(_ENDPOINT, json={"query": question},
                          headers={"Authorization": f"Bearer {key}",
                                   "Content-Type": "application/json"},
                          timeout=_TIMEOUT)
    except requests.RequestException as e:
        return {"ok": False, "error": f"Navigator request failed: {e}",
                "answer": "", "tools": [], "categories": [], "rate_limit": {}}
    if r.status_code != 200:
        return {"ok": False, "error": f"Navigator HTTP {r.status_code}: {r.text[:200]}",
                "answer": "", "tools": [], "categories": [], "rate_limit": {}}
    try:
        data = r.json()
    except ValueError:
        return {"ok": False, "error": "Navigator returned non-JSON",
                "answer": "", "tools": [], "categories": [], "rate_limit": {}}
    tools = data.get("tools") or []
    cats = sorted({t.get("category") for t in tools if t.get("category")})
    return {"ok": True, "error": "", "answer": data.get("answer", ""),
            "tools": tools, "categories": cats, "rate_limit": data.get("rate_limit") or {}}
