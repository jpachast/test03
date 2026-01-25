"""
Agent Cache - Caches agents to avoid recreating them for each message
"""
import time
from typing import Optional, Dict, Any, Tuple

# Cache de agentes por (model, workspace, repo_key)
_agent_cache: Dict[str, Tuple[Any, float]] = {}
_AGENT_CACHE_TTL = 300  # 5 minutos de vida


def _get_cache_key(api_key: str, model: str, workspace: str, repo_info: dict = None) -> str:
    """Genera una clave única para el cache del agente"""
    repo_key = ""
    if repo_info:
        repo_key = f"{repo_info.get('owner', '')}/{repo_info.get('repo', '')}/{repo_info.get('branch', '')}"
    return f"{api_key[:8]}:{model}:{workspace}:{repo_key}"


def get_cached_agent(
    api_key: str, 
    model: str, 
    workspace: str, 
    repo_info: dict = None,
    agent_factory = None
) -> Optional[Any]:
    """
    Obtiene un agente cacheado o crea uno nuevo.
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar
        workspace: Path del workspace
        repo_info: Info del repositorio (opcional)
        agent_factory: Función para crear el agente si no está en cache
        
    Returns:
        Agent instance o None si no se puede crear
    """
    global _agent_cache
    
    cache_key = _get_cache_key(api_key, model, workspace, repo_info)
    current_time = time.time()
    
    # Verificar si hay un agente en cache válido
    if cache_key in _agent_cache:
        agent, timestamp = _agent_cache[cache_key]
        if current_time - timestamp < _AGENT_CACHE_TTL:
            print(f"[AGENT_CACHE] Usando agente cacheado para {cache_key[:50]}")
            return agent
        else:
            # Cache expirado, eliminar
            del _agent_cache[cache_key]
            print(f"[AGENT_CACHE] Cache expirado para {cache_key[:50]}")
    
    # Crear nuevo agente si se proporciona factory
    if agent_factory:
        try:
            agent = agent_factory(api_key, model, workspace, repo_info)
            if agent:
                _agent_cache[cache_key] = (agent, current_time)
                print(f"[AGENT_CACHE] Nuevo agente creado y cacheado para {cache_key[:50]}")
                return agent
        except Exception as e:
            print(f"[AGENT_CACHE] Error creando agente: {e}")
    
    return None


def clear_agent_cache(workspace: str = None) -> int:
    """
    Limpia el cache de agentes.
    
    Args:
        workspace: Si se especifica, solo limpia agentes de ese workspace
        
    Returns:
        Número de agentes eliminados del cache
    """
    global _agent_cache
    
    if workspace:
        # Eliminar solo agentes del workspace específico
        keys_to_delete = [k for k in _agent_cache if workspace in k]
        for key in keys_to_delete:
            del _agent_cache[key]
        return len(keys_to_delete)
    else:
        # Limpiar todo el cache
        count = len(_agent_cache)
        _agent_cache.clear()
        return count


def get_cache_stats() -> dict:
    """Obtiene estadísticas del cache de agentes"""
    current_time = time.time()
    active = sum(1 for _, (_, ts) in _agent_cache.items() if current_time - ts < _AGENT_CACHE_TTL)
    expired = len(_agent_cache) - active
    
    return {
        "total": len(_agent_cache),
        "active": active,
        "expired": expired,
        "ttl_seconds": _AGENT_CACHE_TTL
    }
