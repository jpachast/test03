"""
Configuración del agente OpenHands
"""

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.browser_use import BrowserUseTool
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool

from config.rules import REGLAS_AGENTE


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None) -> Agent:
    """
    Crea y configura el agente OpenHands
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar (default: gemini/gemini-2.5-pro)
        base_url: URL base del LLM (opcional)
    
    Returns:
        Agent configurado
    """
    
    # Configurar LLM
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # Configurar Tools
    tools = [
        # Esenciales
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        
        # Navegador (pruebas visuales)
        Tool(name=BrowserUseTool.name),
        
        # Búsqueda
        Tool(name=GlobTool.name),
        Tool(name=GrepTool.name),
    ]
    
    # Configurar Context con reglas
    agent_context = AgentContext(
        skills=[
            Skill(
                name="reglas_comportamiento",
                content=REGLAS_AGENTE,
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
