"""Endpoints adicionales de Tavily para settings.py"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config.database import Database

router = APIRouter(prefix="/api/settings", tags=["tavily"])
db = Database()


@router.get("/tavily/usage")
async def get_tavily_usage():
    """Obtener estadisticas de uso de Tavily"""
    try:
        from core.tavily_service import get_tavily_service
        service = get_tavily_service(db)
        stats = service.get_usage_stats()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({
            "month": "",
            "plan": "Free",
            "limit": 1000,
            "credits_used": 0,
            "credits_remaining": 1000,
            "percentage_used": 0,
            "is_available": False,
            "error": str(e)
        })


@router.post("/tavily/search")
async def tavily_search(request: Request):
    """Realizar busqueda con Tavily"""
    try:
        from core.tavily_service import get_tavily_service
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return JSONResponse({"success": False, "error": "Query requerido"})
        
        service = get_tavily_service(db)
        result = service.search(
            query=query,
            search_depth=data.get("search_depth", "basic"),
            max_results=data.get("max_results", 5)
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/tavily/reinit")
async def reinit_tavily():
    """Reinicializar servicio Tavily despues de cambiar API key"""
    try:
        from core.tavily_service import reinit_tavily_service
        reinit_tavily_service(db)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
