# -*- coding: utf-8 -*-
"""
crear_grafo_virgen.py - Crea y guarda grafo para Celebración a la Virgen
"""

from grafo_manager import GrafoManager, crear_y_guardar_grafo

def main():
    print("🙏 CREANDO GRAFO PARA CELEBRACIÓN A LA VIRGEN (Q60643381)")
    print("=" * 55)
    
    # Crear y guardar grafo
    manager_virgen = crear_y_guardar_grafo("Q60643381")
    
    if manager_virgen:
        print("\n✅ Proceso completado para Celebración a la Virgen")
        print(f"Archivos creados:")
        print(f"  • grafo_Q60643381.pkl")
        print(f"  • grafo_Q60643381.png")
        print(f"  • analisis_grafo_Q60643381.csv")
    else:
        print("❌ Error al crear grafo para Celebración a la Virgen")

if __name__ == "__main__":
    main()