# integrar_grafos_corregido.py
import json
import pandas as pd
from collections import defaultdict

def cargar_y_procesar_json(nombre_archivo, tipo_dato):
    """Carga un JSON y extrae los datos relevantes"""
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Extraer bindings para formato WCQS
        if isinstance(datos, dict) and 'results' in datos and 'bindings' in datos['results']:
            items = datos['results']['bindings']
            print(f"✅ {len(items)} items de {tipo_dato} (formato WCQS)")
        else:
            items = datos  # Asumir que ya es una lista directa
            print(f"✅ {len(items)} items de {tipo_dato} (formato lista)")
            
        return items
        
    except FileNotFoundError:
        print(f"⚠️  Archivo {nombre_archivo} no encontrado")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando {nombre_archivo}: {e}")
        return []

def extraer_valor_simple(campo):
    """Extrae el valor de manera más robusta"""
    if not campo:
        return ''
    
    if isinstance(campo, dict):
        return campo.get('value', '')
    elif isinstance(campo, str):
        return campo
    else:
        return str(campo)

def construir_grafo_unificado():
    # LISTA ACTUALIZADA con los nombres exactos de tus archivos
    datasets = {
        'nucleo': ('01_nucleo_entidades_principales.json', 'núcleo'),
        'geografia': ('02_conexiones_geograficas_FILTRADO.json', 'geografía'), 
        'unesco': ('03_patrimonio_unesco.json', 'UNESCO'),
        'festividades': ('04_tipos_entidades_FILTRADO.json', 'festividades'),  # NOMBRE CORREGIDO
        'relaciones': ('05_conexiones_cruzadas.json', 'relaciones')
    }
    
    grafo = {'nodos': defaultdict(dict), 'enlaces': []}
    todos_ids = set()
    
    for key, (archivo, tipo_dato) in datasets.items():
        print(f"\n📂 Procesando {archivo}...")
        items = cargar_y_procesar_json(archivo, tipo_dato)
        
        for item in items:
            # EXTRAER ID de diferentes maneras según el formato
            posibles_ids = [
                item.get('item'), item.get('festividad'), 
                item.get('item1'), item.get('item2'),
                item.get('adminArea'), item.get('entidadIntermedia')
            ]
            
            item_id = None
            for posible_id in posibles_ids:
                if posible_id:
                    item_id = extraer_valor_simple(posible_id)
                    if item_id and 'entity/Q' in item_id:
                        break
            
            if not item_id:
                continue
                
            # Extraer QID
            if 'entity/Q' in item_id:
                qid = item_id.split('/')[-1]
                todos_ids.add(qid)
            else:
                continue
            
            # Crear nodo si no existe
            if qid not in grafo['nodos']:
                grafo['nodos'][qid] = {
                    'id': qid,
                    'label': extraer_valor_simple(item.get('itemLabel') or item.get('festividadLabel') or item.get('item1Label') or item.get('adminAreaLabel')),
                    'description': extraer_valor_simple(item.get('itemDescription', '')),
                    'tipo': extraer_valor_simple(item.get('tipoLabel', '')),
                    'categorias': set([tipo_dato]),
                    'propiedades': defaultdict(list)
                }
            else:
                grafo['nodos'][qid]['categorias'].add(tipo_dato)
            
            # PROCESAR PROPIEDADES (más robusto)
            for prop_key in ['propiedad', 'otraPropiedad', 'propiedad1', 'propiedad2']:
                if prop_key in item:
                    prop_val = extraer_valor_simple(item[prop_key])
                    prop_label = extraer_valor_simple(item.get(f'{prop_key}Label', prop_val))
                    
                    # Buscar valor asociado
                    valor_keys = ['valor', 'valor1', 'valor2', 'entidadGrado2', 'entidadIntermedia']
                    valor = None
                    for vk in valor_keys:
                        if vk in item:
                            valor = extraer_valor_simple(item[vk])
                            if valor: break
                    
                    if prop_val and valor:
                        grafo['nodos'][qid]['propiedades'][prop_label].append({
                            'valor': valor,
                            'valor_label': extraer_valor_simple(item.get('valorLabel', valor))
                        })
            
            # EXTRAER ENLACES para relaciones
            if 'item1' in item and 'item2' in item:
                origen = extraer_valor_simple(item['item1']).split('/')[-1]
                destino = extraer_valor_simple(item['item2']).split('/')[-1]
                prop_label = extraer_valor_simple(item.get('propiedadLabel', ''))
                
                if origen and destino and prop_label:
                    grafo['enlaces'].append({
                        'origen': origen, 'destino': destino, 'tipo': prop_label
                    })
    
    # Limpiar estructura final
    for nodo_id, nodo_data in grafo['nodos'].items():
        nodo_data['categorias'] = list(nodo_data['categorias'])
        nodo_data['propiedades'] = dict(nodo_data['propiedades'])
    
    print(f"\n🎯 Grafo unificado creado:")
    print(f"   Nodos únicos: {len(grafo['nodos'])}")
    print(f"   Enlaces: {len(grafo['enlaces'])}")
    print(f"   IDs únicos encontrados: {len(todos_ids)}")
    
    return grafo

# El resto del script igual...
def guardar_grafo(grafo, nombre_archivo):
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(grafo, f, ensure_ascii=False, indent=2)
    print(f"💾 Grafo guardado como {nombre_archivo}")

def generar_estadisticas(grafo):
    print("\n📊 ESTADÍSTICAS DEL GRAFO:")
    print(f"   Total de nodos: {len(grafo['nodos'])}")
    print(f"   Total de enlaces: {len(grafo['enlaces'])}")
    
    categorias_count = defaultdict(int)
    for nodo in grafo['nodos'].values():
        for cat in nodo['categorias']:
            categorias_count[cat] += 1
    
    print("\n   Nodos por categoría:")
    for cat, count in categorias_count.items():
        print(f"     {cat}: {count}")

if __name__ == "__main__":
    print("🚀 Integrando todos los JSONs (versión corregida)...")
    grafo = construir_grafo_unificado()
    guardar_grafo(grafo, '00_grafo_cultural_completo_CORREGIDO.json')
    generar_estadisticas(grafo)