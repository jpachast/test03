#!/usr/bin/env python3
"""
OpenHands Chat - Punto de entrada principal

⚠️ IMPORTANTE: Este archivo auto-instala TODAS las dependencias necesarias
   No necesitas ejecutar pip install ni start.sh manualmente
   
   Incluye:
   - Dependencias Python (requirements.txt)
   - Playwright browsers (para navegación web)
   - Code-server (VS Code)
"""

import os
import sys
import subprocess

# =============================================================================
# AUTO-INSTALACIÓN DE DEPENDENCIAS (OPTIMIZADO - usa cache)
# =============================================================================
def ensure_dependencies():
    """Instala automáticamente todas las dependencias necesarias.
    
    OPTIMIZACIÓN: Usa un archivo de cache para evitar verificar en cada inicio.
    Solo verifica si el cache no existe o si requirements.txt cambió.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements.txt")
    cache_file = os.path.join(script_dir, "data", ".deps_installed")
    
    # Verificar si ya están instaladas (cache)
    # PERO siempre hacer una verificación rápida del módulo más crítico
    if os.path.exists(cache_file) and os.path.exists(requirements_file):
        cache_mtime = os.path.getmtime(cache_file)
        req_mtime = os.path.getmtime(requirements_file)
        if cache_mtime >= req_mtime:
            # Verificación de seguridad: probar que openhands-sdk existe
            try:
                __import__("openhands")
                __import__("fastapi")
                return  # Cache válido Y dependencias existen
            except ImportError:
                pass  # Cache inválido, continuar con verificación completa
    
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
        ("playwright", "playwright"),
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
        
        if os.path.exists(requirements_file):
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q", 
                "-r", requirements_file
            ])
        else:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q"
            ] + missing)
        
        print("  ✅ Dependencias instaladas correctamente")
        print("  🔄 Reiniciando aplicación...")
        print()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Crear cache de instalación
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        f.write('installed')


def ensure_playwright_browsers():
    """Instala los browsers de Playwright si no están instalados.
    
    Usa subprocess para verificar, evitando conflictos con asyncio loop.
    """
    # Verificar si chromium ya está instalado usando subprocess
    # (evita conflictos con asyncio loop de uvicorn)
    check_script = """
import sys
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
        sys.exit(0)  # Instalado
except Exception:
    sys.exit(1)  # No instalado
"""
    result = subprocess.run(
        [sys.executable, "-c", check_script],
        capture_output=True,
        timeout=30
    )
    
    if result.returncode == 0:
        return True  # Ya está instalado
    
    print("=" * 60)
    print("  🌐 INSTALANDO BROWSERS DE PLAYWRIGHT...")
    print("=" * 60)
    print()
    
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("  ✅ Chromium instalado correctamente")
    else:
        print(f"  ⚠️ Error instalando Chromium: {result.stderr}")
    
    print()
    return result.returncode == 0

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
ensure_playwright_browsers()  # Para navegación web
ensure_code_server()

# =============================================================================
# IMPORTS PRINCIPALES (después de asegurar dependencias)
# =============================================================================
import signal
import atexit
import uvicorn
import glob
import time as time_module
from config.settings import Settings
from core.app_server import cleanup_all_servers as cleanup_app_servers
from core.code_server import stop_all_code_servers

# PID file para tracking
PID_FILE = "/tmp/openhands-chat.pid"

# =============================================================================
# CLEANUP DE SERVIDORES HUÉRFANOS (ejecutar INMEDIATAMENTE al cargar)
# =============================================================================
def _initial_cleanup():
    """Limpia servidores huérfanos ANTES de iniciar (como OpenHands)"""
    print("  🧹 Limpiando servidores anteriores...")
    
    # 1. Matar proceso anterior si existe PID file
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGKILL)
            print(f"  ✓ Proceso anterior (PID {old_pid}) terminado")
        except:
            pass
        try:
            os.unlink(PID_FILE)
        except:
            pass
    
    # 2. Liberar puerto 12000 usando ss
    result = subprocess.run(
        "ss -tlnp 'sport = :12000' 2>/dev/null | grep -oP 'pid=\\K[0-9]+' | head -1",
        shell=True, capture_output=True, text=True
    )
    if result.stdout.strip():
        try:
            os.kill(int(result.stdout.strip()), signal.SIGKILL)
            print(f"  ✓ Puerto 12000 liberado")
        except:
            pass
    
    # 3. Matar code-servers huérfanos
    subprocess.run("pkill -9 -f 'code-server.*--bind-addr.*4000' 2>/dev/null", shell=True)
    
    # 4. Matar http.servers huérfanos en puertos 50000+
    subprocess.run("pkill -9 -f 'http.server.*5000' 2>/dev/null", shell=True)
    
    # 5. Limpiar locks
    for pattern in ["/tmp/openhands_*_locks/*.lock", "/tmp/code-server-*.lock"]:
        for f in glob.glob(pattern):
            try:
                os.unlink(f)
            except:
                pass
    
    time_module.sleep(0.5)
    print("  ✓ Limpieza completada")

# Ejecutar cleanup INMEDIATAMENTE
_initial_cleanup()

def cleanup_orphaned_servers():
    """
    Limpia servidores huérfanos de ejecuciones anteriores (como OpenHands).
    Se ejecuta al INICIAR la aplicación.
    """
    import glob
    import time
    
    print("  🧹 Limpiando servidores anteriores...")
    
    # Matar proceso anterior si existe PID file (PRIMERO)
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)
            time.sleep(1)  # Esperar que termine
            try:
                os.kill(old_pid, signal.SIGKILL)  # Forzar si no terminó
            except ProcessLookupError:
                pass
            print(f"  ✓ Proceso anterior (PID {old_pid}) terminado")
        except (ProcessLookupError, ValueError, FileNotFoundError):
            pass
        try:
            os.unlink(PID_FILE)
        except:
            pass
    
    # Liberar puerto principal (12000) - matar cualquier uvicorn en ese puerto
    # Usar ss + awk para encontrar el PID y matarlo
    result = subprocess.run(
        "ss -tlnp 'sport = :12000' | grep -oP 'pid=\\K[0-9]+' | head -1",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        try:
            old_port_pid = int(result.stdout.strip())
            os.kill(old_port_pid, signal.SIGKILL)
            print(f"  ✓ Proceso en puerto 12000 (PID {old_port_pid}) terminado")
            time.sleep(0.5)
        except:
            pass
    
    # Matar code-servers huérfanos por puerto
    for port in range(40000, 40100):
        subprocess.run(
            f"fuser -k {port}/tcp 2>/dev/null",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Matar app-servers huérfanos por puerto
    for port in range(50000, 50200):
        subprocess.run(
            f"fuser -k {port}/tcp 2>/dev/null",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Limpiar archivos de lock huérfanos
    for lock_file in glob.glob("/tmp/openhands_*_locks/*.lock"):
        try:
            os.unlink(lock_file)
        except:
            pass
    
    for lock_file in glob.glob("/tmp/code-server-*.lock"):
        try:
            os.unlink(lock_file)
        except:
            pass
    
    # Pequeña pausa para que los puertos se liberen
    time.sleep(0.5)
    
    print("  ✓ Limpieza completada")


def save_pid():
    """Guarda el PID actual en archivo"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def cleanup():
    """Limpia todos los servidores al salir"""
    print("\n  🧹 Limpiando servidores...")
    cleanup_app_servers()
    stop_all_code_servers()
    # Eliminar PID file
    try:
        os.unlink(PID_FILE)
    except:
        pass


def signal_handler(signum, frame):
    """Maneja señales SIGTERM/SIGINT para cleanup graceful"""
    print(f"\n  📍 Señal {signum} recibida, cerrando...")
    cleanup()
    sys.exit(0)


def main():
    """Iniciar servidor"""
    settings = Settings()
    
    # 1. Limpiar servidores huérfanos ANTES de iniciar
    cleanup_orphaned_servers()
    
    # 2. Guardar PID actual
    save_pid()
    
    # 3. Registrar handlers de señales (como OpenHands)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 4. Registrar cleanup al salir
    atexit.register(cleanup)
    
    print("=" * 60)
    print("  🤖 OPENHANDS CHAT")
    print("=" * 60)
    print(f"  🌐 Chat UI: http://{settings.host}:{settings.port}")
    print(f"  📁 Directorio proyectos: {settings.projects_dir}")
    print(f"  📍 PID: {os.getpid()}")
    print("=" * 60)
    print()
    print("  Arquitectura (como OpenHands):")
    print("  • Code-server: puertos dinámicos 40000-40099 (por conversación)")
    print("  • App-server: puertos dinámicos 50000-50199 (por conversación)")
    print("  • Cleanup automático de servidores huérfanos al iniciar")
    print()
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
