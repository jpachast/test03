"""
Configuración del agente OpenHands
BASADO 100% EN LA DOCUMENTACIÓN OFICIAL Y PROMPTS DE REFERENCIA
"""

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill

# === TODAS LAS TOOLS DISPONIBLES EN openhands-tools ===
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.browser_use import BrowserToolSet  # Conjunto de tools de navegador
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool
from openhands.tools.apply_patch import ApplyPatchTool
from openhands.tools.delegate import DelegateTool

from config.rules import REGLAS_AGENTE, SYSTEM_PROMPT_COMPLETO


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None) -> Agent:
    """
    Crea y configura el agente OpenHands
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar (default: gemini/gemini-2.5-pro)
        base_url: URL base del LLM (opcional)
    
    Returns:
        Agent configurado con TODAS las tools y reglas
    """
    
    # Configurar LLM
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # === TODAS LAS TOOLS DISPONIBLES ===
    tools = [
        # Esenciales
        Tool(name=TerminalTool.name),      # Ejecutar comandos bash
        Tool(name=FileEditorTool.name),    # Crear/editar archivos
        Tool(name=TaskTrackerTool.name),   # Seguimiento de tareas
        
        # Búsqueda
        Tool(name=GlobTool.name),          # Buscar archivos por patrón
        Tool(name=GrepTool.name),          # Buscar contenido en archivos
        
        # Avanzadas
        Tool(name=ApplyPatchTool.name),    # Aplicar parches de código
        Tool(name=DelegateTool.name),      # Delegar a sub-agentes
    ]
    
    # Agregar tools de navegador (es un conjunto de tools)
    for browser_tool in BrowserToolSet:
        tools.append(Tool(name=browser_tool.name))
    
    # === CONTEXT CON SYSTEM PROMPT COMPLETO ===
    agent_context = AgentContext(
        skills=[
            # Reglas de comportamiento personalizadas
            Skill(
                name="reglas_comportamiento",
                content=REGLAS_AGENTE,
                source=None,
                trigger=None,  # Siempre activo
            ),
            # System prompt completo basado en prompts de referencia
            Skill(
                name="system_prompt_completo",
                content=SYSTEM_PROMPT_COMPLETO,
                source=None,
                trigger=None,  # Siempre activo
            ),
        ],
        system_message_suffix=REGLAS_AGENTE,
        load_public_skills=True,
    )
    
    # Crear agente
    agent = Agent(
        llm=llm,
        tools=tools,
        agent_context=agent_context,
    )
    
    return agent
