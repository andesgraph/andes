# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 16:31:43 2025

@author: jvera
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 1. Configuración de paths
def get_file_paths():
    """Configura los paths relativos para encontrar el JSON"""
    # Subir un nivel desde la carpeta actual (grafos) y luego entrar a resultados_queries
    base_dir = Path(__file__).parent.parent  # Sube al directorio padre de "grafos"
    json_path = base_dir / "queries" / "resultados_queries" / "qoyllur_riti_grado2.json"        
    return json_path

# 2. Cargar y parsear el JSON
def load_json_data():
    file_path = get_file_paths()
    
    if not file_path.exists():
        print(f"ERROR: No se encontró el archivo en: {file_path}")
        print("Estructura de carpetas esperada:")
        print("proyecto/")
        print("├── grafos/")
        print("│   └── este_script.py")
        print("└── queries/")
        print("    └── resultados_queries/")
        print("        └── qoyllur_riti_grado2.json")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['results']
    except Exception as e:
        print(f"Error al cargar el JSON: {e}")
        return None

# 3. Crear grafo dirigido desde los resultados
def create_graph_from_results(results):
    G = nx.DiGraph()
    central_node = "Q2408955"
    G.add_node(central_node, label="Qoyllur Rit'i", type='central')
    
    for result in results:
        # Extraer IDs cortos
        intermediate_node = result['entidadIntermedia_short']
        prop1 = result['propiedadGrado1_short']
        target_node = result['entidadGrado2_short']
        prop2 = result['propiedadGrado2_short']
        dimension = result['dimension']
        
        # Agregar nodos con atributos
        G.add_node(intermediate_node, type='intermediate', dimension=dimension)
        G.add_node(target_node, type='target', dimension=dimension)
        
        # Agregar aristas con propiedades como atributos
        G.add_edge(central_node, intermediate_node, label=prop1, dimension=dimension)
        G.add_edge(intermediate_node, target_node, label=prop2, dimension=dimension)
    
    return G

# 4. Calcular métricas del grafo
def calculate_graph_metrics(G):
    metrics = {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'is_directed': G.is_directed(),
        'density': nx.density(G),
        'degree_centrality': nx.degree_centrality(G),
        'betweenness_centrality': nx.betweenness_centrality(G),
        'shortest_paths_from_central': dict(nx.shortest_path_length(G, source="Q2408955"))
    }
    return metrics

# 5. Visualizar el grafo y guardar imagen automáticamente - MODIFICADO
def visualize_and_save_graph(G):
    try:
        plt.figure(figsize=(16, 14))
        
        # Layout para mejor visualización
        pos = nx.kamada_kawai_layout(G)
        
        # Colores por tipo de nodo
        node_colors = []
        node_sizes = []
        for node in G.nodes:
            if node == "Q2408955":
                node_colors.append('red')
                node_sizes.append(800)  # Nodo central más grande
            elif G.nodes[node].get('type') == 'intermediate':
                node_colors.append('blue')
                node_sizes.append(400)
            else:
                node_colors.append('green')
                node_sizes.append(200)
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=15, alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=7, font_weight='bold')
        
        plt.title('Grafo de conexiones de Qoyllur Rit\'i en Wikidata (2do grado)\n', fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        
        # Guardar la imagen automáticamente - NUEVO
        output_filename = "grafo_qoyllur_riti.png"
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"✓ Imagen del grafo guardada como: {output_filename}")
        
        plt.close()  # Cerrar la figura para liberar memoria
        
    except Exception as e:
        print(f"Error al crear la visualización: {e}")

# 6. Exportar resultados a CSV
def export_analysis_to_csv(G, metrics, filename="analisis_grafo.csv"):
    """Exporta el análisis a archivos CSV"""
    # Exportar nodos y sus métricas
    nodes_data = []
    for node in G.nodes:
        nodes_data.append({
            'nodo': node,
            'tipo': G.nodes[node].get('type', 'desconocido'),
            'dimension': G.nodes[node].get('dimension', 'N/A'),
            'grado_centralidad': metrics['degree_centrality'].get(node, 0),
            'intermediacion': metrics['betweenness_centrality'].get(node, 0)
        })
    
    df_nodes = pd.DataFrame(nodes_data)
    df_nodes.to_csv(filename, index=False, encoding='utf-8')
    print(f"✓ Resultados exportados a: {filename}")

# 7. Analizar y mostrar resultados
def analyze_graph(G, metrics):
    print("=== ANÁLISIS DEL GRAFO DE QOYLLUR RIT'I ===")
    print(f"Nodos totales: {metrics['total_nodes']}")
    print(f"Aristas totales: {metrics['total_edges']}")
    print(f"Densidad del grafo: {metrics['density']:.6f}")
    print(f"Es dirigido: {metrics['is_directed']}")
    
    print("\n=== TOP 10 NODOS MÁS CONECTADOS ===")
    degree_centrality = metrics['degree_centrality']
    top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (node, centrality) in enumerate(top_nodes, 1):
        node_type = G.nodes[node].get('type', 'N/A')
        print(f"{i:2d}. {node}: {centrality:.4f} ({node_type})")
    
    print("\n=== TOP 10 NODOS CON MAYOR INTERMEDIACIÓN ===")
    betweenness = metrics['betweenness_centrality']
    top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (node, betweenness_val) in enumerate(top_betweenness, 1):
        node_type = G.nodes[node].get('type', 'N/A')
        print(f"{i:2d}. {node}: {betweenness_val:.4f} ({node_type})")
    
    print("\n=== DISTRIBUCIÓN DE DISTANCIAS DESDE QOYLLUR RIT'I ===")
    path_lengths = list(metrics['shortest_paths_from_central'].values())
    distance_counts = pd.Series(path_lengths).value_counts().sort_index()
    for distance, count in distance_counts.items():
        print(f"Distancia {distance}: {count} nodos")

# 8. Función principal - MODIFICADO
def main():
    print("Cargando datos desde la estructura de carpetas...")
    print("Buscando: ../queries/resultados_queries/qoyllur_riti_grado2.json")
    
    # Cargar datos
    results = load_json_data()
    
    if results is None:
        return None, None
    
    print(f"Datos cargados: {len(results)} conexiones encontradas")
    
    # Crear grafo
    G = create_graph_from_results(results)
    print("Grafo creado exitosamente")
    
    # Calcular métricas
    metrics = calculate_graph_metrics(G)
    
    # Mostrar análisis
    analyze_graph(G, metrics)
    
    # Exportar resultados
    export_analysis_to_csv(G, metrics)
    
    # Crear y guardar imagen automáticamente - NUEVO
    visualize_and_save_graph(G)
    
    return G, metrics

# Ejecutar análisis
if __name__ == "__main__":
    graph, graph_metrics = main()