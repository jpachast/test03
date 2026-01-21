"""
Auto-Healing Loop - Sistema de auto-corrección de código
Similar a Devin: detecta errores, analiza, corrige y reintenta automáticamente
"""

import asyncio
import re
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback


class HealingStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    RETRYING = "retrying"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_RETRIES = "max_retries_reached"


@dataclass
class HealingAttempt:
    """Un intento de corrección"""
    attempt_number: int
    original_error: str
    error_type: str
    analysis: str
    suggested_fix: str
    fixed_code: str
    result_status: str
    result_output: str
    timestamp: str


@dataclass
class HealingSession:
    """Sesión completa de auto-healing"""
    id: str
    original_code: str
    language: str
    status: HealingStatus
    attempts: List[HealingAttempt] = field(default_factory=list)
    final_code: Optional[str] = None
    final_output: Optional[str] = None
    total_time: float = 0.0
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_code": self.original_code,
            "language": self.language,
            "status": self.status.value,
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "error_type": a.error_type,
                    "analysis": a.analysis,
                    "suggested_fix": a.suggested_fix,
                    "result_status": a.result_status,
                    "timestamp": a.timestamp
                }
                for a in self.attempts
            ],
            "final_code": self.final_code,
            "final_output": self.final_output,
            "total_time": self.total_time,
            "created_at": self.created_at,
            "attempts_count": len(self.attempts)
        }


class AutoHealer:
    """
    Sistema de Auto-Healing que corrige código automáticamente.
    
    Flujo:
    1. Ejecuta el código
    2. Si hay error, analiza el tipo de error
    3. Genera una corrección basada en patrones conocidos
    4. Reintenta con el código corregido
    5. Repite hasta éxito o máximo de intentos
    """
    
    # Patrones de errores conocidos y sus correcciones
    ERROR_PATTERNS = {
        'python': {
            # Errores de import
            r"ModuleNotFoundError: No module named '(\w+)'": {
                'type': 'missing_module',
                'fix_template': 'import subprocess; subprocess.run(["pip", "install", "{module}", "-q"])\n{code}'
            },
            r"ImportError: cannot import name '(\w+)'": {
                'type': 'import_error',
                'analysis': "El módulo existe pero no tiene el atributo '{match}'"
            },
            # Errores de sintaxis
            r"SyntaxError: invalid syntax": {
                'type': 'syntax_error',
                'analysis': "Error de sintaxis - revisar paréntesis, comillas o dos puntos"
            },
            r"IndentationError": {
                'type': 'indentation_error',
                'analysis': "Error de indentación - usar 4 espacios consistentemente"
            },
            # Errores de nombre
            r"NameError: name '(\w+)' is not defined": {
                'type': 'name_error',
                'analysis': "Variable '{match}' no definida - verificar declaración"
            },
            # Errores de tipo
            r"TypeError: (.+)": {
                'type': 'type_error',
                'analysis': "Error de tipo: {match}"
            },
            # Errores de valor
            r"ValueError: (.+)": {
                'type': 'value_error',
                'analysis': "Error de valor: {match}"
            },
            # Errores de archivo
            r"FileNotFoundError: \[Errno 2\] No such file or directory: '(.+)'": {
                'type': 'file_not_found',
                'analysis': "Archivo no encontrado: {match}"
            },
            # Errores de clave
            r"KeyError: '?(\w+)'?": {
                'type': 'key_error',
                'analysis': "Clave '{match}' no existe en el diccionario"
            },
            # Errores de índice
            r"IndexError: (.+)": {
                'type': 'index_error',
                'analysis': "Error de índice: {match}"
            },
            # División por cero
            r"ZeroDivisionError": {
                'type': 'zero_division',
                'analysis': "División por cero - añadir validación"
            },
            # Errores de atributo
            r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
                'type': 'attribute_error',
                'analysis': "El objeto '{match}' no tiene el atributo especificado"
            }
        },
        'javascript': {
            r"ReferenceError: (\w+) is not defined": {
                'type': 'reference_error',
                'analysis': "Variable '{match}' no definida"
            },
            r"SyntaxError: (.+)": {
                'type': 'syntax_error',
                'analysis': "Error de sintaxis: {match}"
            },
            r"TypeError: (.+)": {
                'type': 'type_error',
                'analysis': "Error de tipo: {match}"
            },
            r"Cannot find module '(.+)'": {
                'type': 'missing_module',
                'fix_template': 'const {{module}} = require("{module}") || console.log("Módulo no disponible");\n{code}'
            }
        },
        'bash': {
            r"(\w+): command not found": {
                'type': 'command_not_found',
                'analysis': "Comando '{match}' no encontrado - verificar instalación o PATH"
            },
            r"Permission denied": {
                'type': 'permission_denied',
                'analysis': "Permiso denegado - puede necesitar sudo o chmod"
            },
            r"No such file or directory": {
                'type': 'file_not_found',
                'analysis': "Archivo o directorio no existe"
            }
        }
    }
    
    # Correcciones automáticas conocidas
    AUTO_FIXES = {
        'python': {
            'missing_module': lambda code, module: f"# Auto-fix: instalando módulo {module}\nimport subprocess\nsubprocess.run(['pip', 'install', '{module}', '-q'], capture_output=True)\n\n{code}",
            'indentation_error': lambda code, _: code.replace('\t', '    '),
            'zero_division': lambda code, _: code.replace('/ ', '/ (lambda x: x if x != 0 else 1)(') + ')',
        },
        'javascript': {
            'missing_module': lambda code, module: f"// Auto-fix: manejando módulo faltante\nlet {module};\ntry {{ {module} = require('{module}'); }} catch(e) {{ console.log('Módulo {module} no disponible'); }}\n\n{code}",
        }
    }
    
    def __init__(self, sandbox, llm_fixer: Callable = None, max_retries: int = 5):
        """
        Inicializa el auto-healer.
        
        Args:
            sandbox: Instancia del CodeSandbox para ejecutar código
            llm_fixer: Función opcional que usa LLM para corregir (recibe code, error, retorna fixed_code)
            max_retries: Máximo número de reintentos
        """
        self.sandbox = sandbox
        self.llm_fixer = llm_fixer
        self.max_retries = max_retries
        self.sessions: Dict[str, HealingSession] = {}
    
    def analyze_error(self, language: str, stderr: str) -> Dict[str, Any]:
        """
        Analiza un error y determina su tipo y posible corrección.
        """
        patterns = self.ERROR_PATTERNS.get(language, {})
        
        for pattern, info in patterns.items():
            match = re.search(pattern, stderr)
            if match:
                groups = match.groups()
                first_match = groups[0] if groups else ''
                
                analysis = info.get('analysis', f"Error detectado: {info['type']}")
                if '{match}' in analysis:
                    analysis = analysis.format(match=first_match)
                
                return {
                    'type': info['type'],
                    'pattern': pattern,
                    'match': first_match,
                    'analysis': analysis,
                    'has_auto_fix': info['type'] in self.AUTO_FIXES.get(language, {})
                }
        
        # Error no reconocido
        return {
            'type': 'unknown',
            'pattern': None,
            'match': None,
            'analysis': f"Error no reconocido: {stderr[:200]}",
            'has_auto_fix': False
        }
    
    def apply_auto_fix(self, language: str, code: str, error_type: str, match: str) -> Optional[str]:
        """
        Aplica una corrección automática si está disponible.
        """
        fixes = self.AUTO_FIXES.get(language, {})
        fix_func = fixes.get(error_type)
        
        if fix_func:
            try:
                return fix_func(code, match)
            except:
                return None
        return None
    
    async def heal_code(
        self,
        code: str,
        language: str = None,
        timeout: int = None,
        session_id: str = None
    ) -> HealingSession:
        """
        Ejecuta código con auto-healing.
        
        Intenta ejecutar el código y si falla, analiza el error,
        intenta corregirlo y reintenta hasta éxito o máximo de intentos.
        """
        import uuid
        import time
        
        session_id = session_id or str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Auto-detectar lenguaje si no se especifica
        if not language:
            language = self.sandbox.detect_language(code)
        
        session = HealingSession(
            id=session_id,
            original_code=code,
            language=language,
            status=HealingStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        current_code = code
        
        for attempt_num in range(1, self.max_retries + 1):
            session.status = HealingStatus.RETRYING if attempt_num > 1 else HealingStatus.PENDING
            
            # Ejecutar código
            result = await self.sandbox.execute_async(
                current_code, 
                language, 
                timeout
            )
            
            # Si tuvo éxito, terminamos
            if result.status.value == 'success':
                session.status = HealingStatus.SUCCESS
                session.final_code = current_code
                session.final_output = result.stdout
                break
            
            # Si llegamos al máximo de intentos
            if attempt_num >= self.max_retries:
                session.status = HealingStatus.MAX_RETRIES
                session.final_code = current_code
                session.final_output = result.stderr
                break
            
            # Analizar el error
            session.status = HealingStatus.ANALYZING
            error_info = self.analyze_error(language, result.stderr)
            
            # Intentar corrección automática
            session.status = HealingStatus.FIXING
            fixed_code = None
            suggested_fix = ""
            
            # Primero intentar auto-fix basado en patrones
            if error_info['has_auto_fix']:
                fixed_code = self.apply_auto_fix(
                    language, 
                    current_code, 
                    error_info['type'],
                    error_info['match']
                )
                suggested_fix = f"Auto-fix aplicado para {error_info['type']}"
            
            # Si no hay auto-fix y tenemos LLM, usarlo
            if not fixed_code and self.llm_fixer:
                try:
                    fixed_code = await self.llm_fixer(
                        current_code, 
                        result.stderr,
                        language
                    )
                    suggested_fix = "Corrección sugerida por LLM"
                except:
                    pass
            
            # Si no pudimos corregir, registrar el intento y terminar
            if not fixed_code:
                attempt = HealingAttempt(
                    attempt_number=attempt_num,
                    original_error=result.stderr[:500],
                    error_type=error_info['type'],
                    analysis=error_info['analysis'],
                    suggested_fix="No se encontró corrección automática",
                    fixed_code="",
                    result_status="failed",
                    result_output=result.stderr,
                    timestamp=datetime.now().isoformat()
                )
                session.attempts.append(attempt)
                session.status = HealingStatus.FAILED
                session.final_output = result.stderr
                break
            
            # Registrar el intento
            attempt = HealingAttempt(
                attempt_number=attempt_num,
                original_error=result.stderr[:500],
                error_type=error_info['type'],
                analysis=error_info['analysis'],
                suggested_fix=suggested_fix,
                fixed_code=fixed_code[:500] + "..." if len(fixed_code) > 500 else fixed_code,
                result_status="retrying",
                result_output="",
                timestamp=datetime.now().isoformat()
            )
            session.attempts.append(attempt)
            
            # Usar el código corregido para el siguiente intento
            current_code = fixed_code
        
        session.total_time = round(time.time() - start_time, 3)
        self.sessions[session_id] = session
        
        return session
    
    def heal_code_sync(
        self,
        code: str,
        language: str = None,
        timeout: int = None
    ) -> HealingSession:
        """Versión síncrona de heal_code"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.heal_code(code, language, timeout)
            )
        finally:
            loop.close()
    
    def get_session(self, session_id: str) -> Optional[HealingSession]:
        """Obtiene una sesión por ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self, limit: int = 20) -> List[HealingSession]:
        """Lista las últimas sesiones"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return sessions[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del auto-healer"""
        total = len(self.sessions)
        if total == 0:
            return {"total_sessions": 0}
        
        success = sum(1 for s in self.sessions.values() if s.status == HealingStatus.SUCCESS)
        failed = sum(1 for s in self.sessions.values() if s.status == HealingStatus.FAILED)
        max_retries = sum(1 for s in self.sessions.values() if s.status == HealingStatus.MAX_RETRIES)
        
        total_attempts = sum(len(s.attempts) for s in self.sessions.values())
        avg_attempts = total_attempts / total if total > 0 else 0
        
        return {
            "total_sessions": total,
            "success_count": success,
            "failed_count": failed,
            "max_retries_count": max_retries,
            "success_rate": round(success / total * 100, 1) if total > 0 else 0,
            "average_attempts": round(avg_attempts, 2),
            "total_healing_attempts": total_attempts
        }


# Instancia global
_healer_instance: Optional[AutoHealer] = None


def get_auto_healer(sandbox=None) -> AutoHealer:
    """Obtiene la instancia global del auto-healer"""
    global _healer_instance
    if _healer_instance is None:
        if sandbox is None:
            from core.sandbox import get_sandbox
            sandbox = get_sandbox()
        _healer_instance = AutoHealer(sandbox)
    return _healer_instance
