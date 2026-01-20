"""
Agente OpenHands - Sistema Inteligente con Memoria y Razonamiento

ARQUITECTURA:
- Memoria RAG: ChromaDB para recordar conversaciones pasadas
- Indexer: Analiza estructura del código
- Analyzer: Evalúa impacto de cambios
- Condenser: Resume conversaciones largas

El agente sigue un flujo de razonamiento estructurado como los mejores
asistentes de código (Devin, Cursor, GitHub Copilot).
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
# DETECTOR DE DOMINIO
# ============================================================

def detect_domain(message: str) -> str:
    """Detecta si el mensaje es técnico o general."""
    if not message:
        return "general"
    
    message_lower = message.lower()
    
    tech_keywords = [
        'código', 'code', 'función', 'function', 'variable', 'clase', 'class',
        'archivo', 'file', 'carpeta', 'folder', 'python', 'javascript', 'java',
        'html', 'css', 'sql', 'react', 'vue', 'angular', 'django', 'flask',
        'git', 'commit', 'push', 'pull', 'npm', 'pip', 'docker', 'deploy',
        'servidor', 'server', 'api', 'database', 'terminal', 'error', 'bug',
        'arregla', 'modifica', 'crea', 'elimina', 'botón', 'button', 'estilo'
    ]
    
    if any(kw in message_lower for kw in tech_keywords):
        return "technical"
    
    if re.search(r'\.[a-z]{2,4}$|[/\\]|\{|\}|import |def |class ', message_lower):
        return "technical"
    
    return "general"


# ============================================================
# SYSTEM PROMPTS - AGENTE INTELIGENTE
# ============================================================

def get_core_prompt() -> str:
    """CAPA 1: Core - Comportamiento inteligente base (~600 tokens)"""
    return """
<AGENT_CORE>
You are an intelligent AI coding assistant. Always respond in Spanish (Latin American).

## REASONING FRAMEWORK
Before acting, follow this mental process:

1. **UNDERSTAND** - What is the user really asking?
   - Read the full request carefully
   - Check <RELEVANT_MEMORY> for context from past conversations
   - Identify the core goal vs specific details

2. **PLAN** - How should I approach this?
   - For simple tasks: Act directly
   - For complex tasks: Break into steps
   - For unclear requests: Ask clarifying questions

3. **EXECUTE** - Carry out the plan
   - Use the right tools for each step
   - Be efficient - don't repeat unnecessary commands
   - If something fails, analyze why before retrying

4. **VERIFY** - Did it work?
   - Confirm changes were applied
   - Test if possible
   - Report results clearly to user

## MEMORY SYSTEM
- <RELEVANT_MEMORY> contains context from previous conversations (days/weeks ago)
- Use this to maintain continuity: "As we discussed before...", "Building on our previous work..."
- If the user references something from the past, check memory first

## COMMUNICATION STYLE
- Be concise but complete
- Show your reasoning when it helps the user understand
- Don't over-explain simple things
- Ask questions when truly needed, not for every little detail
- If you made a mistake, acknowledge it and fix it

## IMPORTANT BEHAVIORS
- NEVER make changes without understanding what exists first
- ALWAYS verify your changes worked
- When modifying code, understand the context before editing
- If a task is complex, use task_tracker to organize steps
- If you're unsure, say so honestly
</AGENT_CORE>
"""


def get_technical_context(workspace: str = None, repo_info: dict = None, 
                          external_url: str = None) -> str:
    """CAPA 2: Contexto técnico (~400 tokens)"""
    parts = []
    
    parts.append("""
<CODING_INTELLIGENCE>
## Code Understanding
Before modifying ANY code:
1. Understand what the code does currently
2. Identify dependencies and shared components
3. Consider side effects of changes

## Editing Strategy
- **Known location + simple change** → Edit directly
- **Unknown location** → Search first (grep, glob)
- **Shared code (classes used in multiple places)** → Analyze impact first
- **New feature** → Understand existing patterns before adding

## Quality Standards
- Write clean, readable code
- Follow existing code style in the project
- Minimal changes to achieve the goal
- Test changes when possible
</CODING_INTELLIGENCE>
""")
    
    if workspace:
        parts.append(f"""
<WORKSPACE>
Working directory: {workspace}
Tools available: terminal, file_editor, browser, git, grep, glob, task_tracker
</WORKSPACE>
""")
    
    if repo_info:
        repo_owner = repo_info.get('owner', '')
        repo_name = repo_info.get('name', '')
        branch = repo_info.get('branch', 'main')
        if repo_owner and repo_name:
            parts.append(f"""
<REPOSITORY>
GitHub: {repo_owner}/{repo_name}
Branch: {branch}
Use ${{GITHUB_TOKEN}} for git operations requiring authentication.
</REPOSITORY>
""")
    
    if external_url:
        parts.append(f"""
<APP_PREVIEW>
Application URL: {external_url}
Tell user to refresh browser after UI changes.
</APP_PREVIEW>
""")
    
    return "\n".join(parts)


def get_specialized_context(message: str) -> str:
    """CAPA 3: Contexto especializado según el tipo de tarea (~200 tokens)"""
    parts = []
    message_lower = message.lower()
    
    # CSS/UI changes
    if any(kw in message_lower for kw in ['css', 'estilo', 'style', 'color', 'diseño']):
        parts.append("""
<CSS_AWARENESS>
For CSS changes:
- If targeting a specific element (ID or unique class): edit directly
- If targeting a shared class (.btn, .card): check how many elements use it first
- Consider creating a specific selector if the shared class affects multiple unrelated elements
</CSS_AWARENESS>
""")
    
    # Git operations
    if any(kw in message_lower for kw in ['git', 'commit', 'push', 'pull', 'branch', 'pr']):
        parts.append("""
<GIT_OPERATIONS>
Git best practices:
- Never push directly to main/master unless explicitly asked
- Use descriptive commit messages
- Pull before making changes to avoid conflicts
- Add Co-authored-by: openhands <openhands@all-hands.dev> to commits
</GIT_OPERATIONS>
""")
    
    # Complex task
    if any(kw in message_lower for kw in ['crear', 'create', 'sistema', 'system', 'aplicación', 'proyecto']):
        parts.append("""
<COMPLEX_TASK>
For large/complex tasks:
- Use task_tracker to break down into steps
- Complete one step at a time
- Verify each step before moving to next
- Keep user informed of progress
</COMPLEX_TASK>
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
# CREAR AGENTE INTELIGENTE
# ============================================================

def create_agent(api_key: str, model: str = "deepseek/deepseek-chat", base_url: str = None,
                 workspace: str = None, repo_info: dict = None,
                 external_url: str = None, conversation_id: int = None,
                 tavily_api_key: str = None, github_token: str = None,
                 vision_api_key: str = None, vision_model: str = "gemini/gemini-2.0-flash",
                 user_message: str = None) -> Agent:
    """
    Crea un agente inteligente con:
    - Razonamiento estructurado
    - Memoria de conversaciones pasadas
    - Análisis de código antes de editar
    - Herramientas completas
    """

    # 1. LLM principal
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=0.7,
    )

    # 2. Condenser para conversaciones largas
    condenser = LLMSummarizingCondenser(
        llm=llm.model_copy(update={"usage_id": "condenser"}),
        max_size=20,   # Últimos 20 mensajes completos
        keep_first=3,  # Mantener contexto inicial
    )

    # 3. Detectar tipo de mensaje
    domain = detect_domain(user_message) if user_message else "technical"
    
    # 4. Construir system prompt
    suffix_parts = []
    
    # Core siempre
    suffix_parts.append(get_core_prompt())
    
    # Técnico si aplica
    if domain == "technical":
        suffix_parts.append(get_technical_context(workspace, repo_info, external_url))
        
        # Especializado si aplica
        if user_message:
            specialized = get_specialized_context(user_message)
            if specialized:
                suffix_parts.append(specialized)
    
    system_suffix = "\n".join(suffix_parts)

    # 5. Tools completas
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
                description="Analyze the impact of modifying a symbol (CSS class, function, variable). Shows how many files use it and potential side effects. Use before modifying shared code.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The symbol to analyze (e.g., '.btn-primary', 'myFunction', 'CONFIG_VAR')"},
                        "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search (e.g., ['css', 'html'])"}
                    },
                    "required": ["symbol"]
                },
                func=lambda symbol, file_types=None: analyzer.analyze_symbol_impact(symbol, file_types)
            )
            
            find_refs_tool = Tool(
                name="find_references", 
                description="Find all places where a symbol is used in the codebase. Useful for understanding how code is connected.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The symbol to find references for"},
                        "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"}
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
