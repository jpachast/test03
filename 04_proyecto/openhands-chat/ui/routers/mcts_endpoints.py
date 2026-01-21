"""
Endpoints API para MCTS (Monte Carlo Tree Search)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.ml_simulator import get_simulator

router = APIRouter(prefix="/api/mcts", tags=["mcts"])


class MCTSOptimizeRequest(BaseModel):
    """Request para optimización MCTS"""
    objective_code: str  # Código Python de la función objetivo
    param_ranges: Dict[str, List[float]]  # {"param": [min, max]}
    iterations: int = 500
    exploration_weight: float = 1.41
    discretization: int = 10


class MCTSGameRequest(BaseModel):
    """Request para MCTS en juegos/decisiones"""
    initial_state: Dict[str, Any]
    possible_actions: List[str]
    iterations: int = 1000
    exploration_weight: float = 1.41


@router.post("/optimize")
async def mcts_optimize(request: MCTSOptimizeRequest):
    """
    Optimización de parámetros usando MCTS.
    
    Usa Monte Carlo Tree Search para encontrar los mejores parámetros
    que maximizan la función objetivo.
    
    Example:
        objective_code: "lambda p: -(p['x']**2 + p['y']**2)"  # Minimizar distancia al origen
        param_ranges: {"x": [-10, 10], "y": [-10, 10]}
    """
    try:
        # Crear función objetivo desde código
        # NOTA: En producción, esto debería estar sandboxeado
        local_vars = {}
        exec(f"objective_func = {request.objective_code}", {"__builtins__": {"abs": abs, "min": min, "max": max, "sum": sum, "pow": pow}}, local_vars)
        objective_func = local_vars.get("objective_func")
        
        if not callable(objective_func):
            raise ValueError("objective_code debe ser una función válida")
        
        # Convertir param_ranges de List a Tuple
        param_ranges = {
            k: (v[0], v[1]) for k, v in request.param_ranges.items()
        }
        
        simulator = get_simulator()
        result = await simulator.mcts_optimize(
            evaluate_func=objective_func,
            param_ranges=param_ranges,
            iterations=request.iterations,
            exploration_weight=request.exploration_weight,
            discretization=request.discretization
        )
        
        return result.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def mcts_search_simple(request: MCTSGameRequest):
    """
    MCTS simplificado para decisiones/juegos.
    
    Evalúa diferentes acciones desde un estado inicial usando MCTS
    y retorna la mejor acción.
    """
    try:
        simulator = get_simulator()
        
        # Crear funciones simples para MCTS
        def get_actions(state):
            return request.possible_actions
        
        def apply_action(state, action):
            new_state = state.copy()
            new_state["last_action"] = action
            new_state["depth"] = state.get("depth", 0) + 1
            return new_state
        
        def evaluate(state):
            # Evaluación simple basada en profundidad y estado
            depth = state.get("depth", 0)
            # Valor aleatorio + penalización por profundidad
            import random
            return random.random() - depth * 0.1
        
        def is_terminal(state):
            return state.get("depth", 0) >= 5
        
        result = await simulator.mcts_search(
            initial_state=request.initial_state,
            get_actions=get_actions,
            apply_action=apply_action,
            evaluate=evaluate,
            is_terminal=is_terminal,
            iterations=request.iterations,
            exploration_weight=request.exploration_weight
        )
        
        return result.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{result_id}")
async def get_mcts_result(result_id: str):
    """Obtiene detalles de un resultado MCTS"""
    simulator = get_simulator()
    result = simulator.get_mcts_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    
    return result.to_dict()


@router.get("/results")
async def list_mcts_results(limit: int = 20):
    """Lista los últimos resultados MCTS"""
    simulator = get_simulator()
    results = simulator.list_mcts_results(limit)
    
    return {
        "results": [r.to_dict() for r in results],
        "total": len(results)
    }


@router.get("/status")
async def get_mcts_status():
    """Estado del simulador MCTS"""
    simulator = get_simulator()
    return {
        "status": "active",
        "total_mcts_results": len(simulator.mcts_results),
        "total_simulations": len(simulator.simulations),
        "features": [
            "mcts_search - MCTS completo con UCB1",
            "mcts_optimize - Optimización de parámetros",
            "monte_carlo - Simulación Monte Carlo básica",
            "grid_search - Búsqueda exhaustiva",
            "evolutionary - Algoritmo genético"
        ]
    }
