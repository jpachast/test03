"""
Endpoints API para el Test Generator
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.test_generator import get_test_generator

router = APIRouter(prefix="/api/tests", tags=["tests"])


class GenerateTestsRequest(BaseModel):
    code: str
    language: str = "python"


@router.post("/generate")
async def generate_and_run_tests(request: GenerateTestsRequest):
    """
    Genera tests automáticamente para el código y los ejecuta.
    
    Analiza funciones, clases y genera tests unitarios básicos.
    """
    try:
        generator = get_test_generator()
        suite = await generator.generate_and_run(
            code=request.code,
            language=request.language
        )
        return suite.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suite/{suite_id}")
async def get_suite(suite_id: str):
    """Obtiene detalles de una suite de tests"""
    generator = get_test_generator()
    suite = generator.get_suite(suite_id)
    
    if not suite:
        raise HTTPException(status_code=404, detail="Suite no encontrada")
    
    return suite.to_dict()


@router.get("/suites")
async def list_suites(limit: int = 20):
    """Lista las últimas suites de tests"""
    generator = get_test_generator()
    suites = generator.list_suites(limit)
    
    return {
        "suites": [s.to_dict() for s in suites],
        "total": len(suites)
    }


@router.get("/status")
async def get_status():
    """Estado del generador de tests"""
    generator = get_test_generator()
    return {
        "status": "active",
        "total_suites": len(generator.suites)
    }
