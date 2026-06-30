import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from .confidence import normalize as _conf_norm, humanize as _conf_human


class InvestigationGraph:
    def __init__(self, graph_file: str | None = None):
        self.graph = nx.DiGraph()
        self.graph_file = graph_file
        if graph_file and Path(graph_file).exists():
            self.load(graph_file)

    def _node_id(self, value: str, entity_type: str) -> str:
        return hashlib.sha256(f"{entity_type}:{value}".encode()).hexdigest()[:16]

    def add_entity(self, value: str, entity_type: str, source_tool: str,
                   depth: int = 0, confidence: str = "highly_likely",
                   citation: str = "", metadata: dict | None = None) -> str:
        node_id = self._node_id(value, entity_type)

        if self.graph.has_node(node_id):
            existing = self.graph.nodes[node_id]
            sources = existing.get("source_tools", [])
            if source_tool not in sources:
                sources.append(source_tool)
            existing["source_tools"] = sources
            if metadata:
                existing.setdefault("metadata", {}).update(metadata)
            # Honor a re-commit's RE-GRADE. The supervisor (the only caller of add_entity via
            # graph_commit) re-tiers deliberately — a corroboration UPGRADE or a red-team
            # DOWN-tier. Without this the re-grade was a silent no-op, defeating both the
            # red-team gate (CAPABILITY-LOCK #4/#8) and the corroboration chain G14/A1 exist for.
            existing["confidence"] = confidence
            if citation:
                existing["citation"] = citation
            existing["depth"] = min(existing.get("depth", depth), depth)
            return node_id

        self.graph.add_node(node_id, **{
            "value": value,
            "type": entity_type,
            "source_tools": [source_tool],
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "depth": depth,
            "confidence": confidence,
            "citation": citation,
            "metadata": metadata or {},
        })
        return node_id

    def add_relationship(self, source_value: str, source_type: str,
                         target_value: str, target_type: str,
                         relationship: str, source_tool: str,
                         confidence: str = "highly_likely", citation: str = ""):
        src_id = self._node_id(source_value, source_type)
        tgt_id = self._node_id(target_value, target_type)

        if not self.graph.has_node(src_id):
            self.add_entity(source_value, source_type, source_tool)
        if not self.graph.has_node(tgt_id):
            self.add_entity(target_value, target_type, source_tool)

        self.graph.add_edge(src_id, tgt_id, **{
            "relationship": relationship,
            "source_tool": source_tool,
            "confidence": confidence,
            "citation": citation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    def get_entity(self, value: str, entity_type: str) -> dict | None:
        node_id = self._node_id(value, entity_type)
        if self.graph.has_node(node_id):
            data = dict(self.graph.nodes[node_id])
            data["id"] = node_id
            return data
        return None

    def get_neighbors(self, value: str, entity_type: str) -> list[dict]:
        node_id = self._node_id(value, entity_type)
        if not self.graph.has_node(node_id):
            return []
        neighbors = []
        for neighbor_id in self.graph.neighbors(node_id):
            data = dict(self.graph.nodes[neighbor_id])
            data["id"] = neighbor_id
            edge_data = self.graph.edges[node_id, neighbor_id]
            data["edge"] = dict(edge_data)
            neighbors.append(data)
        return neighbors

    def get_all_entities(self) -> list[dict]:
        entities = []
        for node_id, data in self.graph.nodes(data=True):
            entity = dict(data)
            entity["id"] = node_id
            entities.append(entity)
        return entities

    def get_all_relationships(self) -> list[dict]:
        rels = []
        for src, tgt, data in self.graph.edges(data=True):
            rel = dict(data)
            rel["source"] = src
            rel["target"] = tgt
            rel["source_value"] = self.graph.nodes[src].get("value", "")
            rel["target_value"] = self.graph.nodes[tgt].get("value", "")
            rels.append(rel)
        return rels

    def get_entities_by_type(self, entity_type: str) -> list[dict]:
        return [e for e in self.get_all_entities() if e.get("type") == entity_type]

    def get_stats(self) -> dict:
        type_counts = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "entities_by_type": type_counts,
        }

    def save(self, path: str | None = None):
        save_path = path or self.graph_file
        if not save_path:
            raise ValueError("No save path specified")

        data = {
            "nodes": [],
            "edges": [],
        }
        for node_id, node_data in self.graph.nodes(data=True):
            entry = dict(node_data)
            entry["id"] = node_id
            data["nodes"].append(entry)

        for src, tgt, edge_data in self.graph.edges(data=True):
            entry = dict(edge_data)
            entry["source"] = src
            entry["target"] = tgt
            data["edges"].append(entry)

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.graph.clear()
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            self.graph.add_node(node_id, **node)

        for edge in data.get("edges", []):
            src = edge.pop("source")
            tgt = edge.pop("target")
            self.graph.add_edge(src, tgt, **edge)

    def export_for_visualization(self) -> dict:
        type_colors = {
            "username": "#4CAF50",
            "email": "#2196F3",
            "domain": "#FF9800",
            "ip_v4": "#F44336",
            "ip_v6": "#F44336",
            "phone": "#9C27B0",
            "crypto_btc": "#FF5722",
            "crypto_eth": "#607D8B",
            "url": "#00BCD4",
            "hash_md5": "#795548",
            "hash_sha1": "#795548",
            "hash_sha256": "#795548",
            "name": "#8BC34A",
            "company": "#3F51B5",
            "asn": "#CDDC39",
            "telegram_handle": "#009688",
            "discord_id": "#7289DA",
        }

        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            entity_type = data.get("type", "unknown")
            value = data.get("value", node_id)
            label = value
            if len(label) > 40:
                label = label[:37] + "..."
            depth = data.get("depth", 0)
            confidence = _conf_norm(data.get("confidence"), default="highly_likely")
            sources = ", ".join(data.get("source_tools", []))

            border_color = type_colors.get(entity_type, "#9E9E9E")
            bg_color = border_color + "33"
            # Weak tiers (probable/possible) get a dashed border so strong
            # (highly_likely) entities stand out. "possible" is the weakest — kept
            # visible as a pivot, not hidden — see graph_commit.py.
            border_style = confidence in ("probable", "possible")

            nodes.append({
                "id": node_id,
                "label": label,
                "title": f"Type: {entity_type}\nValue: {value}\nConfidence: {_conf_human(confidence)}\nSource: {sources}\nDepth: {depth}\nCitation: {data.get('citation', '')}",
                "color": {
                    "background": bg_color,
                    "border": border_color,
                    "highlight": {"background": border_color, "border": "#ffffff"},
                    "hover": {"background": border_color, "border": "#ffffff"},
                },
                "group": entity_type,
                "entityValue": value,
                "type": entity_type,
                "shape": "dot",
                "size": 30 if depth == 0 else max(18, 26 - depth * 3),
                "font": {
                    "color": "#e6edf3",
                    "size": 14 if depth == 0 else 12,
                    "strokeWidth": 3,
                    "strokeColor": "#0d1117",
                },
                "borderWidth": 3 if depth == 0 else 2,
                "borderWidthSelected": 4,
                "shapeProperties": {"borderDashes": [5, 5] if border_style else False},
                "confidence": confidence,
                "citation": data.get("citation", ""),
                "source_tools": data.get("source_tools", []),
                "depth": depth,
            })

        edges = []
        for src, tgt, data in self.graph.edges(data=True):
            conf = _conf_norm(data.get("confidence"), default="highly_likely")
            # 3-tier edge styling: highly_likely (strong/solid) -> probable (dashed amber)
            # -> possible (faint dotted). Weak links stay visible, just clearly weaker.
            edge_style = {
                "highly_likely": {"color": "#8b949e", "opacity": 0.9, "width": 2, "dashes": False},
                "probable": {"color": "#f0883e", "opacity": 0.8, "width": 1, "dashes": True},
                "possible": {"color": "#b06a2c", "opacity": 0.45, "width": 1, "dashes": [2, 4]},
            }.get(conf, {"color": "#f0883e", "opacity": 0.8, "width": 1, "dashes": True})
            edges.append({
                "from": src,
                "to": tgt,
                "label": data.get("relationship", ""),
                "title": f"Relationship: {data.get('relationship', '')}\nTool: {data.get('source_tool', '')}\nConfidence: {conf}\nCitation: {data.get('citation', '')}",
                "arrows": "to",
                "color": {"color": edge_style["color"], "opacity": edge_style["opacity"]},
                "width": edge_style["width"],
                "dashes": edge_style["dashes"],
                "font": {"color": "#8b949e", "size": 11, "strokeWidth": 2, "strokeColor": "#0d1117"},
            })

        return {"nodes": nodes, "edges": edges, "type_colors": type_colors}
