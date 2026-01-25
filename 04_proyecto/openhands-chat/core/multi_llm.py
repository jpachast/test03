"""
Multi-LLM System - Múltiples LLMs simultáneos

Permite usar diferentes LLMs para diferentes tareas:
- Análisis de código (modelo especializado)
- Generación de texto (modelo creativo)
- Razonamiento (modelo lógico)
- Resumen (modelo eficiente)

Los LLMs se ejecutan en paralelo cuando es posible.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Proveedores de LLM soportados"""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMRole(Enum):
    """Roles especializados para cada LLM"""
    CODER = "coder"           # Análisis y generación de código
    WRITER = "writer"         # Generación de texto y documentación
    REASONER = "reasoner"     # Razonamiento lógico y matemático
    SUMMARIZER = "summarizer" # Resúmenes y síntesis
    REVIEWER = "reviewer"     # Revisión de código y calidad
    FAST = "fast"             # Respuestas rápidas y simples


@dataclass
class LLMConfig:
    """Configuración de un LLM"""
    provider: LLMProvider
    model: str
    role: LLMRole
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    priority: int = 1  # 1 = más alta prioridad


@dataclass
class LLMResponse:
    """Respuesta de un LLM"""
    role: LLMRole
    model: str
    content: str
    tokens_used: int
    latency_ms: float
    success: bool
    error: Optional[str] = None


# Configuraciones predefinidas de LLMs por rol
DEFAULT_LLM_CONFIGS = {
    LLMRole.CODER: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.3-70b-versatile",
        role=LLMRole.CODER,
        temperature=0.3,
        max_tokens=8192,
        priority=1
    ),
    LLMRole.WRITER: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        role=LLMRole.WRITER,
        temperature=0.8,
        max_tokens=4096,
        priority=2
    ),
    LLMRole.REASONER: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.3-70b-versatile",
        role=LLMRole.REASONER,
        temperature=0.2,
        max_tokens=8192,
        priority=1
    ),
    LLMRole.SUMMARIZER: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        role=LLMRole.SUMMARIZER,
        temperature=0.3,
        max_tokens=2048,
        priority=3
    ),
    LLMRole.REVIEWER: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.3-70b-versatile",
        role=LLMRole.REVIEWER,
        temperature=0.2,
        max_tokens=4096,
        priority=2
    ),
    LLMRole.FAST: LLMConfig(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        role=LLMRole.FAST,
        temperature=0.5,
        max_tokens=1024,
        priority=1
    ),
}


class MultiLLMManager:
    """
    Gestor de múltiples LLMs simultáneos.
    
    Permite ejecutar tareas en paralelo con diferentes modelos
    especializados para cada tipo de tarea.
    """
    
    def __init__(self, groq_api_key: str = None, openai_api_key: str = None):
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "") or self._load_groq_key_from_db()
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.configs: Dict[LLMRole, LLMConfig] = DEFAULT_LLM_CONFIGS.copy()
        self._clients: Dict[LLMProvider, Any] = {}
        self._initialized = False
    
    def _load_groq_key_from_db(self) -> str:
        """Intenta cargar GROQ_API_KEY desde la base de datos"""
        try:
            import sqlite3
            from pathlib import Path
            
            # Buscar en diferentes ubicaciones
            db_paths = [
                Path("/app/data/config.db"),
                Path(__file__).parent.parent / "data" / "config.db",
            ]
            
            for db_path in db_paths:
                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute("SELECT value, encrypted FROM settings WHERE key = 'groq_api_key'")
                    row = cur.fetchone()
                    conn.close()
                    
                    if row:
                        value, encrypted = row
                        if encrypted:
                            # Desencriptar si es necesario
                            try:
                                from config.db.settings import SettingsManager
                                sm = SettingsManager(str(db_path))
                                return sm.get_setting('groq_api_key') or ""
                            except:
                                pass
                        return value or ""
            return ""
        except Exception as e:
            logger.debug(f"Could not load groq_api_key from db: {e}")
            return ""
        
    def _get_groq_client(self):
        """Obtiene o crea cliente Groq"""
        if LLMProvider.GROQ not in self._clients:
            try:
                from groq import Groq
                self._clients[LLMProvider.GROQ] = Groq(api_key=self.groq_api_key)
            except ImportError:
                logger.warning("Groq not installed, using httpx")
                self._clients[LLMProvider.GROQ] = None
        return self._clients.get(LLMProvider.GROQ)
    
    def _get_openai_client(self):
        """Obtiene o crea cliente OpenAI"""
        if LLMProvider.OPENAI not in self._clients:
            try:
                from openai import OpenAI
                self._clients[LLMProvider.OPENAI] = OpenAI(api_key=self.openai_api_key)
            except ImportError:
                logger.warning("OpenAI not installed")
                self._clients[LLMProvider.OPENAI] = None
        return self._clients.get(LLMProvider.OPENAI)
    
    async def _call_groq(self, config: LLMConfig, messages: List[Dict]) -> LLMResponse:
        """Llama a Groq API"""
        start_time = time.time()
        
        try:
            import httpx
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config.model,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    
                    return LLMResponse(
                        role=config.role,
                        model=config.model,
                        content=content,
                        tokens_used=tokens,
                        latency_ms=(time.time() - start_time) * 1000,
                        success=True
                    )
                else:
                    return LLMResponse(
                        role=config.role,
                        model=config.model,
                        content="",
                        tokens_used=0,
                        latency_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error=f"API error: {response.status_code}"
                    )
                    
        except Exception as e:
            return LLMResponse(
                role=config.role,
                model=config.model,
                content="",
                tokens_used=0,
                latency_ms=(time.time() - start_time) * 1000,
                success=False,
                error=str(e)
            )
    
    async def query_single(self, role: LLMRole, prompt: str, 
                           system_prompt: str = None) -> LLMResponse:
        """
        Consulta a un LLM específico por rol.
        
        Args:
            role: Rol del LLM a usar
            prompt: Prompt del usuario
            system_prompt: Prompt del sistema (opcional)
        
        Returns:
            LLMResponse con la respuesta
        """
        config = self.configs.get(role)
        if not config:
            return LLMResponse(
                role=role,
                model="unknown",
                content="",
                tokens_used=0,
                latency_ms=0,
                success=False,
                error=f"No config for role: {role}"
            )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        if config.provider == LLMProvider.GROQ:
            return await self._call_groq(config, messages)
        else:
            return LLMResponse(
                role=role,
                model=config.model,
                content="",
                tokens_used=0,
                latency_ms=0,
                success=False,
                error=f"Provider not supported: {config.provider}"
            )
    
    async def query_parallel(self, tasks: List[Dict]) -> List[LLMResponse]:
        """
        Ejecuta múltiples consultas en paralelo.
        
        Args:
            tasks: Lista de dicts con {role, prompt, system_prompt (opcional)}
        
        Returns:
            Lista de LLMResponse en el mismo orden
        """
        coroutines = []
        for task in tasks:
            role = task.get("role", LLMRole.FAST)
            if isinstance(role, str):
                role = LLMRole(role)
            prompt = task.get("prompt", "")
            system_prompt = task.get("system_prompt")
            coroutines.append(self.query_single(role, prompt, system_prompt))
        
        return await asyncio.gather(*coroutines)
    
    async def analyze_with_multiple_perspectives(self, code: str, 
                                                  question: str) -> Dict[str, Any]:
        """
        Analiza código con múltiples LLMs simultáneamente.
        
        Cada LLM aporta una perspectiva diferente:
        - CODER: Análisis técnico del código
        - REVIEWER: Revisión de calidad y mejores prácticas
        - REASONER: Lógica y posibles bugs
        
        Returns:
            Dict con las perspectivas combinadas
        """
        tasks = [
            {
                "role": LLMRole.CODER,
                "prompt": f"Analiza este código desde una perspectiva técnica:\n\n```\n{code}\n```\n\nPregunta: {question}",
                "system_prompt": "Eres un experto programador. Analiza el código técnicamente."
            },
            {
                "role": LLMRole.REVIEWER,
                "prompt": f"Revisa este código buscando problemas de calidad:\n\n```\n{code}\n```\n\nPregunta: {question}",
                "system_prompt": "Eres un revisor de código experto. Busca problemas de calidad, seguridad y mejores prácticas."
            },
            {
                "role": LLMRole.REASONER,
                "prompt": f"Analiza la lógica de este código:\n\n```\n{code}\n```\n\nPregunta: {question}",
                "system_prompt": "Eres un experto en lógica y algoritmos. Analiza el flujo lógico y posibles bugs."
            }
        ]
        
        responses = await self.query_parallel(tasks)
        
        return {
            "technical_analysis": responses[0].content if responses[0].success else responses[0].error,
            "code_review": responses[1].content if responses[1].success else responses[1].error,
            "logic_analysis": responses[2].content if responses[2].success else responses[2].error,
            "models_used": [r.model for r in responses],
            "total_tokens": sum(r.tokens_used for r in responses),
            "total_latency_ms": max(r.latency_ms for r in responses),  # Paralelo = max tiempo
            "all_success": all(r.success for r in responses)
        }
    
    async def get_consensus(self, prompt: str, num_models: int = 3) -> Dict[str, Any]:
        """
        Obtiene consenso de múltiples modelos sobre una pregunta.
        
        Útil para decisiones importantes donde queremos múltiples opiniones.
        """
        roles = [LLMRole.CODER, LLMRole.REASONER, LLMRole.REVIEWER][:num_models]
        
        tasks = [
            {
                "role": role,
                "prompt": prompt,
                "system_prompt": "Responde de forma concisa y directa."
            }
            for role in roles
        ]
        
        responses = await self.query_parallel(tasks)
        
        # Combinar respuestas
        answers = [r.content for r in responses if r.success]
        
        return {
            "answers": answers,
            "num_responses": len(answers),
            "models_used": [r.model for r in responses if r.success],
            "consensus_needed": len(set(answers)) == 1,
            "total_latency_ms": max(r.latency_ms for r in responses)
        }
    
    def get_available_models(self) -> List[Dict]:
        """Retorna lista de modelos disponibles"""
        return [
            {
                "role": config.role.value,
                "provider": config.provider.value,
                "model": config.model,
                "priority": config.priority
            }
            for config in self.configs.values()
        ]


# Singleton global
_multi_llm_manager: Optional[MultiLLMManager] = None


def get_multi_llm_manager() -> MultiLLMManager:
    """Obtiene el gestor global de multi-LLM"""
    global _multi_llm_manager
    if _multi_llm_manager is None:
        _multi_llm_manager = MultiLLMManager()
    return _multi_llm_manager


def set_multi_llm_manager(manager: MultiLLMManager):
    """Establece el gestor global de multi-LLM"""
    global _multi_llm_manager
    _multi_llm_manager = manager


# === CLI para uso desde terminal ===

async def main_cli():
    """CLI para probar multi-LLM"""
    import sys
    
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Uso: python -m core.multi_llm <comando> <prompt>",
            "commands": ["query", "parallel", "analyze", "consensus", "models"]
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    manager = get_multi_llm_manager()
    
    if command == "models":
        print(json.dumps({"models": manager.get_available_models()}))
        return
    
    prompt = " ".join(sys.argv[2:])
    
    if command == "query":
        # query <role> <prompt>
        role_str = sys.argv[2] if len(sys.argv) > 2 else "fast"
        prompt = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        try:
            role = LLMRole(role_str)
        except ValueError:
            role = LLMRole.FAST
        
        response = await manager.query_single(role, prompt)
        print(json.dumps({
            "success": response.success,
            "role": response.role.value,
            "model": response.model,
            "content": response.content,
            "tokens": response.tokens_used,
            "latency_ms": response.latency_ms,
            "error": response.error
        }))
    
    elif command == "consensus":
        result = await manager.get_consensus(prompt)
        print(json.dumps(result))
    
    elif command == "analyze":
        # Para analyze, el primer arg después del comando es el código
        code = sys.argv[2] if len(sys.argv) > 2 else ""
        question = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "¿Qué hace este código?"
        result = await manager.analyze_with_multiple_perspectives(code, question)
        print(json.dumps(result))
    
    else:
        print(json.dumps({"error": f"Comando desconocido: {command}"}))


if __name__ == "__main__":
    asyncio.run(main_cli())
