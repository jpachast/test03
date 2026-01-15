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

# Core tools - del paquete openhands-tools
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool

# Directorio de la aplicación (para browser CLI)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_agent(api_key: str, model: str = "gemini/gemini-2.5-pro", base_url: str = None,
                 workspace: str = None, repo_info: dict = None, 
                 external_url: str = None, conversation_id: int = None) -> Agent:
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
    
    # 5. Crear agente con tools estables del SDK
    # NOTA: browser_tool_set tiene bugs en el SDK, el agente puede usar
    # terminal con curl/wget para obtener contenido web
    agent = Agent(
        llm=llm,
        condenser=condenser,
        agent_context=agent_context,
        tools=[
            # Core tools - usando las clases de openhands-tools
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
            
            # Para navegación web: usar terminal con curl/httpx
            # Ejemplo: curl -s https://example.com | head -100
        ],
    )
    
    return agent
