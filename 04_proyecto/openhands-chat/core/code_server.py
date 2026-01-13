"""
Servicio para manejar code-server (VS Code en el navegador)
Implementación basada en OpenHands: UN code-server POR CONVERSACIÓN con puertos dinámicos
"""

import os
import subprocess
import signal
import socket
import time
import tempfile
import fcntl
from pathlib import Path
from typing import Optional, Dict, Any

# Rango de puertos para code-server (como OpenHands: 40000-49999)
CODE_SERVER_PORT_RANGE = (40000, 40099)

# Diccionario de instancias por conversation_id
# {conv_id: {"process": Popen, "port": int, "lock_fd": int, "path": str}}
CODE_SERVER_INSTANCES: Dict[int, Dict[str, Any]] = {}

# Para compatibilidad con código existente
CODE_SERVER_PORT: Optional[int] = None


def _get_lock_dir() -> str:
    """Directorio para archivos de lock"""
    lock_dir = os.path.join(tempfile.gettempdir(), 'openhands_chat_locks')
    os.makedirs(lock_dir, exist_ok=True)
    return lock_dir


def _check_port_available(port: int) -> bool:
    """Verifica si un puerto está disponible intentando hacer bind"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except OSError:
        return False


def _acquire_port_lock(port: int, timeout: float = 1.0) -> Optional[int]:
    """Adquiere un lock de archivo para el puerto"""
    lock_dir = _get_lock_dir()
    lock_path = os.path.join(lock_dir, f'port_{port}.lock')
    
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.write(fd, f'{port}\n'.encode())
                os.fsync(fd)
                return fd
            except (OSError, IOError):
                time.sleep(0.01)
        
        os.close(fd)
        return None
    except Exception:
        return None


def _release_port_lock(fd: int, port: int):
    """Libera el lock del puerto"""
    if fd is not None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            lock_path = os.path.join(_get_lock_dir(), f'port_{port}.lock')
            os.unlink(lock_path)
        except Exception:
            pass


def _find_available_port():
    """Encuentra un puerto disponible con lock"""
    min_port, max_port = CODE_SERVER_PORT_RANGE
    
    for port in range(min_port, max_port + 1):
        fd = _acquire_port_lock(port)
        if fd is not None:
            if _check_port_available(port):
                return port, fd
            else:
                _release_port_lock(fd, port)
    
    return None, None


def get_code_server_path() -> str:
    """Obtiene la ruta de code-server"""
    local_path = os.path.expanduser("~/.local/bin/code-server")
    if os.path.exists(local_path):
        return local_path
    result = subprocess.run(["which", "code-server"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return "code-server"


def start_code_server(project_path: str, conversation_id: int = 0) -> dict:
    """
    Inicia code-server para una conversación específica.
    Cada conversación tiene su propio code-server (como OpenHands).
    """
    global CODE_SERVER_PORT
    
    if not os.path.isdir(project_path):
        return {"status": "error", "message": f"Directorio no existe: {project_path}"}
    
    # Si ya hay un code-server para esta conversación, reutilizarlo
    if conversation_id in CODE_SERVER_INSTANCES:
        instance = CODE_SERVER_INSTANCES[conversation_id]
        if instance["process"] and instance["process"].poll() is None:
            CODE_SERVER_PORT = instance["port"]
            return {
                "status": "running",
                "port": instance["port"],
                "path": project_path,
                "conversation_id": conversation_id,
                "reused": True
            }
        else:
            # Proceso muerto, limpiar
            stop_code_server(conversation_id)
    
    # Encontrar puerto disponible
    port, lock_fd = _find_available_port()
    if port is None:
        return {"status": "error", "message": "No hay puertos disponibles"}
    
    # Iniciar code-server
    try:
        code_server_bin = get_code_server_path()
        cmd = [
            code_server_bin,
            "--bind-addr", f"0.0.0.0:{port}",
            "--auth", "none",
            "--disable-telemetry",
            "--disable-update-check",
            project_path
        ]
        
        log_file = open(f"/tmp/code-server-{conversation_id}.log", "w")
        env = os.environ.copy()
        env.pop('PORT', None)
        
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
            env=env
        )
        
        # Guardar instancia
        CODE_SERVER_INSTANCES[conversation_id] = {
            "process": process,
            "port": port,
            "lock_fd": lock_fd,
            "path": project_path
        }
        CODE_SERVER_PORT = port
        
        time.sleep(3)
        
        if process.poll() is not None:
            log_file.close()
            with open(f"/tmp/code-server-{conversation_id}.log", "r") as f:
                logs = f.read()
            stop_code_server(conversation_id)
            return {"status": "error", "message": f"code-server falló: {logs[-500:]}"}
        
        return {
            "status": "started",
            "port": port,
            "path": project_path,
            "conversation_id": conversation_id,
            "pid": process.pid
        }
        
    except FileNotFoundError:
        _release_port_lock(lock_fd, port)
        return {"status": "error", "message": "code-server no está instalado"}
    except Exception as e:
        _release_port_lock(lock_fd, port)
        return {"status": "error", "message": str(e)}


def stop_code_server(conversation_id: int = None) -> dict:
    """Detiene code-server de una conversación específica o todas"""
    global CODE_SERVER_PORT
    
    if conversation_id is not None:
        # Detener solo la instancia específica
        if conversation_id in CODE_SERVER_INSTANCES:
            instance = CODE_SERVER_INSTANCES[conversation_id]
            if instance["process"]:
                try:
                    os.killpg(os.getpgid(instance["process"].pid), signal.SIGTERM)
                    instance["process"].wait(timeout=5)
                except Exception:
                    pass
            if instance.get("lock_fd") and instance.get("port"):
                _release_port_lock(instance["lock_fd"], instance["port"])
            del CODE_SERVER_INSTANCES[conversation_id]
    else:
        # Detener todas las instancias
        for conv_id in list(CODE_SERVER_INSTANCES.keys()):
            stop_code_server(conv_id)
    
    CODE_SERVER_PORT = None
    return {"status": "stopped"}


def get_code_server_status(conversation_id: int = None) -> dict:
    """Retorna el estado de code-server para una conversación"""
    
    if conversation_id is not None and conversation_id in CODE_SERVER_INSTANCES:
        instance = CODE_SERVER_INSTANCES[conversation_id]
        if instance["process"] and instance["process"].poll() is None:
            return {
                "status": "running",
                "port": instance["port"],
                "path": instance["path"],
                "conversation_id": conversation_id,
                "pid": instance["process"].pid
            }
    
    # Si no se especifica conversation_id, devolver el último puerto activo
    if CODE_SERVER_PORT:
        return {
            "status": "running",
            "port": CODE_SERVER_PORT
        }
    
    return {"status": "stopped"}


def is_main_project(repo_name: str) -> bool:
    """
    Verifica si es el proyecto principal (test03)
    El proyecto principal no debe tener code-server
    """
    return repo_name and "test03" in repo_name.lower()
