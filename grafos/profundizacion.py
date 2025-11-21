# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 17:50:16 2025

@author: jvera
"""

"""
profundizacion_completa_mejorada.py - Análisis automático de profundización MEJORADO
Ejecuta: Lee CSV → Genera consultas ESPECÍFICAS → Ejecuta → Actualiza grafo SIN DUPLICADOS
"""

import pandas as pd
import json
import os
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

# Configuración
CSV_ANALISIS = "analisis_grafo.csv"
CARPETA_CONSULTAS = "consultas_profundizacion_mejoradas"
CARPETA_RESULTADOS = "resultados_profundizacion_mejoradas"
ENDPOINT_URL = "https://query.wikidata.org/sparql"

def configurar_sparql():
    """Configura el cliente SPARQL con timeout"""
    user_agent = f"QoyllurRiti-Profundizacion/2.0 Python/{sys.version_info[0]}.{sys.version_info[1]}"
    sparql = SPARQLWrapper(ENDPOINT_URL, agent=user_agent)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(300)  # 5 minutos timeout
    return sparql

def cargar_analisis_previo():
    """Carga y analiza el CSV existente"""
    print("📊 Cargando análisis previo...")
    df = pd.read_csv(CSV_ANALISIS)
    
    # Estadísticas básicas
    print(f"   • Total nodos: {len(df)}")
    print(f"   • Dimensiones encontradas: {df['dimension'].nunique()}")
    print(f"   • Nodos centrales: {len(df[df['tipo'] == 'central'])}")
    print(f"   • Nodos intermedios: {len(df[df['tipo'] == 'intermediate'])}")
    
    return df

def identificar_nodos_para_profundizar(df):
    """Identifica nodos específicos que merecen profundización"""
    print("\n🔍 Identificando nodos relevantes para profundización...")
    
    nodos_relevantes = []
    
    # Criterios para seleccionar nodos
    for _, row in df.iterrows():
        # Nodos con alta centralidad y dimensión definida
        if (row['grado_centralidad'] > 0.01 and 
            row['dimension'] != 'N/A' and 
            pd.notna(row['dimension'])):
            
            nodos_relevantes.append((row['nodo'], row['dimension']))
            print(f"   • {row['nodo']} ({row['dimension']}): centralidad {row['grado_centralidad']:.4f}")
    
    # También incluir algunos nodos intermedios importantes
    for _, row in df[df['tipo'] == 'intermediate'].iterrows():
        if row['grado_centralidad'] > 0.05:
            nodos_relevantes.append((row['nodo'], row['dimension']))
            print(f"   • {row['nodo']} ({row['dimension']}): INTERMEDIO centralidad {row['grado_centralidad']:.4f}")
    
    print(f"\n🎯 Total nodos seleccionados para profundización: {len(nodos_relevantes)}")
    return nodos_relevantes

def obtener_propiedades_por_dimension(dimension):
    """Devuelve propiedades relevantes para cada dimensión - MÁS ESPECÍFICAS"""
    propiedades = {
        "Cultural": ["wdt:P135", "wdt:P361", "wdt:P921", "wdt:P136"],
        "Religioso": ["wdt:P140", "wdt:P417", "wdt:P2925"],
        "Patrimonio": ["wdt:P1435", "wdt:P2184"],  # Solo las más relevantes
        "Temporal": ["wdt:P571", "wdt:P585", "wdt:P580"],  # Fechas importantes
        "Digital": ["wdt:P18", "wdt:P856", "wdt:P953"],  # Imágenes y URLs
        "Social": ["wdt:P112", "wdt:P710", "wdt:P127"],
        "Geográfica": ["wdt:P131", "wdt:P276", "wdt:P625", "wdt:P17"],
        "Identidad": ["wdt:P31", "wdt:P17", "wdt:P495"]  # Eliminado P361 duplicado
    }
    return propiedades.get(dimension, [])

def generar_consultas_profundizacion(dimensiones, nodos_relevantes):
    """Genera consultas SPARQL ESPECÍFICAS para cada dimensión y nodos relevantes"""
    print("\n🛠️ Generando consultas de profundización MEJORADAS...")
    
    consultas = {}
    
    for dimension in set([dim for _, dim in nodos_relevantes]):
        propiedades = obtener_propiedades_por_dimension(dimension)
        if not propiedades:
            print(f"   ⚠️  No hay propiedades definidas para dimensión: {dimension}")
            continue
        
        props_str = " ".join(propiedades)
        
        # Filtrar nodos por dimensión
        nodos_filtro = [nodo for nodo, dim in nodos_relevantes if dim == dimension]
        if not nodos_filtro:
            print(f"   ⚠️  No hay nodos relevantes para dimensión: {dimension}")
            continue
        
        # Limitar a 15 nodos por consulta para no sobrecargar
        nodos_str = " ".join([f"wd:{nodo}" for nodo in nodos_filtro[:15]])
        
        consulta = f"""
# Profundización ESPECÍFICA de dimensión {dimension}
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?nodoOrigen ?propiedad ?nodoDestino ?nodoOrigenLabel ?nodoDestinoLabel ?propiedadLabel
WHERE {{
  VALUES ?nodoOrigen {{ {nodos_str} }}
  VALUES ?propiedad {{ {props_str} }}
  
  ?nodoOrigen ?propiedad ?nodoDestino.
  
  # FILTROS ESTRICTOS de calidad
  FILTER(STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q"))
  FILTER(?nodoDestino != ?nodoOrigen)
  FILTER(!CONTAINS(STR(?nodoDestino), "statement"))
  FILTER(!CONTAINS(STR(?nodoDestino), "reference"))
  FILTER(!CONTAINS(STR(?nodoDestino), "ontology"))
  
  # Excluir nodos demasiado genéricos
  FILTER(!STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q1"))
  FILTER(!STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q2"))
  FILTER(!STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q3"))
  FILTER(!STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q4"))
  FILTER(!STRSTARTS(STR(?nodoDestino), "http://www.wikidata.org/entity/Q5"))
  
  # Labels en español
  OPTIONAL {{ ?nodoOrigen rdfs:label ?nodoOrigenLabel. FILTER(LANG(?nodoOrigenLabel) = "es") }}
  OPTIONAL {{ ?nodoDestino rdfs:label ?nodoDestinoLabel. FILTER(LANG(?nodoDestinoLabel) = "es") }}
  OPTIONAL {{ ?propiedad rdfs:label ?propiedadLabel. FILTER(LANG(?propiedadLabel) = "es") }}
}}
LIMIT 200
"""
        consultas[dimension] = consulta
        print(f"   ✅ {dimension}: {len(nodos_filtro)} nodos, {len(propiedades)} propiedades")
    
    return consultas

def guardar_consultas(consultas):
    """Guarda las consultas en archivos SPARQL"""
    os.makedirs(CARPETA_CONSULTAS, exist_ok=True)
    
    for dimension, query in consultas.items():
        filename = os.path.join(CARPETA_CONSULTAS, f"profundizacion_{dimension.lower()}.sparql")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(query)
    
    print(f"\n💾 Consultas MEJORADAS guardadas en: {CARPETA_CONSULTAS}/")

def ejecutar_consultas(consultas):
    """Ejecuta las consultas y guarda los resultados con manejo de errores mejorado"""
    print("\n⚡ Ejecutando consultas MEJORADAS en Wikidata...")
    
    sparql = configurar_sparql()
    os.makedirs(CARPETA_RESULTADOS, exist_ok=True)
    
    resultados_totales = []
    
    for dimension, query in consultas.items():
        try:
            print(f"   🔄 Ejecutando {dimension}...", end=" ", flush=True)
            sparql.setQuery(query)
            resultados = sparql.query().convert()
            
            # Procesar resultados
            resultados_procesados = []
            nodos_destino_vistos = set()
            
            for result in resultados["results"]["bindings"]:
                nodo_destino = result.get('nodoDestino', {}).get('value', '')
                
                # Evitar duplicados en esta ejecución
                if nodo_destino in nodos_destino_vistos:
                    continue
                    
                nodos_destino_vistos.add(nodo_destino)
                
                resultado_procesado = {
                    'dimension': dimension,
                    'nodoOrigen': result.get('nodoOrigen', {}).get('value', ''),
                    'propiedad': result.get('propiedad', {}).get('value', ''),
                    'nodoDestino': nodo_destino,
                    'nodoOrigenLabel': result.get('nodoOrigenLabel', {}).get('value', ''),
                    'nodoDestinoLabel': result.get('nodoDestinoLabel', {}).get('value', ''),
                    'propiedadLabel': result.get('propiedadLabel', {}).get('value', '')
                }
                resultados_procesados.append(resultado_procesado)
            
            # Guardar resultados individuales
            filename = os.path.join(CARPETA_RESULTADOS, f"resultados_{dimension.lower()}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'dimension': dimension,
                        'fecha_ejecucion': datetime.now().isoformat(),
                        'total_resultados': len(resultados_procesados),
                        'consulta': query
                    },
                    'resultados': resultados_procesados
                }, f, ensure_ascii=False, indent=2)
            
            resultados_totales.extend(resultados_procesados)
            print(f"✓ {len(resultados_procesados)} resultados ÚNICOS")
            
        except Exception as e:
            print(f"✗ Error en {dimension}: {str(e)[:100]}...")
    
    return resultados_totales

def actualizar_grafo(resultados):
    """Actualiza el grafo existente con los nuevos datos - EVITANDO DUPLICADOS"""
    print("\n🔄 Actualizando grafo con nuevos datos (sin duplicados)...")
    
    # Cargar grafo existente
    df_original = pd.read_csv(CSV_ANALISIS)
    nodos_existentes = set(df_original['nodo'].tolist())
    
    # Nodos genéricos a excluir
    nodos_excluidos = {'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q15', 'Q16', 'Q17', 'Q18', 'Q20', 'Q30'}
    
    # Crear DataFrame con nuevos resultados
    nuevos_datos = []
    nodos_agregados = set()
    
    for resultado in resultados:
        nodo_destino = resultado['nodoDestino'].split('/')[-1]
        
        # Filtrar nodos no deseados
        if (nodo_destino not in nodos_existentes and 
            nodo_destino not in nodos_agregados and
            nodo_destino not in nodos_excluidos and
            len(nodo_destino) > 3 and  # IDs muy cortos suelen ser genéricos
            not nodo_destino.startswith(('Q0', 'Q1', 'Q2', 'Q3'))):
            
            nuevos_datos.append({
                'nodo': nodo_destino,
                'tipo': 'enriquecido',
                'dimension': resultado['dimension'],
                'grado_centralidad': 0.002,  # Valor más realista
                'intermediacion': 0.0
            })
            nodos_agregados.add(nodo_destino)
    
    if not nuevos_datos:
        print("   ⚠️  No se encontraron nuevos nodos válidos para agregar")
        return df_original
    
    df_nuevo = pd.DataFrame(nuevos_datos)
    
    # Combinar con datos originales
    df_completo = pd.concat([df_original, df_nuevo], ignore_index=True)
    
    # Guardar CSV actualizado
    df_completo.to_csv("analisis_grafo_mejorado.csv", index=False, encoding='utf-8')
    
    print(f"📊 Grafo actualizado SIN DUPLICADOS:")
    print(f"   • Nodos originales: {len(df_original)}")
    print(f"   • Nodos nuevos: {len(df_nuevo)}")
    print(f"   • Nodos totales: {len(df_completo)}")
    
    # Mostrar algunos nodos nuevos como ejemplo
    print(f"   • Ejemplo nodos nuevos: {list(nodos_agregados)[:5]}")
    
    return df_completo

def visualizar_grafo_actualizado(df):
    """Crea visualización del grafo actualizado MEJORADA"""
    print("\n🎨 Creando visualización MEJORADA del grafo actualizado...")
    
    G = nx.DiGraph()
    
    # Añadir nodos con atributos
    for _, row in df.iterrows():
        G.add_node(row['nodo'], 
                  tipo=row['tipo'], 
                  dimension=row['dimension'],
                  centralidad=row['grado_centralidad'])
    
    # Visualización mejorada
    plt.figure(figsize=(16, 12))
    
    # Usar layout de resorte con parámetros optimizados
    pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
    
    # Colores y tamaños por tipo
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        node_data = G.nodes[node]
        if node_data.get('tipo') == 'central':
            node_colors.append('red')
            node_sizes.append(200)
        elif node_data.get('tipo') == 'intermediate':
            node_colors.append('blue')
            node_sizes.append(100)
        elif node_data.get('tipo') == 'enriquecido':
            node_colors.append('orange')
            node_sizes.append(50)
        else:  # target
            node_colors.append('lightgreen')
            node_sizes.append(30)
    
    nx.draw(G, pos, 
            node_color=node_colors, 
            node_size=node_sizes, 
            with_labels=False, 
            alpha=0.7,
            edge_color='gray',
            width=0.5)
    
    # Añadir labels para nodos importantes
    labels = {}
    for node in G.nodes():
        if G.nodes[node].get('centralidad', 0) > 0.01:
            labels[node] = node
    
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    
    plt.title(f"Grafo Actualizado MEJORADO - {len(G.nodes())} nodos\n"
              f"(Rojo: central, Azul: intermedios, Naranja: enriquecidos, Verde: targets)")
    plt.savefig("grafo_actualizado_mejorado.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Visualización MEJORADA guardada como: grafo_actualizado_mejorado.png")

def main():
    print("🎯 INICIANDO PROFUNDIZACIÓN AUTOMÁTICA MEJORADA")
    print("=" * 60)
    
    try:
        # Paso 1: Cargar análisis existente
        df = cargar_analisis_previo()
        
        # Paso 2: Identificar nodos específicos para profundizar
        nodos_relevantes = identificar_nodos_para_profundizar(df)
        
        if not nodos_relevantes:
            print("⚠️ No se encontraron nodos relevantes para profundizar")
            return
        
        # Paso 3: Generar consultas ESPECÍFICAS
        dimensiones_unicas = list(set([dim for _, dim in nodos_relevantes]))
        consultas = generar_consultas_profundizacion(dimensiones_unicas, nodos_relevantes)
        
        if not consultas:
            print("⚠️ No se pudieron generar consultas válidas")
            return
        
        # Paso 4: Guardar consultas
        guardar_consultas(consultas)
        
        # Paso 5: Ejecutar consultas
        resultados = ejecutar_consultas(consultas)
        
        if not resultados:
            print("⚠️ No se obtuvieron resultados de las consultas")
            return
        
        # Paso 6: Actualizar grafo SIN DUPLICADOS
        df_actualizado = actualizar_grafo(resultados)
        
        # Paso 7: Visualizar
        visualizar_grafo_actualizado(df_actualizado)
        
        print("\n🎉 ¡PROCESO MEJORADO COMPLETADO EXITOSAMENTE!")
        print("📁 Archivos generados:")
        print(f"   • Consultas: {CARPETA_CONSULTAS}/")
        print(f"   • Resultados: {CARPETA_RESULTADOS}/")
        print(f"   • CSV actualizado: analisis_grafo_mejorado.csv")
        print(f"   • Visualización: grafo_actualizado_mejorado.png")
        
        # Estadísticas finales
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        print(f"   • Nodos originales: {len(df)}")
        print(f"   • Nodos nuevos agregados: {len(df_actualizado) - len(df)}")
        print(f"   • Total nodos: {len(df_actualizado)}")
        
    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()