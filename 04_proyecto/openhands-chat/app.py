#!/usr/bin/env python3
"""
OpenHands Chat - Punto de entrada principal

⚠️ IMPORTANTE: Este archivo auto-instala TODAS las dependencias necesarias
   No necesitas ejecutar pip install ni start.sh manualmente
"""

import os
import sys
import subprocess

# =============================================================================
# AUTO-INSTALACIÓN DE DEPENDENCIAS (se ejecuta ANTES de cualquier import)
# =============================================================================
def ensure_dependencies():
    """Instala automáticamente todas las dependencias necesarias"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements.txt")
    
    # Lista de módulos críticos para verificar
    critical_modules = [
        ("uvicorn", "uvicorn"),
        ("fastapi", "fastapi"),
        ("jinja2", "jinja2"),
        ("aiohttp", "aiohttp"),
        ("httpx", "httpx"),
        ("cryptography", "cryptography"),
        ("git", "gitpython"),
        ("openhands", "openhands-sdk"),
    ]
    
    missing = []
    for module_name, pip_name in critical_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print("=" * 60)
        print("  📦 INSTALANDO DEPENDENCIAS FALTANTES...")
        print("=" * 60)
        print(f"  Módulos: {', '.join(missing)}")
        print()
        
        # Instalar desde requirements.txt si existe
        if os.path.exists(requirements_file):
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q", 
                "-r", requirements_file
            ])
        else:
            # Instalar módulos faltantes directamente
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q"
            ] + missing)
        
        print("  ✅ Dependencias instaladas correctamente")
        print("  🔄 Reiniciando aplicación...")
        print()
        
        # Reiniciar el proceso para cargar los nuevos módulos
        os.execv(sys.executable, [sys.executable] + sys.argv)

def ensure_code_server():
    """Instala code-server dentro del proyecto para que persista entre sesiones"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Instalar DENTRO del proyecto para que persista
    project_bin = os.path.join(script_dir, ".bin")
    code_server_path = os.path.join(project_bin, "bin", "code-server")
    
    # Agregar al PATH primero
    bin_path = os.path.join(project_bin, "bin")
    if bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
    # Solo instalar si NO existe (persiste entre sesiones)
    if not os.path.exists(code_server_path):
        print("=" * 60)
        print("  💻 INSTALANDO CODE-SERVER (primera vez)...")
        print("  📁 Ubicación: .bin/ (persiste entre sesiones)")
        print("=" * 60)
        print()
        
        # Crear directorio
        os.makedirs(project_bin, exist_ok=True)
        
        # Instalar code-server en el proyecto
        subprocess.run(
            f"curl -fsSL https://code-server.dev/install.sh | sh -s -- --method=standalone --prefix={project_bin}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print("  ✅ code-server instalado (no se reinstalará)")
        print()

# Ejecutar auto-instalación ANTES de cualquier otro import
ensure_dependencies()
ensure_code_server()

# =============================================================================
# IMPORTS PRINCIPALES (después de asegurar dependencias)
# =============================================================================
import signal
import atexit
import uvicorn
from config.settings import Settings

# PID del servidor de proyectos
projects_server_pid = None

def is_port_in_use(port: int) -> bool:
    """Verifica si un puerto está en uso"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_projects_server(projects_dir: str, port: int = 12001):
    """Inicia el servidor HTTP para proyectos si no está corriendo"""
    global projects_server_pid
    
    # Verificar si ya hay un servidor corriendo en el puerto
    if is_port_in_use(port):
        print(f"  ℹ️  Servidor de proyectos ya está corriendo en puerto {port}")
        return -1  # Ya corriendo
    
    # Asegurar que el directorio existe
    os.makedirs(projects_dir, exist_ok=True)
    
    # Iniciar nuevo servidor
    process = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        cwd=projects_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    projects_server_pid = process.pid
    return process.pid

def cleanup():
    """Limpia el servidor de proyectos al salir"""
    global projects_server_pid
    if projects_server_pid:
        try:
            os.kill(projects_server_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

def main():
    """Iniciar servidor"""
    settings = Settings()
    
    # Registrar cleanup al salir
    atexit.register(cleanup)
    
    # Iniciar servidor de proyectos (usa puerto del settings)
    projects_pid = start_projects_server(settings.projects_dir, settings.projects_port)
    
    print("=" * 60)
    print("  🤖 OPENHANDS CHAT")
    print("=" * 60)
    print(f"  🌐 Chat UI: http://{settings.host}:{settings.port}")
    print(f"  🌐 Proyectos: http://{settings.host}:{settings.projects_port}")
    print(f"  📁 Directorio: {settings.projects_dir}")
    print("=" * 60)
    print()
    print("  URLs Públicas:")
    print("  • Chat: https://work-1-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev")
    print("  • Proyectos: https://work-2-ycbycghbyxbnnhxb.prod-runtime.all-hands.dev/PROYECTO/")
    print()
    print(f"  Servidor de proyectos PID: {projects_pid}")
    print("  Presiona Ctrl+C para detener")
    print()
    
    uvicorn.run(
        "ui.web:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Desactivar reload para producción
        log_level="info"
    )

if __name__ == "__main__":
    main()
