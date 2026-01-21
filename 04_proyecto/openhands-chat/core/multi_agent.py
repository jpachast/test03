"""
Multi-Agent System - Múltiples agentes trabajando en paralelo
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class AgentRole(str, Enum):
    RESEARCHER = "researcher"      # Busca información
    CODER = "coder"               # Escribe código
    TESTER = "tester"             # Ejecuta y valida tests
    REVIEWER = "reviewer"         # Revisa código
    DOCUMENTER = "documenter"     # Genera documentación


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Tarea asignada a un agente"""
    id: str
    role: AgentRole
    description: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.IDLE
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentSession:
    """Sesión de trabajo multi-agente"""
    id: str
    objective: str
    tasks: List[AgentTask] = field(default_factory=list)
    status: str = "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "objective": self.objective,
            "status": self.status,
            "tasks": [
                {
                    "id": t.id,
                    "role": t.role.value,
                    "description": t.description,
                    "status": t.status.value,
                    "error": t.error
                }
                for t in self.tasks
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress": {
                "total": len(self.tasks),
                "completed": sum(1 for t in self.tasks if t.status == AgentStatus.COMPLETED),
                "failed": sum(1 for t in self.tasks if t.status == AgentStatus.FAILED)
            }
        }


class MultiAgentOrchestrator:
    """
    Orquestador de múltiples agentes trabajando en paralelo.
    """
    
    def __init__(self, sandbox, scraper=None):
        self.sandbox = sandbox
        self.scraper = scraper
        self.sessions: Dict[str, AgentSession] = {}
        self.agent_handlers: Dict[AgentRole, Callable] = {
            AgentRole.RESEARCHER: self._research_handler,
            AgentRole.CODER: self._coder_handler,
            AgentRole.TESTER: self._tester_handler,
            AgentRole.REVIEWER: self._reviewer_handler,
            AgentRole.DOCUMENTER: self._documenter_handler,
        }
    
    async def create_session(
        self,
        objective: str,
        tasks_config: List[Dict[str, Any]]
    ) -> AgentSession:
        """Crea una sesión multi-agente"""
        session = AgentSession(
            id=str(uuid.uuid4())[:8],
            objective=objective,
            created_at=datetime.now().isoformat()
        )
        
        for config in tasks_config:
            task = AgentTask(
                id=str(uuid.uuid4())[:8],
                role=AgentRole(config.get('role', 'coder')),
                description=config.get('description', ''),
                input_data=config.get('input', {})
            )
            session.tasks.append(task)
        
        self.sessions[session.id] = session
        return session
    
    async def run_session(self, session_id: str) -> AgentSession:
        """Ejecuta todos los agentes de una sesión en paralelo"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = "running"
        
        # Ejecutar tareas en paralelo
        tasks_coros = []
        for task in session.tasks:
            handler = self.agent_handlers.get(task.role)
            if handler:
                tasks_coros.append(self._run_task(task, handler))
        
        await asyncio.gather(*tasks_coros, return_exceptions=True)
        
        # Verificar estado final
        all_completed = all(t.status == AgentStatus.COMPLETED for t in session.tasks)
        any_failed = any(t.status == AgentStatus.FAILED for t in session.tasks)
        
        session.status = "completed" if all_completed else ("partial" if any_failed else "failed")
        session.completed_at = datetime.now().isoformat()
        
        return session
    
    async def _run_task(self, task: AgentTask, handler: Callable):
        """Ejecuta una tarea individual"""
        task.status = AgentStatus.WORKING
        task.started_at = datetime.now().isoformat()
        
        try:
            result = await handler(task.input_data)
            task.output_data = result
            task.status = AgentStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = AgentStatus.FAILED
        
        task.completed_at = datetime.now().isoformat()
    
    async def _research_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agente investigador - busca información"""
        query = input_data.get('query', '')
        urls = input_data.get('urls', [])
        
        results = []
        if self.scraper and urls:
            for url in urls[:3]:  # Limitar a 3 URLs
                data = await self.scraper.scrape(url)
                if data.success:
                    results.append({
                        "url": url,
                        "title": data.title,
                        "summary": data.text_content[:500]
                    })
        
        return {
            "query": query,
            "sources": results,
            "findings_count": len(results)
        }
    
    async def _coder_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agente codificador - escribe y ejecuta código"""
        code = input_data.get('code', '')
        language = input_data.get('language', 'python')
        
        result = await self.sandbox.execute_async(code, language)
        
        return {
            "code": code,
            "language": language,
            "output": result.stdout,
            "error": result.stderr if result.exit_code != 0 else None,
            "success": result.exit_code == 0
        }
    
    async def _tester_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agente tester - ejecuta tests"""
        code = input_data.get('code', '')
        test_code = input_data.get('test_code', '')
        
        # Combinar código y tests
        full_code = f"{code}\n\n# Tests\n{test_code}"
        
        result = await self.sandbox.execute_async(full_code, 'python')
        
        return {
            "tests_run": True,
            "output": result.stdout,
            "passed": result.exit_code == 0,
            "error": result.stderr if result.exit_code != 0 else None
        }
    
    async def _reviewer_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agente revisor - analiza código"""
        code = input_data.get('code', '')
        
        issues = []
        suggestions = []
        
        # Análisis básico
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Líneas muy largas
            if len(line) > 100:
                issues.append(f"Línea {i}: muy larga ({len(line)} caracteres)")
            # TODO/FIXME
            if 'TODO' in line or 'FIXME' in line:
                suggestions.append(f"Línea {i}: contiene TODO/FIXME pendiente")
            # Print statements
            if 'print(' in line and 'def test' not in code:
                suggestions.append(f"Línea {i}: considerar usar logging en lugar de print")
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "lines_analyzed": len(lines),
            "score": max(0, 100 - len(issues) * 10 - len(suggestions) * 5)
        }
    
    async def _documenter_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agente documentador - genera documentación"""
        code = input_data.get('code', '')
        
        # Extraer funciones y clases
        import re
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        classes = re.findall(r'class\s+(\w+)', code)
        
        # Generar documentación básica
        docs = []
        
        for func in functions:
            docs.append(f"### `{func}()`\nFunción que realiza operaciones relacionadas con {func}.\n")
        
        for cls in classes:
            docs.append(f"### Clase `{cls}`\nClase que implementa funcionalidad de {cls}.\n")
        
        return {
            "documentation": "\n".join(docs) if docs else "No se encontraron funciones o clases documentables.",
            "functions_found": len(functions),
            "classes_found": len(classes)
        }
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self.sessions.get(session_id)
    
    def list_sessions(self, limit: int = 20) -> List[AgentSession]:
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return sessions[:limit]


# Instancia global
_orchestrator_instance: Optional[MultiAgentOrchestrator] = None


def get_orchestrator(sandbox=None, scraper=None) -> MultiAgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        if sandbox is None:
            from core.sandbox import get_sandbox
            sandbox = get_sandbox()
        _orchestrator_instance = MultiAgentOrchestrator(sandbox, scraper)
    return _orchestrator_instance
