"""Rutas de configuración"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from config.database import Database

router = APIRouter(prefix="/api/settings", tags=["settings"])
db = Database()


@router.get("/api-key")
async def get_api_key():
    """Obtener API key de Gemini"""
    value = db.get_api_key()
    return JSONResponse({"value": value})


@router.post("/api-key")
async def save_api_key(api_key: str = Form(...)):
    """Guardar API key de Gemini (visión)"""
    db.set_api_key(api_key)
    return JSONResponse({"status": "ok", "message": "API key guardada"})


@router.get("/deepseek-key")
async def get_deepseek_key():
    """Obtener API key de DeepSeek"""
    value = db.get_setting("deepseek_api_key")
    return JSONResponse({"value": value})


@router.post("/deepseek-key")
async def save_deepseek_key(api_key: str = Form(...)):
    """Guardar API key de DeepSeek (código)"""
    db.set_setting("deepseek_api_key", api_key, encrypt=True)
    return JSONResponse({"status": "ok", "message": "DeepSeek API key guardada"})


@router.post("/model")
async def save_model(model: str = Form(...)):
    """Guardar modelo por defecto"""
    db.set_setting("default_model", model)
    return JSONResponse({"status": "ok"})


# === GROQ (Multi-LLM) ===

@router.get("/groq")
async def get_groq_status():
    """Verificar si Groq está configurado"""
    key = db.get_setting('groq_api_key', '')
    return JSONResponse({"connected": bool(key)})


@router.post("/groq")
async def save_groq_api_key(request: Request):
    """Guardar Groq API key"""
    try:
        data = await request.json()
        api_key = data.get("api_key", "").strip()
        
        if not api_key:
            return JSONResponse({"success": False, "error": "API key requerida"})
        
        if not api_key.startswith("gsk_"):
            return JSONResponse({"success": False, "error": "API key debe comenzar con 'gsk_'"})
        
        db.set_setting('groq_api_key', api_key, encrypt=True)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.delete("/groq")
async def delete_groq_api_key():
    """Eliminar Groq API key"""
    db.set_setting('groq_api_key', '')
    return JSONResponse({"success": True})


# === TAVILY ===

@router.get("/tavily")
async def get_tavily_status():
    """Verificar si Tavily está configurado"""
    connected = db.has_tavily_api_key()
    return JSONResponse({"connected": connected})


@router.post("/tavily")
async def save_tavily_api_key(request: Request):
    """Guardar Tavily API key"""
    try:
        data = await request.json()
        api_key = data.get("api_key", "").strip()
        
        if not api_key:
            return JSONResponse({"success": False, "error": "API key requerida"})
        
        # Validar que la key tenga formato razonable
        if len(api_key) < 10:
            return JSONResponse({"success": False, "error": "API key inválida"})
        
        db.set_tavily_api_key(api_key)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.delete("/tavily")
async def delete_tavily_api_key():
    """Eliminar Tavily API key"""
    db.set_tavily_api_key("")
    return JSONResponse({"success": True})


# ============================================
# Hetzner Cloud Endpoints
# ============================================

@router.get("/hetzner")
async def get_hetzner_status():
    """Verificar estado de Hetzner"""
    token = db.get_setting('hetzner_api_token', '')
    if not token:
        return JSONResponse({"connected": False})
    
    # Verificar token y contar servidores
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hetzner.cloud/v1/servers",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                return JSONResponse({
                    "connected": True,
                    "servers": len(data.get("servers", []))
                })
            else:
                return JSONResponse({"connected": False})
    except:
        return JSONResponse({"connected": False})


@router.post("/hetzner")
async def save_hetzner_token(request: Request):
    """Guardar token de Hetzner"""
    data = await request.json()
    token = data.get('token', '')
    
    if not token:
        return JSONResponse({"error": "Token requerido"}, status_code=400)
    
    # Validar token con la API
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hetzner.cloud/v1/servers",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                return JSONResponse({"detail": "Token inválido"}, status_code=400)
            
            servers = len(response.json().get("servers", []))
    except Exception as e:
        return JSONResponse({"detail": f"Error validando token: {str(e)}"}, status_code=400)
    
    # Guardar token
    db.set_setting('hetzner_api_token', token)
    return JSONResponse({"success": True, "servers": servers})


@router.delete("/hetzner")
async def delete_hetzner_token():
    """Eliminar token de Hetzner"""
    db.set_setting('hetzner_api_token', '')
    return JSONResponse({"success": True})


@router.get("/hetzner/server")
async def get_hetzner_server_info():
    """Obtener información del servidor desplegado"""
    token = db.get_setting('hetzner_api_token', '')
    if not token:
        return JSONResponse({"server": None})
    
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hetzner.cloud/v1/servers",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                servers = response.json().get("servers", [])
                # Buscar servidor openhands-chat
                for server in servers:
                    if "openhands" in server.get("name", "").lower():
                        return JSONResponse({
                            "server": {
                                "id": server["id"],
                                "name": server["name"],
                                "ip": server["public_net"]["ipv4"]["ip"],
                                "status": server["status"],
                                "ssh_password": db.get_setting('hetzner_ssh_password', 'kCJHc3sVMwNv')
                            }
                        })
                return JSONResponse({"server": None})
    except Exception as e:
        return JSONResponse({"server": None, "error": str(e)})


@router.get("/hetzner/logs")
async def get_hetzner_logs():
    """Obtener logs del servidor via SSH"""
    token = db.get_setting('hetzner_api_token', '')
    ssh_password = db.get_setting('hetzner_ssh_password', 'kCJHc3sVMwNv')
    
    if not token:
        return JSONResponse({"error": "Token de Hetzner no configurado"})
    
    import httpx
    # Primero obtener la IP del servidor
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hetzner.cloud/v1/servers",
                headers={"Authorization": f"Bearer {token}"}
            )
            servers = response.json().get("servers", [])
            server_ip = None
            for server in servers:
                if "openhands" in server.get("name", "").lower():
                    server_ip = server["public_net"]["ipv4"]["ip"]
                    break
            
            if not server_ip:
                return JSONResponse({"error": "Servidor no encontrado"})
    except Exception as e:
        return JSONResponse({"error": f"Error obteniendo IP: {str(e)}"})
    
    # Conectar por SSH y obtener logs
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server_ip, username='root', password=ssh_password, timeout=10)
        
        stdin, stdout, stderr = client.exec_command("docker logs openhands-chat 2>&1 | tail -100")
        logs = stdout.read().decode()
        client.close()
        
        return JSONResponse({"logs": logs})
    except Exception as e:
        return JSONResponse({"error": f"Error SSH: {str(e)}"})


@router.post("/hetzner/restart")
async def restart_hetzner_container():
    """Reiniciar contenedor en el servidor"""
    token = db.get_setting('hetzner_api_token', '')
    ssh_password = db.get_setting('hetzner_ssh_password', 'kCJHc3sVMwNv')
    
    if not token:
        return JSONResponse({"error": "Token de Hetzner no configurado"})
    
    import httpx
    # Obtener IP
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hetzner.cloud/v1/servers",
                headers={"Authorization": f"Bearer {token}"}
            )
            servers = response.json().get("servers", [])
            server_ip = None
            for server in servers:
                if "openhands" in server.get("name", "").lower():
                    server_ip = server["public_net"]["ipv4"]["ip"]
                    break
    except:
        return JSONResponse({"error": "Error obteniendo servidor"})
    
    if not server_ip:
        return JSONResponse({"error": "Servidor no encontrado"})
    
    # Reiniciar contenedor por SSH
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server_ip, username='root', password=ssh_password, timeout=10)
        
        stdin, stdout, stderr = client.exec_command(
            "cd /opt/openhands-chat/04_proyecto/openhands-chat && docker-compose restart"
        )
        stdout.channel.recv_exit_status()
        client.close()
        
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"error": f"Error reiniciando: {str(e)}"})


# ============================================
# Turso Database Endpoints
# ============================================

@router.get("/turso")
async def get_turso_status():
    """Verificar estado de conexión a Turso"""
    url = db.get_setting('turso_url', '')
    token = db.get_setting('turso_token', '')
    
    if not url or not token:
        return JSONResponse({"connected": False, "url": url})
    
    # Verificar conexión
    try:
        import libsql_experimental as libsql
        conn = libsql.connect("turso-test", sync_url=url, auth_token=token)
        conn.execute("SELECT 1")
        conn.close()
        return JSONResponse({"connected": True, "url": url})
    except Exception as e:
        return JSONResponse({"connected": False, "url": url, "error": str(e)})


@router.post("/turso")
async def save_turso_config(request: Request):
    """Guardar configuración de Turso y migrar datos"""
    data = await request.json()
    url = data.get('url', '').strip()
    token = data.get('token', '').strip()
    
    if not url or not token:
        return JSONResponse({"success": False, "error": "URL y Token requeridos"})
    
    # Validar conexión
    try:
        import libsql_experimental as libsql
        conn = libsql.connect("turso-test", sync_url=url, auth_token=token)
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        return JSONResponse({"success": False, "error": f"No se pudo conectar: {str(e)}"})
    
    # Guardar credenciales (en SQLite local)
    db.set_setting('turso_url', url)
    db.set_setting('turso_token', token, encrypt=True)
    
    # Reconectar a Turso con las nuevas credenciales
    connected = db.reconnect_turso()
    
    if connected:
        return JSONResponse({"success": True, "message": "Conectado a Turso"})
    else:
        return JSONResponse({"success": False, "error": "Credenciales guardadas pero no se pudo conectar"})


@router.delete("/turso")
async def delete_turso_config():
    """Desconectar Turso y volver a SQLite local"""
    db.set_setting('turso_url', '')
    db.set_setting('turso_token', '')
    return JSONResponse({"success": True})


# ============================================
# Code-Server Settings
# ============================================

@router.get("/code-server")
async def get_code_server_settings():
    """Obtener configuración de Code-Server"""
    max_instances = db.get_setting('code_server_max_instances', '3')
    timeout = db.get_setting('code_server_timeout', '300')
    return JSONResponse({
        "max_instances": int(max_instances),
        "timeout": int(timeout),
        "description": {
            "max_instances": "Máximo de editores de código abiertos simultáneamente",
            "timeout": "Segundos de inactividad antes de cerrar automáticamente"
        }
    })


@router.post("/code-server")
async def save_code_server_settings(request: Request):
    """Guardar configuración de Code-Server"""
    try:
        data = await request.json()
        max_instances = data.get("max_instances", 3)
        timeout = data.get("timeout", 300)
        
        # Validar rangos
        max_instances = max(1, min(10, int(max_instances)))
        timeout = max(60, min(3600, int(timeout)))
        
        db.set_setting('code_server_max_instances', str(max_instances))
        db.set_setting('code_server_timeout', str(timeout))
        
        return JSONResponse({"success": True, "max_instances": max_instances, "timeout": timeout})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
