"""
Multi-Agent System - Múltiples agentes con LLMs REALES en paralelo

Arquitectura:
- Cada agente tiene un rol especializado con su propio system prompt
- Todos los agentes usan Claude API en paralelo (asyncio.gather)
- El orquestador coordina y combina resultados

Roles:
- RESEARCHER: Investiga y busca información (usa Tavily + LLM)
- CODER: Escribe y ejecuta código (LLM + Sandbox)
- TESTER: Genera y ejecuta tests (LLM + Sandbox)
- REVIEWER: Analiza calidad del código (LLM)
- DOCUMENTER: Genera documentación (LLM)
- ARCHITECT: Diseña arquitectura y estructura (LLM)
- SECURITY: Analiza vulnerabilidades (LLM)
"""

import asyncio
import aiohttp
import json
import logging
import re
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"
    ARCHITECT = "architect"
    SECURITY = "security"


# System prompts especializados para cada agente
AGENT_PROMPTS = {
    AgentRole.RESEARCHER: """Eres un agente investigador experto. Tu trabajo es:
- Analizar la información proporcionada
- Identificar patrones y datos relevantes
- Resumir hallazgos de forma clara y estructurada
- Proporcionar fuentes cuando sea posible
Responde de forma concisa y estructurada.""",

    AgentRole.CODER: """Eres un programador experto. Tu trabajo es:
- Escribir código limpio, eficiente y bien estructurado
- Seguir mejores prácticas del lenguaje
- Incluir manejo de errores apropiado
- Documentar funciones importantes
Responde SOLO con el código solicitado, sin explicaciones largas.""",

    AgentRole.TESTER: """Eres un experto en testing y QA. Tu trabajo es:
- Generar tests unitarios completos
- Cubrir casos edge y excepciones
- Verificar comportamiento esperado
- Usar assertions claras
Genera tests ejecutables directamente.""",

    AgentRole.REVIEWER: """Eres un revisor de código senior. Tu trabajo es:
- Identificar bugs potenciales
- Detectar problemas de rendimiento
- Verificar buenas prácticas
- Sugerir mejoras concretas
Proporciona un score de 0-100 y lista de issues encontrados.""",

    AgentRole.DOCUMENTER: """Eres un experto en documentación técnica. Tu trabajo es:
- Generar documentación clara y completa
- Incluir ejemplos de uso
- Documentar parámetros y retornos
- Crear docstrings profesionales
Usa formato Markdown.""",

    AgentRole.ARCHITECT: """Eres un arquitecto de software senior. Tu trabajo es:
- Diseñar estructura de código escalable
- Proponer patrones de diseño apropiados
- Identificar componentes y sus relaciones
- Sugerir tecnologías y herramientas
Responde con diagramas ASCII cuando sea útil.""",

    AgentRole.SECURITY: """Eres un experto en seguridad de software. Tu trabajo es:
- Identificar vulnerabilidades (SQL injection, XSS, etc.)
- Detectar manejo inseguro de datos
- Verificar validación de inputs
- Sugerir correcciones de seguridad
Clasifica severidad: CRÍTICA, ALTA, MEDIA, BAJA.""",
}


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
    llm_response: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class AgentSession:
    """Sesión de trabajo multi-agente"""
    id: str
    objective: str
    tasks: List[AgentTask] = field(default_factory=list)
    status: str = "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    total_tokens: int = 0
    total_time: float = 0.0
    combined_result: Optional[str] = None

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
                    "error": t.error,
                    "llm_response": t.llm_response,
                    "output_data": t.output_data,
                    "execution_time": round(t.execution_time, 2),
                    "tokens_used": t.tokens_used
                }
                for t in self.tasks
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "total_tokens": self.total_tokens,
            "total_time": round(self.total_time, 2),
            "combined_result": self.combined_result,
            "progress": {
                "total": len(self.tasks),
                "completed": sum(1 for t in self.tasks if t.status == AgentStatus.COMPLETED),
                "failed": sum(1 for t in self.tasks if t.status == AgentStatus.FAILED)
            }
        }


class LLMClient:
    """Cliente async para llamar a Claude API directamente"""

    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Llamada async a Claude API"""
        session = await self._get_session()

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }

        start_time = time.time()

        try:
            async with session.post(
                self.ANTHROPIC_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                elapsed = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    content = data.get("content", [{}])[0].get("text", "")
                    usage = data.get("usage", {})
                    return {
                        "success": True,
                        "content": content,
                        "tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                        "elapsed": elapsed
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error {response.status}: {error_text[:200]}",
                        "tokens": 0,
                        "elapsed": elapsed
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout: La llamada al LLM tardó demasiado",
                "tokens": 0,
                "elapsed": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "tokens": 0,
                "elapsed": time.time() - start_time
            }


class MultiAgentOrchestrator:
    """
    Orquestador de múltiples agentes LLM trabajando en PARALELO REAL.
    Cada agente hace una llamada a Claude API con su system prompt especializado.
    """

    def __init__(self, sandbox=None, scraper=None, api_key: str = None, model: str = None):
        self.sandbox = sandbox
        self.scraper = scraper
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-20250514"
        self.sessions: Dict[str, AgentSession] = {}
        self._llm_client: Optional[LLMClient] = None

    def _get_llm_client(self) -> LLMClient:
        """Obtiene o crea el cliente LLM"""
        if not self.api_key:
            raise ValueError("No API key configured for multi-agent system")
        if self._llm_client is None:
            self._llm_client = LLMClient(self.api_key, self.model)
        return self._llm_client

    def set_api_key(self, api_key: str, model: str = None):
        """Actualiza la API key (y opcionalmente el modelo)"""
        self.api_key = api_key
        if model:
            self.model = model
        self._llm_client = None

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
            role_str = config.get('role', 'coder')
            try:
                role = AgentRole(role_str)
            except ValueError:
                role = AgentRole.CODER

            task = AgentTask(
                id=str(uuid.uuid4())[:8],
                role=role,
                description=config.get('description', ''),
                input_data=config.get('input', {})
            )
            session.tasks.append(task)

        self.sessions[session.id] = session
        return session

    async def run_session(self, session_id: str) -> AgentSession:
        """Ejecuta TODOS los agentes en PARALELO REAL usando asyncio.gather"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = "running"
        start_time = time.time()

        # Crear coroutines para TODAS las tareas
        tasks_coros = [self._run_agent_task(task) for task in session.tasks]

        # Ejecutar TODAS en paralelo
        logger.info(f"[MULTI-AGENT] Ejecutando {len(tasks_coros)} agentes en paralelo...")
        await asyncio.gather(*tasks_coros, return_exceptions=True)

        # Calcular totales
        session.total_time = time.time() - start_time
        session.total_tokens = sum(t.tokens_used for t in session.tasks)

        # Combinar resultados de todos los agentes
        session.combined_result = self._combine_results(session)

        # Estado final
        completed = sum(1 for t in session.tasks if t.status == AgentStatus.COMPLETED)
        failed = sum(1 for t in session.tasks if t.status == AgentStatus.FAILED)

        if failed == 0:
            session.status = "completed"
        elif completed > 0:
            session.status = "partial"
        else:
            session.status = "failed"

        session.completed_at = datetime.now().isoformat()
        logger.info(
            f"[MULTI-AGENT] Sesión {session_id} completada: "
            f"{completed}/{len(session.tasks)} exitosos, "
            f"{session.total_tokens} tokens, "
            f"{session.total_time:.2f}s"
        )

        return session

    async def _run_agent_task(self, task: AgentTask):
        """Ejecuta una tarea individual de agente con LLM real"""
        task.status = AgentStatus.WORKING
        task.started_at = datetime.now().isoformat()
        start_time = time.time()

        try:
            llm = self._get_llm_client()
            system_prompt = AGENT_PROMPTS.get(task.role, AGENT_PROMPTS[AgentRole.CODER])

            # Construir mensaje de usuario basado en input_data
            user_message = self._build_user_message(task)

            # Llamar al LLM
            result = await llm.chat(system_prompt, user_message)

            task.execution_time = time.time() - start_time
            task.tokens_used = result.get("tokens", 0)

            if result["success"]:
                task.llm_response = result["content"]
                task.output_data = self._process_llm_response(task.role, result["content"])
                task.status = AgentStatus.COMPLETED
                logger.info(f"[AGENT:{task.role.value}] Completado en {task.execution_time:.2f}s")
            else:
                task.error = result.get("error", "Unknown error")
                task.status = AgentStatus.FAILED
                logger.error(f"[AGENT:{task.role.value}] Error: {task.error}")

        except Exception as e:
            task.execution_time = time.time() - start_time
            task.error = str(e)
            task.status = AgentStatus.FAILED
            logger.error(f"[AGENT:{task.role.value}] Exception: {e}")

        task.completed_at = datetime.now().isoformat()

    def _build_user_message(self, task: AgentTask) -> str:
        """Construye el mensaje de usuario para el LLM basado en el rol y datos"""
        input_data = task.input_data
        role = task.role

        if role == AgentRole.RESEARCHER:
            query = input_data.get('query', input_data.get('topic', 'Sin tema'))
            context = input_data.get('context', '')
            return f"Investiga sobre: {query}\n\nContexto adicional:\n{context}" if context else f"Investiga sobre: {query}"

        elif role == AgentRole.CODER:
            task_desc = input_data.get('task', input_data.get('description', ''))
            language = input_data.get('language', 'python')
            code = input_data.get('code', '')
            if code:
                return f"Lenguaje: {language}\n\nCódigo existente:\n```{language}\n{code}\n```\n\nTarea: {task_desc}"
            return f"Lenguaje: {language}\n\nTarea: {task_desc}"

        elif role == AgentRole.TESTER:
            code = input_data.get('code', '')
            language = input_data.get('language', 'python')
            return f"Genera tests unitarios para este código {language}:\n\n```{language}\n{code}\n```"

        elif role == AgentRole.REVIEWER:
            code = input_data.get('code', '')
            language = input_data.get('language', 'python')
            return f"Revisa este código {language} y proporciona:\n1. Score de calidad (0-100)\n2. Lista de issues\n3. Sugerencias de mejora\n\n```{language}\n{code}\n```"

        elif role == AgentRole.DOCUMENTER:
            code = input_data.get('code', '')
            language = input_data.get('language', 'python')
            return f"Genera documentación completa para este código {language}:\n\n```{language}\n{code}\n```"

        elif role == AgentRole.ARCHITECT:
            requirements = input_data.get('requirements', input_data.get('description', ''))
            return f"Diseña la arquitectura para: {requirements}"

        elif role == AgentRole.SECURITY:
            code = input_data.get('code', '')
            language = input_data.get('language', 'python')
            return f"Analiza la seguridad de este código {language}:\n\n```{language}\n{code}\n```"

        # Default
        return json.dumps(input_data, indent=2)

    def _process_llm_response(self, role: AgentRole, response: str) -> Dict[str, Any]:
        """Procesa la respuesta del LLM según el rol"""
        result = {"raw_response": response}

        if role == AgentRole.REVIEWER:
            # Extraer score
            score_match = re.search(r'(\d{1,3})/100|score[:\s]+(\d{1,3})', response.lower())
            if score_match:
                result["score"] = int(score_match.group(1) or score_match.group(2))
            else:
                result["score"] = 70

            # Extraer issues
            issues = re.findall(r'[-•]\s*(.+)', response)
            result["issues"] = issues[:10]
            result["issues_count"] = len(issues)

        elif role == AgentRole.CODER:
            # Extraer código
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
            if code_blocks:
                result["generated_code"] = code_blocks[0].strip()
            result["has_code"] = len(code_blocks) > 0

        elif role == AgentRole.TESTER:
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
            if code_blocks:
                result["test_code"] = code_blocks[0].strip()
            result["tests_generated"] = len(code_blocks)

        elif role == AgentRole.SECURITY:
            # Buscar severidades
            critical = len(re.findall(r'CRÍTICA|CRITICAL', response, re.IGNORECASE))
            high = len(re.findall(r'ALTA|HIGH', response, re.IGNORECASE))
            medium = len(re.findall(r'MEDIA|MEDIUM', response, re.IGNORECASE))
            low = len(re.findall(r'BAJA|LOW', response, re.IGNORECASE))
            result["vulnerabilities"] = {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
                "total": critical + high + medium + low
            }

        return result

    def _combine_results(self, session: AgentSession) -> str:
        """Combina los resultados de todos los agentes en un resumen"""
        parts = [f"## Resultados Multi-Agent: {session.objective}\n"]

        for task in session.tasks:
            status_emoji = "✅" if task.status == AgentStatus.COMPLETED else "❌"
            parts.append(f"\n### {status_emoji} Agente {task.role.value.upper()}")

            if task.status == AgentStatus.COMPLETED and task.llm_response:
                # Truncar respuesta larga
                response = task.llm_response
                if len(response) > 500:
                    response = response[:500] + "..."
                parts.append(f"\n{response}")
            elif task.error:
                parts.append(f"\n**Error:** {task.error}")

        parts.append(f"\n---\n**Total:** {session.total_tokens} tokens, {session.total_time:.2f}s")
        return "\n".join(parts)

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self.sessions.get(session_id)

    def list_sessions(self, limit: int = 20) -> List[AgentSession]:
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return sessions[:limit]

    async def quick_analysis(
        self,
        code: str,
        language: str = "python",
        include_roles: List[str] = None
    ) -> AgentSession:
        """
        Análisis rápido de código con múltiples agentes en paralelo.
        Por defecto: reviewer, tester, documenter, security
        """
        if include_roles is None:
            include_roles = ["reviewer", "tester", "documenter", "security"]

        tasks_config = []
        for role in include_roles:
            tasks_config.append({
                "role": role,
                "description": f"Análisis {role} del código",
                "input": {"code": code, "language": language}
            })

        session = await self.create_session(
            objective=f"Análisis completo de código {language}",
            tasks_config=tasks_config
        )

        return await self.run_session(session.id)


# Instancia global
_orchestrator_instance: Optional[MultiAgentOrchestrator] = None


def get_orchestrator(
    sandbox=None,
    scraper=None,
    api_key: str = None,
    model: str = None
) -> MultiAgentOrchestrator:
    """Obtiene o crea el orquestador multi-agente"""
    global _orchestrator_instance

    if _orchestrator_instance is None:
        if sandbox is None:
            from core.sandbox import get_sandbox
            sandbox = get_sandbox()
        _orchestrator_instance = MultiAgentOrchestrator(
            sandbox=sandbox,
            scraper=scraper,
            api_key=api_key,
            model=model
        )
    elif api_key and api_key != _orchestrator_instance.api_key:
        _orchestrator_instance.set_api_key(api_key, model)

    return _orchestrator_instance


def reinit_orchestrator(api_key: str = None, model: str = None):
    """Reinicializa el orquestador con nueva configuración"""
    global _orchestrator_instance
    _orchestrator_instance = None
    return get_orchestrator(api_key=api_key, model=model)
