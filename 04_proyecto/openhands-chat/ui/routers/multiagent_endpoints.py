"""
Endpoints API para Multi-Agent System con LLMs REALES en paralelo
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.multi_agent import get_orchestrator, AgentRole, reinit_orchestrator
from core.ml_simulator import get_simulator
from config.database import Database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/advanced", tags=["advanced"])


def _get_api_key() -> str:
    """Obtiene la API key de la base de datos"""
    db = Database()
    api_key = db.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="No hay API key configurada. Ve a Configuración para agregar tu API key de Anthropic."
        )
    return api_key


def _get_model() -> str:
    """Obtiene el modelo configurado (sin prefijo de provider)"""
    db = Database()
    model = db.get_setting('llm_model', 'claude-sonnet-4-20250514')
    # Remover prefijo de provider si existe (ej: anthropic/claude-xxx -> claude-xxx)
    if '/' in model:
        model = model.split('/')[-1]
    return model


# === Multi-Agent ===

class CreateSessionRequest(BaseModel):
    objective: str
    tasks: List[Dict[str, Any]]


class RunCodeWithAgentsRequest(BaseModel):
    code: str
    language: str = "python"
    roles: Optional[List[str]] = None  # Roles específicos a usar


class QuickAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    include_roles: Optional[List[str]] = None  # reviewer, tester, documenter, security, architect


@router.post("/multiagent/session")
async def create_agent_session(request: CreateSessionRequest):
    """
    Crea una sesión multi-agente con LLMs REALES.

    Roles disponibles: researcher, coder, tester, reviewer, documenter, architect, security
    """
    try:
        api_key = _get_api_key()
        model = _get_model()

        orchestrator = get_orchestrator(api_key=api_key, model=model)
        session = await orchestrator.create_session(
            objective=request.objective,
            tasks_config=request.tasks
        )
        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/run/{session_id}")
async def run_agent_session(session_id: str):
    """
    Ejecuta todos los agentes de una sesión en PARALELO REAL.
    Cada agente hace una llamada simultánea a Claude API.
    """
    try:
        api_key = _get_api_key()
        model = _get_model()

        orchestrator = get_orchestrator(api_key=api_key, model=model)
        session = await orchestrator.run_session(session_id)
        return session.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/quick-analysis")
async def quick_code_analysis(request: QuickAnalysisRequest):
    """
    Análisis rápido de código con múltiples agentes LLM en PARALELO.

    Por defecto ejecuta: reviewer, tester, documenter, security
    Todos los agentes se ejecutan simultáneamente con Claude API.
    """
    try:
        api_key = _get_api_key()
        model = _get_model()

        orchestrator = get_orchestrator(api_key=api_key, model=model)
        session = await orchestrator.quick_analysis(
            code=request.code,
            language=request.language,
            include_roles=request.include_roles
        )
        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/quick-review")
async def quick_code_review(request: RunCodeWithAgentsRequest):
    """
    Revisión rápida de código usando múltiples agentes LLM en paralelo.
    Ejecuta: reviewer, tester, documenter (3 llamadas simultáneas a Claude)
    """
    try:
        api_key = _get_api_key()
        model = _get_model()

        orchestrator = get_orchestrator(api_key=api_key, model=model)

        roles = request.roles or ["reviewer", "tester", "documenter"]
        tasks_config = [
            {
                "role": role,
                "description": f"Análisis {role}",
                "input": {"code": request.code, "language": request.language}
            }
            for role in roles
        ]

        session = await orchestrator.create_session(
            objective=f"Revisión de código {request.language}",
            tasks_config=tasks_config
        )

        result = await orchestrator.run_session(session.id)
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/full-analysis")
async def full_code_analysis(request: RunCodeWithAgentsRequest):
    """
    Análisis COMPLETO de código con TODOS los agentes disponibles en paralelo.
    Ejecuta: reviewer, tester, documenter, security, architect (5 llamadas simultáneas)
    """
    try:
        api_key = _get_api_key()
        model = _get_model()

        orchestrator = get_orchestrator(api_key=api_key, model=model)

        all_roles = ["reviewer", "tester", "documenter", "security", "architect"]
        tasks_config = [
            {
                "role": role,
                "description": f"Análisis {role} completo",
                "input": {"code": request.code, "language": request.language}
            }
            for role in all_roles
        ]

        session = await orchestrator.create_session(
            objective=f"Análisis completo de código {request.language}",
            tasks_config=tasks_config
        )

        result = await orchestrator.run_session(session.id)
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in full analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multiagent/session/{session_id}")
async def get_session(session_id: str):
    """Obtiene detalles de una sesión"""
    try:
        api_key = _get_api_key()
        orchestrator = get_orchestrator(api_key=api_key)
        session = orchestrator.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multiagent/sessions")
async def list_sessions(limit: int = 20):
    """Lista las últimas sesiones multi-agente"""
    try:
        api_key = _get_api_key()
        orchestrator = get_orchestrator(api_key=api_key)
        sessions = orchestrator.list_sessions(limit)
        return {
            "sessions": [s.to_dict() for s in sessions],
            "total": len(sessions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multiagent/roles")
async def get_available_roles():
    """Lista los roles de agentes disponibles"""
    return {
        "roles": [
            {
                "id": "researcher",
                "name": "Investigador",
                "description": "Investiga y analiza información"
            },
            {
                "id": "coder",
                "name": "Programador",
                "description": "Escribe y mejora código"
            },
            {
                "id": "tester",
                "name": "Tester",
                "description": "Genera tests unitarios"
            },
            {
                "id": "reviewer",
                "name": "Revisor",
                "description": "Analiza calidad del código"
            },
            {
                "id": "documenter",
                "name": "Documentador",
                "description": "Genera documentación"
            },
            {
                "id": "architect",
                "name": "Arquitecto",
                "description": "Diseña estructura y patrones"
            },
            {
                "id": "security",
                "name": "Seguridad",
                "description": "Detecta vulnerabilidades"
            }
        ]
    }


# === ML Simulator ===

class MonteCarloRequest(BaseModel):
    expression: str  # Expresión Python a evaluar, ej: "x**2 + y"
    params_ranges: Dict[str, List[float]]  # {"x": [0, 10], "y": [-5, 5]}
    iterations: int = 1000
    objective: str = "maximize"


class GridSearchRequest(BaseModel):
    expression: str
    params_grid: Dict[str, List[Any]]  # {"x": [1, 2, 3], "y": [0.1, 0.5, 1.0]}
    objective: str = "maximize"


class EvolutionaryRequest(BaseModel):
    expression: str
    params_ranges: Dict[str, List[float]]
    population_size: int = 50
    generations: int = 100
    objective: str = "maximize"


class PredictionRequest(BaseModel):
    data: List[Dict[str, float]]
    target: str
    features: List[str]


def create_eval_func(expression: str):
    """Crea una función evaluable desde una expresión"""
    def eval_func(params):
        # Crear contexto con parámetros
        context = params.copy()
        context['abs'] = abs
        context['max'] = max
        context['min'] = min
        context['sum'] = sum
        context['pow'] = pow
        import math
        context['sin'] = math.sin
        context['cos'] = math.cos
        context['sqrt'] = math.sqrt
        context['log'] = math.log
        context['exp'] = math.exp
        return eval(expression, {"__builtins__": {}}, context)
    return eval_func


@router.post("/ml/monte-carlo")
async def run_monte_carlo(request: MonteCarloRequest):
    """
    Ejecuta simulación Monte Carlo para optimización.
    
    Ejemplo:
    - expression: "x**2 + y*2"
    - params_ranges: {"x": [0, 10], "y": [-5, 5]}
    """
    try:
        simulator = get_simulator()
        func = create_eval_func(request.expression)
        
        # Convertir formato de rangos
        ranges = {k: (v[0], v[1]) for k, v in request.params_ranges.items()}
        
        result = await simulator.monte_carlo(
            func=func,
            params_ranges=ranges,
            iterations=min(request.iterations, 100000),  # Limitar
            objective=request.objective
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/grid-search")
async def run_grid_search(request: GridSearchRequest):
    """
    Ejecuta Grid Search exhaustivo.
    """
    try:
        simulator = get_simulator()
        func = create_eval_func(request.expression)
        
        # Limitar combinaciones
        total_combos = 1
        for v in request.params_grid.values():
            total_combos *= len(v)
        
        if total_combos > 10000:
            raise HTTPException(status_code=400, detail=f"Demasiadas combinaciones ({total_combos}). Máximo 10000.")
        
        result = await simulator.grid_search(
            func=func,
            params_grid=request.params_grid,
            objective=request.objective
        )
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/evolutionary")
async def run_evolutionary(request: EvolutionaryRequest):
    """
    Ejecuta optimización evolutiva (algoritmo genético).
    """
    try:
        simulator = get_simulator()
        func = create_eval_func(request.expression)
        
        ranges = {k: (v[0], v[1]) for k, v in request.params_ranges.items()}
        
        result = await simulator.evolutionary_optimize(
            func=func,
            params_ranges=ranges,
            population_size=min(request.population_size, 200),
            generations=min(request.generations, 500),
            objective=request.objective
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/predict")
async def run_prediction(request: PredictionRequest):
    """
    Ejecuta predicción con regresión lineal simple.
    """
    try:
        simulator = get_simulator()
        result = await simulator.run_prediction_simulation(
            data_points=request.data,
            target_field=request.target,
            feature_fields=request.features
        )
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/simulations")
async def list_simulations(limit: int = 20):
    """Lista las últimas simulaciones"""
    simulator = get_simulator()
    sims = simulator.list_simulations(limit)
    return {
        "simulations": [s.to_dict() for s in sims],
        "total": len(sims)
    }


@router.get("/status")
async def get_advanced_status():
    """Estado de los sistemas avanzados"""
    orchestrator = get_orchestrator()
    simulator = get_simulator()
    
    return {
        "multiagent": {
            "status": "active",
            "sessions": len(orchestrator.sessions),
            "available_roles": [r.value for r in AgentRole]
        },
        "ml_simulator": {
            "status": "active",
            "simulations": len(simulator.simulations),
            "available_methods": ["monte_carlo", "grid_search", "evolutionary", "prediction"]
        }
    }
