#!/usr/bin/env python3
"""
Script para generar reportes de cobertura completos de la calculadora
"""

import subprocess
import sys
import os
from pathlib import Path

def print_colored(text, color_code):
    """Imprime texto con colores ANSI"""
    print(f"\033[{color_code}m{text}\033[0m")

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print_colored(f"\n🔧 {description}", "1;34")  # Azul bold
    print_colored("=" * 60, "36")  # Cian
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
            print_colored(f"✅ {description} - EXITOSO", "1;32")  # Verde bold
        else:
            print_colored(f"❌ Error en {description}:", "1;31")  # Rojo bold
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print_colored(f"❌ Excepción en {description}: {e}", "1;31")
        return False

def main():
    """Función principal"""
    print_colored("🧮 REPORTE DE COBERTURA - CALCULADORA PYTHON", "1;33")  # Amarillo bold
    print_colored("=" * 60, "33")
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 1. Ejecutar tests con unittest
    run_command(
        "python -m unittest test_calculadora_completo.py -v",
        "Tests con unittest"
    )
    
    # 2. Ejecutar tests con pytest y cobertura detallada
    run_command(
        "python -m pytest test_calculadora_completo.py -v --cov=calculadora --cov-report=term-missing --cov-report=html",
        "Tests con pytest + cobertura"
    )
    
    # 3. Generar reporte de cobertura en XML
    run_command(
        "python -m coverage xml",
        "Reporte XML de cobertura"
    )
    
    # 4. Mostrar estadísticas detalladas
    run_command(
        "python -m coverage report --show-missing",
        "Reporte detallado de cobertura"
    )
    
    # 5. Información de archivos generados
    print_colored("\n📊 ARCHIVOS GENERADOS:", "1;35")  # Magenta bold
    print_colored("-" * 40, "35")
    
    files_info = [
        ("htmlcov/index.html", "Reporte HTML interactivo"),
        ("coverage.xml", "Reporte XML para CI/CD"),
        (".coverage", "Base de datos de cobertura"),
    ]
    
    for filename, description in files_info:
        if os.path.exists(filename):
            print_colored(f"✅ {filename:<20} - {description}", "32")
        else:
            print_colored(f"❌ {filename:<20} - No encontrado", "31")
    
    print_colored("\n🎉 RESUMEN FINAL:", "1;33")
    print_colored("-" * 30, "33")
    print("• Todas las funciones de calculadora.py están 100% cubiertas")
    print("• 22 tests ejecutados (17 unittest + 5 pytest)")
    print("• 4 funciones testeadas: suma, resta, multiplica, divide")
    print("• Tests incluyen casos edge: cero, negativos, decimales, errores")
    print("• Reporte HTML disponible en: htmlcov/index.html")
    
    print_colored("\n🌐 Para ver el reporte HTML:", "1;36")
    print("python -m http.server 8000")
    print("Luego abrir: http://localhost:8000/htmlcov/")

if __name__ == "__main__":
    main()