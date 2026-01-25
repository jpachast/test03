"""
Multi-LLM API Endpoints

Endpoints para usar múltiples LLMs simultáneamente.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from core.multi_llm import (
    get_multi_llm_manager, 
    LLMRole, 
    MultiLLMManager
)

router = APIRouter(prefix="/api/multi-llm", tags=["multi-llm"])


class QueryRequest(BaseModel):
    role: str = "fast"
    prompt: str
    system_prompt: Optional[str] = None


class ParallelQueryRequest(BaseModel):
    tasks: List[Dict[str, Any]]


class AnalyzeRequest(BaseModel):
    code: str
    question: str = "¿Qué hace este código?"


class ConsensusRequest(BaseModel):
    prompt: str
    num_models: int = 3


@router.get("/models")
async def get_available_models():
    """Lista los modelos disponibles por rol"""
    manager = get_multi_llm_manager()
    return JSONResponse({
        "success": True,
        "models": manager.get_available_models()
    })


@router.post("/query")
async def query_single_llm(request: QueryRequest):
    """
    Consulta a un LLM específico por rol.
    
    Roles disponibles: coder, writer, reasoner, summarizer, reviewer, fast
    """
    manager = get_multi_llm_manager()
    
    try:
        role = LLMRole(request.role)
    except ValueError:
        role = LLMRole.FAST
    
    response = await manager.query_single(role, request.prompt, request.system_prompt)
    
    return JSONResponse({
        "success": response.success,
        "role": response.role.value,
        "model": response.model,
        "content": response.content,
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms,
        "error": response.error
    })


@router.post("/parallel")
async def query_parallel_llms(request: ParallelQueryRequest):
    """
    Ejecuta múltiples consultas en paralelo.
    
    Cada tarea debe tener: {role, prompt, system_prompt (opcional)}
    """
    manager = get_multi_llm_manager()
    
    responses = await manager.query_parallel(request.tasks)
    
    return JSONResponse({
        "success": True,
        "responses": [
            {
                "role": r.role.value,
                "model": r.model,
                "content": r.content,
                "tokens_used": r.tokens_used,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "error": r.error
            }
            for r in responses
        ],
        "total_tokens": sum(r.tokens_used for r in responses),
        "max_latency_ms": max(r.latency_ms for r in responses) if responses else 0
    })


@router.post("/analyze")
async def analyze_code_multi_perspective(request: AnalyzeRequest):
    """
    Analiza código con múltiples LLMs simultáneamente.
    
    Obtiene perspectivas de:
    - CODER: Análisis técnico
    - REVIEWER: Revisión de calidad
    - REASONER: Análisis lógico
    """
    manager = get_multi_llm_manager()
    
    result = await manager.analyze_with_multiple_perspectives(
        request.code, 
        request.question
    )
    
    return JSONResponse({
        "success": result["all_success"],
        **result
    })


@router.post("/consensus")
async def get_consensus(request: ConsensusRequest):
    """
    Obtiene consenso de múltiples modelos sobre una pregunta.
    
    Útil para decisiones importantes.
    """
    manager = get_multi_llm_manager()
    
    result = await manager.get_consensus(request.prompt, request.num_models)
    
    return JSONResponse({
        "success": True,
        **result
    })


@router.get("/status")
async def get_multi_llm_status():
    """Estado del sistema multi-LLM"""
    manager = get_multi_llm_manager()
    
    return JSONResponse({
        "success": True,
        "status": "active",
        "groq_configured": bool(manager.groq_api_key),
        "openai_configured": bool(manager.openai_api_key),
        "available_roles": [r.value for r in LLMRole],
        "models": manager.get_available_models()
    })
