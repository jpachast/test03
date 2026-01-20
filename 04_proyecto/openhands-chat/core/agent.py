"""
Agente OpenHands - Con análisis de impacto inteligente

Usa los prompts oficiales de OpenHands + herramientas de análisis.
Incluye TODAS las tools oficiales del SDK:
- terminal, file_editor, task_tracker
- browser tools (11 herramientas)
- glob, grep, delegate
- MCP tools (Tavily, GitHub) si están configurados
- analyze_impact, find_references (NUEVAS - análisis antes de editar)

El agente DEBE usar analyze_impact ANTES de modificar código compartido.

Referencia: https://docs.openhands.dev/sdk/getting-started
"""
import os
import logging

# Configurar timeouts de browser-use para contenedores (antes de importar)
# Estos valores aumentan los timeouts default de 30s a 120s
os.environ.setdefault("TIMEOUT_BrowserStartEvent", "120.0")
os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", "120.0")
os.environ.setdefault("TIMEOUT_BrowserConnectedEvent", "120.0")
os.environ.setdefault("TIMEOUT_NavigateToUrlEvent", "60.0")

from pydantic import SecretStr
from openhands.sdk import LLM, Agent, AgentContext
from openhands.sdk.tool import Tool
from openhands.sdk.context.condenser import LLMSummarizingCondenser
from openhands.sdk.mcp import create_mcp_tools

# Core tools - del paquete openhands-tools
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool

# Browser tools - como OpenHands oficial
from openhands.tools.browser_use import BrowserToolSet

# Search tools - como OpenHands oficial
from openhands.tools.glob import GlobTool
from openhands.tools.grep import GrepTool

# Delegate tool - para sub-agentes
from openhands.tools.delegate import DelegateTool

# Analysis tools - NUEVO: análisis de impacto antes de editar
from .indexer import CodeIndexer, set_indexer
from .analyzer import CodeAnalyzer

# Directorio de la aplicación
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


def get_mcp_tools(tavily_api_key: str = None, github_token: str = None) -> list:
    """
    Crea MCP tools si las API keys están disponibles.
    Igual que OpenHands Cloud.
    """
    mcp_tools = []
    
    # Tavily MCP - búsquedas web en tiempo real
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
            logger.info(f"Tavily MCP tools loaded: {[t.name for t in tavily_tools]}")
        except Exception as e:
            logger.warning(f"Failed to load Tavily MCP tools: {e}")
    
    # GitHub MCP - operaciones con GitHub API
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
            logger.info(f"GitHub MCP tools loaded: {[t.name for t in github_tools]}")
        except Exception as e:
            logger.warning(f"Failed to load GitHub MCP tools: {e}")
    
    return mcp_tools


def create_agent(api_key: str, model: str = "deepseek/deepseek-chat", base_url: str = None,
                 workspace: str = None, repo_info: dict = None, 
                 external_url: str = None, conversation_id: int = None,
                 tavily_api_key: str = None, github_token: str = None,
                 vision_api_key: str = None, vision_model: str = "gemini/gemini-2.0-flash") -> Agent:
    """
    Crea el agente OpenHands usando la configuración oficial del SDK.
    
    Modelo híbrido:
    - DeepSeek V3 para código (api_key)
    - Gemini Flash para visión (vision_api_key)
    
    El agente usa los prompts oficiales en inglés (mejor rendimiento),
    pero responde en español según la instrucción en system_message_suffix.
    """
    
    # 1. Configurar LLM principal (DeepSeek para código)
    llm = LLM(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=0.7,  # Respuestas más determinísticas
    )
    
    # 2. Condenser para contextos largos - IGUAL QUE OPENHANDS OFICIAL
    condenser = LLMSummarizingCondenser(
        llm=llm.model_copy(update={"usage_id": "condenser"}),
        max_size=80,   # Oficial: 80
        keep_first=4,  # Oficial: 4
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

    # 3.1a ANÁLISIS DE IMPACTO OBLIGATORIO - Understand Before Modify
    suffix_parts.append("""
<SMART_EDITING>
## Best Practice: Analyze Only When There's Risk

### DECISION TREE:
```
Is the selector SPECIFIC (ID or unique class)?
├── YES (#my-button, .unique-component)
│   └── EDIT DIRECTLY - Safe, only affects one element
│
└── NO (generic: .btn, .card, .text-muted)
    └── QUICK CHECK: grep -c "selector" to count
        ├── 1 occurrence → EDIT DIRECTLY
        └── 2+ occurrences → Ask user or create specific ID
```

### Examples:
1. "Change #btn-limpiar to yellow" → DIRECT (ID = unique)
2. "Change .tool-btn color" → CHECK first, then ask if multiple
3. Already edited in this conversation → DIRECT (you know the location)

### EFFICIENCY:
- Maximum 1 grep for impact check
- Never view a file you just edited
- Never grep twice for the same thing
- Go direct when safe, check when risky
</SMART_EDITING>
""")

    # 3.1b CAMBIOS CONSERVADORES - No modificar más de lo pedido
    suffix_parts.append("""
<CONSERVATIVE_CHANGES>
CRITICAL: Make ONLY the changes the user explicitly requests. Do NOT:
- Modify multiple files when the user asks about one specific element
- Change ALL instances of something when user asks about ONE specific instance
- Add extra features or modifications not requested
- Refactor code unless explicitly asked

If there are multiple instances of something (like a button name appearing in several places),
ASK the user which specific instance they want to modify.

Example:
- User asks: "make the Limpiar button text bold"
- BAD: Change ALL "Limpiar" text in the entire project
- GOOD: Ask "I found 'Limpiar' in 3 places. Which one should I modify?" OR 
        modify only the ONE button you discussed previously in the conversation

ALWAYS follow the conversation context. If you were just modifying a specific file,
continue working on that same file unless told otherwise.
</CONSERVATIVE_CHANGES>
""")

    # 3.1b INTERPRETAR SELECCIONES NUMÉRICAS
    suffix_parts.append("""
<NUMBERED_SELECTIONS>
IMPORTANT: When you present the user with numbered options like:
1. Option A
2. Option B  
3. Option C

And the user responds with just a number (e.g., "2", "opción 2", "la 2", "segunda"),
IMMEDIATELY understand they are selecting that option and EXECUTE the corresponding action.

Do NOT ask again or present new options. Just do what the selected option says.

Example:
- You asked: "Which button? 1. Modal  2. Toolbar  3. Terminal"
- User responds: "2"
- You MUST immediately modify the Toolbar button, not ask more questions.
</NUMBERED_SELECTIONS>
""")

    # 3.1b APP PREVIEW URL - URL externa para ver la aplicación
    if external_url and conversation_id:
        app_preview_url = f"{external_url}/api/app-server/app-preview/?conversation_id={conversation_id}"
        suffix_parts.append(f"""
<APP_PREVIEW_URL>
When the user asks for the URL to view the application, provide this URL:
{app_preview_url}

This is the external URL where the user can see any web application you start.
When you start a web server (npm start, python -m http.server, etc.), 
tell the user they can view it at: {app_preview_url}
</APP_PREVIEW_URL>
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
        
        # Para test03, el repo ya está montado - NO clonar
        if "test03" in repo_name.lower():
            suffix_parts.append(f"""
<REPOSITORY_INFORMATION>
GitHub Repository: {repo_owner}/{repo_name}
Branch: {repo_branch}
Workspace: {workspace}

IMPORTANT: This repository is ALREADY available at {workspace}. Do NOT clone it.
The repository is pre-mounted and ready to use. You can directly read and modify files.

When asked to pull updates:
1. cd {workspace} && git pull origin {repo_branch}
</REPOSITORY_INFORMATION>
""")
        else:
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
    
    # 3.4 ENVIRONMENT_SETUP - Exactamente como OpenHands oficial
    suffix_parts.append("""
<ENVIRONMENT_SETUP>
* When user asks you to run an application, don't stop if the application is not installed. Instead, please install the application and run the command again.
* If you encounter missing dependencies:
  1. First, look around in the repository for existing dependency files (requirements.txt, pyproject.toml, package.json, Gemfile, etc.)
  2. If dependency files exist, use them to install all dependencies at once (e.g., `pip install -r requirements.txt`, `npm install`, etc.)
  3. Only install individual packages directly if no dependency files are found or if only specific packages are needed
* Similarly, if you encounter missing dependencies for essential tools requested by the user, install them when possible.

## Server Management (IMPORTANT):
* Before starting ANY web server (node, python http.server, npm start, etc.), ALWAYS kill existing processes on the same port:
  - For Node.js: pkill -f "node server" || true
  - For Python: pkill -f "python.*http.server" || true  
  - For specific port: fuser -k 3000/tcp 2>/dev/null || true
* When cleaning a directory to start fresh, also kill any running servers from that project.
* Use these common ports: 3000 (Node), 5000 (Flask), 8000 (Python http.server), 8080 (general)
* Always use CDN links for external libraries (Bootstrap, jQuery, etc.) instead of local paths.
* IMPORTANT: Always start servers with nohup to keep them running:
  - Node.js: nohup node server.js > server.log 2>&1 &
  - Python: nohup python -m http.server 8000 > server.log 2>&1 &
  - npm: nohup npm start > server.log 2>&1 &

## Available base tools:
- Python 3.12+ with pip, pipenv, poetry
- Node.js 22+ with npm, yarn, corepack
- git, curl, wget

## On-demand installation examples:
- .NET/Blazor: curl -sSL https://dot.net/v1/dotnet-install.sh | bash -s -- --channel 8.0 --install-dir $HOME/.dotnet && export PATH="$HOME/.dotnet:$PATH" && export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
- Ruby: apt-get update && apt-get install -y ruby-full
- Go: wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz && export PATH=$PATH:/usr/local/go/bin
</ENVIRONMENT_SETUP>
""")
    

    
    # 3.5 FILE_SYSTEM_GUIDELINES - Exactamente como OpenHands oficial
    suffix_parts.append("""
<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
* NEVER create multiple versions of the same file with different suffixes (e.g., file_test.py, file_fix.py, file_simple.py). Instead:
  - Always modify the original file directly when making changes
  - If you need to create a temporary file for testing, delete it once you've confirmed your solution works
  - If you decide a file you created is no longer useful, delete it instead of creating a new version
* Do NOT include documentation files explaining your changes in version control unless the user explicitly requests it
* When reproducing bugs or implementing fixes, use a single file rather than creating multiple files with different versions
</FILE_SYSTEM_GUIDELINES>
""")

    # 3.6 CODE_QUALITY - Exactamente como OpenHands oficial
    suffix_parts.append("""
<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments: Do not repeat information that can be easily inferred from the code itself.
* When implementing solutions, focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
* If you are adding a lot of code to a function or file, consider splitting the function or file into smaller pieces when appropriate.
* Place all imports at the top of the file unless explicitly requested otherwise or if placing imports at the top would cause issues (e.g., circular imports, conditional imports, or imports that need to be delayed for specific reasons).
</CODE_QUALITY>
""")

    # 3.7 TROUBLESHOOTING - Exactamente como OpenHands oficial
    suffix_parts.append("""
<TROUBLESHOOTING>
* If you've made repeated attempts to solve a problem but tests still fail or the user reports it's still broken:
  1. Step back and reflect on 5-7 different possible sources of the problem
  2. Assess the likelihood of each possible cause
  3. Methodically address the most likely causes, starting with the highest probability
  4. Explain your reasoning process in your response to the user
* When you run into any major issue while executing a plan from the user, please don't try to directly work around it. Instead, propose a new plan and confirm with the user before proceeding.
</TROUBLESHOOTING>
""")
    
    system_suffix = "\n".join(suffix_parts)
    
    # 4. AgentContext - Solo agrega contexto, NO reemplaza prompts oficiales
    agent_context = AgentContext(
        system_message_suffix=system_suffix,
        load_public_skills=True,  # Carga skills públicos de OpenHands
    )
    
    # 5. Tools base del SDK - IGUAL QUE OPENHANDS OFICIAL
    # Configuración para browser en contenedor (sin display)
    # Parámetros que van a BrowserToolExecutor y luego a BrowserProfile
    browser_config = {
        "headless": True,
        "init_timeout_seconds": 120,  # Más tiempo para inicializar en contenedor
        "session_timeout_minutes": 30,
        # Estos parámetros van directo a BrowserProfile via **config
        "executable_path": "/usr/bin/chromium",  # Ruta explícita al binario
        "keep_alive": True,  # Mantener browser vivo entre operaciones
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-setuid-sandbox",
            "--headless=new",  # Nuevo modo headless (más estable)
        ],
        "chromium_sandbox": False,  # Desactivar sandbox en contenedor
        "disable_security": True,   # Permite más flexibilidad en contenedor
    }
    
    tools = [
        # Core tools - IGUAL QUE OFICIAL
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        
        # Browser tools - Con configuración para contenedores
        Tool(name=BrowserToolSet.name, params=browser_config),
        
        # Search tools - IGUAL QUE OPENHANDS CLOUD
        Tool(name=GlobTool.name),
        Tool(name=GrepTool.name),
        
        # Delegate tool - para sub-agentes
        Tool(name=DelegateTool.name),
    ]
    
    # 6. MCP Tools (Tavily, GitHub) - si están configurados
    mcp_tools = get_mcp_tools(
        tavily_api_key=tavily_api_key,
        github_token=github_token
    )
    
    # 7. Crear agente con todas las tools
    agent = Agent(
        llm=llm,
        condenser=condenser,
        agent_context=agent_context,
        tools=tools,
        mcp_tools=mcp_tools if mcp_tools else None,
    )
    
    return agent
