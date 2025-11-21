# -*- coding: utf-8 -*-
"""
Integrador de grafos (Wikidata SPARQL JSON) - ejecución simple
--------------------------------------------------------------
- Lee TODOS los .json en la carpeta "data/" (se crea si no existe).
- Integra nodos (QIDs) y aristas (PIDs). Si el objeto no es QID, lo ignora como edge
  (versión simple); puedes ampliar para guardar literales como props si quieres.
- Exporta:
    - data/grafo_unificado.json        (property graph)
    - data/grafo_unificado.gexf        (para Gephi, con atributos saneados)
    - data/grafo_unificado_nodos.csv   (utf-8-sig)
    - data/grafo_unificado_enlaces.csv (utf-8-sig)

Uso:
    python integrar_grafos.py
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import pandas as pd
import networkx as nx

# --------- Config ---------
DATA_DIR = Path("data")
OUT_PREFIX = DATA_DIR / "grafo_unificado"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --------- Utilidades ---------
_QID_RE = re.compile(r"/entity/(Q\d+)$")
_PID_RE = re.compile(r"/prop/direct/(P\d+)$")

def get_value(x):
    if x is None:
        return ""
    if isinstance(x, dict):
        return x.get("value", "")
    if isinstance(x, (str, int, float, bool)):
        return str(x)
    return str(x)

def extract_qid(x) -> Optional[str]:
    m = _QID_RE.search(get_value(x))
    return m.group(1) if m else None

def extract_pid(x) -> Optional[str]:
    m = _PID_RE.search(get_value(x))
    return m.group(1) if m else None

def load_json_any(path: Path):
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # WCQS
    if isinstance(raw, dict) and isinstance(raw.get("results", {}).get("bindings"), list):
        return raw["results"]["bindings"]
    # Lista libre
    if isinstance(raw, list):
        return raw
    # Fallback
    return [raw]

def sanitize_scalar(v):
    """Convierte a tipos permitidos por GEXF: str/int/float/bool o '' si None.
    Para list/dict/set/tuple serializa a JSON compacto."""
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return v
    try:
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(v)

# --------- Builder ---------
class KGBuilder:
    def __init__(self):
        self.nodes = {}                      # qid -> {labels:set, props:dict(list)}
        self.edges = []                      # list of dict
        self.edge_seen = set()
        self.prop_counts = Counter()

    def ensure_node(self, qid: str, label: str = ""):
        n = self.nodes.get(qid)
        if n is None:
            n = {"id": qid, "labels": set(), "props": defaultdict(list)}
            self.nodes[qid] = n
        if label:
            n["labels"].add(label)
        return n

    def add_edge(self, src: str, dst: str, pid: Optional[str], prop_label: Optional[str]):
        key = (src, dst, pid or "", prop_label or "")
        if key in self.edge_seen:
            return
        self.edge_seen.add(key)
        self.edges.append(
            {"source": src, "target": dst, "property_id": pid, "property_label": prop_label}
        )
        self.prop_counts[(pid or "", prop_label or "")] += 1

    def process_row(self, row: dict):
        # Sujetos comunes en WCQS
        subj = (
            extract_qid(row.get("item")) or
            extract_qid(row.get("item1")) or
            extract_qid(row.get("festividad")) or
            extract_qid(row.get("subject")) or
            extract_qid(row.get("adminArea"))
        )
        subj_label = (
            get_value(row.get("itemLabel")) or
            get_value(row.get("item1Label")) or
            get_value(row.get("festividadLabel")) or
            get_value(row.get("subjectLabel")) or
            get_value(row.get("adminAreaLabel"))
        )
        if not subj:
            # Fallback: si viene solo un objeto QID, úsalo como sujeto
            for ob_key in ("item2", "valor", "entidadIntermedia"):
                qid = extract_qid(row.get(ob_key))
                if qid:
                    subj = qid
                    subj_label = get_value(row.get(ob_key + "Label"))
                    break
        if not subj:
            return

        self.ensure_node(subj, subj_label)

        # Slots habituales de propiedad
        pid = (
            extract_pid(row.get("propiedad")) or
            extract_pid(row.get("p"))
        )
        prop_label = (
            get_value(row.get("propiedadLabel")) or
            get_value(row.get("pl_")) or
            pid
        )

        # Objetos: prioriza QID (arista). Si no hay QID, ignoramos literal (versión simple)
        obj = (
            extract_qid(row.get("item2")) or
            extract_qid(row.get("valor")) or
            extract_qid(row.get("entidadIntermedia")) or
            extract_qid(row.get("o"))
        )
        obj_label = (
            get_value(row.get("item2Label")) or
            get_value(row.get("valorLabel")) or
            get_value(row.get("entidadIntermediaLabel")) or
            get_value(row.get("ol_"))
        )

        if obj:
            self.ensure_node(obj, obj_label)
            self.add_edge(subj, obj, pid, prop_label)

    def build(self, files):
        for f in files:
            try:
                rows = load_json_any(f)
            except Exception as e:
                print(f"[WARN] No se pudo leer {f.name}: {e}")
                continue
            for row in rows:
                try:
                    self.process_row(row)
                except Exception as e:
                    print(f"[WARN] Fila problemática en {f.name}: {e}")

        # Normaliza atributos a tipos simples
        nodes_norm = {}
        for q, n in self.nodes.items():
            label = sorted(n["labels"])[0] if n["labels"] else ""
            nodes_norm[q] = {
                "id": q,
                "label": label,
                "labels": sorted(list(n["labels"])),
            }
        self.nodes = nodes_norm

    def to_networkx(self):
        G = nx.MultiDiGraph()
        for n in self.nodes.values():
            # Saneamos atributos por si acaso
            safe_attrs = {k: sanitize_scalar(v) for k, v in n.items() if k != "id"}
            G.add_node(n["id"], **safe_attrs)
        for e in self.edges:
            safe_e = {k: sanitize_scalar(v) for k, v in e.items() if k not in ("source", "target")}
            G.add_edge(e["source"], e["target"], **safe_e)
        return G

# --------- Exportación ---------
def export_all(kg: KGBuilder):
    # JSON (property graph)
    with OUT_PREFIX.with_suffix(".json").open("w", encoding="utf-8") as f:
        json.dump({"nodes": list(kg.nodes.values()), "edges": kg.edges}, f, ensure_ascii=False, indent=2)

    # GEXF (saneado)
    G = kg.to_networkx()
    try:
        nx.write_gexf(G, OUT_PREFIX.with_suffix(".gexf"))
    except Exception as e:
        # plan B: fuerza todos los atributos a string y reintenta
        G2 = nx.MultiDiGraph()
        for n, attrs in G.nodes(data=True):
            G2.add_node(n, **{k: str(v) if v is not None else "" for k, v in attrs.items()})
        for u, v, attrs in G.edges(data=True):
            G2.add_edge(u, v, **{k: str(vv) if vv is not None else "" for k, vv in attrs.items()})
        nx.write_gexf(G2, OUT_PREFIX.with_suffix(".gexf"))
        print(f"[INFO] GEXF exportado usando plan B (string-cast). Motivo: {e}")

    # CSVs (utf-8-sig para Excel en Windows)
    deg = {n: G.degree(n) for n in G.nodes()}
    nodes_df = pd.DataFrame(
        [{"id": n["id"], "label": n["label"], "degree": deg.get(n["id"], 0)} for n in kg.nodes.values()]
    ).sort_values(["degree", "label"], ascending=[False, True])
    edges_df = pd.DataFrame(kg.edges)

    nodes_df.to_csv(OUT_PREFIX.parent / f"{OUT_PREFIX.stem}_nodos.csv", index=False, encoding="utf-8-sig")
    edges_df.to_csv(OUT_PREFIX.parent / f"{OUT_PREFIX.stem}_enlaces.csv", index=False, encoding="utf-8-sig")

def main():
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print(f"No se encontraron .json en {DATA_DIR.resolve()}")
        return
    kg = KGBuilder()
    kg.build(files)
    export_all(kg)
    print(f"Integración completa. Archivos generados en: {DATA_DIR.resolve()}")

if __name__ == "__main__":
    main()
