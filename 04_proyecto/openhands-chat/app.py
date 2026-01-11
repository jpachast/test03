#!/usr/bin/env python3
"""
OpenHands Chat - Punto de entrada principal
"""

import os
import subprocess
import signal
import atexit
import uvicorn
from config.settings import Settings

# PID del servidor de proyectos
projects_server_pid = None

def start_projects_server(projects_dir: str, port: int = 12001):
    """Inicia el servidor HTTP para proyectos"""
    global projects_server_pid
    
    # Matar servidor anterior si existe
    subprocess.run(
        f'pkill -f "http.server {port}"',
        shell=True,
        stderr=subprocess.DEVNULL
    )
    
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
    
    # Iniciar servidor de proyectos
    projects_pid = start_projects_server(settings.projects_dir, 12001)
    
    print("=" * 60)
    print("  🤖 OPENHANDS CHAT")
    print("=" * 60)
    print(f"  🌐 Chat UI: http://{settings.host}:{settings.port}")
    print(f"  🌐 Proyectos: http://{settings.host}:12001")
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
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
