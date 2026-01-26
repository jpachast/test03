"""
Rutas de chat con el agente - 100% compatible con OpenHands SDK

Maneja TODOS los tipos de eventos y observations del SDK:
- ActionEvent, ObservationEvent, MessageEvent, TokenEvent
- TaskTracker, Browser, Terminal, FileEditor observations
- Think action display
"""
import os
import json
import queue
import asyncio
import threading
import time
from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from openhands.sdk import Conversation, ImageContent, TextContent, Message, LLMStreamChunk

# Import observations para type checking (del paquete openhands-tools)
try:
    from openhands.tools.task_tracker import TaskTrackerObservation
    from openhands.tools.browser_use import BrowserObservation
except ImportError:
    # Fallback si no están disponibles
    TaskTrackerObservation = None
    BrowserObservation = None

from config.database import Database
from config.settings import Settings
from core.agent import create_agent
from ui.routers.browser import update_screenshot
from core.memory import (
    save_file_change, save_command, save_agent_action,
    get_context_for_message, get_memory_stats
)
# Preprocesador de mensajes - análisis de impacto OBLIGATORIO
from core.message_preprocessor import analyze_and_enrich_message
from core.smart_chat import (
    process_message as smart_process_message,
    create_checkpoint, get_suggestions, detect_intention,
    pin_file, unpin_file, get_pinned_files, get_pinned_content,
    auto_detect_important_files
)

import re as re_module

def clean_ansi(text):
    """Elimina códigos de escape ANSI y secuencias de terminal"""
    if not text:
        return ""
    # Códigos ANSI estándar
    text = re_module.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    # Secuencias de terminal como [?2004l, [?2004h
    text = re_module.sub(r'\[\?[0-9]+[a-z]', '', text)
    # Secuencias @[?...
    text = re_module.sub(r'@\[\?[0-9]+[a-z]:?', '', text)
    # Caracteres de control
    text = re_module.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()


router = APIRouter(prefix="/api/chat", tags=["chat"])
db = Database()
settings = Settings()

# Estado global
current_conversation = None
current_workspace = None
last_agent_response = ""
last_error_message = ""  # Para mostrar errores de API al usuario
current_conversation_id = None  # Para asociar screenshots con la conversación
# Almacena la referencia a la Conversation activa para poder pausarla
active_sdk_conversations = {}  # {conversation_id: Conversation}

# OPTIMIZACIÓN: Cache de agentes por (model, workspace, repo_key)
# Evita recrear el agente en cada mensaje de la misma conversación
_agent_cache = {}  # {cache_key: (agent, timestamp)}
_AGENT_CACHE_TTL = 300  # 5 minutos de vida


def create_token_callback(q):
    """
    Crea callback para streaming de tokens - Compatible con múltiples formatos
    """
    token_count = [0]
    tokens_sent = [0]
    
    def token_callback(chunk):
        try:
            token_count[0] += 1
            content = None
            
            # Formato 1: choices[0].delta.content (OpenAI/Anthropic streaming)
            if hasattr(chunk, 'choices') and chunk.choices:
                try:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        content = getattr(choice.delta, 'content', None)
                    elif hasattr(choice, 'message') and choice.message:
                        content = getattr(choice.message, 'content', None)
                except (IndexError, AttributeError):
                    pass
            
            # Formato 2: content directo
            if not content and hasattr(chunk, 'content'):
                content = chunk.content
            
            # Formato 3: text directo
            if not content and hasattr(chunk, 'text'):
                content = chunk.text
                
            # Formato 4: String
            if not content and isinstance(chunk, str):
                content = chunk
            
            # Formato 5: ModelResponseStream - acceso directo al delta
            if not content:
                try:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = getattr(chunk.choices[0], 'delta', None)
                        if delta:
                            content = getattr(delta, 'content', None) or \
                                     getattr(delta, 'text', None) or \
                                     getattr(delta, 'message', None)
                except:
                    pass
            
            if content and isinstance(content, str) and len(content) > 0:
                tokens_sent[0] += 1
                # Log TODOS los tokens enviados
                print(f"[TOKEN->SSE #{tokens_sent[0]}] Enviando: '{content[:20]}...'")
                q.put({"type": "token", "content": content})
                    
        except Exception as e:
            print(f"[TOKEN ERROR #{token_count[0]}] {e}")
    
    return token_callback


def _get_cached_agent(api_key: str, model: str, workspace: str, repo_info: dict = None,
                      external_url: str = None, conversation_id: int = None,
                      tavily_api_key: str = None, github_token: str = None,
                      vision_api_key: str = None, vision_model: str = None,
                      base_url: str = None, user_message: str = None):
    """Obtiene un agente del cache o crea uno nuevo"""
    repo_key = f"{repo_info.get('owner', '')}/{repo_info.get('name', '')}" if repo_info else ""
    # Incluir external_url y conversation_id en cache key para que el agente tenga la URL correcta
    # También incluir si hay MCP keys para forzar recreación si cambian
    mcp_key = f"t:{1 if tavily_api_key else 0}:g:{1 if github_token else 0}"
    cache_key = f"{model}:{workspace}:{repo_key}:{external_url}:{conversation_id}:{mcp_key}"
    
    now = time.time()
    if cache_key in _agent_cache:
        agent, ts = _agent_cache[cache_key]
        if now - ts < _AGENT_CACHE_TTL:
            return agent, True  # Cached
    
    # Crear nuevo agente con URL externa y MCP tools
    agent = create_agent(
        api_key, model, base_url=base_url, workspace=workspace, repo_info=repo_info,
        external_url=external_url, conversation_id=conversation_id,
        tavily_api_key=tavily_api_key, github_token=github_token,
        vision_api_key=db.get_api_key(), vision_model=vision_model,
        user_message=user_message
    )
    _agent_cache[cache_key] = (agent, now)
    return agent, False  # Nuevo


def get_workspace():
    return current_workspace


def set_workspace(path):
    global current_workspace
    current_workspace = path


def create_streaming_callback(q, conv_id=None):
    """Crea un callback que envía eventos a la cola SSE"""
    def streaming_callback(event):
        global last_agent_response, last_error_message, current_conversation_id
        event_type = str(type(event).__name__)
        
        # Log de eventos para debug
        print(f"[EVENT] Type: {event_type}")
        if hasattr(event, 'action'):
            print(f"[EVENT] Action: {type(event.action).__name__}")
        if hasattr(event, 'observation'):
            print(f"[EVENT] Observation: {type(event.observation).__name__}")
        
        # Capturar errores de conversación
        if 'Error' in event_type:
            error_detail = getattr(event, 'detail', '') or getattr(event, 'error', '') or getattr(event, 'message', '') or str(event)
            error_code = getattr(event, 'code', '')
            print(f"[EVENT] ERROR: {error_code} - {error_detail}")
            
            # Traducir errores comunes a mensajes amigables
            friendly_msg = str(error_detail)[:200]
            if 'credit balance is too low' in str(error_detail).lower():
                friendly_msg = "⚠️ SIN CRÉDITO: Tu cuenta de Anthropic no tiene saldo suficiente. Por favor recarga créditos en console.anthropic.com"
            elif 'rate limit' in str(error_detail).lower():
                friendly_msg = "⚠️ LÍMITE DE VELOCIDAD: Demasiadas solicitudes. Espera unos segundos e intenta de nuevo."
            elif 'invalid_api_key' in str(error_detail).lower() or 'authentication' in str(error_detail).lower():
                friendly_msg = "⚠️ API KEY INVÁLIDA: La clave de API no es válida. Revisa la configuración en Settings."
            elif 'timeout' in str(error_detail).lower():
                friendly_msg = "⚠️ TIMEOUT: La solicitud tardó demasiado. Intenta de nuevo."
            elif 'connection' in str(error_detail).lower():
                friendly_msg = "⚠️ ERROR DE CONEXIÓN: No se pudo conectar con el servidor de IA."
            
            last_error_message = friendly_msg  # Guardar para mostrar al final
            q.put({"type": "error", "icon": "❌", "text": friendly_msg})
            # También enviar error a la terminal
            q.put({"type": "terminal_output", "output": f"ERROR: {friendly_msg}", "stderr": "", "exit_code": 1})
        
        try:
            if event_type == 'ActionEvent':
                if hasattr(event, 'action') and event.action:
                    action = event.action
                    action_type = str(type(action).__name__)
                    
                    if 'Command' in action_type or 'Bash' in action_type or 'Terminal' in action_type:
                        cmd = getattr(action, 'command', '') or getattr(action, 'code', '')
                        if cmd:
                            q.put({"type": "action", "icon": "🔧", "text": f"Ejecutando: {cmd[:100]}"})
                            # Enviar comando a la terminal (solo lectura)
                            q.put({"type": "terminal_command", "command": cmd})
                    
                    elif 'FileEditor' in action_type or 'File' in action_type or 'Edit' in action_type or 'Create' in action_type:
                        path = getattr(action, 'path', '') or getattr(action, 'file', '')
                        command = getattr(action, 'command', '')  # view, str_replace, create, insert
                        if path:
                            filename = Path(path).name if path else 'archivo'
                            q.put({"type": "action", "icon": "📄", "text": f"Editando: {filename}"})
                            # Enviar a terminal también
                            cmd_text = f"file_editor {command}: {path}"
                            q.put({"type": "terminal_command", "command": cmd_text})
                            
                            # GUARDAR EN MEMORIA RAG (solo cambios, no views)
                            if command in ('str_replace', 'create', 'insert'):
                                old_str_raw = getattr(action, 'old_str', None)
                                new_str_raw = getattr(action, 'new_str', None)
                                old_str = (old_str_raw or '')[:100]
                                new_str = (new_str_raw or '')[:100]
                                desc = f"{command}: {old_str} -> {new_str}" if old_str else f"{command}"
                                save_file_change(
                                    file_path=path,
                                    description=desc,
                                    change_type="modified" if command == 'str_replace' else "created",
                                    conversation_id=current_conversation_id,
                                    project=current_workspace
                                )
                    
                    elif 'Finish' in action_type:
                        if hasattr(action, 'message') and action.message:
                            last_agent_response = action.message
                            q.put({"type": "finish", "icon": "✅", "text": "Completado"})
                    
                    elif 'Think' in action_type:
                        # Think action - mostrar pensamiento del agente
                        thought = getattr(action, 'thought', '') or getattr(action, 'message', '')
                        if thought:
                            q.put({"type": "think", "icon": "🧠", "text": thought})
                            q.put({"type": "terminal_command", "command": f"# Pensando: {thought[:100]}..."})
                    
                    elif 'TaskTracker' in action_type:
                        # TaskTracker action - mostrar actualización de tareas
                        command = getattr(action, 'command', '')
                        task_list = getattr(action, 'task_list', [])
                        if task_list:
                            # Convertir TaskItem a dict para serialización JSON
                            tasks_serializable = []
                            for task in task_list:
                                if hasattr(task, '__dict__'):
                                    tasks_serializable.append(task.__dict__)
                                elif hasattr(task, 'model_dump'):
                                    tasks_serializable.append(task.model_dump())
                                elif isinstance(task, dict):
                                    tasks_serializable.append(task)
                                else:
                                    tasks_serializable.append(str(task))
                            q.put({"type": "task_tracker", "command": command, "tasks": tasks_serializable})
                        elif command == 'view':
                            q.put({"type": "task_tracker", "command": "view", "tasks": []})
                    
                    elif 'Browser' in action_type:
                        # Browser action - navegación web
                        url = getattr(action, 'url', '')
                        if url:
                            q.put({"type": "action", "icon": "🌐", "text": f"Navegando: {url[:60]}"})
                    
                    elif 'Glob' in action_type:
                        pattern = getattr(action, 'pattern', '')
                        q.put({"type": "action", "icon": "🔍", "text": f"Buscando archivos: {pattern}"})
                    
                    elif 'Grep' in action_type:
                        pattern = getattr(action, 'pattern', '')
                        q.put({"type": "action", "icon": "🔎", "text": f"Buscando texto: {pattern}"})
                    
                    elif 'Delegate' in action_type:
                        task = getattr(action, 'task', '') or getattr(action, 'message', '')
                        q.put({"type": "action", "icon": "🤖", "text": f"Delegando: {task[:80]}"})
            
            elif event_type == 'ObservationEvent':
                if hasattr(event, 'observation') and event.observation:
                    obs = event.observation
                    obs_type = str(type(obs).__name__)
                    tool_name = getattr(event, 'tool_name', '') or ''
                    
                    # Detectar screenshots de browser (CLI o MCP)
                    is_browser_tool = 'browser' in tool_name.lower()
                    
                    # Obtener output del comando (varios posibles atributos)
                    output = (
                        getattr(obs, 'stdout', '') or  # BashObservation usa stdout
                        getattr(obs, 'output', '') or 
                        getattr(obs, 'content', '') or
                        ''
                    )
                    if isinstance(output, list):
                        output = ' '.join(str(x) for x in output)
                    
                    # Debug: log output para verificar
                    if output and '"screenshot"' in str(output)[:100]:
                        print(f"[SCREENSHOT DETECTED] Output length: {len(str(output))}")
                    
                    # Buscar JSON con screenshot en la salida (del CLI de browser)
                    if output and '"screenshot"' in output and '"success"' in output:
                        try:
                            # El CLI retorna JSON directo - intentar parsear el output completo
                            # Buscar el inicio del JSON (primera {) y parsearlo
                            json_start = output.find('{')
                            if json_start >= 0:
                                result = json.loads(output[json_start:])
                                if isinstance(result, dict) and result.get('screenshot') and result.get('success'):
                                    screenshot_data = result.get('screenshot', '')
                                    browser_url = result.get('url', '')
                                    if screenshot_data and conv_id:
                                        update_screenshot(conv_id, browser_url, screenshot_data)
                                        q.put({
                                            "type": "browser", 
                                            "icon": "🌐", 
                                            "text": f"Navegando: {browser_url[:50] if browser_url else 'capturado'}",
                                            "screenshot": True
                                        })
                        except (json.JSONDecodeError, TypeError, AttributeError) as e:
                            pass  # No es un JSON válido de browser
                    
                    if is_browser_tool:
                        # Las herramientas de browser MCP retornan content con ImageContent
                        if hasattr(obs, 'content') and obs.content:
                            for item in obs.content:
                                # Buscar texto con resultado JSON de browser tools
                                if hasattr(item, 'text') and item.text:
                                    try:
                                        result = json.loads(item.text)
                                        if isinstance(result, dict) and 'screenshot' in result:
                                            screenshot_data = result.get('screenshot', '')
                                            browser_url = result.get('url', '')
                                            if screenshot_data and conv_id:
                                                update_screenshot(conv_id, browser_url, screenshot_data)
                                                q.put({
                                                    "type": "browser", 
                                                    "icon": "🌐", 
                                                    "text": f"Navegando: {browser_url[:40] if browser_url else 'capturado'}",
                                                    "screenshot": True
                                                })
                                    except (json.JSONDecodeError, TypeError):
                                        pass
                                
                                # También buscar ImageContent (para MCP tools)
                                if isinstance(item, ImageContent):
                                    screenshot_data = item.data if hasattr(item, 'data') else None
                                    if screenshot_data and conv_id:
                                        import re
                                        browser_url = ''
                                        for text_item in obs.content:
                                            if hasattr(text_item, 'text') and text_item.text:
                                                urls = re.findall(r'https?://[^\s"\'<>]+', text_item.text)
                                                if urls:
                                                    browser_url = urls[0]
                                                    break
                                        
                                        update_screenshot(conv_id, browser_url, screenshot_data)
                                        q.put({
                                            "type": "browser", 
                                            "icon": "🌐", 
                                            "text": f"Screenshot: {browser_url[:40] if browser_url else 'capturado'}",
                                            "screenshot": True
                                        })
                    
                    if 'Command' in obs_type or 'Bash' in obs_type or 'Terminal' in obs_type:
                        raw_output = getattr(obs, 'stdout', '') or getattr(obs, 'output', '') or getattr(obs, 'content', '')
                        stderr = getattr(obs, 'stderr', '')
                        exit_code = getattr(obs, 'exit_code', 0)
                        
                        # Extraer texto limpio (puede ser lista de TextContent)
                        if isinstance(raw_output, list):
                            output_parts = []
                            for item in raw_output:
                                if hasattr(item, 'text'):
                                    output_parts.append(item.text)
                                else:
                                    output_parts.append(str(item))
                            output = '\n'.join(output_parts)
                        else:
                            output = str(raw_output) if raw_output else ''
                        
                        if output and len(output) > 0:
                            preview = output[:100].replace('\n', ' ')
                            pass  # No mostrar output técnico del comando
                            # Enviar output a la terminal (solo lectura)
                            q.put({
                                "type": "terminal_output", 
                                "output": clean_ansi(output[:2000]),  # Limitar output
                                "stderr": str(stderr)[:500] if stderr else "",
                                "exit_code": exit_code
                            })
                        
                        # Enviar status de comando completado
                        status_icon = "✅" if exit_code == 0 else "❌"
                        q.put({"type": "command_done", "icon": status_icon, "exit_code": exit_code})
                    
                    elif 'FileEditor' in obs_type:
                        # Obtener contenido del FileEditorObservation
                        content = getattr(obs, 'content', '') or ''
                        if isinstance(content, list):
                            content = '\n'.join(str(c.text if hasattr(c, 'text') else c) for c in content)
                        
                        if content:
                            # Mostrar resumen en output
                            preview = content[:100].replace('\n', ' ')
                            q.put({"type": "output", "icon": "✅", "text": "Archivo modificado"})
                            # Enviar a terminal
                            q.put({
                                "type": "terminal_output",
                                "output": clean_ansi(content[:1000]),
                                "stderr": "",
                                "exit_code": 0
                            })
                    
                    elif 'TaskTracker' in obs_type:
                        # TaskTrackerObservation - resultado del task tracker
                        task_list = getattr(obs, 'task_list', [])
                        content = getattr(obs, 'content', '')
                        
                        # Convertir task_list a formato serializable
                        tasks_data = []
                        if task_list:
                            for task in task_list:
                                if hasattr(task, 'model_dump'):
                                    tasks_data.append(task.model_dump())
                                elif isinstance(task, dict):
                                    tasks_data.append(task)
                                else:
                                    tasks_data.append({
                                        'title': getattr(task, 'title', str(task)),
                                        'status': getattr(task, 'status', 'todo'),
                                        'notes': getattr(task, 'notes', '')
                                    })
                        
                        q.put({
                            "type": "task_tracker_update", 
                            "tasks": tasks_data,
                            "content": str(content) if content else ""
                        })
                        
                        # También enviar a terminal
                        if tasks_data:
                            task_text = "\n".join([f"  {'✓' if t.get('status')=='done' else '○'} {t.get('title', '')}" for t in tasks_data[:5]])
                            q.put({
                                "type": "terminal_output",
                                "output": f"Task Tracker:\n{task_text}",
                                "stderr": "",
                                "exit_code": 0
                            })
                    
                    elif 'BrowserObservation' in obs_type or (BrowserObservation and isinstance(obs, BrowserObservation)):
                        # BrowserObservation nativo del SDK - tiene screenshot_data
                        screenshot_data = getattr(obs, 'screenshot_data', None)
                        content = getattr(obs, 'content', '')
                        
                        if screenshot_data and conv_id:
                            # Extraer URL del contenido si está disponible
                            import re
                            browser_url = ''
                            content_str = str(content) if content else ''
                            urls = re.findall(r'https?://[^\s"\'<>\]]+', content_str)
                            if urls:
                                browser_url = urls[0]
                            
                            update_screenshot(conv_id, browser_url, screenshot_data)
                            q.put({
                                "type": "browser",
                                "icon": "🌐",
                                "text": f"Screenshot: {browser_url[:50] if browser_url else 'capturado'}",
                                "screenshot": True
                            })
                        
                        # Enviar contenido a terminal
                        if content:
                            content_preview = str(content)[:500]
                            q.put({
                                "type": "terminal_output",
                                "output": f"Browser:\n{content_preview}",
                                "stderr": "",
                                "exit_code": 0
                            })
                    
                    elif 'Glob' in obs_type:
                        # GlobObservation - resultado de búsqueda de archivos
                        content = getattr(obs, 'content', '')
                        if content:
                            q.put({
                                "type": "terminal_output",
                                "output": f"Archivos encontrados:\n{str(content)[:1000]}",
                                "stderr": "",
                                "exit_code": 0
                            })
                    
                    elif 'Grep' in obs_type:
                        # GrepObservation - resultado de búsqueda de texto
                        content = getattr(obs, 'content', '')
                        if content:
                            q.put({
                                "type": "terminal_output",
                                "output": f"Coincidencias:\n{str(content)[:1000]}",
                                "stderr": "",
                                "exit_code": 0
                            })
            
            elif event_type == 'MessageEvent':
                if hasattr(event, 'llm_message') and event.llm_message:
                    msg = event.llm_message
                    if hasattr(msg, 'role') and msg.role == 'assistant':
                        if hasattr(msg, 'content') and msg.content:
                            text_parts = []
                            for part in msg.content:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                response = '\n'.join(text_parts)
                                last_agent_response = response
                                q.put({"type": "thinking", "icon": "💭", "text": response[:100]})
        
        except Exception as e:
            print(f"[CALLBACK ERROR] {e}")
    
    return streaming_callback


def capture_response(event):
    """Callback para capturar la respuesta del agente"""
    global last_agent_response
    
    event_type = str(type(event).__name__)
    
    if event_type == 'ActionEvent':
        if hasattr(event, 'action') and event.action:
            action = event.action
            action_type = str(type(action).__name__)
            if 'Finish' in action_type:
                if hasattr(action, 'message') and action.message:
                    last_agent_response = action.message
    
    elif event_type == 'MessageEvent':
        if hasattr(event, 'llm_message') and event.llm_message:
            msg = event.llm_message
            if hasattr(msg, 'role') and msg.role == 'assistant':
                if hasattr(msg, 'content') and msg.content:
                    text_parts = []
                    for part in msg.content:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        last_agent_response = '\n'.join(text_parts)


@router.post("/send")
async def send_message(message: str = Form(...), project: str = Form(None)):
    """Enviar mensaje al agente"""
    global current_conversation, current_workspace, last_agent_response
    
    last_agent_response = ""
    
    # Obtener modelo configurado
    
    # Seleccionar API key y base_url según modelo
    base_url = None
    if model.startswith("deepseek/"):
        api_key = db.get_setting("deepseek_api_key")
        base_url = settings.deepseek_base_url
        if not api_key:
            # Fallback a Gemini si DeepSeek no configurado
            model = settings.default_model
            api_key = db.get_api_key()
            base_url = None
    else:
        api_key = db.get_api_key()
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key no configurada")
    
    # SIEMPRE actualizar workspace según el proyecto actual
    if project:
        current_workspace = str(settings.projects_dir / project)
    else:
        current_workspace = str(settings.projects_dir)
    
    # Crear directorio si no existe
    os.makedirs(current_workspace, exist_ok=True)
    
    try:
        conversation_id = None
        if project:
            proj = db.get_project_by_name(project)
            if proj:
                conv = db.get_conversation(proj['id'])
                conversation_id = conv['id']
        
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
        
        agent = create_agent(api_key, model, workspace=current_workspace)
        
        # Obtener GITHUB_TOKEN para que el agente pueda usarlo
        github_token = db.get_github_token()
        secrets = {"GITHUB_TOKEN": github_token} if github_token else None
        
        current_conversation = Conversation(
            agent=agent, 
            workspace=current_workspace,
            callbacks=[capture_response],
            secrets=secrets
        )
        
        current_conversation.send_message(message)
        await asyncio.to_thread(current_conversation.run)
        
        agent_response = last_agent_response
        if not agent_response:
            agent_response = "✅ Tarea completada. Revisa los archivos creados en tu proyecto."
        
        if conversation_id:
            db.add_message(conversation_id, 'assistant', agent_response)
        
        return JSONResponse({
            "status": "ok",
            "message": agent_response,
            "user_message": message
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


def _is_simple_question(message: str) -> bool:
    """Detecta si es una pregunta simple que no requiere ejecución de comandos"""
    message_lower = message.lower().strip()
    
    # Patrones que indican pregunta simple de conversación
    simple_patterns = [
        "hola", "hello", "hi", "hey",
        "cuéntame", "cuentame", "dime",
        "qué es", "que es", "qué significa", "que significa",
        "explica", "explícame", "explicame",
        "cómo funciona", "como funciona",
        "por qué", "porque", "por que",
        "chiste", "joke", "broma",
        "gracias", "thanks",
        "cuál es", "cual es",
        "recomienda", "sugiere", "consejo"
    ]
    
    # Patrones que requieren ejecución (no usar streaming directo)
    action_patterns = [
        "ejecuta", "run", "crea", "create", "modifica", "edit",
        "elimina", "delete", "instala", "install", "git ",
        "curl ", "python ", "npm ", "pip ", "cd ", "ls ",
        "mkdir", "mv ", "cp ", "cat ", "grep ",
        "archivo", "file", "código", "code"
    ]
    
    # Si contiene patrones de acción, no es simple
    for pattern in action_patterns:
        if pattern in message_lower:
            return False
    
    # Si contiene patrones simples, es simple
    for pattern in simple_patterns:
        if pattern in message_lower:
            return True
    
    # Si es muy corto (< 50 chars) y termina en ? probablemente es simple
    if len(message) < 50 and message.strip().endswith("?"):
        return True
    
    return False


@router.post("/stream")
async def stream_message(
    message: str = Form(...), 
    project: str = Form(None), 
    images: str = Form(None),
    external_url: str = Form(None),
    conversation_id: int = Form(None),
    use_realtime: bool = Form(False)  # Nuevo: forzar streaming directo
):
    """Enviar mensaje al agente con streaming SSE"""
    global current_conversation, current_workspace, last_agent_response, last_error_message
    
    last_agent_response = ""
    last_error_message = ""  # Limpiar errores previos
    
    # NUEVO: Detectar si es pregunta simple para usar streaming directo
    is_simple = _is_simple_question(message)
    
    # Obtener modelo configurado
    model = db.get_setting("llm_model", settings.default_model)
    
    # Seleccionar API key y base_url según modelo
    base_url = None
    if model.startswith("deepseek/"):
        api_key = db.get_setting("deepseek_api_key")
        base_url = settings.deepseek_base_url
        if not api_key:
            model = settings.default_model
            api_key = db.get_api_key()
            base_url = None
    else:
        api_key = db.get_api_key()
    
    if not api_key:
        return JSONResponse({"error": "API key no configurada"}, status_code=400)
    
    # Obtener workspace de la base de datos (guardado al crear el proyecto)
    workspace = None
    if project:
        proj = db.get_project_by_name(project)
        if proj:
            # Usar el path guardado en la base de datos
            workspace = proj.get('path')
            print(f"[WORKSPACE] Using path from DB: {workspace}")
    
    # Fallback si no se encontró en la base de datos
    if not workspace:
        if project:
            if "test03" in project.lower():
                workspace = "/workspace/project/test03"
            else:
                workspace = str(settings.projects_dir / project)
        else:
            workspace = str(settings.projects_dir)
        print(f"[WORKSPACE] Using fallback path: {workspace}")
    
    # Crear directorio si no existe (excepto test03 que ya está montado)
    if "test03" not in workspace:
        os.makedirs(workspace, exist_ok=True)
    current_workspace = workspace
    
    print(f"[WORKSPACE] Project: {project}, Workspace: {workspace}")
    
    # Parsear imágenes si las hay
    image_contents = []
    if images:
        try:
            images_data = json.loads(images)
            print(f"[DEBUG] Received {len(images_data)} images")
            image_urls = []
            for img in images_data:
                # img tiene {name, dataUrl} donde dataUrl es data:image/...;base64,...
                data_url = img.get('dataUrl', '')
                if data_url.startswith('data:image/'):
                    image_urls.append(data_url)
                    print(f"[DEBUG] Added image URL: {data_url[:80]}...")
            if image_urls:
                # ImageContent espera image_urls (lista de URLs o data URLs)
                image_contents.append(ImageContent(image_urls=image_urls))
                print(f"[DEBUG] Created ImageContent with {len(image_urls)} images")
        except Exception as e:
            print(f"Error parsing images: {e}")
    
    async def generate_events():
        nonlocal conversation_id  # Usar el conversation_id del parámetro si existe
        global last_agent_response
        q = queue.Queue()
        
        # Usar conversation_id del frontend si viene, sino derivarlo del project
        conv_id_from_param = conversation_id
        conversation_id = None
        repo_info = None
        print(f"[CHAT] Project received: '{project}', conversation_id from param: {conv_id_from_param}")
        
        # Prioridad: usar conversation_id si viene directamente
        if conv_id_from_param:
            conversation_id = conv_id_from_param
            print(f"[CHAT] Using conversation_id from parameter: {conversation_id}")
        
        if project:
            proj = db.get_project_by_name(project)
            print(f"[CHAT] Project found: {proj is not None}, ID: {proj['id'] if proj else 'N/A'}")
            if proj:
                if not conversation_id:  # Solo buscar si no vino del parámetro
                    conv = db.get_conversation(proj['id'])
                    conversation_id = conv['id'] if conv else None
                print(f"[CHAT] Conversation ID: {conversation_id}")
                # Obtener info del repositorio para pasarla al agente
                repo_info = {
                    'owner': proj.get('repo_owner'),
                    'name': proj.get('repo_name'),
                    'branch': proj.get('branch', 'main')
                }
        else:
            print("[CHAT] WARNING: No project name received!")
        
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
            print(f"[CHAT] User message saved to conversation {conversation_id}")
        else:
            print("[CHAT] WARNING: conversation_id is None, message NOT saved!")
        
        # ============================================================
        # STREAMING DIRECTO para preguntas simples (token por token real)
        # ============================================================
        if is_simple or use_realtime:
            print(f"[STREAM] Using REALTIME streaming for simple question")
            yield f"data: {json.dumps({'type': 'status', 'icon': '⚡', 'text': 'Streaming directo...'})}\n\n"
            
            try:
                from core.realtime_stream import stream_response
                import asyncio
                import sys
                
                # Obtener historial para contexto
                conv_history = []
                if conversation_id:
                    messages = db.get_messages(conversation_id)
                    for msg in messages[-8:]:  # Últimos 8 mensajes
                        conv_history.append({
                            "role": msg["role"],
                            "content": msg["content"][:500]
                        })
                
                full_response = ""
                token_count = 0
                print(f"[REALTIME] Starting stream...", flush=True)
                
                async for event in stream_response(
                    message=message,
                    model=model,
                    api_key=api_key,
                    conversation_history=conv_history
                ):
                    if event["type"] == "token":
                        token_count += 1
                        full_response += event["content"]
                        token_data = json.dumps(event)
                        # Log cada token enviado
                        if token_count <= 10 or token_count % 20 == 0:
                            print(f"[REALTIME TOKEN #{token_count}] {event['content'][:15]}...", flush=True)
                        yield f"data: {token_data}\n\n"
                    elif event["type"] == "error":
                        print(f"[REALTIME ERROR] {event['error']}", flush=True)
                        yield f"data: {json.dumps({'type': 'error', 'text': event['error']})}\n\n"
                
                print(f"[REALTIME] Stream complete. Tokens sent: {token_count}", flush=True)
                
                # Guardar respuesta en BD
                if conversation_id and full_response:
                    db.add_message(conversation_id, 'assistant', full_response)
                
                yield f"data: {json.dumps({'type': 'done', 'message': full_response})}\n\n"
                return  # Terminar aquí para streaming directo
                
            except Exception as e:
                print(f"[STREAM] Realtime streaming failed: {e}, falling back to SDK")
                import traceback
                traceback.print_exc()
                # Si falla, continuar con el flujo normal del SDK
        
        # ============================================================
        # FLUJO NORMAL con SDK (para comandos y operaciones complejas)
        # ============================================================
        
        # OPTIMIZACIÓN UX: Feedback inmediato mientras se prepara el agente
        yield f"data: {json.dumps({'type': 'status', 'icon': '🔄', 'text': 'Conectando...'})}\n\n"
        
        
        # Obtener API keys para MCP tools
        github_token = db.get_github_token()
        tavily_api_key = db.get_tavily_api_key()
        
        # OPTIMIZACIÓN: Usar cache de agentes para respuestas más rápidas
        # Pasar external_url y conversation_id para que el agente conozca la URL del preview
        # Pasar MCP keys para habilitar Tavily (búsquedas) y GitHub (PRs)
        agent, from_cache = _get_cached_agent(
            api_key, model, workspace, repo_info,
            external_url=external_url, conversation_id=conversation_id,
            tavily_api_key=tavily_api_key, github_token=github_token,
            vision_api_key=db.get_api_key(), vision_model=settings.vision_model,
            base_url=base_url, user_message=message
        )
        if from_cache:
            yield f"data: {json.dumps({'type': 'status', 'icon': '⚡', 'text': 'Listo!'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'status', 'icon': '🤖', 'text': 'Preparando agente...'})}\n\n"
        
        # Secrets para la Conversation (el agente ya tiene las MCP tools)
        secrets = {"GITHUB_TOKEN": github_token} if github_token else None
        
        # Callbacks para eventos y tokens (streaming)
        streaming_cb = create_streaming_callback(q, conversation_id)
        token_cb = create_token_callback(q)  # NUEVO: Token streaming
        
        conv = Conversation(
            agent=agent,
            workspace=workspace,
            callbacks=[streaming_cb, capture_response],
            token_callbacks=[token_cb],  # STREAMING DE TOKENS - Igual que OpenHands
            secrets=secrets
        )
        
        # Guardar referencia para poder pausar/reanudar
        if conversation_id:
            active_sdk_conversations[conversation_id] = conv
        
        # ============================================================
        # HISTORIAL DE CONVERSACIÓN - El agente debe recordar mensajes previos
        # ============================================================
        conversation_history = ""
        if conversation_id:
            # Obtener últimos N mensajes de esta conversación (excluyendo el actual)
            messages = db.get_messages(conversation_id)
            # Filtrar: excluir el mensaje actual que acabamos de guardar
            # y limitar a los últimos 10 mensajes para no sobrecargar
            recent_messages = messages[:-1] if messages else []  # Excluir el actual
            recent_messages = recent_messages[-10:]  # Últimos 10
            
            if recent_messages:
                history_parts = []
                for i, msg in enumerate(recent_messages, 1):
                    role = "👤 USUARIO" if msg['role'] == 'user' else "🤖 TÚ (ASISTENTE)"
                    # Truncar mensajes muy largos pero mantener info clave
                    content = msg['content'][:800] + "..." if len(msg['content']) > 800 else msg['content']
                    # Formato más claro con separadores
                    history_parts.append(f"[Mensaje {i}] {role}:\n{content}")
                
                conversation_history = "\n\n" + "="*50 + "\n\n".join(history_parts) + "\n\n" + "="*50
                print(f"[HISTORY] Added {len(recent_messages)} previous messages to context")
                # Debug: mostrar primeros mensajes del historial
                if recent_messages:
                    print(f"[HISTORY DEBUG] First message: {recent_messages[0]['role']}: {recent_messages[0]['content'][:100]}...")
                    print(f"[HISTORY DEBUG] Last message: {recent_messages[-1]['role']}: {recent_messages[-1]['content'][:100]}...")
        
        # MEMORIA RAG: Recuperar contexto relevante del historial
        memory_context = get_context_for_message(message, project=project)
        
        # ============================================================
        # SMART PROCESSING - Inteligencia como los TOP del mercado
        # ============================================================
        actual_message = message
        smart_analysis = None
        
        # Agregar contenido de archivos pinneados al contexto
        try:
            pinned_content = get_pinned_content(project, workspace, max_chars=2000)
            if pinned_content:
                actual_message = f"{message}\n\n{pinned_content}"
                print(f"[PINS] Added {len(pinned_content)} chars of pinned content")
        except Exception as e:
            print(f"[PINS] Error: {e}")
        
        try:
            smart_analysis = smart_process_message(message, workspace)
            
            # Enviar thinking steps al frontend
            for step in smart_analysis.get('thinking_steps', []):
                yield f"data: {json.dumps({'type': 'thinking', 'icon': step['icon'], 'text': step['text']})}\n\n"
            
            # Crear checkpoint si es operación riesgosa
            if smart_analysis.get('should_checkpoint'):
                try:
                    checkpoint = create_checkpoint(workspace)
                    print(f"[CHECKPOINT] Created: {checkpoint.get('id', '')}")
                except:
                    pass
            
            # Mostrar archivos detectados
            if smart_analysis.get('files'):
                files_text = ', '.join([f['file'].split('/')[-1] for f in smart_analysis['files'][:3]])
                yield f"data: {json.dumps({'type': 'status', 'icon': '📂', 'text': 'Archivos detectados'})}\n\n"
        except Exception as e:
            print(f"[SMART] Error: {e}")
        
        # CSS genérico check
        has_generic_css = '.' in message and '#' not in message and any(
            kw in message.lower() for kw in ['css', 'estilo', 'style', 'color']
        )
        if has_generic_css:
            try:
                enriched_message, impact_metadata = analyze_and_enrich_message(message, workspace)
                if impact_metadata.get("high_risk_changes"):
                    actual_message = enriched_message
            except:
                pass
        
        # Construir mensaje completo con historial y memoria
        
        # Agregar historial de conversación (CRÍTICO para que el agente recuerde)
        # NOTA: El condenser del SDK maneja eventos, NO mensajes del usuario
        # Por eso debemos incluir el historial explícitamente en el mensaje
        # FORMATO MEJORADO: Más claro y directo para que el LLM lo entienda
        if conversation_history:
            actual_message = f"""## HISTORIAL DE NUESTRA CONVERSACIÓN (RECUERDA ESTO):

{conversation_history}

---

## MENSAJE ACTUAL DEL USUARIO:
{message}

IMPORTANTE: Usa la información del historial de arriba para responder. Si el usuario mencionó su nombre, recuérdalo. Si dio contexto previo, úsalo."""
            print(f"[HISTORY DEBUG] Final message with history:\n{actual_message[:500]}...")
        
        # Agregar contexto de memoria RAG si existe (limitado a ~500 tokens)
        if memory_context:
            # Limitar a ~2000 caracteres (~500 tokens) - balance entre contexto y eficiencia
            truncated_context = memory_context[:2000] + "..." if len(memory_context) > 2000 else memory_context
            actual_message = f"{actual_message}\n\n{truncated_context}"
            print(f"[MEMORY] Added RAG context ({len(truncated_context)} chars)")
        if repo_info and repo_info.get('owner') and repo_info.get('name'):
            repo_owner = repo_info['owner']
            repo_name = repo_info['name']
            repo_branch = repo_info.get('branch', 'main')
            
            # Si es un comando de pull, agregar contexto mínimo
            if 'pull' in message.lower():
                actual_message = f"{message}\n\nRepo: {repo_owner}/{repo_name} (branch: {repo_branch})\nWorkspace: {workspace}\nUse ${{GITHUB_TOKEN}} for git auth."
        
        # Enviar mensaje con imágenes si las hay
        if image_contents:
            # Construir Message con texto + imágenes
            msg_content = [TextContent(text=actual_message)] + image_contents
            user_message = Message(role="user", content=msg_content, vision_enabled=True)
            print(f"[DEBUG] Sending message with {len(image_contents)} image contents, vision_enabled=True")
            print(f"[DEBUG] Message content types: {[type(c).__name__ for c in msg_content]}")
            conv.send_message(user_message)
        else:
            print(f"[DEBUG] Sending text-only message")
            conv.send_message(actual_message)
        
        def run_agent():
            try:
                conv.run()
            except Exception as e:
                q.put({"type": "error", "icon": "❌", "text": str(e)})
            finally:
                q.put(None)
                # Limpiar referencia cuando termine
                if conversation_id and conversation_id in active_sdk_conversations:
                    del active_sdk_conversations[conversation_id]
        
        thread = threading.Thread(target=run_agent)
        thread.start()
        
        # OPTIMIZACIÓN: Reducir timeout de 0.5s a 0.1s para menor latencia
        while True:
            try:
                event = q.get(timeout=0.1)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                if not thread.is_alive():
                    break
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        thread.join(timeout=3)
        
        agent_response = last_agent_response
        if not agent_response:
            if last_error_message:
                agent_response = f"❌ {last_error_message}"
            else:
                agent_response = "✅ Tarea completada. Revisa los archivos creados."
        
        if conversation_id:
            db.add_message(conversation_id, 'assistant', agent_response)
        
        # Solo enviar evento done (los tokens ya fueron por streaming)
        yield f"data: {json.dumps({'type': 'done', 'message': agent_response})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/reset")
async def reset_chat():
    """Resetear conversación"""
    global current_conversation
    current_conversation = None
    return JSONResponse({"status": "ok"})


@router.delete("/clear-history/{conversation_id}")
async def clear_history(conversation_id: int):
    """Borrar historial de mensajes de una conversación"""
    global current_conversation
    db.clear_messages(conversation_id)
    current_conversation = None  # Reset para empezar fresco
    return JSONResponse({"status": "ok", "message": "Historial borrado"})


@router.post("/message/{conversation_id}")
async def add_message(conversation_id: int, request: Request):
    """Agregar un mensaje a la conversación (usado por Multi-Agent, etc)"""
    try:
        data = await request.json()
        role = data.get('role', 'assistant')
        content = data.get('content', '')
        
        if not content:
            return JSONResponse({"error": "Content required"}, status_code=400)
        
        db.add_message(conversation_id, role, content)
        return JSONResponse({"status": "ok", "message": "Mensaje guardado"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/memory/stats")
async def memory_stats():
    """Obtener estadísticas de la memoria RAG"""
    stats = get_memory_stats()
    return JSONResponse(stats)


@router.get("/messages/{project_name}")
async def get_messages(project_name: str):
    """Obtener mensajes de un proyecto"""
    messages = db.get_messages_by_project(project_name)
    return JSONResponse({"messages": messages})

# ============================================================
# CONTEXT PINNING ENDPOINTS
# ============================================================

@router.get("/pins/{project}")
async def get_pins(project: str):
    """Obtiene archivos pinneados para un proyecto."""
    pins = get_pinned_files(project)
    return {"pins": pins}

@router.post("/pins/{project}")
async def add_pin(project: str, file_path: str = Form(...), description: str = Form(None)):
    """Fija un archivo al contexto."""
    result = pin_file(file_path, project, description)
    return result

@router.delete("/pins/{project}/{file_path:path}")
async def remove_pin(project: str, file_path: str):
    """Quita un archivo del contexto."""
    result = unpin_file(file_path, project)
    return result

@router.get("/pins/{project}/suggestions")
async def get_pin_suggestions(project: str):
    """Sugiere archivos importantes para pinnear."""
    # Obtener workspace del proyecto
    workspace = f"/app/projects/{project}"
    suggestions = auto_detect_important_files(workspace)
    return {"suggestions": suggestions}

