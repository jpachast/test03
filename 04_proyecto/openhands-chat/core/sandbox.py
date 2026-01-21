"""
Sandbox de Ejecución Real - Ejecuta código de forma segura
Similar a como lo hace Devin: ejecuta Python, Node, Bash y captura resultados
"""

import subprocess
import tempfile
import os
import time
import signal
import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import traceback
import shutil
import re


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Resultado de una ejecución de código"""
    id: str
    language: str
    code: str
    stdout: str
    stderr: str
    exit_code: int
    status: ExecutionStatus
    execution_time: float
    created_at: str
    error_analysis: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodeSandbox:
    """
    Sandbox para ejecución segura de código.
    Soporta Python, Node.js, Bash y más.
    """
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'extension': '.py',
            'command': ['python3'],
            'timeout': 30,
            'description': 'Python 3.x'
        },
        'javascript': {
            'extension': '.js',
            'command': ['node'],
            'timeout': 30,
            'description': 'Node.js'
        },
        'typescript': {
            'extension': '.ts',
            'command': ['npx', 'ts-node'],
            'timeout': 45,
            'description': 'TypeScript (ts-node)'
        },
        'bash': {
            'extension': '.sh',
            'command': ['bash'],
            'timeout': 60,
            'description': 'Bash Shell'
        },
        'shell': {
            'extension': '.sh',
            'command': ['sh'],
            'timeout': 60,
            'description': 'Shell Script'
        }
    }
    
    def __init__(self, workspace_dir: str = None, max_output_size: int = 100000):
        """
        Inicializa el sandbox.
        
        Args:
            workspace_dir: Directorio de trabajo para las ejecuciones
            max_output_size: Tamaño máximo del output en bytes
        """
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix='sandbox_')
        self.max_output_size = max_output_size
        self.executions: Dict[str, ExecutionResult] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}
        
        # Crear directorio si no existe
        os.makedirs(self.workspace_dir, exist_ok=True)
        
    def detect_language(self, code: str) -> str:
        """Detecta el lenguaje del código automáticamente"""
        code_lower = code.lower().strip()
        
        # Detectar por shebang
        if code.startswith('#!/usr/bin/env python') or code.startswith('#!/usr/bin/python'):
            return 'python'
        if code.startswith('#!/usr/bin/env node') or code.startswith('#!/usr/bin/node'):
            return 'javascript'
        if code.startswith('#!/bin/bash') or code.startswith('#!/usr/bin/env bash'):
            return 'bash'
        if code.startswith('#!/bin/sh'):
            return 'shell'
            
        # Detectar por patrones de código
        python_patterns = [
            r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+', r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import', r'\bprint\s*\(', r'\bif\s+__name__',
            r'\basync\s+def', r'\bawait\s+', r'\bwith\s+open'
        ]
        js_patterns = [
            r'\bconst\s+\w+', r'\blet\s+\w+', r'\bvar\s+\w+',
            r'\bfunction\s+\w+', r'\bconsole\.log', r'\brequire\s*\(',
            r'\bexport\s+', r'\bimport\s+.*\s+from', r'=>'
        ]
        bash_patterns = [
            r'\becho\s+', r'\bif\s+\[\s*', r'\bfor\s+\w+\s+in',
            r'\bwhile\s+', r'\bcase\s+', r'\$\{?\w+\}?',
            r'\bgrep\s+', r'\bawk\s+', r'\bsed\s+'
        ]
        
        python_score = sum(1 for p in python_patterns if re.search(p, code))
        js_score = sum(1 for p in js_patterns if re.search(p, code))
        bash_score = sum(1 for p in bash_patterns if re.search(p, code))
        
        scores = {'python': python_score, 'javascript': js_score, 'bash': bash_score}
        detected = max(scores, key=scores.get)
        
        # Si no hay patrones claros, asumir Python
        if scores[detected] == 0:
            return 'python'
            
        return detected
    
    def execute_sync(
        self,
        code: str,
        language: str = None,
        timeout: int = None,
        env: Dict[str, str] = None,
        cwd: str = None
    ) -> ExecutionResult:
        """
        Ejecuta código de forma síncrona.
        
        Args:
            code: Código a ejecutar
            language: Lenguaje (auto-detecta si no se especifica)
            timeout: Timeout en segundos
            env: Variables de entorno adicionales
            cwd: Directorio de trabajo
            
        Returns:
            ExecutionResult con stdout, stderr, exit_code, etc.
        """
        execution_id = str(uuid.uuid4())[:8]
        
        # Auto-detectar lenguaje si no se especifica
        if not language:
            language = self.detect_language(code)
            
        if language not in self.SUPPORTED_LANGUAGES:
            return ExecutionResult(
                id=execution_id,
                language=language,
                code=code,
                stdout='',
                stderr=f'Lenguaje no soportado: {language}. Soportados: {list(self.SUPPORTED_LANGUAGES.keys())}',
                exit_code=1,
                status=ExecutionStatus.ERROR,
                execution_time=0,
                created_at=datetime.now().isoformat()
            )
        
        lang_config = self.SUPPORTED_LANGUAGES[language]
        timeout = timeout or lang_config['timeout']
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config['extension'],
            dir=self.workspace_dir,
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name
        
        start_time = time.time()
        stdout = ''
        stderr = ''
        exit_code = 0
        status = ExecutionStatus.PENDING
        
        try:
            # Preparar comando
            cmd = lang_config['command'] + [temp_file]
            
            # Preparar entorno
            run_env = os.environ.copy()
            if env:
                run_env.update(env)
            
            # Ejecutar
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or self.workspace_dir,
                env=run_env,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.running_processes[execution_id] = process
            status = ExecutionStatus.RUNNING
            
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                stdout = stdout_bytes.decode('utf-8', errors='replace')[:self.max_output_size]
                stderr = stderr_bytes.decode('utf-8', errors='replace')[:self.max_output_size]
                exit_code = process.returncode
                status = ExecutionStatus.SUCCESS if exit_code == 0 else ExecutionStatus.ERROR
            except subprocess.TimeoutExpired:
                # Matar proceso y sus hijos
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                process.wait()
                stdout = ''
                stderr = f'Ejecución cancelada: timeout de {timeout} segundos excedido'
                exit_code = -1
                status = ExecutionStatus.TIMEOUT
                
        except Exception as e:
            stderr = f'Error de ejecución: {str(e)}\n{traceback.format_exc()}'
            exit_code = 1
            status = ExecutionStatus.ERROR
        finally:
            # Limpiar
            if execution_id in self.running_processes:
                del self.running_processes[execution_id]
            try:
                os.unlink(temp_file)
            except:
                pass
        
        execution_time = time.time() - start_time
        
        # Analizar errores si los hay
        error_analysis = None
        suggested_fix = None
        if status == ExecutionStatus.ERROR and stderr:
            error_analysis, suggested_fix = self._analyze_error(language, code, stderr)
        
        result = ExecutionResult(
            id=execution_id,
            language=language,
            code=code,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            status=status,
            execution_time=round(execution_time, 3),
            created_at=datetime.now().isoformat(),
            error_analysis=error_analysis,
            suggested_fix=suggested_fix
        )
        
        self.executions[execution_id] = result
        return result
    
    async def execute_async(
        self,
        code: str,
        language: str = None,
        timeout: int = None,
        env: Dict[str, str] = None,
        cwd: str = None
    ) -> ExecutionResult:
        """Versión asíncrona de execute_sync"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_sync(code, language, timeout, env, cwd)
        )
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancela una ejecución en curso"""
        if execution_id in self.running_processes:
            process = self.running_processes[execution_id]
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                return True
            except:
                return False
        return False
    
    def _analyze_error(self, language: str, code: str, stderr: str) -> tuple:
        """
        Analiza errores comunes y sugiere correcciones.
        Retorna (análisis, sugerencia_de_fix)
        """
        analysis = None
        fix = None
        
        if language == 'python':
            # Errores comunes de Python
            if 'ModuleNotFoundError' in stderr or 'ImportError' in stderr:
                match = re.search(r"No module named '(\w+)'", stderr)
                module = match.group(1) if match else 'unknown'
                analysis = f"Módulo '{module}' no instalado"
                fix = f"pip install {module}"
            elif 'SyntaxError' in stderr:
                analysis = "Error de sintaxis en el código"
                match = re.search(r'line (\d+)', stderr)
                if match:
                    analysis += f" en la línea {match.group(1)}"
            elif 'IndentationError' in stderr:
                analysis = "Error de indentación - revisar espacios/tabs"
            elif 'NameError' in stderr:
                match = re.search(r"name '(\w+)' is not defined", stderr)
                var = match.group(1) if match else 'unknown'
                analysis = f"Variable '{var}' no definida"
            elif 'TypeError' in stderr:
                analysis = "Error de tipo - argumentos o operaciones incompatibles"
            elif 'ZeroDivisionError' in stderr:
                analysis = "División por cero"
            elif 'FileNotFoundError' in stderr:
                analysis = "Archivo no encontrado"
            elif 'KeyError' in stderr:
                match = re.search(r"KeyError: '?(\w+)'?", stderr)
                key = match.group(1) if match else 'unknown'
                analysis = f"Clave '{key}' no existe en el diccionario"
                
        elif language == 'javascript':
            if 'ReferenceError' in stderr:
                match = re.search(r"(\w+) is not defined", stderr)
                var = match.group(1) if match else 'unknown'
                analysis = f"Variable '{var}' no definida"
            elif 'SyntaxError' in stderr:
                analysis = "Error de sintaxis JavaScript"
            elif 'TypeError' in stderr:
                analysis = "Error de tipo en JavaScript"
            elif "Cannot find module" in stderr:
                match = re.search(r"Cannot find module '([^']+)'", stderr)
                module = match.group(1) if match else 'unknown'
                analysis = f"Módulo '{module}' no instalado"
                fix = f"npm install {module}"
                
        elif language in ['bash', 'shell']:
            if 'command not found' in stderr:
                match = re.search(r"(\w+): command not found", stderr)
                cmd = match.group(1) if match else 'unknown'
                analysis = f"Comando '{cmd}' no encontrado"
                fix = f"apt-get install {cmd} o verificar PATH"
            elif 'Permission denied' in stderr:
                analysis = "Permiso denegado"
                fix = "chmod +x script.sh o ejecutar con sudo"
            elif 'No such file or directory' in stderr:
                analysis = "Archivo o directorio no existe"
        
        return analysis, fix
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Obtiene el resultado de una ejecución por ID"""
        return self.executions.get(execution_id)
    
    def list_executions(self, limit: int = 20) -> List[ExecutionResult]:
        """Lista las últimas ejecuciones"""
        executions = list(self.executions.values())
        executions.sort(key=lambda x: x.created_at, reverse=True)
        return executions[:limit]
    
    def clear_history(self):
        """Limpia el historial de ejecuciones"""
        self.executions.clear()
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Retorna los lenguajes soportados con sus descripciones"""
        return {k: v['description'] for k, v in self.SUPPORTED_LANGUAGES.items()}
    
    def install_package(self, package: str, language: str = 'python') -> ExecutionResult:
        """Instala un paquete para el lenguaje especificado"""
        if language == 'python':
            code = f"import subprocess; subprocess.run(['pip', 'install', '{package}', '-q'])"
            return self.execute_sync(code, 'python', timeout=120)
        elif language == 'javascript':
            code = f"npm install {package} --save"
            return self.execute_sync(code, 'bash', timeout=120)
        else:
            return ExecutionResult(
                id='install',
                language=language,
                code=f'install {package}',
                stdout='',
                stderr=f'Instalación no soportada para {language}',
                exit_code=1,
                status=ExecutionStatus.ERROR,
                execution_time=0,
                created_at=datetime.now().isoformat()
            )


# Instancia global del sandbox
_sandbox_instance: Optional[CodeSandbox] = None


def get_sandbox(workspace_dir: str = None) -> CodeSandbox:
    """Obtiene la instancia global del sandbox"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = CodeSandbox(workspace_dir)
    return _sandbox_instance


# Funciones helper para uso directo
def run_code(code: str, language: str = None, timeout: int = None) -> ExecutionResult:
    """Ejecuta código y retorna el resultado"""
    sandbox = get_sandbox()
    return sandbox.execute_sync(code, language, timeout)


def run_python(code: str, timeout: int = 30) -> ExecutionResult:
    """Ejecuta código Python"""
    return run_code(code, 'python', timeout)


def run_javascript(code: str, timeout: int = 30) -> ExecutionResult:
    """Ejecuta código JavaScript"""
    return run_code(code, 'javascript', timeout)


def run_bash(code: str, timeout: int = 60) -> ExecutionResult:
    """Ejecuta código Bash"""
    return run_code(code, 'bash', timeout)
