"""
ML & Simulations - Machine Learning y simulaciones avanzadas
Incluye: Monte Carlo Tree Search (MCTS) completo con evaluación UCB1
"""

import random
import math
import asyncio
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy


# ============================================
# MCTS - Monte Carlo Tree Search
# ============================================

@dataclass
class MCTSNode:
    """Nodo del árbol MCTS"""
    state: Any
    parent: Optional['MCTSNode'] = None
    action: Any = None  # Acción que llevó a este estado
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    untried_actions: List[Any] = field(default_factory=list)
    
    def ucb1(self, exploration_weight: float = 1.41) -> float:
        """Calcula UCB1 (Upper Confidence Bound)"""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration
    
    def best_child(self, exploration_weight: float = 1.41) -> 'MCTSNode':
        """Selecciona el mejor hijo según UCB1"""
        return max(self.children, key=lambda c: c.ucb1(exploration_weight))
    
    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0
    
    def is_terminal(self) -> bool:
        return len(self.children) == 0 and len(self.untried_actions) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "visits": self.visits,
            "value": round(self.value, 4),
            "avg_value": round(self.value / self.visits, 4) if self.visits > 0 else 0,
            "children_count": len(self.children),
            "action": str(self.action) if self.action else None
        }


@dataclass
class MCTSResult:
    """Resultado de búsqueda MCTS"""
    id: str
    best_action: Any
    best_value: float
    root_visits: int
    total_simulations: int
    tree_depth: int
    exploration_weight: float
    action_scores: List[Dict[str, Any]]
    execution_time: float
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "best_action": self.best_action,
            "best_value": round(self.best_value, 4),
            "root_visits": self.root_visits,
            "total_simulations": self.total_simulations,
            "tree_depth": self.tree_depth,
            "exploration_weight": self.exploration_weight,
            "action_scores": self.action_scores[:10],  # Top 10 acciones
            "execution_time": self.execution_time,
            "created_at": self.created_at
        }


@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    id: str
    type: str
    iterations: int
    results: Dict[str, Any]
    statistics: Dict[str, float]
    execution_time: float
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "iterations": self.iterations,
            "results": self.results,
            "statistics": self.statistics,
            "execution_time": self.execution_time,
            "created_at": self.created_at
        }


class MLSimulator:
    """
    Simulador para ML y optimización.
    Incluye: Monte Carlo, MCTS completo, Grid Search, optimización evolutiva.
    """
    
    def __init__(self):
        self.simulations: Dict[str, SimulationResult] = {}
        self.mcts_results: Dict[str, MCTSResult] = {}
    
    # ============================================
    # MCTS - Monte Carlo Tree Search COMPLETO
    # ============================================
    
    async def mcts_search(
        self,
        initial_state: Any,
        get_actions: Callable[[Any], List[Any]],
        apply_action: Callable[[Any, Any], Any],
        evaluate: Callable[[Any], float],
        is_terminal: Callable[[Any], bool] = None,
        iterations: int = 1000,
        exploration_weight: float = 1.41,
        max_depth: int = 50,
        simulation_depth: int = 10
    ) -> MCTSResult:
        """
        Monte Carlo Tree Search completo con UCB1.
        
        Args:
            initial_state: Estado inicial del problema
            get_actions: Función que retorna acciones posibles desde un estado
            apply_action: Función que aplica una acción a un estado y retorna nuevo estado
            evaluate: Función heurística que evalúa un estado (retorna valor numérico)
            is_terminal: Función que determina si un estado es terminal
            iterations: Número de iteraciones MCTS
            exploration_weight: Peso de exploración en UCB1 (√2 ≈ 1.41 por defecto)
            max_depth: Profundidad máxima del árbol
            simulation_depth: Profundidad de simulación rollout
            
        Returns:
            MCTSResult con mejor acción y estadísticas
        """
        import uuid
        import time
        
        start_time = time.time()
        
        # Función terminal por defecto
        if is_terminal is None:
            is_terminal = lambda s: len(get_actions(s)) == 0
        
        # Crear nodo raíz
        root = MCTSNode(
            state=deepcopy(initial_state),
            untried_actions=list(get_actions(initial_state))
        )
        
        max_tree_depth = 0
        
        for iteration in range(iterations):
            node = root
            current_depth = 0
            
            # 1. SELECCIÓN - Bajar por el árbol usando UCB1
            while node.is_fully_expanded() and node.children:
                node = node.best_child(exploration_weight)
                current_depth += 1
                if current_depth > max_depth:
                    break
            
            # 2. EXPANSIÓN - Expandir si no es terminal y hay acciones sin probar
            if node.untried_actions and current_depth < max_depth:
                action = random.choice(node.untried_actions)
                node.untried_actions.remove(action)
                
                new_state = apply_action(deepcopy(node.state), action)
                child = MCTSNode(
                    state=new_state,
                    parent=node,
                    action=action,
                    untried_actions=list(get_actions(new_state)) if not is_terminal(new_state) else []
                )
                node.children.append(child)
                node = child
                current_depth += 1
            
            max_tree_depth = max(max_tree_depth, current_depth)
            
            # 3. SIMULACIÓN (Rollout) - Simular hasta terminal o max depth
            sim_state = deepcopy(node.state)
            sim_depth = 0
            
            while not is_terminal(sim_state) and sim_depth < simulation_depth:
                actions = get_actions(sim_state)
                if not actions:
                    break
                action = random.choice(actions)
                sim_state = apply_action(sim_state, action)
                sim_depth += 1
            
            # 4. EVALUACIÓN - Evaluar estado final
            value = evaluate(sim_state)
            
            # 5. BACKPROPAGATION - Propagar valor hacia arriba
            while node is not None:
                node.visits += 1
                node.value += value
                node = node.parent
        
        execution_time = time.time() - start_time
        
        # Obtener mejor acción (la más visitada desde la raíz)
        if root.children:
            # Ordenar por visitas (no por UCB1 para la selección final)
            sorted_children = sorted(root.children, key=lambda c: c.visits, reverse=True)
            best_child = sorted_children[0]
            best_action = best_child.action
            best_value = best_child.value / best_child.visits if best_child.visits > 0 else 0
            
            # Scores de todas las acciones
            action_scores = [
                {
                    "action": str(c.action),
                    "visits": c.visits,
                    "avg_value": round(c.value / c.visits, 4) if c.visits > 0 else 0,
                    "ucb1": round(c.ucb1(exploration_weight), 4) if c.visits > 0 else float('inf')
                }
                for c in sorted_children
            ]
        else:
            best_action = None
            best_value = evaluate(initial_state)
            action_scores = []
        
        result = MCTSResult(
            id=str(uuid.uuid4())[:8],
            best_action=best_action,
            best_value=best_value,
            root_visits=root.visits,
            total_simulations=iterations,
            tree_depth=max_tree_depth,
            exploration_weight=exploration_weight,
            action_scores=action_scores,
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat()
        )
        
        self.mcts_results[result.id] = result
        return result
    
    async def mcts_optimize(
        self,
        evaluate_func: Callable[[Dict[str, float]], float],
        param_ranges: Dict[str, Tuple[float, float]],
        iterations: int = 500,
        exploration_weight: float = 1.41,
        discretization: int = 10
    ) -> MCTSResult:
        """
        MCTS para optimización de parámetros continuos.
        Discretiza el espacio de búsqueda y usa MCTS para encontrar óptimos.
        
        Args:
            evaluate_func: Función objetivo que recibe dict de parámetros
            param_ranges: Rangos de parámetros {"param": (min, max)}
            iterations: Iteraciones MCTS
            exploration_weight: Peso UCB1
            discretization: Número de divisiones por parámetro
        """
        param_names = list(param_ranges.keys())
        
        # Discretizar rangos
        param_values = {}
        for name, (min_val, max_val) in param_ranges.items():
            step = (max_val - min_val) / discretization
            param_values[name] = [min_val + i * step for i in range(discretization + 1)]
        
        # Estado = índices actuales de parámetros
        initial_state = {name: discretization // 2 for name in param_names}  # Empezar en el medio
        
        def get_actions(state):
            """Acciones: incrementar/decrementar cada parámetro"""
            actions = []
            for name in param_names:
                if state[name] > 0:
                    actions.append((name, -1))  # Decrementar
                if state[name] < discretization:
                    actions.append((name, +1))  # Incrementar
            return actions
        
        def apply_action(state, action):
            new_state = state.copy()
            param_name, delta = action
            new_state[param_name] = max(0, min(discretization, state[param_name] + delta))
            return new_state
        
        def evaluate(state):
            # Convertir índices a valores reales
            params = {
                name: param_values[name][state[name]]
                for name in param_names
            }
            try:
                return evaluate_func(params)
            except:
                return float('-inf')
        
        def is_terminal(state):
            return False  # Nunca terminal en optimización
        
        return await self.mcts_search(
            initial_state=initial_state,
            get_actions=get_actions,
            apply_action=apply_action,
            evaluate=evaluate,
            is_terminal=is_terminal,
            iterations=iterations,
            exploration_weight=exploration_weight,
            max_depth=50,
            simulation_depth=5
        )
    
    def get_mcts_result(self, result_id: str) -> Optional[MCTSResult]:
        return self.mcts_results.get(result_id)
    
    def list_mcts_results(self, limit: int = 20) -> List[MCTSResult]:
        results = list(self.mcts_results.values())
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]
    
    async def monte_carlo(
        self,
        func: Callable,
        params_ranges: Dict[str, tuple],
        iterations: int = 1000,
        objective: str = "maximize"
    ) -> SimulationResult:
        """
        Simulación Monte Carlo para encontrar óptimos.
        
        Args:
            func: Función a optimizar (recibe dict de params, retorna número)
            params_ranges: Rangos de parámetros {"param": (min, max)}
            iterations: Número de iteraciones
            objective: "maximize" o "minimize"
        """
        import uuid
        import time
        
        start_time = time.time()
        
        results = []
        best_value = float('-inf') if objective == "maximize" else float('inf')
        best_params = None
        
        for i in range(iterations):
            # Generar parámetros aleatorios
            params = {}
            for param, (min_val, max_val) in params_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param] = random.randint(min_val, max_val)
                else:
                    params[param] = random.uniform(min_val, max_val)
            
            # Evaluar función
            try:
                value = func(params)
                results.append({"params": params, "value": value})
                
                # Actualizar mejor
                if objective == "maximize" and value > best_value:
                    best_value = value
                    best_params = params.copy()
                elif objective == "minimize" and value < best_value:
                    best_value = value
                    best_params = params.copy()
            except:
                continue
        
        execution_time = time.time() - start_time
        
        # Calcular estadísticas
        values = [r["value"] for r in results if isinstance(r["value"], (int, float))]
        
        statistics = {}
        if values:
            statistics = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "std": math.sqrt(sum((x - sum(values)/len(values))**2 for x in values) / len(values)) if len(values) > 1 else 0
            }
        
        sim_result = SimulationResult(
            id=str(uuid.uuid4())[:8],
            type="monte_carlo",
            iterations=iterations,
            results={
                "best_params": best_params,
                "best_value": best_value,
                "samples_evaluated": len(results)
            },
            statistics=statistics,
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat()
        )
        
        self.simulations[sim_result.id] = sim_result
        return sim_result
    
    async def grid_search(
        self,
        func: Callable,
        params_grid: Dict[str, List[Any]],
        objective: str = "maximize"
    ) -> SimulationResult:
        """
        Grid Search exhaustivo sobre combinaciones de parámetros.
        """
        import uuid
        import time
        from itertools import product
        
        start_time = time.time()
        
        # Generar todas las combinaciones
        param_names = list(params_grid.keys())
        param_values = list(params_grid.values())
        combinations = list(product(*param_values))
        
        results = []
        best_value = float('-inf') if objective == "maximize" else float('inf')
        best_params = None
        
        for combo in combinations:
            params = dict(zip(param_names, combo))
            
            try:
                value = func(params)
                results.append({"params": params, "value": value})
                
                if objective == "maximize" and value > best_value:
                    best_value = value
                    best_params = params.copy()
                elif objective == "minimize" and value < best_value:
                    best_value = value
                    best_params = params.copy()
            except:
                continue
        
        execution_time = time.time() - start_time
        
        values = [r["value"] for r in results if isinstance(r["value"], (int, float))]
        statistics = {}
        if values:
            statistics = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
        
        sim_result = SimulationResult(
            id=str(uuid.uuid4())[:8],
            type="grid_search",
            iterations=len(combinations),
            results={
                "best_params": best_params,
                "best_value": best_value,
                "combinations_tested": len(results)
            },
            statistics=statistics,
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat()
        )
        
        self.simulations[sim_result.id] = sim_result
        return sim_result
    
    async def evolutionary_optimize(
        self,
        func: Callable,
        params_ranges: Dict[str, tuple],
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.1,
        objective: str = "maximize"
    ) -> SimulationResult:
        """
        Optimización evolutiva (algoritmo genético simple).
        """
        import uuid
        import time
        
        start_time = time.time()
        
        def create_individual():
            return {
                param: random.uniform(min_val, max_val)
                for param, (min_val, max_val) in params_ranges.items()
            }
        
        def mutate(individual):
            mutated = individual.copy()
            for param, (min_val, max_val) in params_ranges.items():
                if random.random() < mutation_rate:
                    mutated[param] = random.uniform(min_val, max_val)
            return mutated
        
        def crossover(parent1, parent2):
            child = {}
            for param in params_ranges:
                child[param] = parent1[param] if random.random() < 0.5 else parent2[param]
            return child
        
        # Inicializar población
        population = [create_individual() for _ in range(population_size)]
        
        best_ever = None
        best_value_ever = float('-inf') if objective == "maximize" else float('inf')
        history = []
        
        for gen in range(generations):
            # Evaluar fitness
            fitness = []
            for ind in population:
                try:
                    value = func(ind)
                    fitness.append((ind, value))
                except:
                    fitness.append((ind, float('-inf') if objective == "maximize" else float('inf')))
            
            # Ordenar por fitness
            fitness.sort(key=lambda x: x[1], reverse=(objective == "maximize"))
            
            # Actualizar mejor
            if objective == "maximize" and fitness[0][1] > best_value_ever:
                best_value_ever = fitness[0][1]
                best_ever = fitness[0][0].copy()
            elif objective == "minimize" and fitness[0][1] < best_value_ever:
                best_value_ever = fitness[0][1]
                best_ever = fitness[0][0].copy()
            
            history.append({"generation": gen, "best_fitness": fitness[0][1]})
            
            # Selección y reproducción
            top_half = [f[0] for f in fitness[:population_size // 2]]
            
            new_population = top_half.copy()
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(top_half, 2)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)
            
            population = new_population
        
        execution_time = time.time() - start_time
        
        sim_result = SimulationResult(
            id=str(uuid.uuid4())[:8],
            type="evolutionary",
            iterations=generations * population_size,
            results={
                "best_params": best_ever,
                "best_value": best_value_ever,
                "generations": generations,
                "population_size": population_size,
                "convergence": history[-10:] if len(history) >= 10 else history
            },
            statistics={
                "final_best": best_value_ever,
                "improvement": history[-1]["best_fitness"] - history[0]["best_fitness"] if history else 0
            },
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat()
        )
        
        self.simulations[sim_result.id] = sim_result
        return sim_result
    
    async def run_prediction_simulation(
        self,
        data_points: List[Dict[str, float]],
        target_field: str,
        feature_fields: List[str],
        iterations: int = 1000
    ) -> SimulationResult:
        """
        Simulación simple para predicciones usando regresión lineal básica.
        """
        import uuid
        import time
        
        start_time = time.time()
        
        if not data_points or len(data_points) < 2:
            raise ValueError("Se necesitan al menos 2 puntos de datos")
        
        # Extraer valores
        X = [[p.get(f, 0) for f in feature_fields] for p in data_points]
        y = [p.get(target_field, 0) for p in data_points]
        
        # Regresión lineal simple (un solo feature)
        if len(feature_fields) == 1:
            x_vals = [p.get(feature_fields[0], 0) for p in data_points]
            n = len(x_vals)
            
            sum_x = sum(x_vals)
            sum_y = sum(y)
            sum_xy = sum(x * yi for x, yi in zip(x_vals, y))
            sum_x2 = sum(x**2 for x in x_vals)
            
            # Calcular coeficientes
            denom = n * sum_x2 - sum_x**2
            if denom == 0:
                slope, intercept = 0, sum_y / n
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denom
                intercept = (sum_y - slope * sum_x) / n
            
            # Predicciones
            predictions = [slope * x + intercept for x in x_vals]
            
            # Error
            mse = sum((pred - actual)**2 for pred, actual in zip(predictions, y)) / n
            
            results = {
                "model_type": "linear_regression",
                "coefficients": {"slope": round(slope, 4), "intercept": round(intercept, 4)},
                "predictions_sample": predictions[:5],
                "formula": f"y = {round(slope, 4)} * x + {round(intercept, 4)}"
            }
            
            statistics = {
                "mse": round(mse, 4),
                "rmse": round(math.sqrt(mse), 4),
                "r_squared": 1 - (mse / (sum((yi - sum_y/n)**2 for yi in y) / n + 0.0001))
            }
        else:
            # Para múltiples features, usar promedio simple
            results = {
                "model_type": "average_baseline",
                "average": sum(y) / len(y),
                "note": "Para múltiples features, usar modelo más avanzado"
            }
            statistics = {
                "mean": sum(y) / len(y),
                "std": math.sqrt(sum((yi - sum(y)/len(y))**2 for yi in y) / len(y))
            }
        
        execution_time = time.time() - start_time
        
        sim_result = SimulationResult(
            id=str(uuid.uuid4())[:8],
            type="prediction",
            iterations=iterations,
            results=results,
            statistics=statistics,
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat()
        )
        
        self.simulations[sim_result.id] = sim_result
        return sim_result
    
    def get_simulation(self, sim_id: str) -> Optional[SimulationResult]:
        return self.simulations.get(sim_id)
    
    def list_simulations(self, limit: int = 20) -> List[SimulationResult]:
        sims = list(self.simulations.values())
        sims.sort(key=lambda x: x.created_at, reverse=True)
        return sims[:limit]


# Instancia global
_simulator_instance: Optional[MLSimulator] = None


def get_simulator() -> MLSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = MLSimulator()
    return _simulator_instance
