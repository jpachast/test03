"""Router para gestionar el servidor de proyectos (puerto 12001)"""
import os
import subprocess
import socket
from fastapi import APIRouter

from config.settings import Settings

router = APIRouter(prefix="/api/projects-server", tags=["projects-server"])
settings = Settings()

# PID del servidor actual
_server_pid = None


def is_port_in_use(port: int) -> bool:
    """Verifica si un puerto está en uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_projects_server() -> int:
    """Inicia el servidor de proyectos si no está corriendo"""
    global _server_pid
    
    port = settings.projects_port  # 12001
    
    # Verificar si ya hay algo corriendo en el puerto
    if is_port_in_use(port):
        return _server_pid or -1  # Ya está corriendo
    
    # Iniciar servidor
    projects_dir = settings.projects_dir
    
    # Asegurar que el directorio existe
    os.makedirs(projects_dir, exist_ok=True)
    
    process = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        cwd=projects_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    _server_pid = process.pid
    return _server_pid


@router.get("/status")
async def get_status():
    """Obtener estado del servidor de proyectos"""
    port = settings.projects_port
    is_running = is_port_in_use(port)
    
    return {
        "running": is_running,
        "port": port,
        "pid": _server_pid if is_running else None,
        "url": f"https://work-2-pqlteoebiwavskzp.prod-runtime.all-hands.dev"
    }


@router.post("/ensure")
async def ensure_running():
    """Asegura que el servidor de proyectos está corriendo, lo inicia si es necesario"""
    port = settings.projects_port
    
    if is_port_in_use(port):
        return {
            "status": "already_running",
            "port": port,
            "message": "Servidor ya está corriendo"
        }
    
    # Iniciar servidor
    pid = start_projects_server()
    
    return {
        "status": "started",
        "port": port,
        "pid": pid,
        "message": "Servidor iniciado correctamente"
    }
