"""
Servicio para manejar code-server (VS Code en el navegador)
"""

import os
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional

# Puerto para code-server (interno, proxy vía /code-server/)
CODE_SERVER_PORT = 8080
CODE_SERVER_PROCESS: Optional[subprocess.Popen] = None
CURRENT_PROJECT_PATH: Optional[str] = None

def get_code_server_path() -> str:
    """Obtiene la ruta de code-server"""
    # Buscar en ~/.local/bin primero
    local_path = os.path.expanduser("~/.local/bin/code-server")
    if os.path.exists(local_path):
        return local_path
    # Buscar en PATH
    result = subprocess.run(["which", "code-server"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return "code-server"  # Intentar nombre simple


def start_code_server(project_path: str) -> dict:
    """
    Inicia code-server para un proyecto específico
    
    Args:
        project_path: Ruta absoluta al directorio del proyecto
        
    Returns:
        dict con status y url
    """
    global CODE_SERVER_PROCESS, CURRENT_PROJECT_PATH
    
    # Verificar que el directorio existe
    if not os.path.isdir(project_path):
        return {"status": "error", "message": f"Directorio no existe: {project_path}"}
    
    # Si ya hay un code-server corriendo para el mismo proyecto, retornar
    if CODE_SERVER_PROCESS and CURRENT_PROJECT_PATH == project_path:
        if CODE_SERVER_PROCESS.poll() is None:  # Sigue corriendo
            return {
                "status": "running",
                "port": CODE_SERVER_PORT,
                "path": project_path
            }
    
    # Detener cualquier instancia anterior
    stop_code_server()
    
    # Iniciar code-server
    try:
        code_server_bin = get_code_server_path()
        cmd = [
            code_server_bin,
            "--bind-addr", f"0.0.0.0:{CODE_SERVER_PORT}",
            "--auth", "none",
            "--disable-telemetry",
            "--disable-update-check",
            project_path
        ]
        
        # Usar archivo temporal para logs
        log_file = open("/tmp/code-server.log", "w")
        
        # IMPORTANTE: Limpiar variable PORT del entorno porque code-server la lee
        env = os.environ.copy()
        env.pop('PORT', None)  # Remover PORT si existe
        
        CODE_SERVER_PROCESS = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
            env=env
        )
        
        CURRENT_PROJECT_PATH = project_path
        
        # Esperar a que inicie
        time.sleep(3)
        
        if CODE_SERVER_PROCESS.poll() is not None:
            # Proceso terminó - leer logs
            log_file.close()
            with open("/tmp/code-server.log", "r") as f:
                logs = f.read()
            return {"status": "error", "message": f"code-server falló: {logs[-500:]}"}
        
        return {
            "status": "started",
            "port": CODE_SERVER_PORT,
            "path": project_path,
            "pid": CODE_SERVER_PROCESS.pid
        }
        
    except FileNotFoundError:
        return {"status": "error", "message": "code-server no está instalado"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def stop_code_server() -> dict:
    """Detiene code-server si está corriendo"""
    global CODE_SERVER_PROCESS, CURRENT_PROJECT_PATH
    
    if CODE_SERVER_PROCESS:
        try:
            # Enviar SIGTERM al grupo de procesos
            os.killpg(os.getpgid(CODE_SERVER_PROCESS.pid), signal.SIGTERM)
            CODE_SERVER_PROCESS.wait(timeout=5)
        except ProcessLookupError:
            pass  # Ya terminó
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(CODE_SERVER_PROCESS.pid), signal.SIGKILL)
        except Exception:
            pass
        
        CODE_SERVER_PROCESS = None
        CURRENT_PROJECT_PATH = None
    
    return {"status": "stopped"}


def get_code_server_status() -> dict:
    """Retorna el estado actual de code-server"""
    global CODE_SERVER_PROCESS, CURRENT_PROJECT_PATH
    
    if CODE_SERVER_PROCESS and CODE_SERVER_PROCESS.poll() is None:
        return {
            "status": "running",
            "port": CODE_SERVER_PORT,
            "path": CURRENT_PROJECT_PATH,
            "pid": CODE_SERVER_PROCESS.pid
        }
    
    return {"status": "stopped"}


def is_main_project(repo_name: str) -> bool:
    """
    Verifica si es el proyecto principal (test03)
    El proyecto principal no debe tener code-server
    """
    # El repo principal es test03
    return repo_name and "test03" in repo_name.lower()
