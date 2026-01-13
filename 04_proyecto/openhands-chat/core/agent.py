"""
Configuración del agente OpenHands
BASADO 100% EN LA DOCUMENTACIÓN OFICIAL Y PROMPTS DE REFERENCIA

Incluye herramientas de browser para navegación web con screenshots.
"""

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext
from openhands.sdk.context import Skill

from config.rules import REGLAS_AGENTE, SYSTEM_PROMPT_COMPLETO, IN_CONTEXT_EXAMPLE


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
    
    # === CONTEXT CON TODOS LOS PROMPTS INTEGRADOS ===
    agent_context = AgentContext(
        skills=[
            # System prompt completo (basado en system_prompt.j2)
            Skill(
                name="system_prompt_completo",
                content=SYSTEM_PROMPT_COMPLETO,
                source=None,
                trigger=None,  # Siempre activo
            ),
            # Ejemplo de aprendizaje en contexto (basado en in_context_learning_example.j2)
            Skill(
                name="in_context_example",
                content=IN_CONTEXT_EXAMPLE,
                source=None,
                trigger=None,  # Siempre activo
            ),
            # Reglas de comportamiento personalizadas + idioma español
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
    
    # === CARGAR HERRAMIENTAS DE BROWSER ===
    browser_tools = []
    try:
        from core.browser import create_browser_tools
        browser_tools = create_browser_tools()
        print(f"  🌐 {len(browser_tools)} herramientas de browser cargadas")
    except Exception as e:
        print(f"  ⚠️ No se pudieron cargar herramientas de browser: {e}")
    
    # Crear agente con herramientas de browser
    agent = Agent(
        llm=llm,
        agent_context=agent_context,
        tools=browser_tools if browser_tools else None,
    )
    
    return agent
