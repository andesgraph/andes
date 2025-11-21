# -*- coding: utf-8 -*-
"""
visualizar_grafo.py
-------------------
Ejecución directa:    python visualizar_grafo.py

Qué hace por defecto:
- Lee data/grafo_unificado.json (property-graph con 'nodes' y 'edges')
- Toma SOLO la componente conexa más grande (LCC)
- Dibuja nodos en dorado (gold), sin borde
- Aristas delgadas y discretas
- Resalta en CRIMSON (y más grandes) los nodos de la festividad de Qoylluriti
  y la Virgen del Carmen de Paucartambo (detecta por nombre exacto o por palabras clave)
- Etiqueta los 40 nodos de mayor grado (si los especiales no están en ese top, igual se etiquetan)
- Exporta PNG (300 DPI) y SVG en la carpeta data/

Requisitos:
    pip install networkx matplotlib
"""

import json
from pathlib import Path
from math import sqrt
import warnings

import matplotlib.pyplot as plt
import networkx as nx

# -------- Config por defecto --------
INPUT_JSON = Path("data/grafo_unificado.json")
OUTPUT_PREFIX = INPUT_JSON.with_suffix("").parent / (INPUT_JSON.stem + "_viz")

TOP_LABELS = 40        # nº de nodos etiquetados por grado
DPI = 300              # alta resolución
FIGSIZE = (14, 10)     # tamaño de figura

# Labels "ideales" esperados; si no coinciden exacto, se usa un fallback por keywords
DEFAULT_SPECIAL_LABELS = {
    "Festividad de Qoylluriti",
    "Virgen del Carmen de Paucartambo",
}

# Fallback por palabras clave (case-insensitive, búsqueda por substring)
SPECIAL_KEYWORDS = [
    "qoyll", "qoyllur", "qoyllor",        # variantes comunes
    "virgen del carmen", "carmen",
    "paucartambo",
]


def load_property_graph(json_path: Path) -> nx.MultiDiGraph:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    G = nx.MultiDiGraph()
    for n in data.get("nodes", []):
        nid = n.get("id")
        if nid:
            G.add_node(nid, label=n.get("label") or "")
    for e in data.get("edges", []):
        src, dst = e.get("source"), e.get("target")
        if src and dst:
            # conservamos metadata mínima
            G.add_edge(src, dst, property_label=e.get("property_label"))
    return G


def to_simple_graph(Gmulti: nx.MultiDiGraph) -> nx.Graph:
    """Colapsa MultiDiGraph -> Graph sumando pesos por aristas paralelas."""
    Gsimple = nx.Graph()
    Gsimple.add_nodes_from(Gmulti.nodes(data=True))
    for u, v, _k in Gmulti.edges(keys=True):
        if Gsimple.has_edge(u, v):
            Gsimple[u][v]["weight"] += 1
        else:
            Gsimple.add_edge(u, v, weight=1)
    return Gsimple


def largest_connected_component(G: nx.Graph) -> nx.Graph:
    """Devuelve la LCC (tratando como no dirigido)."""
    if G.number_of_nodes() == 0:
        return G
    H = nx.Graph(G)
    comps = list(nx.connected_components(H))
    if not comps:
        return G
    giant = max(comps, key=len)
    return H.subgraph(giant).copy()


def score_node_size(deg, base=120, scale=35, exp=1.15, min_sz=60, max_sz=1200):
    """Tamaño de nodo según grado, en un rango controlado."""
    val = base + scale * (deg ** exp)
    return max(min_sz, min(max_sz, int(val)))


def detect_special_nodes(G: nx.Graph) -> set:
    """
    Devuelve el conjunto de nodos "especiales".
    1) Intenta match EXACTO por label (DEFAULT_SPECIAL_LABELS)
    2) Si no encuentra alguno, activa fallback por SPECIAL_KEYWORDS (substring, case-insensitive)
    """
    by_label = {n for n, d in G.nodes(data=True) if (d.get("label") or "") in DEFAULT_SPECIAL_LABELS}
    # si ya encontró ambos (o todos los que existan), retorna
    if len(by_label) >= 2:
        return by_label

    # fallback por keywords
    lower_kw = [k.lower() for k in SPECIAL_KEYWORDS]
    by_kw = set(by_label)
    for n, d in G.nodes(data=True):
        label = (d.get("label") or "").lower()
        if any(k in label for k in lower_kw):
            by_kw.add(n)
    return by_kw


def pick_labels(G: nx.Graph, top_k=TOP_LABELS, specials=frozenset()):
    """Elige etiquetas: top-k por grado + TODOS los especiales."""
    deg = dict(G.degree())
    top_nodes = {n for n, _ in sorted(deg.items(), key=lambda x: x[1], reverse=True)[:top_k]}
    return top_nodes | set(specials)


def truncate(s: str, maxlen=36):
    s = s or ""
    return (s[: maxlen - 1] + "…") if len(s) > maxlen else s


def draw_graph(G: nx.Graph, output_prefix: Path):
    if G.number_of_nodes() == 0:
        warnings.warn("Grafo vacío; no se generará imagen.")
        return

    # Layout spring con separación razonable
    n = G.number_of_nodes()
    k = 1.2 / max(1.0, sqrt(n))
    pos = nx.spring_layout(G, k=k, seed=42, iterations=200)

    deg = dict(G.degree())
    weights = [G[u][v].get("weight", 1) for u, v in G.edges()]
    max_w = max(weights) if weights else 1

    # Nodos especiales detectados (por label exacto o keywords)
    special_nodes = detect_special_nodes(G)

    # Estética
    node_sizes = []
    node_colors = []
    for node, data in G.nodes(data=True):
        label = data.get("label") or ""
        size = score_node_size(deg.get(node, 0))
        if node in special_nodes:
            size = int(size * 1.8)  # más grandes
            color = "crimson"
        else:
            color = "gold"
        node_sizes.append(size)
        node_colors.append(color)

    # Aristas MUY delgadas y discretas
    edge_widths = [0.25 + 0.9 * (w / max_w) for w in weights]

    # Dibujo
    plt.figure(figsize=FIGSIZE, dpi=DPI)
    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        alpha=0.22,
        edge_color="gray"
    )
    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.95,
        linewidths=0  # sin bordes
    )

    # Etiquetas: top-k por grado + todos los especiales (siempre)
    label_nodes = pick_labels(G, top_k=TOP_LABELS, specials=special_nodes)
    labels = {n: truncate(d.get("label") or n, 34) for n, d in G.nodes(data=True) if n in label_nodes}

    nx.draw_networkx_labels(
        G, pos, labels=labels,
        font_size=9,
        font_weight="regular",
        verticalalignment="center",
        horizontalalignment="center",
        bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="black", alpha=0.65, lw=0.4)
    )

    title = f"Grafo • nodos={G.number_of_nodes()} • aristas={G.number_of_edges()} • etiquetas={len(labels)}"
    plt.title(title, fontsize=12)
    plt.axis("off")

    png_path = output_prefix.with_suffix(".png")
    svg_path = output_prefix.with_suffix(".svg")
    plt.tight_layout(pad=0.5)
    plt.savefig(png_path, dpi=DPI)
    plt.savefig(svg_path)
    plt.close()
    print(f"Visualización exportada:\n  - {png_path}\n  - {svg_path}")


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {INPUT_JSON.resolve()}")
    # 1) Carga y colapso
    Gm = load_property_graph(INPUT_JSON)
    G = to_simple_graph(Gm)
    # 2) LCC por defecto
    G = largest_connected_component(G)
    # 3) Dibujo
    draw_graph(G, OUTPUT_PREFIX)


if __name__ == "__main__":
    main()
