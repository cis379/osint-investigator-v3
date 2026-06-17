import json
from pathlib import Path
from .database import InvestigationGraph


def generate_investigation_html(graph: InvestigationGraph, output_path: str, title: str = "Investigation Graph"):
    viz_data = graph.export_for_visualization()
    stats = graph.get_stats()
    entities_by_type = stats.get("entities_by_type", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; }}
        #header {{
            background: #161b22; border-bottom: 1px solid #30363d;
            padding: 12px 24px; display: flex; align-items: center; justify-content: space-between;
        }}
        #header h1 {{ font-size: 18px; color: #58a6ff; font-weight: 600; }}
        #header .stats {{ font-size: 13px; color: #8b949e; }}
        #container {{ display: flex; height: calc(100vh - 52px); }}
        #graph {{ flex: 1; background: #0d1117; position: relative; }}
        #sidebar {{
            width: 340px; background: #161b22; border-left: 1px solid #30363d;
            padding: 16px; overflow-y: auto;
        }}
        #sidebar h3 {{ font-size: 13px; color: #58a6ff; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .legend-item {{
            display: flex; align-items: center; margin-bottom: 5px; font-size: 13px;
            cursor: pointer; padding: 3px 6px; border-radius: 4px;
        }}
        .legend-item:hover {{ background: #21262d; }}
        .legend-item .count {{ color: #8b949e; margin-left: auto; font-size: 11px; }}
        .legend-dot {{
            width: 14px; height: 14px; border-radius: 50%; margin-right: 10px; flex-shrink: 0;
            border: 2px solid transparent;
        }}
        #node-details {{
            margin-top: 16px; padding-top: 16px; border-top: 1px solid #30363d;
        }}
        .detail-row {{
            font-size: 12px; margin-bottom: 6px; color: #8b949e;
            line-height: 1.5; word-break: break-all;
        }}
        .detail-row strong {{ color: #e6edf3; display: inline-block; min-width: 80px; }}
        .detail-value {{ color: #c9d1d9; }}
        .detail-badge {{
            display: inline-block; padding: 1px 8px; border-radius: 10px;
            font-size: 11px; font-weight: 600;
        }}
        .badge-confirmed {{ background: #238636; color: #fff; }}
        .badge-probable {{ background: #9e6a03; color: #fff; }}
        .badge-possible {{ background: #6e4014; color: #fff; }}
        #search-box {{
            width: 100%; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d;
            border-radius: 6px; color: #c9d1d9; font-size: 13px; margin-bottom: 16px;
        }}
        #search-box:focus {{ border-color: #58a6ff; outline: none; }}
        .filter-btn {{
            display: inline-block; padding: 4px 12px; margin: 2px; border-radius: 12px;
            font-size: 11px; cursor: pointer; border: 1px solid #30363d; background: #21262d;
            color: #c9d1d9; transition: all 0.15s;
        }}
        .filter-btn.active {{ border-color: #58a6ff; background: #1f3a5f; color: #79c0ff; }}
        .filter-btn:hover {{ border-color: #58a6ff; }}
        .section {{ margin-bottom: 20px; }}
        #controls {{
            position: absolute; top: 12px; left: 12px; z-index: 10;
            display: flex; gap: 6px;
        }}
        .ctrl-btn {{
            padding: 6px 12px; background: #21262d; border: 1px solid #30363d;
            border-radius: 6px; color: #c9d1d9; cursor: pointer; font-size: 12px;
        }}
        .ctrl-btn:hover {{ background: #30363d; border-color: #58a6ff; }}
        #relationships-list {{ margin-top: 16px; padding-top: 16px; border-top: 1px solid #30363d; }}
        .rel-row {{
            font-size: 11px; color: #8b949e; padding: 4px 0; border-bottom: 1px solid #21262d;
            line-height: 1.4;
        }}
        .rel-row .rel-type {{ color: #f0883e; font-weight: 600; }}
        .rel-row .rel-src {{ color: #79c0ff; }}
        .rel-row .rel-tgt {{ color: #7ee787; }}
    </style>
</head>
<body>
    <div id="header">
        <h1>{title}</h1>
        <div class="stats">
            Entities: {stats['total_entities']} | Relationships: {stats['total_relationships']}
        </div>
    </div>
    <div id="container">
        <div id="graph">
            <div id="controls">
                <button class="ctrl-btn" onclick="network.fit()">Fit All</button>
                <button class="ctrl-btn" onclick="network.stabilize(100)">Re-layout</button>
                <button class="ctrl-btn" onclick="togglePhysics()">Toggle Physics</button>
            </div>
        </div>
        <div id="sidebar">
            <div class="section">
                <input type="text" id="search-box" placeholder="Search entities..." />
            </div>
            <div class="section">
                <h3>Filter by Type</h3>
                <div id="filters"></div>
            </div>
            <div class="section">
                <h3>Legend</h3>
                <div id="legend"></div>
            </div>
            <div id="node-details">
                <h3>Entity Details</h3>
                <p class="detail-row" style="color:#484f58;">Click a node to view details</p>
            </div>
            <div id="relationships-list">
                <h3>Relationships</h3>
                <div id="rel-content"></div>
            </div>
        </div>
    </div>
    <script>
        const graphData = {json.dumps(viz_data)};
        const nodes = new vis.DataSet(graphData.nodes);
        const edges = new vis.DataSet(graphData.edges);

        let physicsEnabled = true;

        const container = document.getElementById('graph');
        const network = new vis.Network(container, {{ nodes, edges }}, {{
            physics: {{
                forceAtlas2Based: {{
                    gravitationalConstant: -80,
                    centralGravity: 0.005,
                    springLength: 150,
                    springConstant: 0.06,
                    damping: 0.4,
                }},
                solver: 'forceAtlas2Based',
                stabilization: {{ iterations: 200 }},
                maxVelocity: 30,
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 150,
                zoomView: true,
                dragView: true,
                multiselect: true,
            }},
            edges: {{
                font: {{ size: 11, color: '#8b949e', strokeWidth: 2, strokeColor: '#0d1117', align: 'middle' }},
                smooth: {{ type: 'curvedCW', roundness: 0.15 }},
                length: 200,
            }},
            nodes: {{
                font: {{ color: '#e6edf3', size: 13, strokeWidth: 3, strokeColor: '#0d1117' }},
                borderWidth: 2,
                borderWidthSelected: 4,
                chosen: {{
                    node: function(values) {{ values.size *= 1.2; }},
                }},
            }},
        }});

        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
        }}

        // Legend with counts
        const legendEl = document.getElementById('legend');
        const typeCounts = {json.dumps(entities_by_type)};
        const types = Object.keys(typeCounts).sort((a, b) => typeCounts[b] - typeCounts[a]);
        types.forEach(type => {{
            const color = graphData.type_colors[type] || '#9E9E9E';
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-dot" style="background:${{color}}"></div>${{type}}<span class="count">${{typeCounts[type]}}</span>`;
            item.onclick = () => {{
                const matchingNodes = graphData.nodes.filter(n => n.type === type);
                if (matchingNodes.length > 0) {{
                    network.selectNodes(matchingNodes.map(n => n.id));
                    network.fit({{ nodes: matchingNodes.map(n => n.id), animation: true }});
                }}
            }};
            legendEl.appendChild(item);
        }});

        // Filters
        const filtersEl = document.getElementById('filters');
        let activeFilters = new Set(types);
        types.forEach(type => {{
            const btn = document.createElement('span');
            btn.className = 'filter-btn active';
            btn.textContent = type + ' (' + typeCounts[type] + ')';
            btn.onclick = () => {{
                if (activeFilters.has(type)) {{
                    activeFilters.delete(type);
                    btn.classList.remove('active');
                }} else {{
                    activeFilters.add(type);
                    btn.classList.add('active');
                }}
                applyFilters();
            }};
            filtersEl.appendChild(btn);
        }});

        function applyFilters() {{
            const updates = graphData.nodes.map(n => ({{
                id: n.id,
                hidden: !activeFilters.has(n.type),
            }}));
            nodes.update(updates);
        }}

        // Search
        document.getElementById('search-box').addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase();
            if (!query) {{
                nodes.update(graphData.nodes.map(n => ({{ id: n.id, hidden: !activeFilters.has(n.type) }})));
                return;
            }}
            const updates = graphData.nodes.map(n => ({{
                id: n.id,
                hidden: !(n.entityValue.toLowerCase().includes(query) || n.type.toLowerCase().includes(query)),
            }}));
            nodes.update(updates);
        }});

        // Node click details
        function badgeClass(conf) {{
            if (conf === 'confirmed') return 'badge-confirmed';
            if (conf === 'probable') return 'badge-probable';
            return 'badge-possible';
        }}

        network.on('click', (params) => {{
            const detailsEl = document.getElementById('node-details');
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = graphData.nodes.find(n => n.id === nodeId);
                if (node) {{
                    const conf = node.confidence || 'confirmed';
                    const sources = (node.source_tools || []).join(', ');
                    detailsEl.innerHTML = `
                        <h3>Entity Details</h3>
                        <div class="detail-row"><strong>Value:</strong> <span class="detail-value">${{node.entityValue}}</span></div>
                        <div class="detail-row"><strong>Type:</strong> <span class="detail-value">${{node.type}}</span></div>
                        <div class="detail-row"><strong>Confidence:</strong> <span class="detail-badge ${{badgeClass(conf)}}">${{conf}}</span></div>
                        <div class="detail-row"><strong>Sources:</strong> <span class="detail-value">${{sources}}</span></div>
                        <div class="detail-row"><strong>Depth:</strong> <span class="detail-value">${{node.depth}}</span></div>
                        <div class="detail-row"><strong>Citation:</strong> <span class="detail-value">${{node.citation || 'N/A'}}</span></div>
                    `;

                    // Show connected relationships
                    const connectedEdges = graphData.edges.filter(e => e.from === nodeId || e.to === nodeId);
                    if (connectedEdges.length > 0) {{
                        let relHtml = '<h3 style="margin-top:12px;">Connected</h3>';
                        connectedEdges.forEach(edge => {{
                            const srcNode = graphData.nodes.find(n => n.id === edge.from);
                            const tgtNode = graphData.nodes.find(n => n.id === edge.to);
                            relHtml += `<div class="rel-row"><span class="rel-src">${{srcNode ? srcNode.entityValue : '?'}}</span> <span class="rel-type">${{edge.label}}</span> <span class="rel-tgt">${{tgtNode ? tgtNode.entityValue : '?'}}</span></div>`;
                        }});
                        detailsEl.innerHTML += relHtml;
                    }}
                }}
            }} else {{
                detailsEl.innerHTML = '<h3>Entity Details</h3><p class="detail-row" style="color:#484f58;">Click a node to view details</p>';
            }}
        }});

        // Relationships list
        const relContent = document.getElementById('rel-content');
        graphData.edges.forEach(edge => {{
            const srcNode = graphData.nodes.find(n => n.id === edge.from);
            const tgtNode = graphData.nodes.find(n => n.id === edge.to);
            relContent.innerHTML += `<div class="rel-row"><span class="rel-src">${{srcNode ? srcNode.entityValue : '?'}}</span> &rarr; <span class="rel-type">${{edge.label}}</span> &rarr; <span class="rel-tgt">${{tgtNode ? tgtNode.entityValue : '?'}}</span></div>`;
        }});

        // Double-click to focus on a node's neighborhood
        network.on('doubleClick', (params) => {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const connectedNodes = network.getConnectedNodes(nodeId);
                connectedNodes.push(nodeId);
                network.fit({{ nodes: connectedNodes, animation: true }});
            }}
        }});
    </script>
</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
