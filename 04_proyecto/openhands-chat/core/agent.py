"""
Agente OpenHands - 100% IDÉNTICO AL SDK OFICIAL

Usa los prompts oficiales de OpenHands SIN modificaciones.
Incluye TODAS las tools oficiales del SDK:
- terminal, file_editor, task_tracker
- browser tools (10 herramientas)
- glob, grep, delegate

Referencia: https://docs.openhands.dev/sdk/getting-started
"""
import os

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext, Tool
from openhands.sdk.context.condenser import LLMSummarizingCondenser

# Core tools
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool

# Search tools
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool

# Delegate tool (sub-agents)
from openhands.tools.delegate import DelegateTool

# Browser tools (10 herramientas nativas)
from openhands.tools.browser_use import (
    BrowserNavigateTool,
    BrowserClickTool,
    BrowserTypeTool,
    BrowserScrollTool,
    BrowserGetStateTool,
    BrowserGetContentTool,
    BrowserGoBackTool,
    BrowserListTabsTool,
    BrowserSwitchTabTool,
    BrowserCloseTabTool,
)

# Directorio de la aplicación (para browser CLI)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None,
                 workspace: str = None, repo_info: dict = None) -> Agent:
    """
    Crea el agente OpenHands usando la configuración oficial del SDK.
    
    El agente usa los prompts oficiales en inglés (mejor rendimiento),
    pero responde en español según la instrucción en system_message_suffix.
    """
    
    # 1. Configurar LLM
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    # 2. Condenser para contextos largos (igual que OpenHands)
    condenser = LLMSummarizingCondenser(
        llm=llm,
        max_size=240,
        keep_first=2,
    )
    
    # 3. Construir el suffix con contexto adicional
    suffix_parts = []
    
    # 3.1 IDIOMA - Instrucción para responder en español
    suffix_parts.append("""
<LANGUAGE>
IMPORTANT: Always respond in Spanish (Latin American). 
All messages to the user must be in Spanish.
Code comments can be in English if the project requires it.
</LANGUAGE>
""")
    
    # 3.2 RUNTIME INFO - Working directory
    if workspace:
        suffix_parts.append(f"""
<RUNTIME_INFORMATION>
Your current working directory is: {workspace}
</RUNTIME_INFORMATION>
""")
    
    # 3.3 REPO INFO - Información del repositorio GitHub
    if repo_info and repo_info.get('owner') and repo_info.get('name'):
        repo_owner = repo_info['owner']
        repo_name = repo_info['name']
        repo_branch = repo_info.get('branch', 'main')
        suffix_parts.append(f"""
<REPOSITORY_INFORMATION>
GitHub Repository: {repo_owner}/{repo_name}
Branch: {repo_branch}
Clone URL: https://github.com/{repo_owner}/{repo_name}.git
Workspace: {workspace}

When asked to pull/clone the repository:
1. Check if .git exists: ls {workspace}/.git 2>/dev/null && echo "GIT_EXISTS" || echo "NO_GIT"
2. If NO_GIT: git clone https://github.com/{repo_owner}/{repo_name}.git {workspace} --branch {repo_branch}
3. If GIT_EXISTS: cd {workspace} && git pull origin {repo_branch}
</REPOSITORY_INFORMATION>
""")
    
    # 3.4 BROWSER - Ahora usa las tools nativas del SDK
    # Ya no necesita CLI manual, el SDK provee browser_navigate, browser_click, etc.
    
    system_suffix = "\n".join(suffix_parts)
    
    # 4. AgentContext - Solo agrega contexto, NO reemplaza prompts oficiales
    agent_context = AgentContext(
        system_message_suffix=system_suffix,
        load_public_skills=True,  # Carga skills públicos de OpenHands
    )
    
    # 5. Crear agente con TODAS las tools oficiales del SDK
    agent = Agent(
        llm=llm,
        condenser=condenser,
        agent_context=agent_context,
        tools=[
            # Core tools
            Tool(name=TerminalTool.name),        # "terminal"
            Tool(name=FileEditorTool.name),      # "file_editor"
            Tool(name=TaskTrackerTool.name),     # "task_tracker"
            
            # Search tools
            Tool(name=GlobTool.name),            # "glob"
            Tool(name=GrepTool.name),            # "grep"
            
            # Delegate (sub-agents)
            Tool(name=DelegateTool.name),        # "delegate"
            
            # Browser tools (10 herramientas nativas)
            Tool(name=BrowserNavigateTool.name),    # "browser_navigate"
            Tool(name=BrowserClickTool.name),       # "browser_click"
            Tool(name=BrowserTypeTool.name),        # "browser_type"
            Tool(name=BrowserScrollTool.name),      # "browser_scroll"
            Tool(name=BrowserGetStateTool.name),    # "browser_get_state"
            Tool(name=BrowserGetContentTool.name),  # "browser_get_content"
            Tool(name=BrowserGoBackTool.name),      # "browser_go_back"
            Tool(name=BrowserListTabsTool.name),    # "browser_list_tabs"
            Tool(name=BrowserSwitchTabTool.name),   # "browser_switch_tab"
            Tool(name=BrowserCloseTabTool.name),    # "browser_close_tab"
        ],
    )
    
    return agent
