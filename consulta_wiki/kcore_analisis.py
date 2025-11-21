# onion_export.py
# ---------------------------------------------
# Lee data/grafo_unificado.json (con claves 'nodes' y 'edges'),
# calcula onion layers + degree y exporta onion_layers.csv
# ordenado por layer desc y degree desc.
#
# Uso:
#   python onion_export.py
#
# Requisitos:
#   pip install networkx pandas

import json
from pathlib import Path
import pandas as pd
import networkx as nx
from networkx.algorithms.core import onion_layers

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
            Gm.add_edge(s, t)

    # Colapsar a grafo simple no dirigido
    G = nx.Graph()
    G.add_nodes_from(Gm.nodes(data=True))
    for u, v in Gm.edges():
        if not G.has_edge(u, v):
            G.add_edge(u, v)

    # Quedarse con la componente conexa más grande
    if G.number_of_nodes() > 0:
        comps = list(nx.connected_components(G))
        if comps:
            G = G.subgraph(max(comps, key=len)).copy()
    return G

def main():
    BASE_DIR = Path(__file__).resolve().parent
    INPUT_JSON = BASE_DIR / "data" / "grafo_unificado.json"
    OUTPUT_CSV  = BASE_DIR / "onion_layers.csv"

    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"No existe {INPUT_JSON}")

    G = load_property_graph(INPUT_JSON)
    if G.number_of_nodes() == 0:
        print("Grafo vacío.")
        return

    # onion_layers puede devolver:
    # - dict: nodo -> int(layer)  (algunas versiones)
    # - dict: nodo -> (core, layer) (otras versiones)
    ol = onion_layers(G)
    core_num = nx.core_number(G)

    rows = []
    for n in G.nodes():
        val = ol.get(n, None)
        if isinstance(val, tuple) and len(val) == 2:
            core_k, layer_j = val
        else:
            core_k = core_num.get(n, None)
            layer_j = int(val) if val is not None else None

        rows.append({
            "node_id": n,
            "label": G.nodes[n].get("label") or "",
            "core": core_k,
            "layer": layer_j,
            "degree": G.degree(n),
        })

    df = pd.DataFrame(rows)

    # Asegurar tipos numéricos
    df["layer"] = pd.to_numeric(df["layer"], errors="coerce")
    df["degree"] = pd.to_numeric(df["degree"], errors="coerce").fillna(0).astype(int)

    # Orden: layer descendente, degree descendente
    df = df.sort_values(by=["layer", "degree"], ascending=[False, False])

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"CSV generado: {OUTPUT_CSV.resolve()}  ({len(df)} nodos)")

if __name__ == "__main__":
    main()
