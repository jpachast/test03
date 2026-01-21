"""
Background Agents - Sistema de agentes en background con ejecución paralela real

Características:
- Ejecución paralela real usando asyncio + ThreadPoolExecutor
- Cola de tareas persistente
- Estado de cada agente en tiempo real
- Callbacks para notificaciones
- Límite de concurrencia configurable
"""

import asyncio
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from queue import Queue
import threading

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class BackgroundTask:
    """Representa una tarea en background"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.value,
            "result": self.result if self.status == TaskStatus.COMPLETED else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "duration": (self.completed_at - self.started_at).total_seconds() if self.completed_at and self.started_at else None,
            "metadata": self.metadata
        }


@dataclass 
class AgentWorker:
    """Un worker que ejecuta tareas"""
    id: str
    name: str
    status: str = "idle"
    current_task: Optional[str] = None
    tasks_completed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "uptime": (datetime.now() - self.created_at).total_seconds()
        }


class BackgroundAgentManager:
    """
    Gestor de agentes en background con ejecución paralela real.
    
    Usa ThreadPoolExecutor para ejecutar múltiples tareas en paralelo,
    combinado con asyncio para operaciones no bloqueantes.
    """
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Estado
        self._tasks: Dict[str, BackgroundTask] = {}
        self._workers: Dict[str, AgentWorker] = {}
        self._task_queue: asyncio.Queue = None
        self._executor: ThreadPoolExecutor = None
        self._running = False
        self._lock = threading.Lock()
        
        # Callbacks
        self._on_task_complete: Optional[Callable] = None
        self._on_task_error: Optional[Callable] = None
        self._on_task_progress: Optional[Callable] = None
        
        # Inicializar workers
        for i in range(max_workers):
            worker_id = f"worker-{i+1}"
            self._workers[worker_id] = AgentWorker(
                id=worker_id,
                name=f"Background Agent #{i+1}"
            )
    
    async def start(self):
        """Inicia el manager"""
        if self._running:
            return
        
        self._running = True
        self._task_queue = asyncio.Queue(maxsize=self.max_queue_size)
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Iniciar workers
        for worker_id in self._workers:
            asyncio.create_task(self._worker_loop(worker_id))
        
        logger.info(f"[BACKGROUND] Manager iniciado con {self.max_workers} workers")
    
    async def stop(self):
        """Detiene el manager"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False)
        logger.info("[BACKGROUND] Manager detenido")
    
    def submit_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: dict = None
    ) -> str:
        """
        Envía una tarea para ejecución en background.
        
        Returns:
            task_id: ID único de la tarea
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        # Agregar a la cola (no bloqueante)
        if self._task_queue:
            try:
                self._task_queue.put_nowait(task_id)
                logger.info(f"[BACKGROUND] Tarea '{name}' (id={task_id}) encolada")
            except asyncio.QueueFull:
                task.status = TaskStatus.FAILED
                task.error = "Cola llena"
                logger.error(f"[BACKGROUND] Cola llena, tarea rechazada: {name}")
        
        return task_id
    
    async def submit_task_async(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: dict = None
    ) -> str:
        """Versión async de submit_task"""
        task_id = str(uuid.uuid4())[:8]
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        if self._task_queue:
            await self._task_queue.put(task_id)
            logger.info(f"[BACKGROUND] Tarea '{name}' (id={task_id}) encolada")
        
        return task_id
    
    async def _worker_loop(self, worker_id: str):
        """Loop principal de un worker"""
        worker = self._workers[worker_id]
        
        while self._running:
            try:
                # Esperar tarea de la cola
                try:
                    task_id = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                task = self._tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # Ejecutar tarea
                worker.status = "working"
                worker.current_task = task_id
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                logger.info(f"[BACKGROUND] Worker {worker_id} ejecutando: {task.name}")
                
                try:
                    # Ejecutar en ThreadPool para no bloquear
                    loop = asyncio.get_event_loop()
                    
                    if asyncio.iscoroutinefunction(task.func):
                        # Si es async, ejecutar directamente
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        # Si es sync, usar executor
                        result = await loop.run_in_executor(
                            self._executor,
                            lambda: task.func(*task.args, **task.kwargs)
                        )
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.progress = 100
                    worker.tasks_completed += 1
                    
                    logger.info(f"[BACKGROUND] Tarea completada: {task.name}")
                    
                    if self._on_task_complete:
                        try:
                            self._on_task_complete(task)
                        except:
                            pass
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now()
                    
                    logger.error(f"[BACKGROUND] Error en tarea {task.name}: {e}")
                    
                    if self._on_task_error:
                        try:
                            self._on_task_error(task, e)
                        except:
                            pass
                
                finally:
                    worker.status = "idle"
                    worker.current_task = None
                    self._task_queue.task_done()
                    
            except Exception as e:
                logger.error(f"[BACKGROUND] Error en worker {worker_id}: {e}")
                await asyncio.sleep(1)
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Obtiene el estado de una tarea"""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_all_tasks(self, limit: int = 50) -> List[Dict]:
        """Obtiene todas las tareas"""
        tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]
    
    def get_pending_tasks(self) -> List[Dict]:
        """Obtiene tareas pendientes"""
        return [
            t.to_dict() for t in self._tasks.values()
            if t.status == TaskStatus.PENDING
        ]
    
    def get_running_tasks(self) -> List[Dict]:
        """Obtiene tareas en ejecución"""
        return [
            t.to_dict() for t in self._tasks.values()
            if t.status == TaskStatus.RUNNING
        ]
    
    def get_workers(self) -> List[Dict]:
        """Obtiene estado de los workers"""
        return [w.to_dict() for w in self._workers.values()]
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del sistema"""
        tasks = list(self._tasks.values())
        
        return {
            "total_tasks": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "workers": {
                "total": len(self._workers),
                "busy": sum(1 for w in self._workers.values() if w.status == "working"),
                "idle": sum(1 for w in self._workers.values() if w.status == "idle")
            },
            "queue_size": self._task_queue.qsize() if self._task_queue else 0
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea pendiente"""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            return True
        return False
    
    def clear_completed(self):
        """Limpia tareas completadas"""
        to_remove = [
            task_id for task_id, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        for task_id in to_remove:
            del self._tasks[task_id]
        return len(to_remove)
    
    def set_callbacks(
        self,
        on_complete: Callable = None,
        on_error: Callable = None,
        on_progress: Callable = None
    ):
        """Configura callbacks para eventos"""
        self._on_task_complete = on_complete
        self._on_task_error = on_error
        self._on_task_progress = on_progress


# Instancia global del manager
_manager: Optional[BackgroundAgentManager] = None


async def get_manager() -> BackgroundAgentManager:
    """Obtiene o crea el manager global"""
    global _manager
    if _manager is None:
        _manager = BackgroundAgentManager(max_workers=4)
        await _manager.start()
    return _manager


def get_manager_sync() -> Optional[BackgroundAgentManager]:
    """Obtiene el manager de forma síncrona (si existe)"""
    return _manager


# ============================================
# Tareas de ejemplo para demostración
# ============================================

def demo_task_slow(seconds: int = 5, name: str = "Demo") -> Dict:
    """Tarea de demostración que toma tiempo"""
    import time
    time.sleep(seconds)
    return {
        "task": name,
        "duration": seconds,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }


def demo_task_compute(n: int = 1000000) -> Dict:
    """Tarea de cómputo intensivo"""
    result = sum(i * i for i in range(n))
    return {
        "computation": "sum of squares",
        "n": n,
        "result": result
    }


async def demo_task_async(url: str = "https://httpbin.org/delay/2") -> Dict:
    """Tarea async de demostración"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "fetched_at": datetime.now().isoformat()
            }


def demo_task_analyze_code(code: str) -> Dict:
    """Analiza código (demo)"""
    lines = code.count('\n') + 1
    functions = code.count('def ') + code.count('function ')
    classes = code.count('class ')
    
    return {
        "lines": lines,
        "functions": functions,
        "classes": classes,
        "complexity": "low" if lines < 50 else "medium" if lines < 200 else "high"
    }
