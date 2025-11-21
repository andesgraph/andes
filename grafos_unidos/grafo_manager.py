# -*- coding: utf-8 -*-
"""
grafo_manager.py - Módulo para manejar grafos de Wikidata
"""

import pickle
import networkx as nx
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import matplotlib.pyplot as plt

class GrafoManager:
    def __init__(self, entidad_wikidata):
        self.entidad_wikidata = entidad_wikidata
        self.q_id = entidad_wikidata.split('/')[-1] if '/' in entidad_wikidata else entidad_wikidata
        self.grafo = nx.DiGraph()
        
    def determinar_dimension(self, propiedad):
        """Determina la dimensión basada en la propiedad"""
        dimensiones_propiedades = {
            'P17': 'Geográfica', 'P131': 'Geográfica', 'P276': 'Geográfica', 'P625': 'Geográfica',
            'P135': 'Cultural', 'P361': 'Cultural', 'P921': 'Cultural', 'P136': 'Cultural',
            'P31': 'Identidad', 'P495': 'Identidad',
            'P1435': 'Patrimonio', 'P2184': 'Patrimonio', 'P8415': 'Patrimonio',
            'P571': 'Temporal', 'P585': 'Temporal', 'P580': 'Temporal',
            'P112': 'Social', 'P710': 'Social', 'P127': 'Social',
            'P140': 'Religioso', 'P417': 'Religioso', 'P2925': 'Religioso',
            'P18': 'Digital', 'P856': 'Digital', 'P953': 'Digital'
        }
        return dimensiones_propiedades.get(propiedad, 'N/A')
    
    def ejecutar_consulta_wikidata(self, query):
        """Ejecuta consulta SPARQL a Wikidata"""
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(180)
        
        try:
            sparql.setQuery(query)
            resultados = sparql.query().convert()
            return resultados['results']['bindings']
        except Exception as e:
            print(f"Error en consulta SPARQL: {e}")
            return None
    
    def crear_grafo_grado2(self):
        """Crea grafo de segundo grado desde Wikidata"""
        query = f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?propiedadGrado1 ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2 
               ?entidadIntermediaLabel ?entidadGrado2Label ?propiedadGrado1Label ?propiedadGrado2Label
        WHERE {{
          wd:{self.q_id} ?propiedadGrado1 ?entidadIntermedia.
          ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2.
          
          FILTER(STRSTARTS(STR(?entidadIntermedia), "http://www.wikidata.org/entity/Q"))
          FILTER(STRSTARTS(STR(?entidadGrado2), "http://www.wikidata.org/entity/Q"))
          FILTER(?entidadGrado2 != wd:{self.q_id})
          FILTER(?entidadIntermedia != ?entidadGrado2)
          
          OPTIONAL {{ ?entidadIntermedia rdfs:label ?entidadIntermediaLabel. 
                     FILTER(LANG(?entidadIntermediaLabel) = "es") }}
          OPTIONAL {{ ?entidadGrado2 rdfs:label ?entidadGrado2Label. 
                     FILTER(LANG(?entidadGrado2Label) = "es") }}
          OPTIONAL {{ ?propiedadGrado1 rdfs:label ?propiedadGrado1Label. 
                     FILTER(LANG(?propiedadGrado1Label) = "es") }}
          OPTIONAL {{ ?propiedadGrado2 rdfs:label ?propiedadGrado2Label. 
                     FILTER(LANG(?propiedadGrado2Label) = "es") }}
        }}
        LIMIT 500
        """
        
        print(f"Ejecutando consulta para {self.q_id}...")
        resultados = self.ejecutar_consulta_wikidata(query)
        
        if not resultados:
            return False
        
        self.grafo.add_node(self.q_id, label=self.entidad_wikidata, type='central', dimension='Central')
        
        for result in resultados:
            prop1 = result['propiedadGrado1']['value'].split('/')[-1]
            intermedia = result['entidadIntermedia']['value'].split('/')[-1]
            prop2 = result['propiedadGrado2']['value'].split('/')[-1]
            grado2 = result['entidadGrado2']['value'].split('/')[-1]
            
            dim1 = self.determinar_dimension(prop1)
            dim2 = self.determinar_dimension(prop2)
            
            self.grafo.add_node(intermedia, type='intermediate', dimension=dim1,
                              label=result.get('entidadIntermediaLabel', {}).get('value', ''))
            self.grafo.add_node(grado2, type='target', dimension=dim2,
                             label=result.get('entidadGrado2Label', {}).get('value', ''))
            
            self.grafo.add_edge(self.q_id, intermedia, label=prop1, dimension=dim1,
                              prop_label=result.get('propiedadGrado1Label', {}).get('value', ''))
            self.grafo.add_edge(intermedia, grado2, label=prop2, dimension=dim2,
                             prop_label=result.get('propiedadGrado2Label', {}).get('value', ''))
        
        print(f"✓ Grafo creado: {len(self.grafo.nodes())} nodos, {len(self.grafo.edges())} aristas")
        return True
    
    def calcular_metricas(self):
        """Calcula métricas del grafo"""
        return {
            'total_nodes': self.grafo.number_of_nodes(),
            'total_edges': self.grafo.number_of_edges(),
            'density': nx.density(self.grafo),
            'degree_centrality': nx.degree_centrality(self.grafo),
            'betweenness_centrality': nx.betweenness_centrality(self.grafo)
        }
    
    def exportar_a_csv(self, filename=None):
        """Exporta el análisis to CSV"""
        if filename is None:
            filename = f"analisis_grafo_{self.q_id}.csv"
        
        metrics = self.calcular_metricas()
        
        nodes_data = []
        for node in self.grafo.nodes():
            nodes_data.append({
                'nodo': node,
                'tipo': self.grafo.nodes[node].get('type', 'desconocido'),
                'dimension': self.grafo.nodes[node].get('dimension', 'N/A'),
                'grado_centralidad': metrics['degree_centrality'].get(node, 0),
                'intermediacion': metrics['betweenness_centrality'].get(node, 0)
            })
        
        df_nodes = pd.DataFrame(nodes_data)
        df_nodes.to_csv(filename, index=False, encoding='utf-8')
        print(f"✓ Resultados exportados a: {filename}")
        return df_nodes
    
    def visualizar_grafo(self, filename=None):
        """Visualiza y guarda el grafo"""
        if filename is None:
            filename = f"grafo_{self.q_id}.png"
        
        try:
            plt.figure(figsize=(16, 14))
            pos = nx.spring_layout(self.grafo, k=1, iterations=50)
            
            node_colors = []
            node_sizes = []
            for node in self.grafo.nodes():
                if node == self.q_id:
                    node_colors.append('red')
                    node_sizes.append(800)
                elif self.grafo.nodes[node].get('type') == 'intermediate':
                    node_colors.append('blue')
                    node_sizes.append(400)
                else:
                    node_colors.append('green')
                    node_sizes.append(200)
            
            nx.draw_networkx_nodes(self.grafo, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
            nx.draw_networkx_edges(self.grafo, pos, edge_color='gray', arrows=True, arrowsize=15, alpha=0.6)
            nx.draw_networkx_labels(self.grafo, pos, font_size=7, font_weight='bold')
            
            plt.title(f'Grafo de {self.q_id} en Wikidata (2do grado)\n', fontsize=14)
            plt.axis('off')
            plt.tight_layout()
            
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Visualización guardada como: {filename}")
            
        except Exception as e:
            print(f"Error al visualizar: {e}")
    
    def guardar_pkl(self, filename=None):
        """Guarda el grafo en formato PKL"""
        if filename is None:
            filename = f"grafo_{self.q_id}.pkl"
        
        with open(filename, 'wb') as f:
            pickle.dump(self.grafo, f)
        print(f"✓ Grafo guardado como PKL: {filename}")
        return filename

# Función de conveniencia
def crear_y_guardar_grafo(q_id):
    """Función helper para crear y guardar grafo"""
    manager = GrafoManager(q_id)
    if manager.crear_grafo_grado2():
        manager.exportar_a_csv()
        manager.visualizar_grafo()
        manager.guardar_pkl()
        return manager
    return None