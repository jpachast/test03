"""
Sandbox Integration - Ejecución REAL de código integrada con el chat
Este módulo:
1. Detecta bloques de código en respuestas del agente
2. Los ejecuta automáticamente en contexto del proyecto
3. Muestra resultados inline
4. Activa auto-fix si hay errores
"""
import re
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, List, Tuple


class IntegratedSandbox:
    """Sandbox integrado con el contexto del proyecto"""
    
    def __init__(self, project_path: str = "/workspace/project/test03"):
        self.project_path = project_path
        self.execution_history = []
        self.max_retries = 3
        
    def detect_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        """Detecta bloques de código en el texto con su lenguaje"""
        pattern = r"```(\w+)?\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        return [(lang or "python", code.strip()) for lang, code in matches]
    
    def execute_in_context(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Ejecuta código en el contexto del proyecto"""
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "language": language,
            "error_type": None,
            "suggested_fix": None
        }
        
        try:
            if language in ["python", "py"]:
                result = self._execute_python(code)
            elif language in ["bash", "sh", "shell"]:
                result = self._execute_bash(code)
            elif language in ["javascript", "js", "node"]:
                result = self._execute_javascript(code)
            else:
                result["stderr"] = f"Lenguaje no soportado: {language}"
                
        except Exception as e:
            result["stderr"] = str(e)
            result["error_type"] = type(e).__name__
            
        self.execution_history.append(result)
        return result
    
    def _execute_python(self, code: str) -> Dict[str, Any]:
        """Ejecuta Python con acceso al proyecto"""
        setup_code = f'''import sys
import os
sys.path.insert(0, "{self.project_path}")
os.chdir("{self.project_path}")
'''
        full_code = setup_code + "\n" + code
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            f.flush()
            
            try:
                proc = subprocess.run(
                    ["python3", f.name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.project_path
                )
                
                result = {
                    "success": proc.returncode == 0,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "language": "python",
                    "error_type": None,
                    "suggested_fix": None
                }
                
                if proc.returncode != 0:
                    result["error_type"], result["suggested_fix"] = self._analyze_python_error(proc.stderr, code)
                    
                return result
                
            finally:
                os.unlink(f.name)
    
    def _execute_bash(self, code: str) -> Dict[str, Any]:
        """Ejecuta Bash en el contexto del proyecto"""
        try:
            proc = subprocess.run(
                ["bash", "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )
            
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "language": "bash",
                "error_type": None,
                "suggested_fix": None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout: comando tardó más de 30 segundos",
                "exit_code": -1,
                "language": "bash",
                "error_type": "Timeout",
                "suggested_fix": None
            }
    
    def _execute_javascript(self, code: str) -> Dict[str, Any]:
        """Ejecuta JavaScript/Node.js"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            
            try:
                proc = subprocess.run(
                    ["node", f.name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.project_path
                )
                
                return {
                    "success": proc.returncode == 0,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                    "language": "javascript",
                    "error_type": None,
                    "suggested_fix": None
                }
            finally:
                os.unlink(f.name)
    
    def _analyze_python_error(self, stderr: str, code: str) -> Tuple[Optional[str], Optional[str]]:
        """Analiza errores de Python y sugiere correcciones"""
        error_patterns = {
            "NameError": (r"NameError: name '(\w+)' is not defined", 
                         lambda m: f"Variable '{m.group(1)}' no definida. Añade: {m.group(1)} = None"),
            "ImportError": (r"No module named '(\w+)'",
                           lambda m: f"Módulo '{m.group(1)}' no instalado. Ejecuta: pip install {m.group(1)}"),
            "SyntaxError": (r"SyntaxError: (.+)",
                           lambda m: f"Error de sintaxis: {m.group(1)}"),
            "IndentationError": (r"IndentationError: (.+)",
                                lambda m: f"Error de indentación: {m.group(1)}"),
            "TypeError": (r"TypeError: (.+)",
                         lambda m: f"Error de tipo: {m.group(1)}"),
            "FileNotFoundError": (r"FileNotFoundError: (.+)",
                                  lambda m: f"Archivo no encontrado: {m.group(1)}"),
            "KeyError": (r"KeyError: (.+)",
                        lambda m: f"Clave no encontrada: {m.group(1)}"),
            "AttributeError": (r"AttributeError: (.+)",
                              lambda m: f"Atributo no encontrado: {m.group(1)}"),
        }
        
        for error_type, (pattern, fix_func) in error_patterns.items():
            match = re.search(pattern, stderr)
            if match:
                return error_type, fix_func(match)
        
        return None, None
    
    def auto_fix_and_retry(self, code: str, language: str = "python", max_retries: int = 3) -> Dict[str, Any]:
        """Intenta ejecutar y auto-corregir errores"""
        attempts = []
        current_code = code
        
        for attempt in range(max_retries):
            result = self.execute_in_context(current_code, language)
            attempts.append({
                "attempt": attempt + 1,
                "code": current_code,
                "result": result
            })
            
            if result["success"]:
                return {
                    "final_success": True,
                    "attempts": attempts,
                    "final_code": current_code,
                    "output": result["stdout"]
                }
            
            if not result["suggested_fix"]:
                break
        
        return {
            "final_success": False,
            "attempts": attempts,
            "final_code": current_code,
            "error": result["stderr"],
            "suggested_fix": result["suggested_fix"]
        }


# Instancia global
integrated_sandbox = IntegratedSandbox()


def process_agent_response(response_text: str) -> Dict[str, Any]:
    """
    Procesa la respuesta del agente, detecta código y lo ejecuta
    """
    code_blocks = integrated_sandbox.detect_code_blocks(response_text)
    
    if not code_blocks:
        return {"response": response_text, "executions": []}
    
    executions = []
    for language, code in code_blocks:
        result = integrated_sandbox.execute_in_context(code, language)
        executions.append({
            "language": language,
            "code": code[:200] + "..." if len(code) > 200 else code,
            "result": result
        })
    
    return {
        "response": response_text,
        "executions": executions,
        "has_errors": any(not e["result"]["success"] for e in executions)
    }
