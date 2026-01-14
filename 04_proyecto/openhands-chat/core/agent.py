"""
Configuración del agente OpenHands
BASADO 100% EN LA DOCUMENTACIÓN OFICIAL Y PROMPTS DE REFERENCIA

El agente usa el CLI de browser para navegar (python -m core.browser).

IMPORTANTE: Los tools se importan de openhands.tools y se agregan usando Tool(name=X.name)
- TerminalTool.name = "terminal" (para ejecutar bash)
- FileEditorTool.name = "file_editor" (para editar archivos)
"""
import os

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context import Skill
from openhands.sdk.context.condenser import LLMSummarizingCondenser

# Importar las herramientas CORRECTAS del SDK
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool

from config.rules import REGLAS_AGENTE, SYSTEM_PROMPT_COMPLETO, IN_CONTEXT_EXAMPLE


def _create_agent_safe(llm, agent_context, condenser):
    """
    Crea el agente con las herramientas correctas.
    
    IMPORTANTE: Usar Tool(name=TerminalTool.name), NO Tool(name="TerminalTool")
    - TerminalTool.name = "terminal"
    - FileEditorTool.name = "file_editor"
    """
    return Agent(
        llm=llm,
        agent_context=agent_context,
        condenser=condenser,
        tools=[
            Tool(name=TerminalTool.name),      # "terminal" - ejecutar bash
            Tool(name=FileEditorTool.name),    # "file_editor" - editar archivos
        ],
    )


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


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None, 
                 workspace: str = None, repo_info: dict = None) -> Agent:
    """
    Crea y configura el agente OpenHands
    
    IMPORTANTE: Usa LLMSummarizingCondenser para manejar contextos largos,
    exactamente como lo hace OpenHands. Esto permite usar prompts completos
    sin reducirlos, resumiendo automáticamente el historial cuando es necesario.
    
    Args:
        api_key: API key del LLM
        model: Modelo a usar (default: gemini/gemini-2.5-pro)
        base_url: URL base del LLM (opcional)
        workspace: Directorio de trabajo (se agrega al prompt como en additional_info.j2)
        repo_info: Diccionario con info del repositorio GitHub (owner, name, branch)
    
    Returns:
        Agent configurado con TODAS las tools, reglas y condenser
    """
    
    # Configurar LLM principal para el agente
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # === CONDENSER: Manejo de contextos largos (como OpenHands) ===
    # El condenser resume automáticamente el historial cuando excede max_size
    # o max_tokens. Usa el mismo LLM para generar resúmenes.
    # Referencia: https://docs.openhands.dev/sdk/guides/context-condenser
    condenser = LLMSummarizingCondenser(
        llm=llm,  # Usa el mismo LLM para resumir
        max_size=240,  # Máximo de eventos antes de condensar
        max_tokens=None,  # Opcional: límite de tokens (None = sin límite)
        keep_first=2,  # Mantener primeros N eventos (system prompt, etc.)
    )
    
    # Combinar reglas con instrucciones de browser
    full_rules = REGLAS_AGENTE + "\n\n" + BROWSER_INSTRUCTIONS
    
    # === RUNTIME INFO (como additional_info.j2 de OpenHands) ===
    # OpenHands agrega el working directory en el prompt via additional_info.j2
    runtime_info = ""
    if workspace:
        runtime_info = f"""
<RUNTIME_INFORMATION>
The current working directory is {workspace}
</RUNTIME_INFORMATION>
"""
    
    # === REPO INFO (información del repositorio GitHub) ===
    if repo_info and repo_info.get('owner') and repo_info.get('name'):
        repo_owner = repo_info['owner']
        repo_name = repo_info['name']
        repo_branch = repo_info.get('branch', 'main')
        runtime_info += f"""
<REPOSITORY_INFORMATION>
GitHub Repository: {repo_owner}/{repo_name}
Branch: {repo_branch}
Clone URL: https://github.com/{repo_owner}/{repo_name}.git
Workspace: {workspace}

CRITICAL: When asked to pull/clone the repository, execute these commands IN ORDER:
1. First check if there's a .git directory IN the workspace: ls {workspace}/.git 2>/dev/null && echo "GIT_EXISTS" || echo "NO_GIT"
2. If NO_GIT: Clone with: rm -rf {workspace}/* {workspace}/.* 2>/dev/null; git clone https://github.com/{repo_owner}/{repo_name}.git {workspace} --branch {repo_branch}
3. If GIT_EXISTS: Check remote with: cd {workspace} && git remote get-url origin
4. If remote contains "{repo_name}": Do pull: cd {workspace} && git pull origin {repo_branch}
5. If remote does NOT contain "{repo_name}": Re-clone: rm -rf {workspace}; git clone https://github.com/{repo_owner}/{repo_name}.git {workspace} --branch {repo_branch}

IMPORTANT: Execute each command and check the output before proceeding to the next step.
</REPOSITORY_INFORMATION>
"""
    
    # === CONTEXT CON TODOS LOS PROMPTS INTEGRADOS ===
    # OpenHands usa prompts largos y completos, el condenser maneja
    # la reducción de contexto cuando es necesario.
    
    # Lista de skills - repo_info va PRIMERO para que no se trunque
    skills_list = []
    
    # Si hay repo info, agregarlo como skill prioritario
    if repo_info and repo_info.get('owner') and repo_info.get('name'):
        skills_list.append(Skill(
            name="repository_context",
            content=runtime_info,  # Contiene RUNTIME_INFORMATION + REPOSITORY_INFORMATION
            source=None,
            trigger=None,  # Siempre activo
        ))
    
    # System prompt (puede ser truncado si es muy largo)
    skills_list.append(Skill(
        name="system_prompt_completo",
        content=SYSTEM_PROMPT_COMPLETO,
        source=None,
        trigger=None,
    ))
    
    # Ejemplo de aprendizaje
    skills_list.append(Skill(
        name="in_context_example", 
        content=IN_CONTEXT_EXAMPLE,
        source=None,
        trigger=None,
    ))
    
    # Reglas de comportamiento
    skills_list.append(Skill(
        name="reglas_comportamiento",
        content=full_rules,
        source=None,
        trigger=None,
    ))
    
    agent_context = AgentContext(
        skills=skills_list,
        system_message_suffix=runtime_info,  # Solo runtime_info (más corto)
        load_public_skills=True,
    )
    
    # Crear agente usando función segura (NUNCA agregar tools= manualmente)
    agent = _create_agent_safe(llm, agent_context, condenser)
    
    return agent
