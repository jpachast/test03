"""
Agente OpenHands - Optimizado para eficiencia de tokens

ARQUITECTURA DE CAPAS:
- CAPA 1: Core Universal (siempre) ~300 tokens
- CAPA 2: Contexto Técnico (solo si aplica) ~500 tokens  
- CAPA 3: Especializado (solo si aplica) ~200 tokens

Detecta el dominio del mensaje (técnico vs general) y envía SOLO
el contexto necesario. Igual capacidad, menos tokens desperdiciados.
"""
import os
import re
import logging

os.environ.setdefault("TIMEOUT_BrowserStartEvent", "120.0")
os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", "120.0")
os.environ.setdefault("TIMEOUT_BrowserConnectedEvent", "120.0")
os.environ.setdefault("TIMEOUT_NavigateToUrlEvent", "60.0")

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext
from openhands.sdk.tool import Tool
from openhands.sdk.context.condenser import LLMSummarizingCondenser
from openhands.sdk.mcp import create_mcp_tools

from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.browser_use import BrowserToolSet
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool
from openhands.tools.delegate import DelegateTool

from .indexer import CodeIndexer, set_indexer
from .analyzer import CodeAnalyzer

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)


# ============================================================
# DETECTOR DE DOMINIO - Técnico vs General
# ============================================================

def detect_domain(message: str) -> str:
    """
    Detecta si el mensaje es técnico/código o general.
    
    Returns:
        "technical" - Para código, desarrollo, sistemas
        "general" - Para cualquier otra cosa (vida, consejos, etc.)
    """
    if not message:
        return "general"
    
    message_lower = message.lower()
    
    # Keywords técnicos
    tech_keywords = [
        # Acciones de código
        'código', 'code', 'función', 'function', 'variable', 'clase', 'class',
        'método', 'method', 'archivo', 'file', 'carpeta', 'folder', 'directorio',
        # Lenguajes
        'python', 'javascript', 'typescript', 'java', 'c#', 'csharp', '.net',
        'dotnet', 'php', 'ruby', 'go', 'rust', 'html', 'css', 'sql',
        # Frameworks
        'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring',
        'node', 'express', 'laravel', 'blazor', 'asp.net',
        # Herramientas
        'git', 'commit', 'push', 'pull', 'branch', 'merge', 'npm', 'pip',
        'docker', 'kubernetes', 'deploy', 'servidor', 'server', 'api',
        'database', 'base de datos', 'terminal', 'consola', 'comando',
        # Acciones técnicas
        'instalar', 'install', 'ejecutar', 'run', 'compilar', 'build',
        'debugg', 'error', 'bug', 'fix', 'arregla', 'modifica', 'crea',
        'elimina', 'borra', 'actualiza', 'refactoriza',
        # UI/Frontend
        'botón', 'button', 'formulario', 'form', 'estilo', 'style',
        'componente', 'component', 'página', 'page', 'vista', 'view',
    ]
    
    # Si contiene keywords técnicos
    for kw in tech_keywords:
        if kw in message_lower:
            return "technical"
    
    # Patrones técnicos (rutas, extensiones, etc.)
    tech_patterns = [
        r'\.[a-z]{2,4}$',  # extensiones como .py, .js, .html
        r'[/\\]',  # rutas de archivos
        r'\{|\}|\[|\]',  # código
        r'import |from |def |class |function',  # código
        r'<[a-z]+>|</[a-z]+>',  # HTML tags
    ]
    
    for pattern in tech_patterns:
        if re.search(pattern, message_lower):
            return "technical"
    
    return "general"


# ============================================================
# CAPAS DEL SYSTEM PROMPT
# ============================================================

def get_core_prompt() -> str:
    """CAPA 1: Core Universal - Siempre se envía (~400 tokens)"""
    return """
<CORE>
IMPORTANT: Always respond in Spanish (Latin American).

WORKFLOW - Follow this order:
1. UNDERSTAND: Read the request carefully. If there's RELEVANT_MEMORY, use it.
2. THINK: What's being asked? What files/code are involved?
3. ACT: Execute the minimal steps needed.
4. VERIFY: Confirm the change was applied correctly.

MEMORY: If you see <RELEVANT_MEMORY>, that's context from previous conversations.
Use it to maintain continuity (e.g., "last week we worked on X").

STYLE:
- Be concise and direct
- Don't repeat unnecessary explanations
- If unsure, ask clarifying questions
</CORE>
"""


def get_technical_context(workspace: str = None, repo_info: dict = None, 
                          external_url: str = None) -> str:
    """CAPA 2: Contexto Técnico - Solo para mensajes técnicos (~500 tokens)"""
    parts = []
    
    # Información del workspace
    if workspace:
        parts.append(f"""
<WORKSPACE>
Working directory: {workspace}
You have access to: terminal, file_editor, browser, git tools.
</WORKSPACE>
""")
    
    # Información del repositorio
    if repo_info:
        repo_owner = repo_info.get('owner', '')
        repo_name = repo_info.get('name', '')
        branch = repo_info.get('branch', 'main')
        if repo_owner and repo_name:
            parts.append(f"""
<REPOSITORY>
GitHub: {repo_owner}/{repo_name}
Branch: {branch}
</REPOSITORY>
""")
    
    # URL de preview
    if external_url:
        parts.append(f"""
<APP_URL>
Application preview: {external_url}
</APP_URL>
""")
    
    # Reglas básicas de código
    parts.append("""
<CODE_RULES>
BEFORE EDITING:
- Understand what exists before changing it
- For complex changes: explore the codebase first (ls, cat, grep)
- For simple changes to known files: edit directly

WHEN EDITING:
- Write clean, efficient code
- Make minimal changes to solve the problem
- Don't modify more than requested
- Shared code (generic classes): check impact with grep -c first
- Specific code (IDs, unique names): edit directly

AFTER EDITING:
- Verify the change was applied (cat or grep the result)
- If it's a UI change, tell user to refresh
</CODE_RULES>
""")
    
    return "\n".join(parts)


def get_specialized_context(message: str) -> str:
    """CAPA 3: Contexto Especializado - Solo cuando aplica (~200 tokens)"""
    parts = []
    message_lower = message.lower()
    
    # Si menciona CSS/estilos con clases genéricas
    if any(kw in message_lower for kw in ['css', 'estilo', 'style', 'color', 'clase', '.btn', '.card']):
        if '.' in message and '#' not in message:  # Clase genérica, no ID
            parts.append("""
<CSS_IMPACT>
For generic CSS classes (.btn, .card, etc.): run grep -c first to check usage count.
If 2+ uses: ask user or create specific ID/class.
For IDs (#specific): edit directly.
</CSS_IMPACT>
""")
    
    # Si menciona git/deploy
    if any(kw in message_lower for kw in ['git', 'commit', 'push', 'pull', 'deploy', 'pr', 'merge']):
        parts.append("""
<GIT_RULES>
- Never push to main/master directly unless asked
- Use descriptive commit messages
- Add Co-authored-by: openhands <openhands@all-hands.dev>
</GIT_RULES>
""")
    
    return "\n".join(parts)


# ============================================================
# MCP TOOLS
# ============================================================

def get_mcp_tools(tavily_api_key: str = None, github_token: str = None) -> list:
    """Crea MCP tools si las API keys están disponibles."""
    mcp_tools = []

    if tavily_api_key:
        try:
            tavily_config = {
                "mcpServers": {
                    "tavily": {
                        "command": "npx",
                        "args": ["-y", "@tavily/mcp-server"],
                        "env": {"TAVILY_API_KEY": tavily_api_key}
                    }
                }
            }
            tavily_tools = create_mcp_tools(tavily_config, timeout=30.0)
            mcp_tools.extend(tavily_tools)
        except Exception as e:
            logger.warning(f"Failed to load Tavily MCP: {e}")

    if github_token:
        try:
            github_config = {
                "mcpServers": {
                    "github": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-github"],
                        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token}
                    }
                }
            }
            github_tools = create_mcp_tools(github_config, timeout=30.0)
            mcp_tools.extend(github_tools)
        except Exception as e:
            logger.warning(f"Failed to load GitHub MCP: {e}")

    return mcp_tools


# ============================================================
# CREAR AGENTE
# ============================================================

def create_agent(api_key: str, model: str = "deepseek/deepseek-chat", base_url: str = None,
                 workspace: str = None, repo_info: dict = None,
                 external_url: str = None, conversation_id: int = None,
                 tavily_api_key: str = None, github_token: str = None,
                 vision_api_key: str = None, vision_model: str = "gemini/gemini-2.0-flash",
                 user_message: str = None) -> Agent:
    """
    Crea el agente OpenHands con contexto optimizado.
    
    Detecta el dominio del mensaje y envía SOLO el contexto necesario:
    - General: ~300 tokens (core)
    - Técnico: ~800-1000 tokens (core + técnico + especializado)
    """

    # 1. LLM principal
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=0.7,
    )

    # 2. Condenser optimizado (15 mensajes en vez de 80)
    condenser = LLMSummarizingCondenser(
        llm=llm.model_copy(update={"usage_id": "condenser"}),
        max_size=15,   # Optimizado: 15 (antes 80)
        keep_first=3,  # Mantener contexto inicial
    )

    # 3. Detectar dominio del mensaje
    domain = detect_domain(user_message) if user_message else "technical"
    
    # 4. Construir system prompt por capas
    suffix_parts = []
    
    # CAPA 1: Core Universal (siempre)
    suffix_parts.append(get_core_prompt())
    
    # CAPA 2: Contexto Técnico (solo si es técnico)
    if domain == "technical":
        suffix_parts.append(get_technical_context(workspace, repo_info, external_url))
        
        # CAPA 3: Especializado (solo si aplica)
        if user_message:
            specialized = get_specialized_context(user_message)
            if specialized:
                suffix_parts.append(specialized)
    
    system_suffix = "\n".join(suffix_parts)

    # 5. Tools
    tools = [
        TerminalTool(),
        FileEditorTool(),
        TaskTrackerTool(),
        GlobTool(),
        GrepTool(),
        DelegateTool(),
    ]
    
    # Browser tools
    try:
        browser_toolset = BrowserToolSet()
        tools.extend(browser_toolset.get_tools())
    except Exception as e:
        logger.warning(f"Browser tools not available: {e}")
    
    # MCP tools
    mcp_tools = get_mcp_tools(tavily_api_key, github_token)
    tools.extend(mcp_tools)
    
    # Analysis tools
    try:
        if workspace:
            indexer = CodeIndexer(workspace)
            set_indexer(indexer)
            analyzer = CodeAnalyzer(workspace, indexer)
            
            analyze_tool = Tool(
                name="analyze_impact",
                description="Analyze the impact of modifying a CSS selector, function, or variable. Use BEFORE modifying shared code.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The symbol to analyze (e.g., '.btn-primary', 'myFunction')"},
                        "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"}
                    },
                    "required": ["symbol"]
                },
                func=lambda symbol, file_types=None: analyzer.analyze_symbol_impact(symbol, file_types)
            )
            
            find_refs_tool = Tool(
                name="find_references",
                description="Find all references to a symbol in the codebase.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The symbol to find"},
                        "file_types": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["symbol"]
                },
                func=lambda symbol, file_types=None: analyzer.find_all_references(symbol, file_types)
            )
            
            tools.extend([analyze_tool, find_refs_tool])
    except Exception as e:
        logger.warning(f"Analysis tools not available: {e}")

    # 6. Context
    agent_context = AgentContext(
        system_message_suffix=system_suffix,
        condenser=condenser,
    )

    # 7. Crear agente
    agent = Agent(
        llm=llm,
        tools=tools,
        agent_context=agent_context,
    )

    return agent
