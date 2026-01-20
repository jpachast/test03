"""
Smart Chat Module - Inteligencia para el chat como los TOP del mercado

Implementa:
1. Detección automática de archivos mencionados
2. Detección de intenciones (reemplaza /commands)
3. Generación de diff previews
4. Sugerencias de siguiente paso
5. Sistema de checkpoints
6. Preferencias del usuario
"""

import re
import os
import json
import hashlib
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


# ============================================================
# 1. DETECTOR DE ARCHIVOS MENCIONADOS
# ============================================================

def detect_mentioned_files(message: str, workspace: str) -> List[Dict[str, Any]]:
    """Detecta archivos mencionados en el mensaje del usuario."""
    detected = []
    if not workspace or not os.path.exists(workspace):
        return detected
    
    # Buscar nombres de archivo con extensión
    file_pattern = r'([\w\-./]+\.(?:py|js|jsx|ts|tsx|html|css|json|yml|yaml|md|sql|java|go|rs|rb|php|vue))'
    matches = re.findall(file_pattern, message, re.IGNORECASE)
    
    for filename in matches:
        # Buscar en workspace
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv']]
            for f in files:
                if f == filename.split('/')[-1]:
                    full_path = os.path.join(root, f)
                    detected.append({
                        'file': full_path,
                        'mentioned_as': filename,
                        'confidence': 'high'
                    })
                    break
    
    return detected[:5]


# ============================================================
# 2. DETECTOR DE INTENCIONES
# ============================================================

INTENTIONS = {
    'fix': {'keywords': ['arregla', 'corrige', 'fix', 'error', 'bug', 'falla'], 'icon': '🔧'},
    'explain': {'keywords': ['explica', 'qué hace', 'cómo funciona'], 'icon': '📖'},
    'create': {'keywords': ['crea', 'genera', 'nuevo', 'agrega', 'implementa'], 'icon': '✨'},
    'modify': {'keywords': ['modifica', 'cambia', 'actualiza', 'edita'], 'icon': '✏️'},
    'delete': {'keywords': ['elimina', 'borra', 'quita', 'delete'], 'icon': '🗑️'},
    'test': {'keywords': ['test', 'prueba', 'testing'], 'icon': '🧪'},
    'refactor': {'keywords': ['refactoriza', 'mejora', 'optimiza'], 'icon': '♻️'},
    'deploy': {'keywords': ['deploy', 'push', 'commit'], 'icon': '🚀'},
}

def detect_intention(message: str) -> Dict[str, Any]:
    """Detecta la intención del usuario."""
    message_lower = message.lower()
    
    for intent, data in INTENTIONS.items():
        for kw in data['keywords']:
            if kw in message_lower:
                return {
                    'intention': intent,
                    'icon': data['icon'],
                    'confidence': 'high'
                }
    
    return {'intention': 'general', 'icon': '💬', 'confidence': 'low'}


# ============================================================
# 3. SISTEMA DE CHECKPOINTS
# ============================================================

CHECKPOINTS_DIR = '/app/data/checkpoints'

def create_checkpoint(workspace: str, name: str = None) -> Dict[str, Any]:
    """Crea un checkpoint del workspace."""
    if not name:
        name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    checkpoint_id = hashlib.md5(f"{workspace}:{name}".encode()).hexdigest()[:12]
    checkpoint_path = os.path.join(CHECKPOINTS_DIR, checkpoint_id)
    os.makedirs(checkpoint_path, exist_ok=True)
    
    metadata = {
        'id': checkpoint_id,
        'name': name,
        'workspace': workspace,
        'created_at': datetime.now().isoformat(),
        'files': []
    }
    
    # Copiar archivos de código
    try:
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            for f in files:
                if f.endswith(('.py', '.js', '.html', '.css', '.json')):
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, workspace)
                    try:
                        with open(src, 'r') as file:
                            content = file.read()
                        dst_dir = os.path.join(checkpoint_path, os.path.dirname(rel))
                        os.makedirs(dst_dir, exist_ok=True)
                        with open(os.path.join(checkpoint_path, rel), 'w') as file:
                            file.write(content)
                        metadata['files'].append(rel)
                    except:
                        pass
    except:
        pass
    
    with open(os.path.join(checkpoint_path, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
    
    return metadata

def list_checkpoints(workspace: str = None) -> List[Dict]:
    """Lista checkpoints disponibles."""
    checkpoints = []
    if not os.path.exists(CHECKPOINTS_DIR):
        return checkpoints
    
    for cp_id in os.listdir(CHECKPOINTS_DIR):
        meta_path = os.path.join(CHECKPOINTS_DIR, cp_id, 'metadata.json')
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                if workspace is None or meta.get('workspace') == workspace:
                    checkpoints.append(meta)
            except:
                pass
    
    return sorted(checkpoints, key=lambda x: x.get('created_at', ''), reverse=True)

def rollback_to_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Restaura un checkpoint."""
    cp_path = os.path.join(CHECKPOINTS_DIR, checkpoint_id)
    meta_path = os.path.join(cp_path, 'metadata.json')
    
    if not os.path.exists(meta_path):
        return {'success': False, 'error': 'Checkpoint not found'}
    
    with open(meta_path) as f:
        meta = json.load(f)
    
    workspace = meta.get('workspace')
    restored = []
    
    for rel in meta.get('files', []):
        src = os.path.join(cp_path, rel)
        dst = os.path.join(workspace, rel)
        if os.path.exists(src):
            try:
                with open(src) as f:
                    content = f.read()
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, 'w') as f:
                    f.write(content)
                restored.append(rel)
            except:
                pass
    
    return {'success': True, 'restored': len(restored)}


# ============================================================
# 4. PREFERENCIAS DEL USUARIO
# ============================================================

PREFS_FILE = '/app/data/user_preferences.json'

def get_preferences() -> Dict:
    """Obtiene preferencias del usuario."""
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {'code_style': {}, 'learned': []}

def save_preference(key: str, value: Any) -> bool:
    """Guarda una preferencia."""
    prefs = get_preferences()
    prefs[key] = value
    try:
        os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
        with open(PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
        return True
    except:
        return False


# ============================================================
# 5. SUGERENCIAS DE SIGUIENTE PASO
# ============================================================

SUGGESTIONS = {
    'fix': [
        {'icon': '🧪', 'text': 'Generar tests para verificar', 'action': 'test'},
        {'icon': '🔍', 'text': 'Buscar errores similares', 'action': 'search'},
        {'icon': '🚀', 'text': 'Hacer commit', 'action': 'commit'},
    ],
    'create': [
        {'icon': '📚', 'text': 'Documentar el código', 'action': 'document'},
        {'icon': '🧪', 'text': 'Crear tests', 'action': 'test'},
    ],
    'modify': [
        {'icon': '✅', 'text': 'Verificar cambios', 'action': 'verify'},
        {'icon': '🚀', 'text': 'Hacer commit', 'action': 'commit'},
    ],
}

def get_suggestions(intention: str) -> List[Dict]:
    """Obtiene sugerencias basadas en la intención."""
    base = SUGGESTIONS.get(intention, [])
    base.append({'icon': '⏪', 'text': 'Deshacer (rollback)', 'action': 'rollback'})
    return base[:5]


# ============================================================
# 6. DIFF PREVIEW
# ============================================================

def generate_diff(original: str, modified: str, filename: str) -> Dict:
    """Genera diff preview."""
    diff = list(difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        fromfile=f'a/{filename}',
        tofile=f'b/{filename}',
        lineterm=''
    ))
    
    lines = []
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            lines.append({'type': 'add', 'content': line[1:]})
        elif line.startswith('-') and not line.startswith('---'):
            lines.append({'type': 'remove', 'content': line[1:]})
        elif line.startswith('@@'):
            lines.append({'type': 'hunk', 'content': line})
        else:
            lines.append({'type': 'context', 'content': line})
    
    return {
        'filename': filename,
        'lines': lines,
        'additions': sum(1 for l in lines if l['type'] == 'add'),
        'deletions': sum(1 for l in lines if l['type'] == 'remove')
    }


# ============================================================
# 7. PROCESADOR INTELIGENTE
# ============================================================

def process_message(message: str, workspace: str) -> Dict[str, Any]:
    """Procesa mensaje de forma inteligente."""
    intention = detect_intention(message)
    files = detect_mentioned_files(message, workspace)
    
    # Determinar si crear checkpoint
    risky = intention['intention'] in ['modify', 'delete', 'refactor']
    
    thinking_steps = [
        {'icon': '🔍', 'text': f"Analizando: {intention['intention']}"},
    ]
    
    if files:
        thinking_steps.append({
            'icon': '📂', 
            'text': f"Archivos: {', '.join([f['file'].split('/')[-1] for f in files[:3]])}"
        })
    
    if risky:
        thinking_steps.append({'icon': '💾', 'text': 'Creando checkpoint...'})
    
    thinking_steps.extend([
        {'icon': '🧠', 'text': 'Planificando...'},
        {'icon': '✏️', 'text': 'Ejecutando...'},
        {'icon': '✅', 'text': 'Verificando...'},
    ])
    
    return {
        'intention': intention,
        'files': files,
        'should_checkpoint': risky,
        'thinking_steps': thinking_steps,
        'suggestions': get_suggestions(intention['intention'])
    }


# ============================================================
# 8. CONTEXT PINNING - Archivos importantes siempre en contexto
# ============================================================

PINS_FILE = '/app/data/pinned_files.json'

def get_pinned_files(project: str = None) -> List[Dict]:
    """Obtiene archivos pinneados para un proyecto."""
    if not os.path.exists(PINS_FILE):
        return []
    try:
        with open(PINS_FILE, 'r') as f:
            all_pins = json.load(f)
        if project:
            return all_pins.get(project, [])
        return all_pins
    except:
        return []

def pin_file(file_path: str, project: str, description: str = None) -> Dict:
    """Fija un archivo para que siempre esté en contexto."""
    all_pins = {}
    if os.path.exists(PINS_FILE):
        try:
            with open(PINS_FILE, 'r') as f:
                all_pins = json.load(f)
        except:
            pass
    if project not in all_pins:
        all_pins[project] = []
    for pin in all_pins[project]:
        if pin['path'] == file_path:
            return {'success': False, 'error': 'Already pinned'}
    pin_data = {
        'path': file_path,
        'description': description or os.path.basename(file_path),
        'pinned_at': datetime.now().isoformat()
    }
    all_pins[project].append(pin_data)
    try:
        os.makedirs(os.path.dirname(PINS_FILE), exist_ok=True)
        with open(PINS_FILE, 'w') as f:
            json.dump(all_pins, f, indent=2)
        return {'success': True, 'pin': pin_data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def unpin_file(file_path: str, project: str) -> Dict:
    """Quita un archivo del contexto fijo."""
    if not os.path.exists(PINS_FILE):
        return {'success': False, 'error': 'No pins file'}
    try:
        with open(PINS_FILE, 'r') as f:
            all_pins = json.load(f)
        if project not in all_pins:
            return {'success': False, 'error': 'Project not found'}
        original_count = len(all_pins[project])
        all_pins[project] = [p for p in all_pins[project] if p['path'] != file_path]
        if len(all_pins[project]) == original_count:
            return {'success': False, 'error': 'File not pinned'}
        with open(PINS_FILE, 'w') as f:
            json.dump(all_pins, f, indent=2)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_pinned_content(project: str, workspace: str, max_chars: int = 3000) -> str:
    """Obtiene el contenido de archivos pinneados para incluir en contexto."""
    pins = get_pinned_files(project)
    if not pins:
        return ""
    contents = []
    total_chars = 0
    for pin in pins:
        file_path = pin['path']
        full_path = os.path.join(workspace, file_path) if not file_path.startswith('/') else file_path
        if not os.path.exists(full_path):
            continue
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if len(content) > 1000:
                content = content[:1000] + '... (truncado)'
            if total_chars + len(content) > max_chars:
                break
            contents.append(f"📌 {pin['path']}:" + "\n```\n" + content + "\n```")
            total_chars += len(content)
        except:
            continue
    if not contents:
        return ""
    return "<PINNED_FILES>\n" + "\n\n".join(contents) + "\n</PINNED_FILES>"

def auto_detect_important_files(workspace: str) -> List[str]:
    """Detecta automáticamente archivos importantes del proyecto."""
    important_patterns = [
        'README.md', 'config.py', 'config.json', 'settings.py',
        '.env.example', 'requirements.txt', 'package.json',
        'main.py', 'app.py', 'index.js',
    ]
    found = []
    for pattern in important_patterns:
        full_path = os.path.join(workspace, pattern)
        if os.path.exists(full_path):
            found.append(pattern)
    return found[:5]
