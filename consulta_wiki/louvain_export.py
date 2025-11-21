# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 11:35:26 2025

@author: jvera
"""

# louvain_export.py
# ---------------------------------------------
# Lee data/grafo_unificado.json (claves 'nodes' y 'edges'),
# calcula comunidades Louvain y exporta un CSV con:
#   node_id, label, community
# ordenado por community asc y luego por label asc.
#
# Uso:
#   python louvain_export.py
#
# Requisitos:
#   pip install networkx python-louvain pandas

import json
from pathlib import Path
import pandas as pd
import networkx as nx

# Intentar importar python-louvain con manejo amigable
try:
    import community as community_louvain  # paquete: python-louvain
except ImportError as e:
    raise SystemExit(
        "Falta el paquete 'python-louvain'. Instálalo con:\n"
        "    pip install python-louvain\n"
        f"Detalle: {e}"
    )

def load_property_graph(json_path: Path) -> nx.Graph:
    """Carga el JSON (property graph) y devuelve la LCC como grafo simple no dirigido."""
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Construir MultiDiGraph desde 'nodes' y 'edges'
    Gm = nx.MultiDiGraph()
    for n in data.get("nodes", []):
        nid = n.get("id")
        if nid:
            Gm.add_node(nid, label=n.get("label") or "")
    for e in data.get("edges", []):
        s, t = e.get("source"), e.get("target")
        if s and t:
            # guardamos multiplicidad como edges paralelos
            Gm.add_edge(s, t)

    # Colapsar a grafo simple no dirigido, acumulando peso por multiplicidad
    G = nx.Graph()
    G.add_nodes_from(Gm.nodes(data=True))
    for u, v in Gm.edges():
        if G.has_edge(u, v):
            G[u][v]["weight"] += 1
        else:
            G.add_edge(u, v, weight=1)

    # Quedarse con la componente conexa más grande
    if G.number_of_nodes() > 0:
        comps = list(nx.connected_components(G))
        if comps:
            G = G.subgraph(max(comps, key=len)).copy()
    return G

def main():
    BASE_DIR = Path(__file__).resolve().parent
    INPUT_JSON = BASE_DIR / "data" / "grafo_unificado.json"
    OUTPUT_CSV  = BASE_DIR / "communities_louvain.csv"

    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"No existe {INPUT_JSON}")

    G = load_property_graph(INPUT_JSON)
    if G.number_of_nodes() == 0:
        print("Grafo vacío.")
        return

    # Partición Louvain (usa peso si está disponible)
    partition = community_louvain.best_partition(G, weight="weight", random_state=42)  # dict: node -> community_id

    # Construir DataFrame simple (nombre y comunidad)
    rows = []
    for n in G.nodes():
        rows.append({
            "node_id": n,
            "label": G.nodes[n].get("label") or "",
            "community": partition.get(n)
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["community", "label"], ascending=[True, True])

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"CSV generado: {OUTPUT_CSV.resolve()}  ({len(df)} nodos)")

if __name__ == "__main__":
    main()
