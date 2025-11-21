# -*- coding: utf-8 -*-
"""
crear_grafo_qoyllur.py - Crea y guarda grafo para Qoyllur Riti
"""

from grafo_manager import GrafoManager, crear_y_guardar_grafo

def main():
    print("🎭 CREANDO GRAFO PARA QOYLLUR RIT'I (Q2408955)")
    print("=" * 50)
    
    # Crear y guardar grafo
    manager_qoyllur = crear_y_guardar_grafo("Q2408955")
    
    if manager_qoyllur:
        print("\n✅ Proceso completado para Qoyllur Riti")
        print(f"Archivos creados:")
        print(f"  • grafo_Q2408955.pkl")
        print(f"  • grafo_Q2408955.png")
        print(f"  • analisis_grafo_Q2408955.csv")
    else:
        print("❌ Error al crear grafo para Qoyllur Riti")

if __name__ == "__main__":
    main()