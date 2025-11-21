import json

# 1. Cargar el JSON crudo descargado de Wikidata
archivo_entrada = '04_tipos_entidades_RAW.json'
with open(archivo_entrada, 'r', encoding='utf-8') as f:
    datos_completos = json.load(f)

# 2. Extraer los resultados reales del formato WCQS
# Los datos están en datos_completos['results']['bindings']
datos = datos_completos['results']['bindings']

# 3. Palabras clave para buscar en etiquetas y descripciones
palabras_clave = {
    'es': ['fiesta', 'festividad', 'danza', 'peregrinación', 'carnaval', 'celebración', 
           'rito', 'tradición', 'patronal', 'virgen', 'señor', 'santo', 'carmen', 'qoyllur'],
    'qu': ['raymi'],  # Fiesta en quechua
    'en': ['festival', 'feast', 'celebration', 'pilgrimage', 'dance', 'ritual', 'tradition']
}

# 4. QIDs de tipos de entidades relevantes
tipos_relevantes_qids = {
    'Q200538',   # fiesta
    'Q375011',   # festividad religiosa
    'Q4579447',  # peregrinación
    'Q131036',   # danza
    'Q20203314'  # festividad religiosa
}

# 5. Función para extraer el valor de un campo del formato WCQS
def obtener_valor(campo):
    """Extrae el valor de un campo en formato WCQS, o cadena vacía si no existe"""
    if campo and 'value' in campo:
        return campo['value']
    return ''

# 6. Función para determinar si un ítem es relevante
def es_relevante(item):
    # Verificar por tipo de entidad (QIDs de festividades, danzas, etc.)
    tipo_url = obtener_valor(item.get('tipo'))
    if tipo_url:
        tipo_qid = tipo_url.split('/')[-1]  # Extraer QID de la URL
        if tipo_qid in tipos_relevantes_qids:
            return True

    # Verificar por palabras clave en labels y descripciones
    item_label = obtener_valor(item.get('itemLabel', {})).lower()
    item_desc = obtener_valor(item.get('itemDescription', {})).lower()
    texto_busqueda = f"{item_label} {item_desc}"
    
    for idioma, palabras in palabras_clave.items():
        for palabra in palabras:
            if palabra.lower() in texto_busqueda:
                return True
    
    return False

# 7. Filtrar los datos
datos_filtrados = [item for item in datos if es_relevante(item)]

# 8. Guardar el resultado filtrado (en el mismo formato WCQS para consistencia)
resultado_filtrado = {
    "head": datos_completos["head"],
    "results": {"bindings": datos_filtrados}
}

archivo_salida = '04_tipos_entidades_RAW_FILTRADO.json'
with open(archivo_salida, 'w', encoding='utf-8') as f:
    json.dump(resultado_filtrado, f, ensure_ascii=False, indent=2)

print(f"✅ Filtrado completado!")
print(f"   Entradas originales: {len(datos)}")
print(f"   Entradas filtradas: {len(datos_filtrados)}")
print(f"   Archivo guardado como: {archivo_salida}")

# 9. Mostrar preview de los resultados
if datos_filtrados:
    print("\n🔍 Primeras entradas filtradas:")
    for i, item in enumerate(datos_filtrados[:10]):
        label = obtener_valor(item.get('itemLabel', {}))
        tipo = obtener_valor(item.get('tipoLabel', {}))
        desc = obtener_valor(item.get('itemDescription', {}))
        print(f"   {i+1}. {label} | Tipo: {tipo} | Desc: {desc}")
else:
    print("\n❌ No se encontraron entidades relevantes con los criterios actuales.")
    
    # Diagnóstico: mostrar todos los tipos encontrados
    todos_tipos = set()
    for item in datos:
        tipo_label = obtener_valor(item.get('tipoLabel', {}))
        if tipo_label:
            todos_tipos.add(tipo_label)
    
    print(f"   Tipos encontrados en el RAW: {sorted(todos_tipos)}")