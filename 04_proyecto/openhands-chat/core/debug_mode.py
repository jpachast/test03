"""
Debug Mode - Sistema de debugging estructurado como Cursor

Implementa el flujo de debugging TOP:
1. HIPÓTESIS: Genera posibles causas del bug
2. INSTRUMENTACIÓN: Agrega logging automático
3. REPRODUCCIÓN: Guía para reproducir el bug
4. ANÁLISIS: Analiza logs y comportamiento
5. FIX TARGETED: Corrige basado en evidencia

Uso:
    debug_session = DebugSession(workspace, bug_description)
    hypotheses = debug_session.generate_hypotheses()
    instrumentation = debug_session.suggest_instrumentation()
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Hypothesis:
    """Una hipótesis sobre la causa del bug"""
    id: int
    description: str
    likelihood: str  # "high", "medium", "low"
    files_to_check: List[str] = field(default_factory=list)
    logs_to_add: List[Dict[str, Any]] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)


@dataclass
class InstrumentationPoint:
    """Un punto donde agregar logging"""
    file: str
    line: int
    log_statement: str
    purpose: str
    language: str


@dataclass 
class DebugSession:
    """
    Sesión de debugging estructurado.
    
    Guía al agente a través del proceso de debug sistemático.
    """
    
    workspace: str
    bug_description: str
    error_message: str = ""
    stack_trace: str = ""
    reproduction_steps: List[str] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    instrumentation: List[InstrumentationPoint] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    status: str = "investigating"  # investigating, instrumented, analyzed, fixed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def generate_hypotheses(self, context: str = "") -> List[Hypothesis]:
        """
        Genera hipótesis basadas en el bug y contexto.
        
        Esta función es llamada por el agente para estructurar
        su pensamiento sobre las posibles causas.
        """
        # Templates de hipótesis comunes por tipo de error
        common_patterns = self._identify_error_patterns()
        
        hypotheses = []
        h_id = 1
        
        for pattern in common_patterns:
            hypotheses.append(Hypothesis(
                id=h_id,
                description=pattern["description"],
                likelihood=pattern["likelihood"],
                files_to_check=pattern.get("files", []),
                logs_to_add=pattern.get("logs", []),
                verification_steps=pattern.get("steps", [])
            ))
            h_id += 1
        
        self.hypotheses = hypotheses
        return hypotheses
    
    def _identify_error_patterns(self) -> List[Dict[str, Any]]:
        """Identifica patrones de error comunes"""
        patterns = []
        bug_lower = self.bug_description.lower()
        error_lower = self.error_message.lower()
        combined = f"{bug_lower} {error_lower}"
        
        # Patrones de error comunes
        if any(kw in combined for kw in ["undefined", "null", "none", "attributeerror"]):
            patterns.append({
                "description": "Variable no definida o valor nulo inesperado",
                "likelihood": "high",
                "steps": [
                    "Verificar que todas las variables estén inicializadas",
                    "Agregar verificaciones de null/undefined",
                    "Revisar flujo de datos desde el origen"
                ]
            })
        
        if any(kw in combined for kw in ["timeout", "connection", "network"]):
            patterns.append({
                "description": "Problema de conexión o timeout",
                "likelihood": "high",
                "steps": [
                    "Verificar URLs y endpoints",
                    "Revisar timeouts configurados",
                    "Comprobar conectividad de red"
                ]
            })
        
        if any(kw in combined for kw in ["async", "await", "promise", "race condition"]):
            patterns.append({
                "description": "Problema de concurrencia o async",
                "likelihood": "high",
                "steps": [
                    "Verificar que todos los await estén presentes",
                    "Revisar orden de ejecución",
                    "Buscar race conditions"
                ]
            })
        
        if any(kw in combined for kw in ["import", "module", "not found"]):
            patterns.append({
                "description": "Problema de importación o módulo faltante",
                "likelihood": "high",
                "steps": [
                    "Verificar que el módulo esté instalado",
                    "Revisar rutas de importación",
                    "Comprobar versiones de dependencias"
                ]
            })
        
        if any(kw in combined for kw in ["type", "cannot read", "is not a"]):
            patterns.append({
                "description": "Error de tipo o estructura de datos incorrecta",
                "likelihood": "medium",
                "steps": [
                    "Verificar tipos de datos esperados vs recibidos",
                    "Agregar type hints o validaciones",
                    "Revisar transformaciones de datos"
                ]
            })
        
        if any(kw in combined for kw in ["permission", "access", "denied", "forbidden"]):
            patterns.append({
                "description": "Problema de permisos o autenticación",
                "likelihood": "medium",
                "steps": [
                    "Verificar tokens y credenciales",
                    "Revisar permisos de archivos",
                    "Comprobar configuración de acceso"
                ]
            })
        
        # Si no hay patrones específicos, agregar genéricos
        if not patterns:
            patterns = [
                {
                    "description": "Error en la lógica del código",
                    "likelihood": "medium",
                    "steps": ["Revisar la lógica paso a paso", "Agregar logs en puntos clave"]
                },
                {
                    "description": "Datos de entrada incorrectos",
                    "likelihood": "medium", 
                    "steps": ["Validar datos de entrada", "Verificar formato esperado"]
                },
                {
                    "description": "Estado inconsistente",
                    "likelihood": "low",
                    "steps": ["Revisar flujo de estado", "Buscar efectos secundarios"]
                }
            ]
        
        return patterns
    
    def suggest_instrumentation(self, file_path: str = None) -> List[InstrumentationPoint]:
        """
        Sugiere puntos donde agregar logging para diagnóstico.
        
        Args:
            file_path: Archivo específico para instrumentar
        """
        instrumentation = []
        
        if not file_path:
            # Sin archivo específico, dar guías generales
            return instrumentation
        
        workspace_path = Path(self.workspace)
        full_path = workspace_path / file_path
        
        if not full_path.exists():
            return instrumentation
        
        try:
            content = full_path.read_text()
            lines = content.split('\n')
            ext = full_path.suffix.lower()
            
            # Detectar lenguaje
            if ext == ".py":
                instrumentation = self._instrument_python(file_path, lines)
            elif ext in {".js", ".ts", ".jsx", ".tsx"}:
                instrumentation = self._instrument_javascript(file_path, lines)
            
        except Exception as e:
            print(f"[DEBUG] Error leyendo archivo: {e}")
        
        self.instrumentation = instrumentation
        return instrumentation
    
    def _instrument_python(self, file_path: str, lines: List[str]) -> List[InstrumentationPoint]:
        """Genera puntos de instrumentación para Python"""
        points = []
        
        # Patrones donde agregar logs
        patterns = [
            (r'^\s*def\s+(\w+)', "Entrada a función"),
            (r'^\s*try:', "Inicio de try block"),
            (r'^\s*except', "Captura de excepción"),
            (r'^\s*return\s+', "Punto de retorno"),
            (r'=\s*await\s+', "Llamada async"),
            (r'\.get\(|\.post\(|requests\.', "Llamada HTTP"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, purpose in patterns:
                if re.search(pattern, line):
                    # Determinar indentación
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    
                    if "def " in line:
                        func_match = re.search(r'def\s+(\w+)', line)
                        func_name = func_match.group(1) if func_match else "unknown"
                        log_stmt = f'{indent_str}print(f"[DEBUG] Entering {func_name}, args={{locals()}}")'
                    elif "except" in line:
                        log_stmt = f'{indent_str}    import traceback; print(f"[DEBUG] Exception: {{traceback.format_exc()}}")'
                    elif "return" in line:
                        log_stmt = f'{indent_str}print(f"[DEBUG] Returning from line {i}")'
                    else:
                        log_stmt = f'{indent_str}print(f"[DEBUG] Line {i}: checkpoint")'
                    
                    points.append(InstrumentationPoint(
                        file=file_path,
                        line=i,
                        log_statement=log_stmt,
                        purpose=purpose,
                        language="python"
                    ))
                    break
        
        return points[:10]  # Limitar a 10 puntos más relevantes
    
    def _instrument_javascript(self, file_path: str, lines: List[str]) -> List[InstrumentationPoint]:
        """Genera puntos de instrumentación para JavaScript"""
        points = []
        
        patterns = [
            (r'^\s*(?:async\s+)?function\s+(\w+)', "Entrada a función"),
            (r'^\s*const\s+(\w+)\s*=\s*(?:async\s+)?\(', "Entrada a arrow function"),
            (r'^\s*try\s*{', "Inicio de try block"),
            (r'^\s*catch', "Captura de error"),
            (r'^\s*return\s+', "Punto de retorno"),
            (r'await\s+', "Llamada async"),
            (r'fetch\(|axios\.', "Llamada HTTP"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, purpose in patterns:
                if re.search(pattern, line):
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent
                    
                    if "function" in line or "=>" in line:
                        log_stmt = f'{indent_str}console.log("[DEBUG] Entering function at line {i}", arguments);'
                    elif "catch" in line:
                        log_stmt = f'{indent_str}  console.error("[DEBUG] Caught error:", error);'
                    elif "return" in line:
                        log_stmt = f'{indent_str}console.log("[DEBUG] Returning at line {i}");'
                    else:
                        log_stmt = f'{indent_str}console.log("[DEBUG] Checkpoint line {i}");'
                    
                    points.append(InstrumentationPoint(
                        file=file_path,
                        line=i,
                        log_statement=log_stmt,
                        purpose=purpose,
                        language="javascript"
                    ))
                    break
        
        return points[:10]
    
    def record_finding(self, finding: str):
        """Registra un hallazgo durante el debug"""
        self.findings.append(f"[{datetime.now().strftime('%H:%M:%S')}] {finding}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de la sesión de debug"""
        return {
            "bug": self.bug_description,
            "status": self.status,
            "hypotheses_count": len(self.hypotheses),
            "instrumentation_points": len(self.instrumentation),
            "findings": self.findings,
            "created_at": self.created_at
        }
    
    def to_prompt_context(self) -> str:
        """
        Genera contexto para incluir en el prompt del agente.
        
        Este contexto guía al agente a seguir el proceso de debug estructurado.
        """
        context = f"""
## 🔍 DEBUG SESSION ACTIVE

**Bug reportado:** {self.bug_description}
"""
        
        if self.error_message:
            context += f"\n**Error message:** {self.error_message}\n"
        
        if self.hypotheses:
            context += "\n### Hipótesis a investigar:\n"
            for h in self.hypotheses:
                context += f"\n**{h.id}. [{h.likelihood.upper()}] {h.description}**\n"
                if h.verification_steps:
                    for step in h.verification_steps:
                        context += f"   - {step}\n"
        
        if self.instrumentation:
            context += "\n### Puntos de instrumentación sugeridos:\n"
            for inst in self.instrumentation[:5]:
                context += f"- {inst.file}:{inst.line} - {inst.purpose}\n"
        
        if self.findings:
            context += "\n### Hallazgos hasta ahora:\n"
            for finding in self.findings[-5:]:
                context += f"- {finding}\n"
        
        context += """
### Proceso a seguir:
1. **NO adivines** - Basa tus decisiones en evidencia
2. Agrega logs en los puntos sugeridos
3. Pide reproducir el bug
4. Analiza los logs
5. Corrige basándote en lo que encontraste
"""
        
        return context


def create_debug_session(workspace: str, bug_description: str, 
                         error_message: str = "", stack_trace: str = "") -> DebugSession:
    """
    Crea una nueva sesión de debugging.
    
    Args:
        workspace: Directorio del proyecto
        bug_description: Descripción del bug
        error_message: Mensaje de error (opcional)
        stack_trace: Stack trace (opcional)
        
    Returns:
        Sesión de debug configurada
    """
    session = DebugSession(
        workspace=workspace,
        bug_description=bug_description,
        error_message=error_message,
        stack_trace=stack_trace
    )
    
    # Generar hipótesis iniciales
    session.generate_hypotheses()
    
    return session


# Sesión global activa
_active_session: Optional[DebugSession] = None


def get_active_debug_session() -> Optional[DebugSession]:
    """Obtiene la sesión de debug activa"""
    global _active_session
    return _active_session


def set_active_debug_session(session: DebugSession):
    """Establece la sesión de debug activa"""
    global _active_session
    _active_session = session


def clear_debug_session():
    """Limpia la sesión de debug activa"""
    global _active_session
    _active_session = None
