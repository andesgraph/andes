# -*- coding: utf-8 -*-
"""
unir_grafos.py - Une y analiza COMPLETAMENTE los grafos de Qoyllur Riti y Celebración a la Virgen
"""

import pickle
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import Counter

def cargar_grafo(filename):
    """Carga un grafo desde archivo PKL"""
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error al cargar {filename}: {e}")
        return None

def unir_grafos():
    """Une los dos grafos y analiza la red combinada"""
    print("🔗 UNIENDO Y ANALIZANDO GRAFOS COMBINADOS")
    print("=" * 65)
    print("Qoyllur Riti (Q2408955) + Celebración a la Virgen (Q60643381)")
    print("=" * 65)
    
    # Cargar grafos individuales
    print("📂 Cargando grafos individuales...")
    grafo_qoyllur = cargar_grafo("grafo_Q2408955.pkl")
    grafo_virgen = cargar_grafo("grafo_Q60643381.pkl")
    
    if not grafo_qoyllur or not grafo_virgen:
        print("❌ No se pudieron cargar ambos grafos")
        return None
    
    # Mostrar stats iniciales
    print(f"   • Qoyllur Riti: {grafo_qoyllur.number_of_nodes()} nodos, {grafo_qoyllur.number_of_edges()} aristas")
    print(f"   • Celebración Virgen: {grafo_virgen.number_of_nodes()} nodos, {grafo_virgen.number_of_edges()} aristas")
    
    # Crear grafo combinado
    print("🔄 Combinando grafos...")
    grafo_combinado = nx.compose(grafo_qoyllur, grafo_virgen)
    
    # Agregar conexión entre las dos entidades principales
    grafo_combinado.add_edge("Q2408955", "Q60643381", 
                           label="P361",  # parte de
                           prop_label="parte de",
                           dimension="Relacional")
    grafo_combinado.add_edge("Q60643381", "Q2408955", 
                           label="P527",  # tiene parte
                           prop_label="tiene parte",
                           dimension="Relacional")
    
    # Guardar grafo combinado
    with open("grafo_combinado.pkl", 'wb') as f:
        pickle.dump(grafo_combinado, f)
    
    print(f"✅ Grafos unidos exitosamente")
    print(f"   • Nodos totales: {grafo_combinado.number_of_nodes()}")
    print(f"   • Aristas totales: {grafo_combinado.number_of_edges()}")
    print(f"   • Densidad: {nx.density(grafo_combinado):.6f}")
    
    return grafo_combinado, grafo_qoyllur, grafo_virgen

def analizar_grafo_combinado(grafo, grafo_qoyllur, grafo_virgen):
    """Analiza COMPLETAMENTE el grafo combinado"""
    print("\n" + "="*60)
    print("📊 ANÁLISIS COMPLETO DEL GRAFO COMBINADO")
    print("="*60)
    
    # 1. ESTADÍSTICAS BÁSICAS
    print("\n1. 📈 ESTADÍSTICAS BÁSICAS")
    print("-" * 30)
    print(f"• Nodos totales: {grafo.number_of_nodes()}")
    print(f"• Aristas totales: {grafo.number_of_edges()}")
    print(f"• Densidad: {nx.density(grafo):.6f}")
    print(f"• Diámetro: {nx.diameter(grafo.to_undirected()) if nx.is_connected(grafo.to_undirected()) else 'No conectado'}")
    print(f"• Radio: {nx.radius(grafo.to_undirected()) if nx.is_connected(grafo.to_undirected()) else 'N/A'}")
    
    # 2. COMPONENTES CONECTADOS
    print("\n2. 🔗 COMPONENTES CONECTADOS")
    print("-" * 30)
    componentes = list(nx.connected_components(grafo.to_undirected()))
    print(f"• Componentes conectados: {len(componentes)}")
    
    componente_principal = max(componentes, key=len)
    print(f"• Nodos en componente principal: {len(componente_principal)} ({len(componente_principal)/grafo.number_of_nodes()*100:.1f}%)")
    
    # 3. CENTRALIDAD
    print("\n3. 🎯 ANÁLISIS DE CENTRALIDAD")
    print("-" * 30)
    
    # Grado de centralidad
    centralidad_grado = nx.degree_centrality(grafo)
    top_grado = sorted(centralidad_grado.items(), key=lambda x: x[1], reverse=True)[:15]
    
    print("🔝 TOP 15 NODOS POR GRADO DE CENTRALIDAD:")
    for i, (nodo, cent) in enumerate(top_grado, 1):
        tipo = grafo.nodes[nodo].get('type', 'N/A')
        dimension = grafo.nodes[nodo].get('dimension', 'N/A')
        print(f"   {i:2d}. {nodo}: {cent:.4f} ({tipo}, {dimension})")
    
    # Betweenness centrality
    betweenness = nx.betweenness_centrality(grafo)
    top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\n🔝 TOP 10 NODOS POR INTERMEDIACIÓN:")
    for i, (nodo, bet) in enumerate(top_betweenness, 1):
        tipo = grafo.nodes[nodo].get('type', 'N/A')
        print(f"   {i:2d}. {nodo}: {bet:.4f} ({tipo})")
    
    # 4. DISTRIBUCIÓN DE GRADOS
    print("\n4. 📊 DISTRIBUCIÓN DE GRADOS")
    print("-" * 30)
    grados = [deg for node, deg in grafo.degree()]
    print(f"• Grado promedio: {np.mean(grados):.2f}")
    print(f"• Grado máximo: {max(grados)}")
    print(f"• Grado mínimo: {min(grados)}")
    print(f"• Desviación estándar: {np.std(grados):.2f}")
    
    # 5. ANÁLISIS DE DIMENSIONES
    print("\n5. 🌐 DISTRIBUCIÓN POR DIMENSIONES")
    print("-" * 30)
    dimensiones = [grafo.nodes[node].get('dimension', 'N/A') for node in grafo.nodes()]
    contador_dim = Counter(dimensiones)
    
    for dim, count in contador_dim.most_common():
        print(f"• {dim}: {count} nodos ({count/grafo.number_of_nodes()*100:.1f}%)")
    
    # 6. NODOS COMPARTIDOS
    print("\n6. 🤝 NODOS COMPARTIDOS ENTRE GRAFOS")
    print("-" * 30)
    nodos_qoyllur = set(grafo_qoyllur.nodes())
    nodos_virgen = set(grafo_virgen.nodes())
    nodos_comunes = nodos_qoyllur.intersection(nodos_virgen)
    
    print(f"• Nodos en común: {len(nodos_comunes)}")
    if nodos_comunes:
        print("• Ejemplos de nodos compartidos:")
        for i, nodo in enumerate(list(nodos_comunes)[:10], 1):
            tipo = grafo.nodes[nodo].get('type', 'N/A')
            print(f"   {i}. {nodo} ({tipo})")
    
    # 7. PROPIEDADES MÁS COMUNES
    print("\n7. 🔗 PROPIEDADES MÁS FRECUENTES")
    print("-" * 30)
    propiedades = []
    for u, v, data in grafo.edges(data=True):
        if 'label' in data:
            propiedades.append(data['label'])
    
    contador_prop = Counter(propiedades)
    print("Top propiedades:")
    for prop, count in contador_prop.most_common(10):
        print(f"• {prop}: {count} aristas")
    
    # 8. ANÁLISIS DE CONECTIVIDAD
    print("\n8. 📡 CONECTIVIDAD ENTRE NODOS PRINCIPALES")
    print("-" * 30)
    try:
        camino = nx.shortest_path(grafo, "Q2408955", "Q60643381")
        print(f"• Camino más corto Q2408955 → Q60643381: {len(camino)-1} saltos")
        print(f"• Ruta: {' → '.join(camino)}")
    except:
        print("• No hay camino directo entre los nodos principales")
    
    # 9. EXPORTAR DATOS COMPLETOS
    print("\n9. 💾 EXPORTANDO DATOS DE ANÁLISIS")
    print("-" * 30)
    exportar_analisis_completo(grafo, centralidad_grado, betweenness)
    
    return {
        'centralidad_grado': centralidad_grado,
        'betweenness': betweenness,
        'componentes': componentes,
        'dimensiones': contador_dim,
        'nodos_comunes': nodos_comunes
    }

def exportar_analisis_completo(grafo, centralidad_grado, betweenness):
    """Exporta análisis completo a CSV CON NOMBRE DEL NODO"""
    datos_completos = []
    
    for node in grafo.nodes():
        # ✅ Obtener el nombre (label) del nodo
        nombre_nodo = grafo.nodes[node].get('label', '')
        # Si no hay label, usar el ID como fallback
        if not nombre_nodo:
            nombre_nodo = node
        
        datos_completos.append({
            'nodo_id': node,  # ✅ Mantener el ID
            'nombre_nodo': nombre_nodo,  # ✅ NUEVA COLUMNA CON NOMBRE
            'tipo': grafo.nodes[node].get('type', 'N/A'),
            'dimension': grafo.nodes[node].get('dimension', 'N/A'),
            'grado_centralidad': centralidad_grado.get(node, 0),
            'intermediacion': betweenness.get(node, 0),
            'grado': grafo.degree(node),
            'es_principal': node in ["Q2408955", "Q60643381"]
        })
    
    df_completo = pd.DataFrame(datos_completos)
    
    df_completo = df_completo.sort_values('grado_centralidad', ascending=False)
    df_completo.to_csv("analisis_completo_combinado.csv", index=False, encoding='utf-8')
    print("✓ Análisis completo exportado a: analisis_completo_combinado.csv")
    
    # Estadísticas por dimensión
    stats_dimension = df_completo.groupby('dimension').agg({
        'grado_centralidad': 'mean',
        'intermediacion': 'mean', 
        'grado': 'mean',
        'nodo_id': 'count'
    }).rename(columns={'nodo_id': 'cantidad_nodos'})
    
    stats_dimension.to_csv("estadisticas_por_dimension.csv", encoding='utf-8')
    print("✓ Estadísticas por dimensión exportadas a: estadisticas_por_dimension.csv")

def visualizar_grafo_combinado(grafo):
    """Visualiza el grafo combinado con mejoras"""
    print("\n🎨 CREANDO VISUALIZACIÓN MEJORADA...")
    
    plt.figure(figsize=(20, 16))
    
    # Layout mejorado
    pos = nx.spring_layout(grafo, k=3, iterations=100, seed=42)
    
    # Colores y tamaños personalizados
    node_colors = []
    node_sizes = []
    labels = {}
    
    for node in grafo.nodes():
        if node == "Q2408955":
            node_colors.append('red')
            node_sizes.append(1200)
            labels[node] = "Qoyllur\nRiti"
        elif node == "Q60643381":
            node_colors.append('purple')
            node_sizes.append(1200)
            labels[node] = "Celebración\nVirgen"
        elif grafo.nodes[node].get('type') == 'intermediate':
            node_colors.append('blue')
            node_sizes.append(400)
            if grafo.degree(node) > 5:  # Etiquetar intermediarios importantes
                labels[node] = node
        else:
            node_colors.append('green')
            node_sizes.append(200)
            # No etiquetar targets para evitar sobrecarga
    
    # Dibujar grafo
    nx.draw_networkx_nodes(grafo, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_edges(grafo, pos, edge_color='lightgray', alpha=0.6, width=0.8)
    nx.draw_networkx_labels(grafo, pos, labels, font_size=8, font_weight='bold')
    
    # Leyenda
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Qoyllur Riti'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='Celebración Virgen'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=8, label='Intermedios'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=6, label='Targets')
    ]
    
    plt.legend(handles=legend_elements, loc='upper right')
    plt.title("🌄 RED COMBINADA: Qoyllur Riti + Celebración a la Virgen\nAnálisis de Conectividad Cultural en Wikidata", 
              fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    
    # Guardar en alta resolución
    plt.savefig("grafo_combinado_detallado.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print("✅ Visualización detallada guardada como: grafo_combinado_detallado.png")

def main():
    # Unir grafos
    grafo_combinado, grafo_qoyllur, grafo_virgen = unir_grafos()
    
    if grafo_combinado:
        # Analizar completo
        resultados = analizar_grafo_combinado(grafo_combinado, grafo_qoyllur, grafo_virgen)
        
        # Visualizar
        visualizar_grafo_combinado(grafo_combinado)
        
        print("\n" + "="*60)
        print("🎉 ANÁLISIS COMPLETO FINALIZADO")
        print("="*60)
        print("📁 Archivos generados:")
        print("  • grafo_combinado.pkl (grafo completo)")
        print("  • grafo_combinado_detallado.png (visualización)")
        print("  • analisis_completo_combinado.csv (datos completos)")
        print("  • estadisticas_por_dimension.csv (stats por dimensión)")
        print("\n📊 Resumen estadístico:")
        print(f"  • {grafo_combinado.number_of_nodes()} nodos analizados")
        print(f"  • {grafo_combinado.number_of_edges()} conexiones mapeadas")
        print(f"  • {len(resultados['nodos_comunes'])} nodos compartidos entre celebraciones")
        
        return grafo_combinado
    return None

if __name__ == "__main__":
    grafo_combinado = main()