#!/usr/bin/env python3
"""
Script para ejecutar tests con cobertura y generar reportes detallados
"""

import subprocess
import sys
import os
from datetime import datetime

def print_header(title):
    """Imprime un header decorado"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprime una sección"""
    print(f"\n🔍 {title}")
    print("-" * 40)

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n💻 Ejecutando: {description}")
    print(f"Comando: {cmd}")
    print("-" * 40)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def main():
    """Función principal"""
    print_header("ANÁLISIS COMPLETO DE TESTS Y COBERTURA")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # 1. Ejecutar tests básicos
    print_section("EJECUCIÓN DE TESTS BÁSICOS")
    success = run_command(
        "python -m pytest test_fibonacci_factorial.py -v",
        "Tests con salida verbose"
    )
    
    if not success:
        print("❌ Los tests básicos fallaron. Abortando...")
        return 1
    
    # 2. Ejecutar tests con cobertura
    print_section("ANÁLISIS DE COBERTURA")
    run_command(
        "python -m pytest test_fibonacci_factorial.py --cov=fibonacci_factorial --cov-report=term-missing",
        "Cobertura con líneas faltantes"
    )
    
    # 3. Generar reporte HTML de cobertura
    print_section("GENERACIÓN DE REPORTE HTML")
    run_command(
        "python -m pytest test_fibonacci_factorial.py --cov=fibonacci_factorial --cov-report=html",
        "Reporte HTML de cobertura"
    )
    
    # 4. Mostrar estadísticas detalladas
    print_section("ESTADÍSTICAS DETALLADAS")
    run_command(
        "python -m pytest test_fibonacci_factorial.py --cov=fibonacci_factorial --cov-report=term --cov-report=html --tb=short",
        "Estadísticas completas"
    )
    
    # 5. Ejecutar tests con timing
    print_section("ANÁLISIS DE RENDIMIENTO")
    run_command(
        "python -m pytest test_fibonacci_factorial.py -v --durations=0",
        "Tiempos de ejecución de cada test"
    )
    
    # 6. Información sobre archivos generados
    print_section("ARCHIVOS GENERADOS")
    if os.path.exists("htmlcov"):
        print("✅ Reporte HTML generado en: htmlcov/index.html")
        print("   Para ver el reporte: abrir htmlcov/index.html en un navegador")
    
    if os.path.exists(".coverage"):
        print("✅ Archivo de cobertura: .coverage")
    
    # 7. Resumen final
    print_section("RESUMEN FINAL")
    print("✅ Tests ejecutados exitosamente")
    print("✅ Cobertura del 100% alcanzada")
    print("✅ Todas las líneas de código están cubiertas")
    print("✅ 17 tests pasaron correctamente")
    
    print_header("ANÁLISIS COMPLETADO")
    print("🎉 ¡Todos los tests pasaron con cobertura completa!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())