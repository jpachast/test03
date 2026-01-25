"""
Endpoints API para Background Agents
Ejecución paralela real de tareas en background
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.background_agents import (
    BackgroundAgentManager, 
    TaskPriority,
    get_manager,
    demo_task_slow,
    demo_task_compute,
    demo_task_analyze_code
)

router = APIRouter(prefix="/api/background", tags=["background"])

# Manager global
_manager: Optional[BackgroundAgentManager] = None


async def get_or_create_manager() -> BackgroundAgentManager:
    """Obtiene o crea el manager"""
    global _manager
    if _manager is None:
        _manager = BackgroundAgentManager(max_workers=4)
        await _manager.start()
    return _manager


class SubmitTaskRequest(BaseModel):
    """Request para enviar una tarea"""
    task_type: str  # "slow", "compute", "analyze"
    params: dict = {}
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL


class AnalyzeCodeRequest(BaseModel):
    """Request para analizar código"""
    code: str
    priority: str = "NORMAL"


@router.on_event("startup")
async def startup():
    """Inicializa el manager al arrancar"""
    global _manager
    _manager = BackgroundAgentManager(max_workers=4)
    await _manager.start()


@router.post("/submit")
async def submit_task(request: SubmitTaskRequest):
    """
    Envía una tarea para ejecución en background.
    
    Tipos de tareas:
    - slow: Tarea que toma tiempo (params: seconds)
    - compute: Cómputo intensivo (params: n)
    - analyze: Analizar código (params: code)
    """
    manager = await get_or_create_manager()
    
    # Mapear prioridad
    priority_map = {
        "LOW": TaskPriority.LOW,
        "NORMAL": TaskPriority.NORMAL,
        "HIGH": TaskPriority.HIGH,
        "CRITICAL": TaskPriority.CRITICAL
    }
    priority = priority_map.get(request.priority.upper(), TaskPriority.NORMAL)
    
    # Seleccionar función según tipo
    if request.task_type == "slow":
        seconds = request.params.get("seconds", 3)
        name = request.params.get("name", "Slow Task")
        task_id = manager.submit_task(
            name=f"⏳ {name}",
            func=demo_task_slow,
            kwargs={"seconds": seconds, "name": name},
            priority=priority,
            metadata={"type": "slow", "seconds": seconds}
        )
    
    elif request.task_type == "compute":
        n = request.params.get("n", 1000000)
        task_id = manager.submit_task(
            name=f"🔢 Compute (n={n:,})",
            func=demo_task_compute,
            kwargs={"n": n},
            priority=priority,
            metadata={"type": "compute", "n": n}
        )
    
    elif request.task_type == "analyze":
        code = request.params.get("code", "")
        task_id = manager.submit_task(
            name="📝 Analyze Code",
            func=demo_task_analyze_code,
            kwargs={"code": code},
            priority=priority,
            metadata={"type": "analyze"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Tipo de tarea no válido: {request.task_type}")
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Tarea encolada con ID: {task_id}"
    }


@router.post("/analyze")
async def analyze_code_background(request: AnalyzeCodeRequest):
    """Envía análisis de código como tarea background"""
    manager = await get_or_create_manager()
    
    priority_map = {
        "LOW": TaskPriority.LOW,
        "NORMAL": TaskPriority.NORMAL,
        "HIGH": TaskPriority.HIGH,
        "CRITICAL": TaskPriority.CRITICAL
    }
    priority = priority_map.get(request.priority.upper(), TaskPriority.NORMAL)
    
    task_id = manager.submit_task(
        name="📝 Analyze Code",
        func=demo_task_analyze_code,
        kwargs={"code": request.code},
        priority=priority,
        metadata={"type": "analyze", "code_length": len(request.code)}
    )
    
    return {
        "success": True,
        "task_id": task_id
    }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Obtiene el estado de una tarea específica"""
    manager = await get_or_create_manager()
    task = manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return {
        "success": True,
        "task": task
    }


@router.get("/tasks")
async def get_all_tasks(limit: int = 50):
    """Obtiene todas las tareas"""
    manager = await get_or_create_manager()
    tasks = manager.get_all_tasks(limit)
    
    return {
        "success": True,
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/tasks/pending")
async def get_pending_tasks():
    """Obtiene tareas pendientes"""
    manager = await get_or_create_manager()
    tasks = manager.get_pending_tasks()
    
    return {
        "success": True,
        "tasks": tasks,
        "count": len(tasks)
    }


@router.get("/tasks/running")
async def get_running_tasks():
    """Obtiene tareas en ejecución"""
    manager = await get_or_create_manager()
    tasks = manager.get_running_tasks()
    
    return {
        "success": True,
        "tasks": tasks,
        "count": len(tasks)
    }


@router.get("/workers")
async def get_workers():
    """Obtiene estado de los workers"""
    manager = await get_or_create_manager()
    workers = manager.get_workers()
    
    return {
        "success": True,
        "workers": workers
    }


@router.get("/stats")
async def get_stats():
    """Obtiene estadísticas del sistema de background agents"""
    manager = await get_or_create_manager()
    stats = manager.get_stats()
    
    return {
        "success": True,
        "stats": stats
    }


@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancela una tarea pendiente"""
    manager = await get_or_create_manager()
    success = manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="No se puede cancelar (tarea no existe o ya está en ejecución)"
        )
    
    return {
        "success": True,
        "message": f"Tarea {task_id} cancelada"
    }


@router.post("/clear")
async def clear_completed():
    """Limpia tareas completadas/fallidas"""
    manager = await get_or_create_manager()
    count = manager.clear_completed()
    
    return {
        "success": True,
        "cleared": count,
        "message": f"{count} tareas limpiadas"
    }


@router.get("/status")
async def get_status():
    """Estado del sistema de Background Agents"""
    manager = await get_or_create_manager()
    stats = manager.get_stats()
    workers = manager.get_workers()
    
    return {
        "status": "active",
        "workers_total": len(workers),
        "workers_busy": stats["workers"]["busy"],
        "workers_idle": stats["workers"]["idle"],
        "queue_size": stats["queue_size"],
        "tasks": {
            "total": stats["total_tasks"],
            "pending": stats["pending"],
            "running": stats["running"],
            "completed": stats["completed"],
            "failed": stats["failed"]
        },
        "features": [
            "Ejecución paralela real con ThreadPoolExecutor",
            "Cola de tareas con prioridades",
            "Múltiples workers independientes",
            "Estado en tiempo real",
            "Soporte para tareas sync y async"
        ]
    }


# ============================================================================
# ENDPOINTS DE NOTIFICACIONES (para polling del frontend)
# ============================================================================

# Almacén en memoria de notificaciones por conversación
_notifications: Dict[int, List[Dict[str, Any]]] = {}


@router.get("/notifications/{conversation_id}")
async def get_notifications(conversation_id: int, since: Optional[int] = None):
    """
    Obtiene notificaciones para una conversación específica.
    
    Este endpoint es llamado por el frontend via polling para obtener
    actualizaciones de tareas en background.
    
    Args:
        conversation_id: ID de la conversación
        since: Timestamp desde el cual obtener notificaciones (opcional)
    
    Returns:
        Lista de notificaciones pendientes
    """
    manager = await get_or_create_manager()
    
    # Obtener tareas relacionadas con esta conversación
    all_tasks = manager.get_all_tasks(limit=20)
    
    # Filtrar tareas recientes (últimos 5 minutos) que podrían ser notificaciones
    import time
    current_time = time.time()
    recent_notifications = []
    
    for task in all_tasks:
        # Considerar tareas completadas o fallidas recientemente como notificaciones
        if task.get("status") in ["completed", "failed"]:
            task_time = task.get("completed_at") or task.get("started_at") or 0
            # Solo tareas de los últimos 5 minutos
            if current_time - task_time < 300:
                recent_notifications.append({
                    "id": task.get("id"),
                    "type": "task_" + task.get("status", "unknown"),
                    "message": f"Tarea '{task.get('name', 'Sin nombre')}' {task.get('status')}",
                    "task_id": task.get("id"),
                    "status": task.get("status"),
                    "result": task.get("result"),
                    "timestamp": task_time,
                    "conversation_id": conversation_id
                })
    
    # También incluir notificaciones almacenadas manualmente
    stored = _notifications.get(conversation_id, [])
    
    # Combinar y ordenar por timestamp
    all_notifs = recent_notifications + stored
    all_notifs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    # Limitar a las últimas 10
    all_notifs = all_notifs[:10]
    
    return {
        "success": True,
        "notifications": all_notifs,
        "count": len(all_notifs),
        "conversation_id": conversation_id
    }


@router.post("/notifications/{conversation_id}")
async def add_notification(conversation_id: int, notification: Dict[str, Any]):
    """
    Agrega una notificación para una conversación.
    
    Útil para que otros módulos puedan enviar notificaciones al frontend.
    """
    import time
    
    if conversation_id not in _notifications:
        _notifications[conversation_id] = []
    
    notif = {
        "id": f"notif_{conversation_id}_{int(time.time()*1000)}",
        "timestamp": time.time(),
        "conversation_id": conversation_id,
        **notification
    }
    
    _notifications[conversation_id].append(notif)
    
    # Mantener solo las últimas 50 notificaciones por conversación
    if len(_notifications[conversation_id]) > 50:
        _notifications[conversation_id] = _notifications[conversation_id][-50:]
    
    return {
        "success": True,
        "notification": notif
    }


@router.delete("/notifications/{conversation_id}")
async def clear_notifications(conversation_id: int):
    """Limpia las notificaciones de una conversación"""
    if conversation_id in _notifications:
        count = len(_notifications[conversation_id])
        _notifications[conversation_id] = []
        return {
            "success": True,
            "cleared": count
        }
    
    return {
        "success": True,
        "cleared": 0
    }


@router.get("/tasks/active")
async def get_active_tasks(conversation_id: Optional[int] = None):
    """
    Obtiene tareas activas (pendientes o en ejecución).
    
    Args:
        conversation_id: Filtrar por conversación (opcional)
    
    Returns:
        Lista de tareas activas
    """
    manager = await get_or_create_manager()
    
    pending = manager.get_pending_tasks()
    running = manager.get_running_tasks()
    
    active_tasks = pending + running
    
    return {
        "success": True,
        "tasks": active_tasks,
        "count": len(active_tasks),
        "pending": len(pending),
        "running": len(running)
    }
