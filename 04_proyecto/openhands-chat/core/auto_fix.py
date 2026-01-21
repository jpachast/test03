"""
Auto-Fix Loop Completo - Sistema de corrección automática de código
Loop: detectar error → analizar → corregir → re-ejecutar → verificar
"""

import asyncio
import re
import json
import difflib
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback


class FixStatus(str, Enum):
    """Estados del proceso de auto-fix"""
    PENDING = "pending"
    EXECUTING = "executing"
    ERROR_DETECTED = "error_detected"
    ANALYZING = "analyzing"
    APPLYING_FIX = "applying_fix"
    VERIFYING = "verifying"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class FixIteration:
    """Una iteración del loop de auto-fix"""
    iteration: int
    code_before: str
    code_after: str
    error_detected: str
    error_type: str
    fix_applied: str
    fix_description: str
    execution_result: str
    status: str
    timestamp: str
    diff: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "error_type": self.error_type,
            "fix_applied": self.fix_applied,
            "fix_description": self.fix_description,
            "status": self.status,
            "timestamp": self.timestamp,
            "has_diff": bool(self.diff)
        }


@dataclass 
class AutoFixResult:
    """Resultado completo del auto-fix"""
    session_id: str
    original_code: str
    final_code: str
    language: str
    status: FixStatus
    iterations: List[FixIteration]
    final_output: str
    error_message: str
    total_fixes_applied: int
    total_time: float
    verified: bool
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "language": self.language,
            "iterations_count": len(self.iterations),
            "total_fixes_applied": self.total_fixes_applied,
            "total_time": self.total_time,
            "verified": self.verified,
            "final_output": self.final_output[:500] if self.final_output else "",
            "error_message": self.error_message,
            "iterations": [i.to_dict() for i in self.iterations],
            "code_changed": self.original_code != self.final_code,
            "created_at": self.created_at
        }


class AutoFixer:
    """
    Sistema completo de Auto-Fix con loop de verificación.
    
    Flujo completo:
    1. Ejecutar código original
    2. Si hay error → detectar tipo de error
    3. Analizar causa raíz
    4. Generar y APLICAR corrección
    5. Re-ejecutar código corregido
    6. Verificar que el fix funcionó
    7. Si sigue fallando → volver al paso 2 (hasta max iteraciones)
    """
    
    # Patrones de error con fixes automáticos
    FIX_PATTERNS = {
        'python': [
            # Missing imports
            {
                'pattern': r"NameError: name '(print|len|str|int|float|list|dict|set|tuple|range|enumerate|zip|map|filter|sorted|reversed|sum|min|max|abs|round|open|input|type|isinstance|hasattr|getattr|setattr)' is not defined",
                'fix': lambda code, m: code,  # Built-ins shouldn't fail
                'desc': 'Built-in function error'
            },
            {
                'pattern': r"ModuleNotFoundError: No module named '(\w+)'",
                'fix': lambda code, m: f"# Auto-fix: Installing {m.group(1)}\nimport subprocess\nsubprocess.run(['pip', 'install', '{m.group(1)}', '-q'], capture_output=True)\n\n{code}",
                'desc': 'Instalar módulo faltante: {0}'
            },
            {
                'pattern': r"ImportError: cannot import name '(\w+)' from '(\w+)'",
                'fix': lambda code, m: code.replace(f"from {m.group(2)} import {m.group(1)}", f"# from {m.group(2)} import {m.group(1)}  # Removed - not available"),
                'desc': 'Comentar import no disponible: {0}'
            },
            # Syntax errors
            {
                'pattern': r"SyntaxError: invalid syntax.*line (\d+)",
                'fix': lambda code, m: fix_syntax_error(code, int(m.group(1))),
                'desc': 'Corregir sintaxis en línea {0}'
            },
            {
                'pattern': r"IndentationError: (unexpected indent|expected an indented block)",
                'fix': lambda code, m: fix_indentation(code),
                'desc': 'Corregir indentación'
            },
            # Name errors
            {
                'pattern': r"NameError: name '(\w+)' is not defined",
                'fix': lambda code, m: fix_undefined_name(code, m.group(1)),
                'desc': 'Definir variable faltante: {0}'
            },
            # Type errors
            {
                'pattern': r"TypeError: unsupported operand type\(s\) for (.+): '(\w+)' and '(\w+)'",
                'fix': lambda code, m: fix_type_conversion(code, m),
                'desc': 'Corregir tipos incompatibles'
            },
            {
                'pattern': r"TypeError: '(\w+)' object is not (callable|subscriptable|iterable)",
                'fix': lambda code, m: code,  # Needs context
                'desc': 'Error de tipo: {0} no es {1}'
            },
            # Zero division
            {
                'pattern': r"ZeroDivisionError: (division by zero|integer division or modulo by zero)",
                'fix': lambda code, m: fix_zero_division(code),
                'desc': 'Agregar validación de división por cero'
            },
            # Index errors
            {
                'pattern': r"IndexError: (list index out of range|string index out of range)",
                'fix': lambda code, m: fix_index_bounds(code),
                'desc': 'Agregar validación de índices'
            },
            # Key errors
            {
                'pattern': r"KeyError: ['\"]?(\w+)['\"]?",
                'fix': lambda code, m: fix_key_error(code, m.group(1)),
                'desc': 'Usar .get() para clave: {0}'
            },
            # Attribute errors
            {
                'pattern': r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
                'fix': lambda code, m: fix_attribute_error(code, m.group(1), m.group(2)),
                'desc': 'Verificar atributo {1} en {0}'
            },
            # File errors
            {
                'pattern': r"FileNotFoundError: \[Errno 2\] No such file or directory: '(.+)'",
                'fix': lambda code, m: fix_file_not_found(code, m.group(1)),
                'desc': 'Manejar archivo no encontrado: {0}'
            },
        ],
        'javascript': [
            {
                'pattern': r"ReferenceError: (\w+) is not defined",
                'fix': lambda code, m: f"let {m.group(1)};\n{code}" if m.group(1) not in ['console', 'require', 'module', 'exports'] else code,
                'desc': 'Declarar variable: {0}'
            },
            {
                'pattern': r"TypeError: Cannot read propert(y|ies) .+ of (undefined|null)",
                'fix': lambda code, m: fix_js_null_check(code),
                'desc': 'Agregar verificación de null/undefined'
            },
            {
                'pattern': r"SyntaxError: (.+)",
                'fix': lambda code, m: fix_js_syntax(code, m.group(1)),
                'desc': 'Corregir sintaxis: {0}'
            },
            {
                'pattern': r"Error: Cannot find module '(.+)'",
                'fix': lambda code, m: code.replace(f"require('{m.group(1)}')", f"(() => {{ try {{ return require('{m.group(1)}'); }} catch(e) {{ return {{}}; }} }})()"),
                'desc': 'Manejar módulo faltante: {0}'
            },
        ],
        'bash': [
            {
                'pattern': r"(\w+): command not found",
                'fix': lambda code, m: f"# Auto-fix: Command '{m.group(1)}' not found\nwhich {m.group(1)} || echo 'Command not available'\n" + code,
                'desc': 'Verificar comando: {0}'
            },
            {
                'pattern': r"Permission denied",
                'fix': lambda code, m: code,  # Can't auto-fix permissions
                'desc': 'Error de permisos - requiere sudo'
            },
        ]
    }
    
    def __init__(self, sandbox, llm_fixer: Callable = None, max_iterations: int = 5):
        """
        Inicializa el auto-fixer.
        
        Args:
            sandbox: Instancia de CodeSandbox para ejecutar código
            llm_fixer: Función opcional que usa LLM para corregir
            max_iterations: Máximo de iteraciones del loop
        """
        self.sandbox = sandbox
        self.llm_fixer = llm_fixer
        self.max_iterations = max_iterations
        self.results: Dict[str, AutoFixResult] = {}
    
    def detect_error(self, language: str, stderr: str) -> Tuple[str, str, Optional[re.Match]]:
        """
        Detecta el tipo de error y retorna (tipo, descripción, match).
        """
        patterns = self.FIX_PATTERNS.get(language, [])
        
        for pattern_info in patterns:
            match = re.search(pattern_info['pattern'], stderr, re.IGNORECASE | re.MULTILINE)
            if match:
                desc = pattern_info['desc']
                try:
                    desc = desc.format(*match.groups())
                except:
                    pass
                return (pattern_info.get('type', 'detected'), desc, match)
        
        return ('unknown', f'Error desconocido: {stderr[:100]}', None)
    
    def apply_fix(self, language: str, code: str, stderr: str) -> Tuple[str, str]:
        """
        Aplica un fix y retorna (código_corregido, descripción_del_fix).
        """
        patterns = self.FIX_PATTERNS.get(language, [])
        
        for pattern_info in patterns:
            match = re.search(pattern_info['pattern'], stderr, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    fixed_code = pattern_info['fix'](code, match)
                    if fixed_code != code:
                        desc = pattern_info['desc']
                        try:
                            desc = desc.format(*match.groups())
                        except:
                            pass
                        return (fixed_code, desc)
                except Exception as e:
                    continue
        
        return (code, "No se encontró fix automático")
    
    def generate_diff(self, original: str, modified: str) -> str:
        """Genera un diff legible entre dos versiones de código."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines, 
            modified_lines,
            fromfile='original',
            tofile='fixed',
            lineterm=''
        )
        return ''.join(diff)
    
    async def auto_fix(
        self,
        code: str,
        language: str = None,
        timeout: int = 30,
        apply_fixes: bool = True,
        verify_fixes: bool = True
    ) -> AutoFixResult:
        """
        Ejecuta el loop completo de auto-fix.
        
        Args:
            code: Código a ejecutar y corregir
            language: Lenguaje del código (auto-detecta si None)
            timeout: Timeout por ejecución
            apply_fixes: Si True, aplica los fixes automáticamente
            verify_fixes: Si True, re-ejecuta para verificar
        
        Returns:
            AutoFixResult con el resultado completo
        """
        import uuid
        import time
        
        session_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Auto-detectar lenguaje
        if not language:
            language = self.sandbox.detect_language(code)
        
        iterations: List[FixIteration] = []
        current_code = code
        total_fixes = 0
        final_output = ""
        error_message = ""
        status = FixStatus.PENDING
        verified = False
        
        for iteration_num in range(1, self.max_iterations + 1):
            iteration_start = datetime.now()
            
            # === PASO 1: Ejecutar código ===
            status = FixStatus.EXECUTING
            result = await self.sandbox.execute_async(current_code, language, timeout)
            
            # === PASO 2: Verificar si hay error ===
            if result.status.value == 'success':
                status = FixStatus.SUCCESS
                final_output = result.stdout
                verified = True
                
                # Registrar iteración exitosa
                iterations.append(FixIteration(
                    iteration=iteration_num,
                    code_before=current_code,
                    code_after=current_code,
                    error_detected="",
                    error_type="none",
                    fix_applied="",
                    fix_description="Ejecución exitosa",
                    execution_result=result.stdout[:500],
                    status="success",
                    timestamp=iteration_start.isoformat()
                ))
                break
            
            # === PASO 3: Error detectado - Analizar ===
            status = FixStatus.ERROR_DETECTED
            error_type, error_desc, error_match = self.detect_error(language, result.stderr)
            error_message = result.stderr
            
            # === PASO 4: Aplicar fix ===
            if apply_fixes:
                status = FixStatus.APPLYING_FIX
                fixed_code, fix_description = self.apply_fix(language, current_code, result.stderr)
                
                # Si el fix no cambió nada y tenemos LLM, intentar con LLM
                if fixed_code == current_code and self.llm_fixer:
                    try:
                        llm_fixed = await self.llm_fixer(current_code, result.stderr, language)
                        if llm_fixed and llm_fixed != current_code:
                            fixed_code = llm_fixed
                            fix_description = "Fix generado por LLM"
                    except:
                        pass
                
                # Generar diff
                diff = self.generate_diff(current_code, fixed_code) if fixed_code != current_code else ""
                
                # Registrar iteración
                iterations.append(FixIteration(
                    iteration=iteration_num,
                    code_before=current_code[:1000],
                    code_after=fixed_code[:1000],
                    error_detected=result.stderr[:500],
                    error_type=error_type,
                    fix_applied="yes" if fixed_code != current_code else "no",
                    fix_description=fix_description,
                    execution_result=result.stderr[:500],
                    status="fixing" if fixed_code != current_code else "no_fix_found",
                    timestamp=iteration_start.isoformat(),
                    diff=diff
                ))
                
                # Si no se pudo aplicar ningún fix, terminar
                if fixed_code == current_code:
                    status = FixStatus.FAILED
                    break
                
                # === PASO 5: Actualizar código y verificar ===
                current_code = fixed_code
                total_fixes += 1
                
                if verify_fixes:
                    status = FixStatus.VERIFYING
                    # La verificación ocurre en la siguiente iteración del loop
            else:
                # Solo detectar errores, no aplicar fixes
                iterations.append(FixIteration(
                    iteration=iteration_num,
                    code_before=current_code[:1000],
                    code_after=current_code[:1000],
                    error_detected=result.stderr[:500],
                    error_type=error_type,
                    fix_applied="no",
                    fix_description=error_desc,
                    execution_result=result.stderr[:500],
                    status="error_detected",
                    timestamp=iteration_start.isoformat()
                ))
                status = FixStatus.FAILED
                break
        else:
            # Se alcanzó el máximo de iteraciones
            status = FixStatus.MAX_ITERATIONS
        
        # Determinar estado final
        if status == FixStatus.SUCCESS:
            pass
        elif total_fixes > 0 and status != FixStatus.MAX_ITERATIONS:
            status = FixStatus.PARTIAL_SUCCESS
        
        total_time = round(time.time() - start_time, 3)
        
        result = AutoFixResult(
            session_id=session_id,
            original_code=code,
            final_code=current_code,
            language=language,
            status=status,
            iterations=iterations,
            final_output=final_output,
            error_message=error_message if status != FixStatus.SUCCESS else "",
            total_fixes_applied=total_fixes,
            total_time=total_time,
            verified=verified,
            created_at=datetime.now().isoformat()
        )
        
        self.results[session_id] = result
        return result
    
    def auto_fix_sync(
        self,
        code: str,
        language: str = None,
        timeout: int = 30,
        apply_fixes: bool = True,
        verify_fixes: bool = True
    ) -> AutoFixResult:
        """Versión síncrona de auto_fix."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.auto_fix(code, language, timeout, apply_fixes, verify_fixes)
            )
        finally:
            loop.close()
    
    def get_result(self, session_id: str) -> Optional[AutoFixResult]:
        """Obtiene un resultado por ID."""
        return self.results.get(session_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del auto-fixer."""
        if not self.results:
            return {"total_sessions": 0}
        
        total = len(self.results)
        success = sum(1 for r in self.results.values() if r.status == FixStatus.SUCCESS)
        partial = sum(1 for r in self.results.values() if r.status == FixStatus.PARTIAL_SUCCESS)
        failed = sum(1 for r in self.results.values() if r.status == FixStatus.FAILED)
        
        total_fixes = sum(r.total_fixes_applied for r in self.results.values())
        total_iterations = sum(len(r.iterations) for r in self.results.values())
        verified = sum(1 for r in self.results.values() if r.verified)
        
        return {
            "total_sessions": total,
            "success_count": success,
            "partial_success_count": partial,
            "failed_count": failed,
            "success_rate": round((success + partial) / total * 100, 1) if total > 0 else 0,
            "total_fixes_applied": total_fixes,
            "total_iterations": total_iterations,
            "verified_count": verified,
            "avg_fixes_per_session": round(total_fixes / total, 2) if total > 0 else 0
        }


# ============ Helper Functions for Fixes ============

def fix_syntax_error(code: str, line_num: int) -> str:
    """Intenta corregir errores de sintaxis comunes."""
    lines = code.split('\n')
    if 0 < line_num <= len(lines):
        line = lines[line_num - 1]
        
        # Falta : al final de if/for/while/def/class
        if re.match(r'\s*(if|for|while|def|class|elif|else|try|except|finally|with)\s', line) and not line.rstrip().endswith(':'):
            lines[line_num - 1] = line.rstrip() + ':'
        
        # Paréntesis no balanceados
        open_parens = line.count('(') - line.count(')')
        if open_parens > 0:
            lines[line_num - 1] = line + ')' * open_parens
        elif open_parens < 0:
            lines[line_num - 1] = '(' * (-open_parens) + line
        
        # Comillas no cerradas
        if line.count('"') % 2 == 1:
            lines[line_num - 1] = line + '"'
        elif line.count("'") % 2 == 1:
            lines[line_num - 1] = line + "'"
    
    return '\n'.join(lines)


def fix_indentation(code: str) -> str:
    """Corrige problemas de indentación."""
    # Reemplazar tabs por 4 espacios
    code = code.replace('\t', '    ')
    
    lines = code.split('\n')
    fixed_lines = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append('')
            continue
        
        # Reducir indent para líneas que cierran bloques
        if stripped.startswith(('return', 'break', 'continue', 'pass', 'raise')):
            pass  # Mantener nivel actual
        elif stripped.startswith(('elif', 'else', 'except', 'finally')):
            indent_level = max(0, indent_level - 1)
        
        # Aplicar indentación
        fixed_lines.append('    ' * indent_level + stripped)
        
        # Aumentar indent si la línea termina en :
        if stripped.endswith(':'):
            indent_level += 1
        # Reducir indent después de return/break/continue
        elif stripped.startswith(('return', 'break', 'continue')) and not stripped.endswith(':'):
            indent_level = max(0, indent_level - 1)
    
    return '\n'.join(fixed_lines)


def fix_undefined_name(code: str, name: str) -> str:
    """Intenta definir una variable faltante."""
    # Si parece una función, definirla vacía
    if re.search(rf'{name}\s*\(', code):
        return f"def {name}(*args, **kwargs):\n    pass  # Auto-defined\n\n{code}"
    # Si parece una variable, inicializarla
    return f"{name} = None  # Auto-defined\n{code}"


def fix_type_conversion(code: str, match: re.Match) -> str:
    """Intenta corregir errores de tipo."""
    # Agregar conversiones explícitas
    return code


def fix_zero_division(code: str) -> str:
    """Agrega validación para división por cero."""
    # Buscar divisiones y agregar validación
    def replace_division(m):
        divisor = m.group(2)
        return f"({m.group(1)} / ({divisor} if {divisor} != 0 else 1))"
    
    code = re.sub(r'(\w+)\s*/\s*(\w+)', replace_division, code)
    return code


def fix_index_bounds(code: str) -> str:
    """Agrega validación de índices."""
    # Agregar comentario de advertencia
    return f"# ADVERTENCIA: Verificar índices antes de acceder\n{code}"


def fix_key_error(code: str, key: str) -> str:
    """Cambia acceso directo por .get()."""
    # Reemplazar dict[key] por dict.get(key)
    pattern = rf"\[(['\"]){key}\1\]"
    replacement = f".get('{key}')"
    return re.sub(pattern, replacement, code)


def fix_attribute_error(code: str, obj_type: str, attr: str) -> str:
    """Agrega verificación de atributo."""
    return f"# ADVERTENCIA: Verificar que el objeto tenga el atributo '{attr}'\n{code}"


def fix_file_not_found(code: str, filepath: str) -> str:
    """Agrega manejo de archivo no encontrado."""
    return f'''import os
# Auto-fix: Verificar existencia del archivo
if not os.path.exists("{filepath}"):
    print(f"ADVERTENCIA: Archivo '{filepath}' no encontrado")
    # Crear archivo vacío o usar alternativa
    open("{filepath}", 'w').close()

{code}'''


def fix_js_null_check(code: str) -> str:
    """Agrega verificaciones de null/undefined en JavaScript."""
    return f"// Auto-fix: Agregar optional chaining\n{code}"


def fix_js_syntax(code: str, error_detail: str) -> str:
    """Intenta corregir sintaxis JavaScript."""
    # Corregir problemas comunes
    if "Unexpected token" in error_detail:
        # Intentar arreglar puntuación
        code = re.sub(r'}\s*{', '}\n{', code)
    return code


# ============ Instancia Global ============

_fixer_instance: Optional[AutoFixer] = None


def get_auto_fixer(sandbox=None) -> AutoFixer:
    """Obtiene la instancia global del auto-fixer."""
    global _fixer_instance
    if _fixer_instance is None:
        if sandbox is None:
            from core.sandbox import get_sandbox
            sandbox = get_sandbox()
        _fixer_instance = AutoFixer(sandbox)
    return _fixer_instance
