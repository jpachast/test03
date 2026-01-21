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
    with_coverage: bool = True  # Análisis de cobertura real


@router.post("/generate")
async def generate_and_run_tests(request: GenerateTestsRequest):
    """
    Genera tests automáticamente para el código y los ejecuta.
    
    Analiza funciones, clases y genera tests unitarios básicos.
    Incluye análisis de cobertura REAL (líneas y funciones cubiertas).
    """
    try:
        generator = get_test_generator()
        suite = await generator.generate_and_run(
            code=request.code,
            language=request.language,
            with_coverage=request.with_coverage
        )
        return suite.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coverage")
async def analyze_coverage(request: GenerateTestsRequest):
    """
    Analiza cobertura de código sin generar tests nuevos.
    Útil para código que ya tiene tests.
    """
    try:
        generator = get_test_generator()
        
        # Si no tiene tests, generarlos primero
        suite = await generator.generate_and_run(
            code=request.code,
            language=request.language,
            with_coverage=True
        )
        
        # Retornar solo datos de cobertura
        result = suite.to_dict()
        return {
            "coverage_percent": result.get("coverage_estimate", 0),
            "coverage_report": result.get("coverage_report"),
            "tests_passed": result.get("passed", 0),
            "tests_failed": result.get("failed", 0),
            "tests_total": result.get("tests_count", 0)
        }
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
