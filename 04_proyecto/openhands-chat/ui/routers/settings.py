"""Rutas de configuración"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from config.database import Database

router = APIRouter(prefix="/api/settings", tags=["settings"])
db = Database()


@router.post("/api-key")
async def save_api_key(api_key: str = Form(...)):
    """Guardar API key de Gemini (visión)"""
    db.set_api_key(api_key)
    return JSONResponse({"status": "ok", "message": "API key guardada"})


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
