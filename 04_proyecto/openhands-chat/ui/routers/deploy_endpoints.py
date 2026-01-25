"""
Deploy Endpoints - API para deploy a producción con dominio y SSL.

Endpoints:
    GET  /api/deploy/status - Estado actual del deploy
    POST /api/deploy/domain - Configurar dominio
    POST /api/deploy/ssl - Configurar SSL
    POST /api/deploy/run - Ejecutar deploy
    GET  /api/deploy/verify - Verificar configuración
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deploy", tags=["deploy"])


@router.get("/status")
async def get_deploy_status():
    """Obtener estado actual del deploy a producción"""
    try:
        from core.production_deploy import ProductionDeployManager
        manager = ProductionDeployManager()
        result = manager.get_status()
        manager.close()
        return JSONResponse(result.to_dict())
    except Exception as e:
        logger.error(f"Error getting deploy status: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error obteniendo estado",
            "error": str(e)
        })


@router.post("/domain")
async def setup_domain(request: Request):
    """Configurar dominio para producción"""
    try:
        data = await request.json()
        domain = data.get("domain", "").strip()
        
        if not domain:
            return JSONResponse({
                "success": False,
                "message": "Dominio requerido",
                "error": "empty_domain"
            })
        
        from core.production_deploy import ProductionDeployManager
        manager = ProductionDeployManager()
        result = manager.setup_domain(domain)
        manager.close()
        return JSONResponse(result.to_dict())
    except Exception as e:
        logger.error(f"Error setting up domain: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error configurando dominio",
            "error": str(e)
        })


@router.post("/ssl")
async def setup_ssl(request: Request):
    """Configurar SSL con Let's Encrypt"""
    try:
        data = await request.json()
        domain = data.get("domain", "").strip()
        email = data.get("email", "").strip()
        
        from core.production_deploy import ProductionDeployManager
        manager = ProductionDeployManager()
        result = manager.setup_ssl(domain, email)
        manager.close()
        return JSONResponse(result.to_dict())
    except Exception as e:
        logger.error(f"Error setting up SSL: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error configurando SSL",
            "error": str(e)
        })


@router.post("/run")
async def run_deploy(request: Request):
    """Ejecutar deploy a producción"""
    try:
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
        rebuild = data.get("rebuild", False)
        
        from core.production_deploy import ProductionDeployManager
        manager = ProductionDeployManager()
        result = manager.deploy(rebuild=rebuild)
        manager.close()
        return JSONResponse(result.to_dict())
    except Exception as e:
        logger.error(f"Error running deploy: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error en deploy",
            "error": str(e)
        })


@router.get("/verify")
async def verify_deploy(domain: str = ""):
    """Verificar que dominio y SSL funcionan"""
    try:
        from core.production_deploy import ProductionDeployManager
        manager = ProductionDeployManager()
        result = manager.verify(domain)
        manager.close()
        return JSONResponse(result.to_dict())
    except Exception as e:
        logger.error(f"Error verifying deploy: {e}")
        return JSONResponse({
            "success": False,
            "message": "Error verificando",
            "error": str(e)
        })


@router.get("/info")
async def get_deploy_info():
    """Información sobre comandos de deploy disponibles"""
    return JSONResponse({
        "success": True,
        "commands": {
            "status": "python -m core.production_deploy status",
            "setup_domain": "python -m core.production_deploy setup-domain <domain>",
            "setup_ssl": "python -m core.production_deploy setup-ssl <domain> [email]",
            "deploy": "python -m core.production_deploy deploy [--rebuild]",
            "verify": "python -m core.production_deploy verify [domain]"
        },
        "workflow": [
            "1. Apuntar DNS del dominio a la IP del servidor",
            "2. Ejecutar setup-domain para configurar nginx",
            "3. Ejecutar setup-ssl para obtener certificado SSL",
            "4. Verificar con verify que todo funciona"
        ]
    })
