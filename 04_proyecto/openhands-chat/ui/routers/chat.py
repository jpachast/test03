"""Rutas de chat con el agente"""
import json
import queue
import asyncio
import threading
from pathlib import Path
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from openhands.sdk import Conversation, ImageContent

from config.database import Database
from config.settings import Settings
from core.agent import create_agent
from ui.routers.browser import update_screenshot

router = APIRouter(prefix="/api/chat", tags=["chat"])
db = Database()
settings = Settings()

# Estado global
current_conversation = None
current_workspace = None
last_agent_response = ""
current_conversation_id = None  # Para asociar screenshots con la conversación


def get_workspace():
    return current_workspace


def set_workspace(path):
    global current_workspace
    current_workspace = path


def create_streaming_callback(q, conv_id=None):
    """Crea un callback que envía eventos a la cola SSE"""
    def streaming_callback(event):
        global last_agent_response, current_conversation_id
        event_type = str(type(event).__name__)
        
        # Log de eventos para debug
        print(f"[EVENT] Type: {event_type}")
        if hasattr(event, 'action'):
            print(f"[EVENT] Action: {type(event.action).__name__}")
        if hasattr(event, 'observation'):
            print(f"[EVENT] Observation: {type(event.observation).__name__}")
        
        # Capturar errores de conversación
        if 'Error' in event_type:
            error_msg = getattr(event, 'error', None) or getattr(event, 'message', None) or str(event)
            print(f"[EVENT] ERROR: {error_msg}")
            if hasattr(event, '__dict__'):
                print(f"[EVENT] ERROR ATTRS: {event.__dict__}")
            q.put({"type": "error", "icon": "❌", "text": str(error_msg)[:200]})
        
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
                    
                    elif 'File' in action_type or 'Edit' in action_type or 'Create' in action_type:
                        path = getattr(action, 'path', '') or getattr(action, 'file', '')
                        if path:
                            filename = Path(path).name if path else 'archivo'
                            q.put({"type": "action", "icon": "📄", "text": f"Editando: {filename}"})
                    
                    elif 'Finish' in action_type:
                        if hasattr(action, 'message') and action.message:
                            last_agent_response = action.message
                            q.put({"type": "finish", "icon": "✅", "text": "Completado"})
                    
                    elif 'Think' in action_type or 'Message' in action_type:
                        msg = getattr(action, 'message', '') or getattr(action, 'thought', '')
                        if msg:
                            q.put({"type": "thinking", "icon": "💭", "text": msg[:150]})
            
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
                            q.put({"type": "output", "icon": "📋", "text": f"Resultado: {preview}"})
                            # Enviar output a la terminal (solo lectura)
                            q.put({
                                "type": "terminal_output", 
                                "output": output[:2000],  # Limitar output
                                "stderr": str(stderr)[:500] if stderr else "",
                                "exit_code": exit_code
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
    
    api_key = db.get_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="API key no configurada")
    
    # SIEMPRE actualizar workspace según el proyecto actual
    if project:
        current_workspace = str(settings.projects_dir / project)
    else:
        current_workspace = str(settings.projects_dir)
    
    try:
        conversation_id = None
        if project:
            proj = db.get_project_by_name(project)
            if proj:
                conv = db.get_conversation(proj['id'])
                conversation_id = conv['id']
        
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
        
        model = db.get_setting("llm_model", settings.default_model)
        agent = create_agent(api_key, model)
        current_conversation = Conversation(
            agent=agent, 
            workspace=current_workspace,
            callbacks=[capture_response]
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


@router.post("/stream")
async def stream_message(message: str = Form(...), project: str = Form(None)):
    """Enviar mensaje al agente con streaming SSE"""
    global current_conversation, current_workspace, last_agent_response
    
    last_agent_response = ""
    
    api_key = db.get_api_key()
    if not api_key:
        return JSONResponse({"error": "API key no configurada"}, status_code=400)
    
    if project:
        workspace = str(settings.projects_dir / project)
    else:
        workspace = str(settings.projects_dir)
    current_workspace = workspace
    
    async def generate_events():
        global last_agent_response
        q = queue.Queue()
        
        conversation_id = None
        if project:
            proj = db.get_project_by_name(project)
            if proj:
                conv = db.get_conversation(proj['id'])
                conversation_id = conv['id']
        
        if conversation_id:
            db.add_message(conversation_id, 'user', message)
        
        yield f"data: {json.dumps({'type': 'start', 'icon': '🚀', 'text': 'Iniciando...'})}\n\n"
        
        model = db.get_setting("llm_model", settings.default_model)
        agent = create_agent(api_key, model)
        
        streaming_cb = create_streaming_callback(q, conversation_id)
        conv = Conversation(
            agent=agent,
            workspace=workspace,
            callbacks=[streaming_cb, capture_response]
        )
        
        conv.send_message(message)
        
        def run_agent():
            try:
                conv.run()
            except Exception as e:
                q.put({"type": "error", "icon": "❌", "text": str(e)})
            finally:
                q.put(None)
        
        thread = threading.Thread(target=run_agent)
        thread.start()
        
        while True:
            try:
                event = q.get(timeout=0.5)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        thread.join(timeout=5)
        
        agent_response = last_agent_response
        if not agent_response:
            agent_response = "✅ Tarea completada. Revisa los archivos creados."
        
        if conversation_id:
            db.add_message(conversation_id, 'assistant', agent_response)
        
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


@router.get("/messages/{project_name}")
async def get_messages(project_name: str):
    """Obtener mensajes de un proyecto"""
    messages = db.get_messages_by_project(project_name)
    return JSONResponse({"messages": messages})
