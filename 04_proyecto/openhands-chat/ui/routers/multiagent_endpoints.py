"""
Endpoints API para Multi-Agent System y ML Simulator
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.multi_agent import get_orchestrator, AgentRole
from core.ml_simulator import get_simulator

router = APIRouter(prefix="/api/advanced", tags=["advanced"])


# === Multi-Agent ===

class CreateSessionRequest(BaseModel):
    objective: str
    tasks: List[Dict[str, Any]]


class RunCodeWithAgentsRequest(BaseModel):
    code: str
    language: str = "python"


@router.post("/multiagent/session")
async def create_agent_session(request: CreateSessionRequest):
    """
    Crea una sesión multi-agente.
    
    Roles disponibles: researcher, coder, tester, reviewer, documenter
    """
    try:
        orchestrator = get_orchestrator()
        session = await orchestrator.create_session(
            objective=request.objective,
            tasks_config=request.tasks
        )
        return session.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/run/{session_id}")
async def run_agent_session(session_id: str):
    """Ejecuta todos los agentes de una sesión en paralelo"""
    try:
        orchestrator = get_orchestrator()
        session = await orchestrator.run_session(session_id)
        return session.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multiagent/quick-review")
async def quick_code_review(request: RunCodeWithAgentsRequest):
    """
    Revisión rápida de código usando múltiples agentes en paralelo.
    Ejecuta: coder (test), tester, reviewer, documenter
    """
    orchestrator = get_orchestrator()
    
    # Crear sesión con múltiples tareas
    session = await orchestrator.create_session(
        objective=f"Revisar código {request.language}",
        tasks_config=[
            {
                "role": "coder",
                "description": "Ejecutar código",
                "input": {"code": request.code, "language": request.language}
            },
            {
                "role": "reviewer",
                "description": "Revisar calidad",
                "input": {"code": request.code}
            },
            {
                "role": "documenter",
                "description": "Generar documentación",
                "input": {"code": request.code}
            }
        ]
    )
    
    # Ejecutar
    result = await orchestrator.run_session(session.id)
    return result.to_dict()


@router.get("/multiagent/session/{session_id}")
async def get_session(session_id: str):
    """Obtiene detalles de una sesión"""
    orchestrator = get_orchestrator()
    session = orchestrator.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return session.to_dict()


@router.get("/multiagent/sessions")
async def list_sessions(limit: int = 20):
    """Lista las últimas sesiones"""
    orchestrator = get_orchestrator()
    sessions = orchestrator.list_sessions(limit)
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions)
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
