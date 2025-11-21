# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 15:18:15 2025

@author: jvera
"""

import sys
import json
import os
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

endpoint_url = "https://query.wikidata.org/sparql"

query = """#title: Grado 2 - Conexiones expandidas (PROPIEDADES ENRIQUECIDAS)
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?dimension ?propiedadGrado1 ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2 
       ?entidadIntermediaLabel ?entidadGrado2Label ?propiedadGrado1Label ?propiedadGrado2Label
WHERE {
  # Usar propiedades expandidas para mayor riqueza semántica
  VALUES (?dimension ?propiedadGrado1) {
    ("Identidad" wdt:P31)      # instancia de
    ("Identidad" wdt:P17)      # país
    ("Identidad" wdt:P495)     # país de origen
    ("Identidad" wdt:P361)     # parte de
    ("Identidad" wdt:P527)     # tiene parte(s)
    
    ("Geográfica" wdt:P131)    # ubicación administrativa
    ("Geográfica" wdt:P276)    # ubicación
    ("Geográfica" wdt:P625)    # coordenadas
    ("Geográfica" wdt:P17)     # país (también geográfico)
    ("Geográfica" wdt:P706)    # ubicado en terreno físico
    
    ("Temporal" wdt:P580)      # fecha de inicio
    ("Temporal" wdt:P582)      # fecha de fin
    ("Temporal" wdt:P585)      # punto en el tiempo
    ("Temporal" wdt:P571)      # fecha de creación
    ("Temporal" wdt:P575)      # fecha de descubrimiento
    
    ("Cultural" wdt:P135)      # movimiento
    ("Cultural" wdt:P361)      # parte de (también cultural)
    ("Cultural" wdt:P921)      # tema principal
    ("Cultural" wdt:P1269)     # facet of
    ("Cultural" wdt:P136)      # género
    
    ("Digital" wdt:P18)        # imagen
    ("Digital" wdt:P373)       # contenido multimedia
    ("Digital" wdt:P1617)      # URL de Spotify
    ("Digital" wdt:P856)       # sitio web oficial
    ("Digital" wdt:P953)       # URL completa
    
    ("Social" wdt:P112)        # fundado por
    ("Social" wdt:P710)        # participante
    ("Social" wdt:P127)        # propiedad de
    ("Social" wdt:P1830)       # propietario de
    ("Social" wdt:P749)        # organización matriz
    
    ("Patrimonio" wdt:P1435)   # patrimonio cultural
    ("Patrimonio" wdt:P6104)   # estado de conservación
    ("Patrimonio" wdt:P2184)   # historia del tema
    ("Patrimonio" wdt:P8415)   # patrimonio inmaterial
    ("Patrimonio" wdt:P6375)   # lugar del patrimonio cultural
    
    ("Religioso" wdt:P140)     # religión
    ("Religioso" wdt:P417)     # patrón santo
    ("Religioso" wdt:P2925)    # tradición religiosa
    
    ("Económico" wdt:P2139)    # ingresos totales
    ("Económico" wdt:P2130)    # costo
    ("Económico" wdt:P1114)    # cantidad
    
    ("Artístico" wdt:P170)     # creador
    ("Artístico" wdt:P175)     # ejecutante
    ("Artístico" wdt:P180)     # representa
  }
  
  # Grado 1: Qoyllur Rit'i -> Entidad Intermedia
  wd:Q2408955 ?propiedadGrado1 ?entidadIntermedia.
  FILTER(STRSTARTS(STR(?entidadIntermedia), "http://www.wikidata.org/entity/"))
  
  # Grado 2: Entidad Intermedia -> Entidad Grado 2
  ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2.
  FILTER(STRSTARTS(STR(?propiedadGrado2), "http://www.wikidata.org/prop/direct/"))
  FILTER(STRSTARTS(STR(?entidadGrado2), "http://www.wikidata.org/entity/"))
  
  # Obtener labels para mejor legibilidad
  OPTIONAL { ?entidadIntermedia rdfs:label ?entidadIntermediaLabel . FILTER(LANG(?entidadIntermediaLabel) = "es") }
  OPTIONAL { ?entidadGrado2 rdfs:label ?entidadGrado2Label . FILTER(LANG(?entidadGrado2Label) = "es") }
  OPTIONAL { ?propiedadGrado1 rdfs:label ?propiedadGrado1Label . FILTER(LANG(?propiedadGrado1Label) = "es") }
  OPTIONAL { ?propiedadGrado2 rdfs:label ?propiedadGrado2Label . FILTER(LANG(?propiedadGrado2Label) = "es") }
}
ORDER BY ?dimension ?propiedadGrado1
LIMIT 1500"""


def get_results(endpoint_url, query):
    user_agent = "QoyllurRiti-Analysis/1.0 (https://example.org; contact@example.org) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def main():
    try:
        print("Ejecutando consulta SPARQL en Wikidata...")
        results = get_results(endpoint_url, query)
        
        # Estructurar datos para JSON
        output_data = {
            "metadata": {
                "query_executed": query,
                "endpoint": endpoint_url,
                "execution_date": datetime.now().isoformat(),
                "total_results": len(results["results"]["bindings"]),
                "dimensions_included": [
                    "Identidad", "Geográfica", "Temporal", "Cultural", "Digital",
                    "Social", "Patrimonio", "Religioso", "Económico", "Artístico"
                ]
            },
            "results": []
        }

        for result in results["results"]["bindings"]:
            processed_result = {}
            for key, value in result.items():
                processed_result[key] = value["value"]
                
                # Extraer IDs cortos para mejor legibilidad
                if "wikidata.org" in value["value"]:
                    if "/entity/Q" in value["value"]:
                        processed_result[f"{key}_short"] = value["value"].split("/entity/Q")[1].split("/")[0]
                        processed_result[f"{key}_short"] = "Q" + processed_result[f"{key}_short"]
                    elif "/prop/direct/P" in value["value"]:
                        processed_result[f"{key}_short"] = value["value"].split("/prop/direct/P")[1].split("/")[0]
                        processed_result[f"{key}_short"] = "P" + processed_result[f"{key}_short"]
            
            output_data["results"].append(processed_result)

        # Crear directorio si no existe
        os.makedirs("resultados_queries", exist_ok=True)

        filename = os.path.join("resultados_queries", "qoyllur_riti_grado2_enriquecido.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Resultados guardados en: {filename}")
        print(f"📊 Total de registros: {len(output_data['results'])}")
        print(f"🎯 Dimensiones incluidas: {', '.join(output_data['metadata']['dimensions_included'])}")

        # Mostrar estadísticas por dimensión
        dimension_counts = {}
        for result in output_data["results"]:
            dim = result.get("dimension", "Sin dimensión")
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
        
        print("\n📈 Distribución por dimensión:")
        for dim, count in sorted(dimension_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {dim}: {count} resultados")

        # Preview de los primeros 3 resultados
        print("\n👀 Preview de los primeros 3 resultados:")
        for i, result in enumerate(output_data["results"][:3]):
            print(f"\n{i+1}. Dimensión: {result.get('dimension', 'N/A')}")
            print(f"   Propiedad G1: {result.get('propiedadGrado1Label', result.get('propiedadGrado1_short', 'N/A'))}")
            print(f"   Entidad Intermedia: {result.get('entidadIntermediaLabel', result.get('entidadIntermedia_short', 'N/A'))}")
            print(f"   Propiedad G2: {result.get('propiedadGrado2Label', result.get('propiedadGrado2_short', 'N/A'))}")
            print(f"   Entidad G2: {result.get('entidadGrado2Label', result.get('entidadGrado2_short', 'N/A'))}")

    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()