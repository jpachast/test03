"""Rutas de configuración"""
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from config.database import Database

router = APIRouter(prefix="/api/settings", tags=["settings"])
db = Database()


@router.post("/api-key")
async def save_api_key(api_key: str = Form(...)):
    """Guardar API key"""
    db.set_api_key(api_key)
    return JSONResponse({"status": "ok", "message": "API key guardada"})


@router.post("/model")
async def save_model(model: str = Form(...)):
    """Guardar modelo por defecto"""
    db.set_setting("default_model", model)
    return JSONResponse({"status": "ok"})
