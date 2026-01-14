"""
Configuración del agente OpenHands
Incluye herramienta bash para ejecutar comandos y browser CLI.
"""
import os

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill

# Importar y registrar la herramienta bash personalizada
from core.bash_tool import BashTool  # noqa: F401 - registra 'bash' automáticamente


# Directorio de la aplicación (para browser CLI)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Prompt compacto con instrucciones esenciales
AGENT_PROMPT = f"""
Eres un asistente de desarrollo. Responde SIEMPRE en ESPAÑOL.

## Herramientas disponibles:
- **bash**: Ejecuta comandos en terminal. Usa esto para TODAS las acciones.
- **think**: Para razonar sobre problemas complejos.
- **finish**: Para terminar la tarea con un mensaje.

## Browser CLI (navegación web):
Para navegar la web, usa bash con estos comandos:
- Navegar: `cd {APP_DIR} && python -m core.browser navigate "URL"`
- Estado: `cd {APP_DIR} && python -m core.browser state`
- Click: `cd {APP_DIR} && python -m core.browser click "selector"`
- Escribir: `cd {APP_DIR} && python -m core.browser type "selector" "texto"`
- Scroll: `cd {APP_DIR} && python -m core.browser scroll down`
- Contenido: `cd {APP_DIR} && python -m core.browser content`

Los screenshots se muestran automáticamente en la UI.

## Reglas importantes:
1. USA la herramienta bash para ejecutar comandos
2. NO termines la tarea sin hacer lo que se te pide
3. Si te piden navegar a una URL, EJECUTA el comando browser CLI
4. Muestra los resultados al usuario
"""


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None) -> Agent:
    """
    Crea y configura el agente OpenHands
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar (default: gemini/gemini-2.5-pro)
        base_url: URL base del LLM (opcional)
    
    Returns:
        Agent configurado con herramientas bash y browser
    """
    
    # Configurar LLM
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # Context con prompt simplificado
    agent_context = AgentContext(
        skills=[
            Skill(
                name="instrucciones_agente",
                content=AGENT_PROMPT,
                source=None,
                trigger=None,  # Siempre activo
            ),
        ],
        system_message_suffix=AGENT_PROMPT,
        load_public_skills=False,  # No cargar skills públicos para reducir tokens
    )
    
    # Crear agente con herramienta bash personalizada para ejecutar comandos
    agent = Agent(
        llm=llm,
        agent_context=agent_context,
        tools=[
            Tool(name="bash"),  # Herramienta bash personalizada (core/bash_tool.py)
        ],
    )
    
    return agent
