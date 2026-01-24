"""
Auto-Fix Integration para Chat
Detecta errores en respuestas y aplica correcciones automáticamente
"""

import re
import asyncio
from typing import Optional, Dict, Any, Tuple

# Patrones de error comunes
ERROR_PATTERNS = [
    (r"(SyntaxError|IndentationError|TabError):\s*(.+)", "syntax"),
    (r"(NameError|UnboundLocalError):\s*name\s+'([^']+)'\s+is not defined", "name"),
    (r"(TypeError):\s*(.+)", "type"),
    (r"(ZeroDivisionError):\s*(.+)", "zero_division"),
    (r"(IndexError|KeyError):\s*(.+)", "index"),
    (r"(ImportError|ModuleNotFoundError):\s*(.+)", "import"),
    (r"(ValueError):\s*(.+)", "value"),
    (r"(AttributeError):\s*(.+)", "attribute"),
    (r"(FileNotFoundError):\s*(.+)", "file"),
    (r"(ReferenceError):\s*(.+)", "js_error"),
    (r"Traceback \(most recent call last\)", "traceback"),
    (r"Error:\s*(.+)", "generic_error"),
]


def detect_error_in_output(output: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Detecta si hay un error en el output de ejecucion."""
    if not output:
        return False, None, None
    
    for pattern, error_type in ERROR_PATTERNS:
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if match:
            return True, error_type, match.group(0)
    
    return False, None, None


def extract_code_from_message(message: str) -> Optional[str]:
    """Extrae codigo de un mensaje del usuario."""
    code_blocks = re.findall(r'```(?:python|py)?\n([\s\S]*?)```', message)
    if code_blocks:
        return code_blocks[0].strip()
    return None


async def try_auto_fix(code: str, error_output: str, language: str = "python") -> Dict[str, Any]:
    """Intenta corregir el codigo automaticamente usando Auto-Fix."""
    try:
        from core.auto_fix import get_auto_fixer
        
        fixer = get_auto_fixer()
        result = await fixer.auto_fix(
            code=code,
            language=language,
            timeout=30,
            apply_fixes=True,
            verify_fixes=True
        )
        
        return {
            "success": result.status.value in ['success', 'partial_success'],
            "original_code": result.original_code,
            "fixed_code": result.final_code,
            "code_changed": result.original_code != result.final_code,
            "fixes_applied": result.total_fixes_applied,
            "iterations": len(result.iterations),
            "final_output": result.final_output,
            "verified": result.verified,
            "error_message": result.error_message if result.error_message else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_autofix_result(result: Dict[str, Any]) -> str:
    """Formatea el resultado del auto-fix para mostrarlo en el chat."""
    if not result.get("success") or not result.get("code_changed"):
        return ""
    
    lines = [
        "\n---",
        "### 🔧 Auto-Fix Aplicado",
        "",
        f"✅ **{result.get('fixes_applied', 0)} correccion(es) aplicada(s)**",
    ]
    
    if result.get("verified"):
        lines.append("✅ **Codigo verificado - ejecuta correctamente**")
    
    lines.extend([
        "",
        "**Codigo corregido:**",
        "```python",
        result.get("fixed_code", ""),
        "```",
    ])
    
    if result.get("final_output"):
        lines.extend([
            "",
            "**Resultado de ejecucion:**",
            "```",
            result.get("final_output", "")[:500],
            "```",
        ])
    
    lines.append("---")
    return "\n".join(lines)


class ChatAutoFixIntegration:
    """Integracion de Auto-Fix con el sistema de chat."""
    
    def __init__(self):
        self.enabled = True
        self.auto_apply = True
        self.last_code = None
        self.last_error = None
    
    async def process_terminal_output(self, output: str, code_context: str = None) -> Optional[str]:
        """Procesa output de terminal buscando errores y aplica auto-fix."""
        if not self.enabled:
            return None
        
        has_error, error_type, error_msg = detect_error_in_output(output)
        if not has_error:
            return None
        
        self.last_error = error_msg
        code = code_context or self.last_code
        
        if code and self.auto_apply:
            result = await try_auto_fix(code, output)
            if result.get("success") and result.get("code_changed"):
                return format_autofix_result(result)
        
        return None
    
    def set_code_context(self, code: str):
        self.last_code = code
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False


_chat_autofix = None

def get_chat_autofix() -> ChatAutoFixIntegration:
    global _chat_autofix
    if _chat_autofix is None:
        _chat_autofix = ChatAutoFixIntegration()
    return _chat_autofix
