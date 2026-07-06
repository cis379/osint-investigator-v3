"""Rebuild the ontology visualization HTML from expanded ontology data."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # <repo>/src/tools/ -> <repo>
ONTOLOGY_DIR = BASE_DIR / "src" / "ontology"

# Load expanded data
with open(ONTOLOGY_DIR / "tools_registry_expanded.json", "r", encoding="utf-8") as f:
    registry = json.load(f)["tools"]

with open(ONTOLOGY_DIR / "pivot_map_expanded.json", "r", encoding="utf-8") as f:
    pivot_map = json.load(f)["pivot_map"]

with open(ONTOLOGY_DIR / "selector_types_expanded.json", "r", encoding="utf-8") as f:
    selector_types = json.load(f)["selector_types"]

# Color palette by category
CATEGORY_COLORS = {
    "identity": "#4CAF50",
    "infrastructure": "#FF9800",
    "financial": "#FF5722",
    "malware": "#795548",
    "security": "#F44336",
    "media": "#00BCD4",
    "search": "#9C27B0",
    "social": "#E91E63",
    "geospatial": "#8BC34A",
    "transport": "#3F51B5",
    "device": "#607D8B",
    "unknown": "#9E9E9E",
}

# Build selector type nodes
selector_nodes = []
for stype, info in selector_types.items():
    tool_count = info.get("tool_count", 0)
    if tool_count == 0:
        continue
    cat = info.get("category", "unknown")
    color = CATEGORY_COLORS.get(cat, "#9E9E9E")
    size = min(50, max(15, 10 + tool_count * 0.5))
    selector_nodes.append({
        "id": f"sel_{stype}",
        "label": stype,
        "title": f"{info.get('description', stype)}\\nTools: {tool_count}\\nYields: {', '.join(info.get('yields_to', [])[:10])}",
        "color": color,
        "shape": "dot",
        "size": size,
        "font": {"color": "#fff", "size": max(10, min(14, 8 + tool_count // 10))},
        "group": cat,
        "nodeKind": "selector",
        "selectorType": stype,
        "toolCount": tool_count,
        "category": cat,
    })

# Build tool category aggregate nodes (instead of individual tools - too many)
# Group tools by category
tool_categories = {}
for tool in registry:
    cat = tool.get("category", "uncategorized")
    if cat not in tool_categories:
        tool_categories[cat] = {
            "tools": [],
            "input_types": set(),
            "output_types": set(),
        }
    tool_categories[cat]["tools"].append(tool)
    tool_categories[cat]["input_types"].update(tool.get("input_types", []))
    tool_categories[cat]["output_types"].update(tool.get("output_types", []))

# For a cleaner viz, show individual tools only for categories with < 15 tools
# and aggregate nodes for larger categories
tool_nodes = []
edges = []
edge_set = set()

for cat, data in tool_categories.items():
    tools_in_cat = data["tools"]

    if len(tools_in_cat) <= 12:
        # Individual tool nodes
        for tool in tools_in_cat:
            tid = tool["id"]
            tool_nodes.append({
                "id": f"tool_{tid}",
                "label": tool["name"][:25],
                "title": f"{tool['name']}\\n{tool.get('description', '')[:80]}\\nMethod: {tool.get('method', '?')}\\nURL: {tool.get('url', '')}",
                "color": {"background": "#21262d", "border": "#58a6ff"},
                "shape": "box",
                "size": 10,
                "font": {"color": "#c9d1d9", "size": 9},
                "nodeKind": "tool",
                "category": cat,
            })
            for inp in tool.get("input_types", []):
                edge_key = f"sel_{inp}->tool_{tid}"
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({"from": f"sel_{inp}", "to": f"tool_{tid}", "arrows": "to", "color": {"color": "#30363d", "opacity": 0.5}, "width": 1})
            for out in tool.get("output_types", []):
                edge_key = f"tool_{tid}->sel_{out}"
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({"from": f"tool_{tid}", "to": f"sel_{out}", "arrows": "to", "color": {"color": "#56d364", "opacity": 0.4}, "width": 1, "dashes": True})
    else:
        # Aggregate category node
        tool_names = [t["name"] for t in tools_in_cat[:20]]
        tool_list = "\\n".join(tool_names)
        if len(tools_in_cat) > 20:
            tool_list += f"\\n... and {len(tools_in_cat) - 20} more"

        tool_nodes.append({
            "id": f"cat_{cat.replace(' ', '_').replace('>', '_')}",
            "label": f"{cat}\n({len(tools_in_cat)} tools)",
            "title": f"Category: {cat}\\nTools: {len(tools_in_cat)}\\n\\n{tool_list}",
            "color": {"background": "#1f3a5f", "border": "#58a6ff"},
            "shape": "box",
            "size": min(30, 12 + len(tools_in_cat) // 5),
            "font": {"color": "#79c0ff", "size": 10, "multi": True},
            "nodeKind": "category",
            "category": cat,
        })
        cat_id = f"cat_{cat.replace(' ', '_').replace('>', '_')}"
        for inp in data["input_types"]:
            edge_key = f"sel_{inp}->{cat_id}"
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({"from": f"sel_{inp}", "to": cat_id, "arrows": "to", "color": {"color": "#30363d", "opacity": 0.5}, "width": 2})
        for out in data["output_types"]:
            edge_key = f"{cat_id}->sel_{out}"
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({"from": cat_id, "to": f"sel_{out}", "arrows": "to", "color": {"color": "#56d364", "opacity": 0.4}, "width": 2, "dashes": True})

all_nodes = selector_nodes + tool_nodes

# Stats
stats = {
    "total_tools": len(registry),
    "selector_types": len([s for s in selector_nodes]),
    "tool_categories": len(tool_categories),
    "total_edges": len(edges),
}

viz_data = {
    "nodes": all_nodes,
    "edges": edges,
    "stats": stats,
    "category_colors": CATEGORY_COLORS,
    "pivot_map": pivot_map,
    "tool_categories": {k: {"count": len(v["tools"]), "tools": [t["name"] for t in v["tools"]]} for k, v in tool_categories.items()},
}

# Save viz data for the HTML to consume
with open(BASE_DIR / "ontology_viz" / "ontology_data.json", "w", encoding="utf-8") as f:
    json.dump(viz_data, f, indent=2, ensure_ascii=False)

print(f"Nodes: {len(all_nodes)} ({len(selector_nodes)} selectors + {len(tool_nodes)} tools/categories)")
print(f"Edges: {len(edges)}")
print(f"Saved ontology_data.json")
print(json.dumps(stats, indent=2))
