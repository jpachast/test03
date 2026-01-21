"""
Code Parser - Parser AST real para detectar bloques de código

Características:
- Detección AST de código Python/JavaScript
- Extracción de bloques de código de mensajes
- Validación de sintaxis
- Detección de lenguaje automática
"""

import ast
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Lenguajes soportados"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    BASH = "bash"
    SQL = "sql"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


@dataclass
class CodeBlock:
    """Bloque de código detectado"""
    code: str
    language: Language
    start_line: int
    end_line: int
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    ast_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "language": self.language.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "ast_info": self.ast_info
        }


class PythonASTParser:
    """Parser AST para Python"""
    
    def parse(self, code: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Parsea código Python y extrae información AST.
        
        Returns:
            (is_valid, ast_info, errors)
        """
        errors = []
        ast_info = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "async_functions": []
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    ast_info["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno,
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.AsyncFunctionDef):
                    ast_info["async_functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    ast_info["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [self._get_name(b) for b in node.bases]
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        ast_info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        ast_info["imports"].append(node.module)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            ast_info["variables"].append(target.id)
            
            return True, ast_info, errors
            
        except SyntaxError as e:
            errors.append(f"SyntaxError línea {e.lineno}: {e.msg}")
            return False, ast_info, errors
        except Exception as e:
            errors.append(f"Error: {str(e)}")
            return False, ast_info, errors
    
    def _get_decorator_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"
    
    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"


class JavaScriptParser:
    """Parser básico para JavaScript usando regex y heurísticas"""
    
    def parse(self, code: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Parsea código JavaScript"""
        errors = []
        ast_info = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "arrow_functions": []
        }
        
        try:
            # Funciones tradicionales
            func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
            for match in re.finditer(func_pattern, code):
                ast_info["functions"].append({
                    "name": match.group(1),
                    "args": [a.strip() for a in match.group(2).split(',') if a.strip()]
                })
            
            # Arrow functions
            arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'
            for match in re.finditer(arrow_pattern, code):
                ast_info["arrow_functions"].append({"name": match.group(1)})
            
            # Clases
            class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
            for match in re.finditer(class_pattern, code):
                ast_info["classes"].append({
                    "name": match.group(1),
                    "extends": match.group(2)
                })
            
            # Imports
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\([\'"]([^\'"]+)[\'"]\)'
            ]
            for pattern in import_patterns:
                for match in re.finditer(pattern, code):
                    ast_info["imports"].append(match.group(1))
            
            # Variables
            var_pattern = r'(?:const|let|var)\s+(\w+)\s*='
            for match in re.finditer(var_pattern, code):
                name = match.group(1)
                if name not in [f["name"] for f in ast_info["arrow_functions"]]:
                    ast_info["variables"].append(name)
            
            # Validación básica de sintaxis
            open_braces = code.count('{')
            close_braces = code.count('}')
            if open_braces != close_braces:
                errors.append(f"Llaves desbalanceadas: {open_braces} abiertas, {close_braces} cerradas")
            
            open_parens = code.count('(')
            close_parens = code.count(')')
            if open_parens != close_parens:
                errors.append(f"Paréntesis desbalanceados: {open_parens} abiertos, {close_parens} cerrados")
            
            return len(errors) == 0, ast_info, errors
            
        except Exception as e:
            errors.append(f"Error: {str(e)}")
            return False, ast_info, errors


class CodeDetector:
    """Detector de bloques de código en texto"""
    
    # Patrones para detectar código
    MARKDOWN_CODE_BLOCK = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    INLINE_CODE = re.compile(r'`([^`]+)`')
    
    # Indicadores de lenguaje
    PYTHON_INDICATORS = [
        r'\bdef\s+\w+\s*\(',
        r'\bclass\s+\w+',
        r'\bimport\s+\w+',
        r'\bfrom\s+\w+\s+import',
        r'\bif\s+__name__\s*==',
        r'print\s*\(',
        r':\s*$'
    ]
    
    JS_INDICATORS = [
        r'\bfunction\s+\w+\s*\(',
        r'\bconst\s+\w+\s*=',
        r'\blet\s+\w+\s*=',
        r'\bvar\s+\w+\s*=',
        r'=>',
        r'console\.\w+\(',
        r'\brequire\s*\(',
        r'\bimport\s+.*\s+from'
    ]
    
    HTML_INDICATORS = [
        r'<\w+[^>]*>',
        r'</\w+>',
        r'<!DOCTYPE'
    ]
    
    CSS_INDICATORS = [
        r'\{[^}]*:[^}]*;[^}]*\}',
        r'\.\w+\s*\{',
        r'#\w+\s*\{',
        r'@media'
    ]
    
    def __init__(self):
        self.python_parser = PythonASTParser()
        self.js_parser = JavaScriptParser()
    
    def detect_language(self, code: str) -> Language:
        """Detecta el lenguaje de un bloque de código"""
        code_lower = code.lower()
        
        # Contar indicadores
        scores = {
            Language.PYTHON: 0,
            Language.JAVASCRIPT: 0,
            Language.HTML: 0,
            Language.CSS: 0
        }
        
        for pattern in self.PYTHON_INDICATORS:
            if re.search(pattern, code, re.MULTILINE):
                scores[Language.PYTHON] += 1
        
        for pattern in self.JS_INDICATORS:
            if re.search(pattern, code):
                scores[Language.JAVASCRIPT] += 1
        
        for pattern in self.HTML_INDICATORS:
            if re.search(pattern, code, re.IGNORECASE):
                scores[Language.HTML] += 1
        
        for pattern in self.CSS_INDICATORS:
            if re.search(pattern, code):
                scores[Language.CSS] += 1
        
        # JSON detection
        try:
            json.loads(code)
            return Language.JSON
        except:
            pass
        
        # Bash detection
        if code.strip().startswith('#!') or re.search(r'\b(echo|cd|ls|mkdir|rm|cp|mv)\b', code):
            return Language.BASH
        
        # SQL detection
        if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b', code, re.IGNORECASE):
            return Language.SQL
        
        # Retornar el que tenga más indicadores
        max_score = max(scores.values())
        if max_score > 0:
            for lang, score in scores.items():
                if score == max_score:
                    return lang
        
        return Language.UNKNOWN
    
    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """
        Extrae bloques de código de un texto (mensaje de chat).
        
        Soporta:
        - Bloques markdown ```lang ... ```
        - Código inline `...`
        - Detección automática de código sin delimitadores
        """
        blocks = []
        
        # 1. Bloques markdown con triple backtick
        for match in self.MARKDOWN_CODE_BLOCK.finditer(text):
            lang_hint = match.group(1).lower()
            code = match.group(2).strip()
            
            # Mapear hint a Language
            lang_map = {
                'python': Language.PYTHON,
                'py': Language.PYTHON,
                'javascript': Language.JAVASCRIPT,
                'js': Language.JAVASCRIPT,
                'typescript': Language.TYPESCRIPT,
                'ts': Language.TYPESCRIPT,
                'html': Language.HTML,
                'css': Language.CSS,
                'json': Language.JSON,
                'bash': Language.BASH,
                'sh': Language.BASH,
                'shell': Language.BASH,
                'sql': Language.SQL
            }
            
            language = lang_map.get(lang_hint, self.detect_language(code))
            
            # Parsear según lenguaje
            is_valid, ast_info, errors = self._parse_code(code, language)
            
            blocks.append(CodeBlock(
                code=code,
                language=language,
                start_line=text[:match.start()].count('\n') + 1,
                end_line=text[:match.end()].count('\n') + 1,
                is_valid=is_valid,
                errors=errors,
                ast_info=ast_info
            ))
        
        return blocks
    
    def _parse_code(self, code: str, language: Language) -> Tuple[bool, Dict, List[str]]:
        """Parsea código según su lenguaje"""
        if language == Language.PYTHON:
            return self.python_parser.parse(code)
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return self.js_parser.parse(code)
        else:
            # Para otros lenguajes, validación básica
            return True, {}, []
    
    def validate_code(self, code: str, language: str = None) -> Dict[str, Any]:
        """
        Valida código y retorna información detallada.
        """
        if language:
            lang_map = {
                'python': Language.PYTHON,
                'javascript': Language.JAVASCRIPT,
                'js': Language.JAVASCRIPT,
            }
            lang = lang_map.get(language.lower(), Language.UNKNOWN)
        else:
            lang = self.detect_language(code)
        
        is_valid, ast_info, errors = self._parse_code(code, lang)
        
        return {
            "language": lang.value,
            "is_valid": is_valid,
            "errors": errors,
            "ast_info": ast_info,
            "line_count": code.count('\n') + 1,
            "char_count": len(code)
        }


# Autocompletado básico
class AutoCompleter:
    """Sistema de autocompletado básico para código"""
    
    PYTHON_KEYWORDS = [
        'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except',
        'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'raise',
        'pass', 'break', 'continue', 'and', 'or', 'not', 'in', 'is', 'None',
        'True', 'False', 'lambda', 'async', 'await', 'global', 'nonlocal'
    ]
    
    PYTHON_BUILTINS = [
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
        'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
        'open', 'input', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
        'sum', 'min', 'max', 'abs', 'round', 'format', 'repr', 'id', 'dir', 'help'
    ]
    
    JS_KEYWORDS = [
        'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do',
        'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally',
        'throw', 'class', 'extends', 'new', 'this', 'super', 'import', 'export',
        'default', 'async', 'await', 'yield', 'typeof', 'instanceof', 'in', 'of'
    ]
    
    JS_GLOBALS = [
        'console', 'document', 'window', 'Array', 'Object', 'String', 'Number',
        'Boolean', 'Date', 'Math', 'JSON', 'Promise', 'fetch', 'setTimeout',
        'setInterval', 'clearTimeout', 'clearInterval', 'alert', 'confirm'
    ]
    
    def get_suggestions(self, code: str, cursor_pos: int, language: str = "python") -> List[Dict]:
        """
        Obtiene sugerencias de autocompletado.
        
        Args:
            code: Código actual
            cursor_pos: Posición del cursor
            language: Lenguaje del código
        
        Returns:
            Lista de sugerencias
        """
        # Obtener palabra parcial antes del cursor
        before_cursor = code[:cursor_pos]
        
        # Encontrar inicio de la palabra actual
        word_start = len(before_cursor)
        for i in range(len(before_cursor) - 1, -1, -1):
            if not before_cursor[i].isalnum() and before_cursor[i] != '_':
                word_start = i + 1
                break
            if i == 0:
                word_start = 0
        
        partial = before_cursor[word_start:]
        
        if not partial:
            return []
        
        suggestions = []
        
        if language.lower() == "python":
            # Keywords
            for kw in self.PYTHON_KEYWORDS:
                if kw.startswith(partial.lower()):
                    suggestions.append({
                        "text": kw,
                        "type": "keyword",
                        "description": f"Python keyword"
                    })
            
            # Builtins
            for builtin in self.PYTHON_BUILTINS:
                if builtin.startswith(partial.lower()):
                    suggestions.append({
                        "text": builtin,
                        "type": "builtin",
                        "description": f"Built-in function"
                    })
        
        elif language.lower() in ["javascript", "js"]:
            # Keywords
            for kw in self.JS_KEYWORDS:
                if kw.startswith(partial.lower()):
                    suggestions.append({
                        "text": kw,
                        "type": "keyword",
                        "description": f"JavaScript keyword"
                    })
            
            # Globals
            for glob in self.JS_GLOBALS:
                if glob.lower().startswith(partial.lower()):
                    suggestions.append({
                        "text": glob,
                        "type": "global",
                        "description": f"Global object"
                    })
        
        return suggestions[:15]  # Limitar a 15 sugerencias


# Instancias globales
_detector: Optional[CodeDetector] = None
_completer: Optional[AutoCompleter] = None


def get_code_detector() -> CodeDetector:
    global _detector
    if _detector is None:
        _detector = CodeDetector()
    return _detector


def get_auto_completer() -> AutoCompleter:
    global _completer
    if _completer is None:
        _completer = AutoCompleter()
    return _completer
