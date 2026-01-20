"""
Code Analyzer - Herramientas de análisis de impacto para el agente

Estas herramientas son OBLIGATORIAS antes de editar código.
El agente las usa para entender el impacto de sus cambios.

Herramientas:
1. find_references - Encuentra todas las referencias a un símbolo
2. analyze_impact - Analiza el impacto de modificar algo
3. suggest_safe_change - Sugiere cómo hacer un cambio seguro

Uso por el agente:
    # ANTES de editar .tool-btn:
    impact = analyze_impact(".tool-btn")
    # Si afecta múltiples archivos, el agente propone alternativa
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .indexer import CodeIndexer, get_indexer, set_indexer


@dataclass
class ImpactReport:
    """Reporte de impacto de un cambio"""
    symbol: str
    total_references: int
    files_affected: int
    risk_level: str  # "low", "medium", "high"
    affected_files: List[str]
    details: Dict[str, List[Dict]]
    recommendation: str
    safe_alternatives: List[str]
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "total_references": self.total_references,
            "files_affected": self.files_affected,
            "risk_level": self.risk_level,
            "affected_files": self.affected_files,
            "details": self.details,
            "recommendation": self.recommendation,
            "safe_alternatives": self.safe_alternatives
        }
    
    def to_markdown(self) -> str:
        """Genera reporte en formato markdown para el agente"""
        md = f"""## 📊 Impact Analysis: `{self.symbol}`

### Summary
- **Total References:** {self.total_references}
- **Files Affected:** {self.files_affected}
- **Risk Level:** {'🔴' if self.risk_level == 'high' else '🟡' if self.risk_level == 'medium' else '🟢'} {self.risk_level.upper()}

### Affected Files
"""
        for file in self.affected_files:
            refs_in_file = len(self.details.get(file, []))
            md += f"- `{file}` ({refs_in_file} references)\n"
        
        md += f"""
### Recommendation
{self.recommendation}
"""
        
        if self.safe_alternatives:
            md += "\n### Safe Alternatives\n"
            for alt in self.safe_alternatives:
                md += f"- {alt}\n"
        
        return md


class CodeAnalyzer:
    """
    Analizador de código que el agente usa ANTES de modificar.
    
    Flujo obligatorio:
    1. Usuario pide cambio
    2. Agente llama analyze_impact()
    3. Si riesgo alto, agente propone alternativa
    4. Solo entonces ejecuta el cambio
    """
    
    def __init__(self, workspace: str):
        """
        Inicializa el analizador.
        
        Args:
            workspace: Directorio raíz del proyecto
        """
        self.workspace = Path(workspace)
        self.indexer = get_indexer(workspace)
        
        if self.indexer is None:
            self.indexer = CodeIndexer(workspace)
            set_indexer(self.indexer)
    
    def ensure_indexed(self) -> Dict[str, Any]:
        """Asegura que el código esté indexado"""
        if not self.indexer.index:
            return self.indexer.index(incremental=True)
        return {"status": "already_indexed", "files": len(self.indexer.index)}
    
    def find_references(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Encuentra todas las referencias a un símbolo.
        
        Args:
            symbol: Nombre del símbolo (ej: ".tool-btn", "MyClass", "my_function")
            
        Returns:
            Lista de referencias con archivo, línea, tipo, contexto
        """
        self.ensure_indexed()
        return self.indexer.find_references(symbol)
    
    def analyze_impact(self, symbol: str, change_type: str = "modify") -> ImpactReport:
        """
        Analiza el impacto de modificar un símbolo.
        
        Args:
            symbol: Símbolo a modificar
            change_type: Tipo de cambio ("modify", "delete", "rename")
            
        Returns:
            ImpactReport con análisis completo
        """
        self.ensure_indexed()
        
        # Obtener referencias
        refs = self.indexer.find_references(symbol)
        
        # Agrupar por archivo
        files_affected = {}
        for ref in refs:
            f = ref["file"]
            if f not in files_affected:
                files_affected[f] = []
            files_affected[f].append(ref)
        
        # Determinar nivel de riesgo
        num_files = len(files_affected)
        num_refs = len(refs)
        
        if num_files == 0:
            risk = "low"
        elif num_files == 1:
            risk = "low"
        elif num_files <= 3:
            risk = "medium"
        else:
            risk = "high"
        
        # Generar recomendación
        recommendation = self._generate_recommendation(symbol, files_affected, change_type)
        
        # Generar alternativas seguras
        safe_alternatives = self._suggest_safe_alternatives(symbol, files_affected, change_type)
        
        return ImpactReport(
            symbol=symbol,
            total_references=num_refs,
            files_affected=num_files,
            risk_level=risk,
            affected_files=list(files_affected.keys()),
            details=files_affected,
            recommendation=recommendation,
            safe_alternatives=safe_alternatives
        )
    
    def _generate_recommendation(self, symbol: str, files_affected: Dict, change_type: str) -> str:
        """Genera recomendación basada en el análisis"""
        num_files = len(files_affected)
        
        if num_files == 0:
            return f"✅ Symbol `{symbol}` not found in codebase. Safe to create new."
        
        elif num_files == 1:
            file = list(files_affected.keys())[0]
            return f"✅ Symbol `{symbol}` only exists in `{file}`. Safe to {change_type}."
        
        else:
            files_list = ", ".join(f"`{f}`" for f in list(files_affected.keys())[:3])
            if num_files > 3:
                files_list += f" and {num_files - 3} more"
            
            return (
                f"⚠️ **CAUTION**: Symbol `{symbol}` is used in {num_files} files: {files_list}.\n\n"
                f"Modifying this will affect ALL these files. Consider:\n"
                f"1. Creating a new, specific selector instead of modifying the shared one\n"
                f"2. Adding a unique ID or class to target only the intended element\n"
                f"3. Asking the user which specific element they want to change"
            )
    
    def _suggest_safe_alternatives(self, symbol: str, files_affected: Dict, change_type: str) -> List[str]:
        """Sugiere alternativas seguras"""
        alternatives = []
        num_files = len(files_affected)
        
        if num_files <= 1:
            return []  # No necesita alternativas
        
        # Para selectores CSS
        if symbol.startswith(".") or symbol.startswith("#"):
            base_name = symbol[1:]  # Sin el . o #
            
            alternatives.append(
                f"Create a specific class: `.{base_name}-specific` and apply only to target element"
            )
            alternatives.append(
                f"Use an ID for unique targeting: `#{base_name}-unique`"
            )
            alternatives.append(
                f"Use descendant selector: `.parent-container {symbol}` to scope the change"
            )
            alternatives.append(
                f"Add data attribute: `[data-variant='special']` to target specific variant"
            )
        
        # Para funciones/clases
        else:
            alternatives.append(
                f"Create a new function with specific behavior instead of modifying shared one"
            )
            alternatives.append(
                f"Add a parameter to control behavior: `{symbol}(specific=True)`"
            )
            alternatives.append(
                f"Create a wrapper function that calls the original with modifications"
            )
        
        return alternatives
    
    def suggest_safe_change(self, user_request: str, target_file: str = None) -> Dict[str, Any]:
        """
        Analiza una solicitud del usuario y sugiere cambio seguro.
        
        Args:
            user_request: Lo que el usuario quiere cambiar
            target_file: Archivo específico si se conoce
            
        Returns:
            Sugerencia de cómo hacer el cambio de forma segura
        """
        self.ensure_indexed()
        
        # Extraer posibles símbolos de la solicitud
        symbols = self._extract_symbols(user_request)
        
        analysis_results = []
        for symbol in symbols:
            impact = self.analyze_impact(symbol)
            analysis_results.append({
                "symbol": symbol,
                "impact": impact.to_dict()
            })
        
        # Determinar si es seguro proceder
        max_risk = "low"
        for result in analysis_results:
            risk = result["impact"]["risk_level"]
            if risk == "high":
                max_risk = "high"
            elif risk == "medium" and max_risk != "high":
                max_risk = "medium"
        
        return {
            "user_request": user_request,
            "symbols_found": symbols,
            "analysis": analysis_results,
            "overall_risk": max_risk,
            "proceed_safely": max_risk == "low",
            "action_required": self._get_action_required(max_risk, analysis_results)
        }
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extrae posibles símbolos de un texto"""
        symbols = []
        
        # CSS classes
        css_classes = re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', text)
        symbols.extend([f".{c}" for c in css_classes])
        
        # CSS IDs
        css_ids = re.findall(r'#([a-zA-Z_-][a-zA-Z0-9_-]*)', text)
        symbols.extend([f"#{i}" for i in css_ids])
        
        # Quoted strings (posibles nombres)
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        for q in quoted:
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', q):
                symbols.append(q)
        
        # Palabras que parecen identificadores
        # Buscar patrones como "botón X", "clase X", "función X"
        patterns = [
            r'(?:botón|button|clase|class|función|function|elemento|element)\s+["\']?([a-zA-Z_-][a-zA-Z0-9_-]*)["\']?',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            symbols.extend(matches)
        
        return list(set(symbols))
    
    def _get_action_required(self, risk: str, analysis: List[Dict]) -> str:
        """Determina qué acción se requiere"""
        if risk == "low":
            return "Safe to proceed with the change."
        elif risk == "medium":
            return "Review the affected files before proceeding. Consider using a more specific selector."
        else:
            return (
                "⚠️ HIGH RISK: Multiple files will be affected. "
                "MUST ask user for clarification or create a specific selector for the target element only."
            )
    
    def get_context_for_edit(self, file_path: str, symbol: str = None) -> Dict[str, Any]:
        """
        Obtiene contexto completo antes de editar un archivo.
        
        Args:
            file_path: Archivo a editar
            symbol: Símbolo específico a modificar (opcional)
            
        Returns:
            Contexto con símbolos, referencias, y recomendaciones
        """
        self.ensure_indexed()
        
        context = {
            "file": file_path,
            "symbols_in_file": [],
            "external_references": [],
            "symbol_analysis": None
        }
        
        # Símbolos en el archivo
        if file_path in self.indexer.index:
            context["symbols_in_file"] = [
                s.to_dict() for s in self.indexer.index[file_path].symbols
            ]
        
        # Si hay un símbolo específico, analizarlo
        if symbol:
            context["symbol_analysis"] = self.analyze_impact(symbol).to_dict()
        
        # Encontrar qué otros archivos referencian símbolos de este archivo
        for sym_name, symbols in self.indexer.symbol_table.items():
            for sym in symbols:
                if sym.file == file_path:
                    # Este símbolo está definido en el archivo
                    refs = self.indexer.find_references(sym_name)
                    external_refs = [r for r in refs if r.get("file") != file_path]
                    if external_refs:
                        context["external_references"].append({
                            "symbol": sym_name,
                            "referenced_from": [r["file"] for r in external_refs]
                        })
        
        return context


# Funciones de conveniencia para usar desde el agente

def analyze_before_edit(workspace: str, symbol: str) -> str:
    """
    Función que el agente DEBE llamar antes de editar.
    
    Returns:
        Reporte de impacto en formato markdown
    """
    analyzer = CodeAnalyzer(workspace)
    impact = analyzer.analyze_impact(symbol)
    return impact.to_markdown()


def find_all_references(workspace: str, symbol: str) -> List[Dict[str, Any]]:
    """
    Encuentra todas las referencias a un símbolo.
    
    Returns:
        Lista de referencias
    """
    analyzer = CodeAnalyzer(workspace)
    return analyzer.find_references(symbol)


def is_safe_to_modify(workspace: str, symbol: str) -> bool:
    """
    Verifica si es seguro modificar un símbolo.
    
    Returns:
        True si solo afecta 1 archivo
    """
    analyzer = CodeAnalyzer(workspace)
    impact = analyzer.analyze_impact(symbol)
    return impact.risk_level == "low"


def get_edit_context(workspace: str, file_path: str, symbol: str = None) -> Dict[str, Any]:
    """
    Obtiene contexto antes de editar.
    
    Returns:
        Contexto con análisis de impacto
    """
    analyzer = CodeAnalyzer(workspace)
    return analyzer.get_context_for_edit(file_path, symbol)
