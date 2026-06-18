import json
from pathlib import Path
from .base import BaseTool

from . import username_tools
from . import email_tools
from . import domain_tools
from . import ip_tools
from . import phone_tools
from . import crypto_tools
from . import social_tools
from . import image_tools
from . import paste_tools
from . import name_tools

ALL_TOOL_MODULES = [
    username_tools,
    email_tools,
    domain_tools,
    ip_tools,
    phone_tools,
    crypto_tools,
    social_tools,
    image_tools,
    paste_tools,
    name_tools,
]

_tool_instances: dict[str, BaseTool] = {}


def _load_tools():
    if _tool_instances:
        return
    for module in ALL_TOOL_MODULES:
        for tool in getattr(module, "TOOLS", []):
            _tool_instances[tool.name] = tool


def get_all_tools() -> dict[str, BaseTool]:
    _load_tools()
    return _tool_instances


def get_tool(name: str) -> BaseTool | None:
    _load_tools()
    return _tool_instances.get(name)


def get_tools_for_selector(selector_type: str) -> list[BaseTool]:
    _load_tools()
    ontology_path = Path(__file__).parent.parent / "ontology" / "pivot_map.json"
    with open(ontology_path, "r", encoding="utf-8") as f:
        pivot_map = json.load(f)["pivot_map"]

    if selector_type not in pivot_map:
        return []

    tool_ids = pivot_map[selector_type]["tools"]
    return [_tool_instances[tid] for tid in tool_ids if tid in _tool_instances]


def get_selector_capability(selector_type: str) -> dict:
    """Honest view of a selector type: what ACTUALLY runs vs. the catalog claim.

    Recomputed from the live registry (not the annotated fields), so it is always
    truthful even if pivot_map's annotations are stale.
    """
    _load_tools()
    ontology_path = Path(__file__).parent.parent / "ontology" / "pivot_map.json"
    with open(ontology_path, "r", encoding="utf-8") as f:
        pivot_map = json.load(f)["pivot_map"]

    if selector_type not in pivot_map:
        return {"selector_type": selector_type, "exists": False,
                "implemented": [], "implemented_count": 0, "catalog_count": 0, "yields": []}

    entry = pivot_map[selector_type]
    impl = [tid for tid in entry.get("tools", []) if tid in _tool_instances]
    return {
        "selector_type": selector_type,
        "exists": True,
        "implemented": impl,
        "implemented_count": len(impl),
        "catalog_count": entry.get("tool_count", len(entry.get("tools", []))),
        "yields": entry.get("yields", []),
    }


def get_web_search_profile(selector_type: str, selector: str | None = None) -> dict:
    """Web-search line profile for a selector type (the SEPARATE collection line,
    distinct from structured tools). Returns the strategy, seed query templates,
    fetch priorities, and extract targets that guide the web-search collector skill.

    If `selector` is given, the templates are rendered into ready-to-run `queries`
    ({selector}, and for emails {local}/{domain}).
    """
    path = Path(__file__).parent.parent / "ontology" / "web_search.json"
    with open(path, "r", encoding="utf-8") as f:
        profiles = json.load(f)["web_search"]

    prof = profiles.get(selector_type)
    if not prof:
        return {"selector_type": selector_type, "searchable": False}

    prof = dict(prof)
    prof["selector_type"] = selector_type
    if selector is not None:
        local, domain = selector, selector
        if "@" in selector:
            local, _, domain = selector.partition("@")
        rendered = []
        for t in prof.get("query_templates", []):
            try:
                rendered.append(t.format(selector=selector, domain=domain, local=local))
            except (KeyError, IndexError, ValueError):
                rendered.append(t)
        prof["queries"] = rendered
    return prof


def run_tool(tool_name: str, selector: str, selector_type: str):
    tool = get_tool(tool_name)
    if not tool:
        return None
    return tool.query(selector, selector_type)


def run_all_tools_for_selector(selector: str, selector_type: str) -> list:
    tools = get_tools_for_selector(selector_type)
    results = []
    for tool in tools:
        result = tool.query(selector, selector_type)
        results.append(result)
    return results


def check_tool_availability() -> dict[str, bool]:
    _load_tools()
    status = {}
    for name, tool in _tool_instances.items():
        if tool.method in ("api", "library", "generator"):
            status[name] = True
        else:
            status[name] = tool.check_installed()
    return status


if __name__ == "__main__":
    print("=== Tool Registry ===")
    availability = check_tool_availability()
    for name, available in sorted(availability.items()):
        status = "READY" if available else "NOT INSTALLED"
        tool = get_tool(name)
        print(f"  {name:25s} [{status:15s}] inputs: {tool.input_types}  outputs: {tool.output_types}")
