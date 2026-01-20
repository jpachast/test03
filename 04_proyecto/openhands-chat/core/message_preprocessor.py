"""
Message Preprocessor - Analiza mensajes del usuario ANTES de enviar al agente

Este módulo detecta intenciones de modificación de código y automáticamente:
1. Analiza el impacto del cambio solicitado
2. Agrega contexto al mensaje para que el agente tome decisiones informadas
3. Previene cambios no deseados a código compartido

Esto es OBLIGATORIO y automático - el LLM no puede saltárselo.
"""

import re
from typing import Dict, List, Optional, Tuple
from .analyzer import CodeAnalyzer
from .indexer import CodeIndexer, set_indexer


def detect_css_modification_intent(message: str) -> List[str]:
    """
    Detecta si el usuario quiere modificar CSS.
    
    Returns:
        Lista de posibles selectores CSS mencionados o inferidos
    """
    selectors = []
    
    # Patrones para detectar intención de modificar CSS
    css_keywords = [
        r'color', r'texto', r'text', r'fuente', r'font', r'tamaño', r'size',
        r'fondo', r'background', r'borde', r'border', r'margen', r'margin',
        r'padding', r'estilo', r'style', r'clase', r'class', r'css',
        r'blanco', r'white', r'negro', r'black', r'rojo', r'red', r'azul', r'blue',
        r'verde', r'green', r'amarillo', r'yellow', r'gris', r'gray', r'grey'
    ]
    
    # Patrones para detectar elementos UI
    ui_elements = [
        (r'bot[oó]n', 'button'),
        (r'button', 'button'),
        (r'enlace', 'link'),
        (r'link', 'link'),
        (r't[ií]tulo', 'title'),
        (r'title', 'title'),
        (r'header', 'header'),
        (r'footer', 'footer'),
        (r'menu', 'menu'),
        (r'nav', 'nav'),
        (r'sidebar', 'sidebar'),
        (r'card', 'card'),
        (r'modal', 'modal'),
        (r'input', 'input'),
        (r'label', 'label'),
    ]
    
    message_lower = message.lower()
    
    # Verificar si hay intención de cambio visual
    has_css_intent = any(re.search(kw, message_lower) for kw in css_keywords)
    
    if not has_css_intent:
        return []
    
    # Buscar clases CSS explícitas (.nombre-clase)
    explicit_classes = re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', message)
    selectors.extend([f".{c}" for c in explicit_classes])
    
    # Buscar IDs explícitos (#nombre-id)
    explicit_ids = re.findall(r'#([a-zA-Z_-][a-zA-Z0-9_-]*)', message)
    selectors.extend([f"#{i}" for i in explicit_ids])
    
    # Buscar nombres de elementos en comillas
    quoted_names = re.findall(r'["\']([^"\']+)["\']', message)
    for name in quoted_names:
        # Convertir nombre a posible selector
        name_lower = name.lower().replace(' ', '-').replace('_', '-')
        if len(name_lower) > 2:
            selectors.append(f".{name_lower}")
            selectors.append(f"#{name_lower}")
    
    # Buscar nombres de elementos después de "botón", "el", "la", etc.
    element_patterns = [
        r'bot[oó]n\s+(?:de\s+)?["\']?(\w+)["\']?',
        r'el\s+(\w+)\s+bot[oó]n',
        r'texto\s+(?:del?\s+)?["\']?(\w+)["\']?',
        r'clase\s+["\']?\.?(\w+)["\']?',
    ]
    
    for pattern in element_patterns:
        matches = re.findall(pattern, message_lower)
        for match in matches:
            if len(match) > 2:
                selectors.append(f".{match}")
                selectors.append(f"#{match}")
                # Variantes comunes
                selectors.append(f".{match}-btn")
                selectors.append(f".btn-{match}")
                selectors.append(f"#{match}-btn")
    
    return list(set(selectors))


def detect_code_modification_intent(message: str) -> List[str]:
    """
    Detecta si el usuario quiere modificar código (funciones, clases).
    
    Returns:
        Lista de posibles símbolos a modificar
    """
    symbols = []
    message_lower = message.lower()
    
    # Patrones para detectar intención de modificar código
    code_keywords = [
        r'funci[oó]n', r'function', r'm[eé]todo', r'method',
        r'clase', r'class', r'variable', r'constante', r'const',
        r'cambiar', r'change', r'modificar', r'modify', r'actualizar', r'update',
        r'renombrar', r'rename', r'eliminar', r'delete', r'borrar', r'remove'
    ]
    
    has_code_intent = any(re.search(kw, message_lower) for kw in code_keywords)
    
    if not has_code_intent:
        return []
    
    # Buscar nombres de funciones/clases en comillas
    quoted = re.findall(r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']', message)
    symbols.extend(quoted)
    
    # Buscar patrones como "función X", "clase Y"
    patterns = [
        r'funci[oó]n\s+["\']?(\w+)["\']?',
        r'm[eé]todo\s+["\']?(\w+)["\']?',
        r'clase\s+["\']?(\w+)["\']?',
        r'variable\s+["\']?(\w+)["\']?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message_lower)
        symbols.extend(matches)
    
    return list(set(symbols))


def analyze_and_enrich_message(message: str, workspace: str) -> Tuple[str, Dict]:
    """
    Analiza el mensaje del usuario y lo enriquece con información de impacto.
    
    Args:
        message: Mensaje original del usuario
        workspace: Directorio del proyecto
        
    Returns:
        Tuple (mensaje enriquecido, metadata del análisis)
    """
    metadata = {
        "original_message": message,
        "css_selectors_detected": [],
        "code_symbols_detected": [],
        "impact_analysis": [],
        "high_risk_changes": [],
        "recommendations": []
    }
    
    # Inicializar analizador
    try:
        analyzer = CodeAnalyzer(workspace)
        analyzer.ensure_indexed()
    except Exception as e:
        # Si falla el análisis, devolver mensaje original
        return message, metadata
    
    # Detectar intención de modificar CSS
    css_selectors = detect_css_modification_intent(message)
    metadata["css_selectors_detected"] = css_selectors
    
    # Detectar intención de modificar código
    code_symbols = detect_code_modification_intent(message)
    metadata["code_symbols_detected"] = code_symbols
    
    # Si no se detectó nada, devolver mensaje original
    if not css_selectors and not code_symbols:
        return message, metadata
    
    # Analizar impacto de cada selector/símbolo detectado
    all_symbols = css_selectors + code_symbols
    impact_warnings = []
    
    for symbol in all_symbols:
        try:
            impact = analyzer.analyze_impact(symbol)
            
            if impact.files_affected > 1:
                metadata["high_risk_changes"].append({
                    "symbol": symbol,
                    "files_affected": impact.files_affected,
                    "risk_level": impact.risk_level,
                    "affected_files": impact.affected_files
                })
                
                if impact.risk_level in ("medium", "high"):
                    warning = (
                        f"⚠️ ANÁLISIS DE IMPACTO para '{symbol}':\n"
                        f"   - Usado en {impact.files_affected} archivos: {', '.join(impact.affected_files[:3])}\n"
                        f"   - Riesgo: {impact.risk_level.upper()}\n"
                        f"   - Recomendación: {impact.recommendation}\n"
                    )
                    impact_warnings.append(warning)
                    metadata["recommendations"].append(impact.safe_alternatives)
        except Exception as e:
            pass
    
    # Si hay advertencias de alto riesgo, enriquecer el mensaje
    if impact_warnings:
        enriched_message = f"""{message}

---
🔍 **ANÁLISIS DE IMPACTO AUTOMÁTICO** (el agente DEBE leer esto):

{''.join(impact_warnings)}

**INSTRUCCIÓN OBLIGATORIA**: 
Dado que los selectores/símbolos detectados son compartidos, el agente DEBE:
1. NO modificar directamente los selectores compartidos
2. Crear un selector/ID ESPECÍFICO para el elemento que el usuario quiere cambiar
3. Aplicar los cambios SOLO a ese selector específico

Ejemplo correcto:
- Agregar id="btn-limpiar" al botón específico en HTML
- Agregar CSS: #btn-limpiar {{ color: white; }}

NO hacer:
- Modificar .tool-btn directamente (afectaría otros botones)
---
"""
        return enriched_message, metadata
    
    return message, metadata


def get_impact_summary(workspace: str, selectors: List[str]) -> str:
    """
    Obtiene un resumen de impacto para una lista de selectores.
    
    Returns:
        Resumen en formato texto
    """
    if not selectors:
        return ""
    
    try:
        analyzer = CodeAnalyzer(workspace)
        analyzer.ensure_indexed()
        
        summaries = []
        for selector in selectors:
            impact = analyzer.analyze_impact(selector)
            if impact.files_affected > 0:
                summaries.append(
                    f"- `{selector}`: {impact.files_affected} archivo(s), riesgo {impact.risk_level}"
                )
        
        if summaries:
            return "**Análisis de impacto:**\n" + "\n".join(summaries)
    except:
        pass
    
    return ""


def should_warn_user(message: str, workspace: str) -> Optional[str]:
    """
    Determina si se debe advertir al usuario antes de proceder.
    
    Returns:
        Mensaje de advertencia o None si es seguro proceder
    """
    _, metadata = analyze_and_enrich_message(message, workspace)
    
    if metadata["high_risk_changes"]:
        high_risk = metadata["high_risk_changes"]
        warning = "⚠️ **Cambio de alto riesgo detectado**\n\n"
        warning += "Los siguientes selectores son compartidos:\n"
        for change in high_risk:
            warning += f"- `{change['symbol']}` usado en {change['files_affected']} archivos\n"
        warning += "\n¿Desea continuar? El agente intentará usar selectores específicos."
        return warning
    
    return None
