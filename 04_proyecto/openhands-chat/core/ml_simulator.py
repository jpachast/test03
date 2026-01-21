"""
ML & Simulations - Machine Learning básico y simulaciones
"""

import random
import math
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime


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
    Incluye: Monte Carlo, Grid Search, optimización evolutiva.
    """
    
    def __init__(self):
        self.simulations: Dict[str, SimulationResult] = {}
    
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
