"""
App Server Manager - Servidor de aplicaciones por conversación
Implementación idéntica a OpenHands con puertos dinámicos y file-based locking
"""
import os
import subprocess
import socket
import fcntl
import time
from typing import Dict, Optional, Tuple

# Rangos de puertos como OpenHands
APP_PORT_RANGE_1 = (50000, 50099)  # Primer puerto de app
APP_PORT_RANGE_2 = (50100, 50199)  # Segundo puerto de app (backup)

# Instancias de servidores por conversación
APP_SERVER_INSTANCES: Dict[int, dict] = {}

# Directorio para locks
LOCK_DIR = "/tmp/openhands_app_locks"
os.makedirs(LOCK_DIR, exist_ok=True)


def _is_port_available(port: int) -> bool:
    """Verifica si un puerto está disponible"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False


def _acquire_port_lock(port: int) -> Optional[int]:
    """Adquiere un lock exclusivo para un puerto (file-based locking)"""
    lock_file = os.path.join(LOCK_DIR, f"port_{port}.lock")
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (OSError, IOError):
        return None


def _release_port_lock(lock_fd: Optional[int], port: int):
    """Libera el lock de un puerto"""
    if lock_fd is not None:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        except:
            pass
    # Limpiar archivo de lock
    lock_file = os.path.join(LOCK_DIR, f"port_{port}.lock")
    try:
        os.unlink(lock_file)
    except:
        pass


def find_available_port(port_range: Tuple[int, int]) -> Tuple[Optional[int], Optional[int]]:
    """
    Encuentra un puerto disponible con locking (como OpenHands)
    Returns: (port, lock_fd) o (None, None) si no hay puerto disponible
    """
    min_port, max_port = port_range
    
    for port in range(min_port, max_port + 1):
        # Intentar adquirir lock
        lock_fd = _acquire_port_lock(port)
        if lock_fd is None:
            continue
        
        # Verificar que el puerto está disponible
        if _is_port_available(port):
            return port, lock_fd
        
        # Puerto no disponible, liberar lock e intentar siguiente
        _release_port_lock(lock_fd, port)
    
    return None, None


def start_app_server(workspace_path: str, conversation_id: int) -> dict:
    """
    Inicia un servidor de aplicaciones para una conversación específica.
    Cada conversación tiene su propio servidor en puerto dinámico.
    """
    # Verificar si ya hay un servidor para esta conversación
    if conversation_id in APP_SERVER_INSTANCES:
        instance = APP_SERVER_INSTANCES[conversation_id]
        if instance["process"] and instance["process"].poll() is None:
            return {
                "status": "running",
                "port": instance["port"],
                "path": instance["path"],
                "conversation_id": conversation_id
            }
        else:
            # Proceso terminado, limpiar
            stop_app_server(conversation_id)
    
    # Verificar que el workspace existe
    if not os.path.isdir(workspace_path):
        return {"status": "error", "message": f"Workspace no existe: {workspace_path}"}
    
    # Encontrar puerto disponible con locking
    port, lock_fd = find_available_port(APP_PORT_RANGE_1)
    
    if port is None:
        # Intentar con el segundo rango
        port, lock_fd = find_available_port(APP_PORT_RANGE_2)
    
    if port is None:
        return {"status": "error", "message": "No hay puertos disponibles para el servidor de app"}
    
    try:
        # Iniciar servidor HTTP con anti-caché
        log_file = open(f"/tmp/app-server-{conversation_id}.log", "w")
        
        # Usar nuestro servidor personalizado con headers anti-caché
        server_script = os.path.join(os.path.dirname(__file__), "simple_http_server.py")
        
        process = subprocess.Popen(
            ["python3", server_script, str(port)],
            cwd=workspace_path,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        
        # Guardar instancia
        APP_SERVER_INSTANCES[conversation_id] = {
            "process": process,
            "port": port,
            "lock_fd": lock_fd,
            "path": workspace_path,
            "log_file": log_file
        }
        
        # Verificar rápido que inició
        time.sleep(0.15)  # Reducido de 0.3s a 0.15s
        
        if process.poll() is not None:
            # Proceso falló
            log_file.close()
            _release_port_lock(lock_fd, port)
            del APP_SERVER_INSTANCES[conversation_id]
            return {"status": "error", "message": "El servidor falló al iniciar"}
        
        return {
            "status": "started",
            "port": port,
            "path": workspace_path,
            "conversation_id": conversation_id,
            "pid": process.pid
        }
        
    except Exception as e:
        _release_port_lock(lock_fd, port)
        return {"status": "error", "message": str(e)}


def stop_app_server(conversation_id: int) -> dict:
    """Detiene el servidor de app de una conversación"""
    if conversation_id not in APP_SERVER_INSTANCES:
        return {"status": "not_running"}
    
    instance = APP_SERVER_INSTANCES[conversation_id]
    
    # Terminar proceso
    if instance["process"]:
        try:
            instance["process"].terminate()
            instance["process"].wait(timeout=5)
        except:
            try:
                instance["process"].kill()
            except:
                pass
    
    # Cerrar log file
    if instance.get("log_file"):
        try:
            instance["log_file"].close()
        except:
            pass
    
    # Liberar lock
    _release_port_lock(instance.get("lock_fd"), instance["port"])
    
    del APP_SERVER_INSTANCES[conversation_id]
    
    return {"status": "stopped", "conversation_id": conversation_id}


def get_app_server_status(conversation_id: int = None) -> dict:
    """Obtiene el estado del servidor de app"""
    if conversation_id is not None and conversation_id in APP_SERVER_INSTANCES:
        instance = APP_SERVER_INSTANCES[conversation_id]
        if instance["process"] and instance["process"].poll() is None:
            return {
                "status": "running",
                "port": instance["port"],
                "path": instance["path"],
                "conversation_id": conversation_id,
                "pid": instance["process"].pid
            }
    
    # Buscar cualquier servidor activo
    for conv_id, instance in APP_SERVER_INSTANCES.items():
        if instance["process"] and instance["process"].poll() is None:
            return {
                "status": "running",
                "port": instance["port"],
                "path": instance["path"],
                "conversation_id": conv_id
            }
    
    return {"status": "stopped"}


def get_app_url(conversation_id: int) -> Optional[str]:
    """Obtiene la URL del servidor de app para una conversación"""
    if conversation_id in APP_SERVER_INSTANCES:
        instance = APP_SERVER_INSTANCES[conversation_id]
        if instance["process"] and instance["process"].poll() is None:
            return f"http://localhost:{instance['port']}"
    return None


def cleanup_all_servers():
    """Limpia todos los servidores de app (llamar al cerrar la aplicación)"""
    for conv_id in list(APP_SERVER_INSTANCES.keys()):
        stop_app_server(conv_id)
