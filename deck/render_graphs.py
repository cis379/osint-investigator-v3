"""Render static PNGs from the REAL investigation graph (INV-20260626-001) for the deck.

Build-only (matplotlib + networkx). networkx is a system dep; matplotlib is build-only.
Run:  python deck/render_graphs.py   ->   deck/img/*.png
Produces:
  graph_overview.png    the full 119-node estate, colored by entity type (scale)
  graph_attribution.png the "who runs it" cluster: operator/company + corroborators (labeled)
  graph_tracker.png     one shared tracker ID linking multiple domains (the corroborator mechanism)
"""
import json, os
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(__file__)
CASE = os.path.join(HERE, "..", "investigations", "INV-20260626-001", "graph.json")
OUT = os.path.join(HERE, "img"); os.makedirs(OUT, exist_ok=True)

BG = "#0D1B2A"
TYPE_COLOR = {
    "domain": "#58A6FF", "ip_v4": "#3FB950", "tracker_id": "#BC8CFF", "company": "#D29922",
    "name": "#FF7B72", "favicon_hash": "#39C5CF", "email": "#F778BA", "phone": "#7EE787",
    "identifier": "#FFA657", "asn": "#A5D6FF", "location": "#D2A8FF", "url": "#79C0FF",
}
TIER_EDGE = {"highly_likely": ("#3FB950", 1.0, "solid"),
             "probable": ("#D29922", 0.8, "dashed"),
             "possible": ("#8B949E", 0.5, "dotted")}


def load():
    g = json.load(open(CASE, encoding="utf-8"))
    G = nx.DiGraph()
    idmap = {}
    for n in g["nodes"]:
        G.add_node(n["id"], value=n.get("value", ""), type=n.get("type", "?"),
                   conf=n.get("confidence", "possible"))
        idmap[n["id"]] = n
    for e in g["edges"]:
        if e["source"] in G and e["target"] in G:
            G.add_edge(e["source"], e["target"], rel=e.get("relationship", ""),
                       conf=e.get("confidence", "possible"))
    return G


def color_for(G, n):
    return TYPE_COLOR.get(G.nodes[n]["type"], "#8B949E")


def short(v, n=22):
    v = str(v)
    return v if len(v) <= n else v[:n - 1] + "…"


def fig(w=16, h=9):
    f, ax = plt.subplots(figsize=(w, h)); f.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off"); return f, ax


def draw_edges(G, pos, ax, edges=None, width_scale=1.0):
    for u, v, d in (edges if edges is not None else G.edges(data=True)):
        col, alpha, style = TIER_EDGE.get(d.get("conf", "possible"), TIER_EDGE["possible"])
        ax.annotate("", xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle="-", color=col, alpha=alpha,
                                    lw=0.6 * width_scale,
                                    linestyle=style, connectionstyle="arc3,rad=0.05"))


def legend_types(ax, types):
    handles = [Patch(facecolor=TYPE_COLOR.get(t, "#8B949E"), edgecolor="none", label=t)
               for t in types]
    lg = ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=11,
                   labelcolor="#E6EDF3", ncol=1, bbox_to_anchor=(0.0, 1.0))
    return lg


# ---------- 1. OVERVIEW (scale) ----------
def overview(G):
    f, ax = fig()
    pos = nx.spring_layout(G, k=0.55, iterations=120, seed=7)
    draw_edges(G, pos, ax, width_scale=1.0)
    deg = dict(G.degree())
    for n in G.nodes():
        sz = 40 + 26 * deg.get(n, 1)
        ax.scatter(*pos[n], s=sz, c=color_for(G, n), edgecolors="#0D1B2A", linewidths=0.5, zorder=3)
    present = [t for t in TYPE_COLOR if any(G.nodes[n]["type"] == t for n in G.nodes())]
    legend_types(ax, present)
    tier_handles = [Line2D([0], [0], color=c, lw=2, ls=("--" if k == "probable" else (":" if k == "possible" else "-")),
                    label=k.replace("_", " ")) for k, (c, a, s) in TIER_EDGE.items()]
    ax.legend(handles=tier_handles, loc="lower left", frameon=False, fontsize=11, labelcolor="#E6EDF3")
    ax.add_artist(legend_types(ax, present))
    ax.set_title("INV-20260626-001 — 119 entities / 170 relationships, auto-generated from one seed",
                 color="#E6EDF3", fontsize=17, pad=14)
    f.tight_layout(); p = os.path.join(OUT, "graph_overview.png")
    f.savefig(p, dpi=150, facecolor=BG); plt.close(f); print("wrote", p)


# ---------- 2. ATTRIBUTION cluster (who runs it) ----------
def attribution(G):
    id_keys = {"company", "name", "email", "phone", "identifier"}
    core = {n for n in G.nodes() if G.nodes[n]["type"] in id_keys}
    keep_rel = {"operated_by", "same_operator_as", "has_contact", "has_identifier", "registered_by"}
    sub = set(core)
    for u, v, d in G.edges(data=True):
        if d.get("rel") in keep_rel:
            sub.add(u); sub.add(v)
    # cap size for legibility: keep the giant component of the induced subgraph
    H = G.subgraph(sub).copy()
    if H.number_of_nodes() > 34:
        comps = sorted(nx.weakly_connected_components(H), key=len, reverse=True)
        H = G.subgraph(comps[0]).copy()
    f, ax = fig(16, 9)
    pos = nx.spring_layout(H, k=0.9, iterations=200, seed=3)
    draw_edges(H, pos, ax, edges=H.edges(data=True), width_scale=2.2)
    # Label ONLY the identity/attribution nodes (companies, names, emails, phones, IDs) so the
    # "who runs it" story is legible; domains stay as unlabeled blue dots = the estate they run.
    LABEL = {"company", "name", "email", "phone", "identifier"}
    for n in H.nodes():
        t = H.nodes[n]["type"]
        sz = 1100 if t in ("company", "name") else (520 if t in LABEL else 150)
        ax.scatter(*pos[n], s=sz, c=color_for(H, n), edgecolors="#0D1B2A", linewidths=1.0, zorder=3)
        if t in LABEL:
            ax.text(pos[n][0], pos[n][1] - 0.055, short(H.nodes[n]["value"], 26), color="#E6EDF3",
                    fontsize=10, ha="center", va="top", zorder=4,
                    fontweight=("bold" if t in ("company", "name") else "normal"))
    legend_types(ax, [t for t in TYPE_COLOR if any(H.nodes[n]["type"] == t for n in H.nodes())])
    ax.text(0.5, 0.015, "blue dots = the domain estate these entities operate (labels omitted for clarity)",
            transform=ax.transAxes, color="#8B949E", fontsize=11, ha="center")
    ax.set_title("Attribution cluster — 'who runs it': operator entities + independent corroborators",
                 color="#E6EDF3", fontsize=17, pad=14)
    f.tight_layout(); p = os.path.join(OUT, "graph_attribution.png")
    f.savefig(p, dpi=150, facecolor=BG); plt.close(f); print("wrote", p, "|", H.number_of_nodes(), "nodes")


# ---------- 3. TRACKER hub (the corroborator mechanism) ----------
def tracker(G):
    # tracker_id node with the most embeds_tracker connections
    trackers = [n for n in G.nodes() if G.nodes[n]["type"] == "tracker_id"]
    best, best_deg = None, -1
    for t in trackers:
        d = G.in_degree(t) + G.out_degree(t)
        if d > best_deg:
            best, best_deg = t, d
    if best is None:
        print("no tracker node"); return
    neigh = set(G.predecessors(best)) | set(G.successors(best)) | {best}
    H = G.subgraph(neigh).copy()
    f, ax = fig(15, 9)
    pos = nx.spring_layout(H, k=1.2, iterations=200, seed=5)
    draw_edges(H, pos, ax, edges=H.edges(data=True), width_scale=2.5)
    for n in H.nodes():
        is_t = H.nodes[n]["type"] == "tracker_id"
        ax.scatter(*pos[n], s=(1400 if is_t else 420), c=color_for(H, n),
                   edgecolors="#0D1B2A", linewidths=1.0, zorder=3)
        ax.text(pos[n][0], pos[n][1] - 0.07, short(H.nodes[n]["value"], 28), color="#E6EDF3",
                fontsize=(11 if is_t else 8.5), ha="center", va="top",
                fontweight=("bold" if is_t else "normal"), zorder=4)
    legend_types(ax, [t for t in TYPE_COLOR if any(H.nodes[n]["type"] == t for n in H.nodes())])
    val = G.nodes[best]["value"]
    ax.set_title(f"One shared tracker ID ({val}) links {H.number_of_nodes()-1} domains — the ownership corroborator",
                 color="#E6EDF3", fontsize=16, pad=14)
    f.tight_layout(); p = os.path.join(OUT, "graph_tracker.png")
    f.savefig(p, dpi=150, facecolor=BG); plt.close(f); print("wrote", p, "|", H.number_of_nodes(), "nodes")


if __name__ == "__main__":
    G = load()
    print("loaded", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges")
    overview(G); attribution(G); tracker(G)
    print("done -> deck/img/")
