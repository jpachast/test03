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
