"""
Configuración del agente OpenHands
BASADO 100% EN LA DOCUMENTACIÓN OFICIAL Y PROMPTS DE REFERENCIA

Incluye herramientas de browser para navegación web con screenshots.
El agente usa el CLI de browser para navegar (python -m core.browser).
"""
import os

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill

from config.rules import REGLAS_AGENTE, SYSTEM_PROMPT_COMPLETO, IN_CONTEXT_EXAMPLE


# Directorio de la aplicación (para browser CLI)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BROWSER_INSTRUCTIONS = f"""
## HERRAMIENTAS DE NAVEGACIÓN WEB

Tienes acceso a un browser headless mediante comandos de terminal.
Para navegar en la web, usa estos comandos:

### Navegar a una URL:
```bash
cd {APP_DIR} && python -m core.browser navigate "https://www.google.com"
```

### Obtener estado actual (URL, título, elementos):
```bash
cd {APP_DIR} && python -m core.browser state
```

### Hacer clic en un elemento:
```bash
cd {APP_DIR} && python -m core.browser click "button.submit"
```

### Escribir en un campo:
```bash
cd {APP_DIR} && python -m core.browser type "input#search" "texto a buscar"
```

### Hacer scroll:
```bash
cd {APP_DIR} && python -m core.browser scroll down
```

### Obtener contenido de texto:
```bash
cd {APP_DIR} && python -m core.browser content
```

Los comandos retornan JSON con:
- success: true/false
- url: URL actual
- title: título de la página
- screenshot: imagen en base64 (se muestra automáticamente en la UI)
- elements: elementos interactivos (para state)
- content: texto de la página (para content)

IMPORTANTE: Los screenshots se muestran automáticamente en la pestaña "Navegador" de la UI.
"""


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
    
    # Combinar reglas con instrucciones de browser
    full_rules = REGLAS_AGENTE + "\n\n" + BROWSER_INSTRUCTIONS
    
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
            # Reglas de comportamiento personalizadas + idioma español + browser
            Skill(
                name="reglas_comportamiento",
                content=full_rules,
                source=None,
                trigger=None,  # Siempre activo
            ),
        ],
        system_message_suffix=full_rules,
        load_public_skills=True,
    )
    
    # Crear agente con herramientas de terminal para poder ejecutar browser CLI
    agent = Agent(
        llm=llm,
        agent_context=agent_context,
        tools=[
            Tool(name="TerminalTool"),     # Para ejecutar comandos bash (browser CLI)
            Tool(name="FileEditorTool"),   # Para editar archivos
        ],
    )
    
    return agent
