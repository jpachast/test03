"""
Analysis Tools - Herramientas de análisis para el agente OpenHands

Estas herramientas se registran como Tools del SDK y están disponibles
para el agente. Son OBLIGATORIAS antes de modificar código.

Tools:
1. analyze_impact - Analiza impacto antes de modificar
2. find_references - Encuentra todas las referencias a un símbolo
3. get_edit_context - Obtiene contexto completo antes de editar

El agente DEBE usar estas herramientas ANTES de editar archivos,
especialmente para CSS, clases, y funciones compartidas.
"""

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Importar desde el SDK de OpenHands
try:
    from openhands.sdk.tool import BaseTool, ToolResult
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    # Fallback para desarrollo
    class BaseTool:
        name = "base_tool"
        description = ""
        def execute(self, **kwargs) -> Dict:
            return {}
    
    class ToolResult:
        def __init__(self, output: str = "", error: str = ""):
            self.output = output
            self.error = error

from .indexer import CodeIndexer, get_indexer, set_indexer
from .analyzer import CodeAnalyzer, ImpactReport


class AnalyzeImpactParams(BaseModel):
    """Parámetros para analyze_impact"""
    symbol: str = Field(
        description="Symbol to analyze (e.g., '.tool-btn', 'MyClass', 'my_function')"
    )
    change_type: str = Field(
        default="modify",
        description="Type of change: 'modify', 'delete', or 'rename'"
    )


class AnalyzeImpactTool(BaseTool):
    """
    Analyzes the impact of modifying a symbol in the codebase.
    
    IMPORTANT: Use this tool BEFORE editing any CSS class, function, or 
    shared code to understand what will be affected.
    
    Example:
        analyze_impact(symbol=".tool-btn")
        # Returns: impact report showing all files that use .tool-btn
    """
    
    name = "analyze_impact"
    description = """Analyzes the impact of modifying a symbol (CSS class, function, variable).
    
MANDATORY: Call this BEFORE modifying any:
- CSS classes (.class-name)
- CSS IDs (#id-name)
- Functions/methods
- Shared variables or constants

Returns a detailed impact report showing:
- How many files are affected
- Risk level (low/medium/high)
- Specific locations where the symbol is used
- Safe alternatives if risk is high

Example usage:
- Before changing '.tool-btn': analyze_impact(symbol=".tool-btn")
- Before renaming a function: analyze_impact(symbol="my_function", change_type="rename")
"""
    
    params_schema = AnalyzeImpactParams
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self._analyzer = None
    
    def _get_analyzer(self) -> CodeAnalyzer:
        if self._analyzer is None:
            self._analyzer = CodeAnalyzer(self.workspace)
        return self._analyzer
    
    def execute(self, symbol: str, change_type: str = "modify") -> ToolResult:
        """Execute the analysis"""
        try:
            analyzer = self._get_analyzer()
            impact = analyzer.analyze_impact(symbol, change_type)
            
            # Formatear resultado
            output = impact.to_markdown()
            
            # Agregar advertencia si es riesgo alto
            if impact.risk_level == "high":
                output = f"""⚠️ **HIGH RISK CHANGE DETECTED**

{output}

**ACTION REQUIRED**: Before proceeding, you MUST either:
1. Ask the user which specific element they want to modify
2. Create a more specific selector that only targets the intended element
3. Get explicit confirmation that changing ALL instances is intended

DO NOT proceed with a blanket change to `{symbol}` without user confirmation.
"""
            
            return ToolResult(output=output)
            
        except Exception as e:
            return ToolResult(error=f"Error analyzing impact: {str(e)}")


class FindReferencesParams(BaseModel):
    """Parámetros para find_references"""
    symbol: str = Field(
        description="Symbol to find references for (e.g., '.my-class', 'myFunction')"
    )


class FindReferencesTool(BaseTool):
    """
    Finds all references to a symbol in the codebase.
    
    Use this to understand where a symbol is used before modifying it.
    """
    
    name = "find_references"
    description = """Finds all references to a symbol (CSS class, function, variable) in the codebase.

Returns a list of all locations where the symbol appears, including:
- File path
- Line number
- Whether it's a definition or usage
- Code context

Example usage:
- Find all uses of a CSS class: find_references(symbol=".btn-primary")
- Find all calls to a function: find_references(symbol="handle_click")
"""
    
    params_schema = FindReferencesParams
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self._analyzer = None
    
    def _get_analyzer(self) -> CodeAnalyzer:
        if self._analyzer is None:
            self._analyzer = CodeAnalyzer(self.workspace)
        return self._analyzer
    
    def execute(self, symbol: str) -> ToolResult:
        """Execute the search"""
        try:
            analyzer = self._get_analyzer()
            refs = analyzer.find_references(symbol)
            
            if not refs:
                return ToolResult(output=f"No references found for `{symbol}`")
            
            # Formatear resultado
            output = f"## References to `{symbol}`\n\n"
            output += f"Found **{len(refs)}** reference(s):\n\n"
            
            # Agrupar por archivo
            by_file = {}
            for ref in refs:
                f = ref["file"]
                if f not in by_file:
                    by_file[f] = []
                by_file[f].append(ref)
            
            for file, file_refs in by_file.items():
                output += f"### `{file}`\n"
                for ref in file_refs:
                    line = ref.get("line", "?")
                    ref_type = ref.get("type", "reference")
                    context = ref.get("context", "")[:80]
                    output += f"- Line {line} ({ref_type}): `{context}`\n"
                output += "\n"
            
            return ToolResult(output=output)
            
        except Exception as e:
            return ToolResult(error=f"Error finding references: {str(e)}")


class GetEditContextParams(BaseModel):
    """Parámetros para get_edit_context"""
    file_path: str = Field(
        description="Path to the file to get context for"
    )
    symbol: str = Field(
        default=None,
        description="Optional: specific symbol to analyze within the file"
    )


class GetEditContextTool(BaseTool):
    """
    Gets complete context before editing a file.
    
    Provides information about:
    - Symbols defined in the file
    - External references to those symbols
    - Impact analysis for specific symbols
    """
    
    name = "get_edit_context"
    description = """Gets complete context before editing a file.

Returns:
- All symbols (classes, functions, CSS selectors) defined in the file
- Which other files reference symbols from this file
- Impact analysis if a specific symbol is provided

Use this to understand a file before making changes.

Example:
- Before editing a CSS file: get_edit_context(file_path="static/css/index.css")
- Before modifying a specific class: get_edit_context(file_path="styles.css", symbol=".tool-btn")
"""
    
    params_schema = GetEditContextParams
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self._analyzer = None
    
    def _get_analyzer(self) -> CodeAnalyzer:
        if self._analyzer is None:
            self._analyzer = CodeAnalyzer(self.workspace)
        return self._analyzer
    
    def execute(self, file_path: str, symbol: str = None) -> ToolResult:
        """Execute the context gathering"""
        try:
            analyzer = self._get_analyzer()
            context = analyzer.get_context_for_edit(file_path, symbol)
            
            output = f"## Edit Context for `{file_path}`\n\n"
            
            # Símbolos en el archivo
            symbols = context.get("symbols_in_file", [])
            if symbols:
                output += f"### Symbols Defined ({len(symbols)})\n"
                for sym in symbols[:20]:  # Limitar a 20
                    output += f"- `{sym['name']}` ({sym['type']}) - line {sym['line']}\n"
                if len(symbols) > 20:
                    output += f"- ... and {len(symbols) - 20} more\n"
                output += "\n"
            
            # Referencias externas
            ext_refs = context.get("external_references", [])
            if ext_refs:
                output += "### External References ⚠️\n"
                output += "These symbols are referenced from other files:\n\n"
                for ref in ext_refs:
                    sym = ref["symbol"]
                    files = ref["referenced_from"]
                    output += f"- `{sym}` is used in: {', '.join(f'`{f}`' for f in files[:3])}"
                    if len(files) > 3:
                        output += f" and {len(files) - 3} more"
                    output += "\n"
                output += "\n"
            
            # Análisis de símbolo específico
            if symbol and context.get("symbol_analysis"):
                analysis = context["symbol_analysis"]
                output += f"### Impact Analysis for `{symbol}`\n"
                output += f"- Risk Level: **{analysis['risk_level'].upper()}**\n"
                output += f"- Files Affected: {analysis['files_affected']}\n"
                output += f"- Recommendation: {analysis['recommendation']}\n"
            
            return ToolResult(output=output)
            
        except Exception as e:
            return ToolResult(error=f"Error getting edit context: {str(e)}")


class IndexCodebaseParams(BaseModel):
    """Parámetros para index_codebase"""
    incremental: bool = Field(
        default=True,
        description="If True, only index changed files. If False, full re-index."
    )


class IndexCodebaseTool(BaseTool):
    """
    Indexes or re-indexes the codebase for analysis.
    
    Usually called automatically, but can be called manually to refresh the index.
    """
    
    name = "index_codebase"
    description = """Indexes the codebase to enable impact analysis.

This is usually done automatically, but you can call it to refresh the index
after major changes or if analysis results seem outdated.

Returns statistics about what was indexed.
"""
    
    params_schema = IndexCodebaseParams
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self._indexer = None
    
    def _get_indexer(self) -> CodeIndexer:
        if self._indexer is None:
            self._indexer = get_indexer(self.workspace)
            if self._indexer is None:
                self._indexer = CodeIndexer(self.workspace)
                set_indexer(self._indexer)
        return self._indexer
    
    def execute(self, incremental: bool = True) -> ToolResult:
        """Execute the indexing"""
        try:
            indexer = self._get_indexer()
            stats = indexer.index(incremental=incremental)
            
            output = f"""## Codebase Index Results

- **Files Scanned:** {stats['files_scanned']}
- **Files Indexed:** {stats['files_indexed']}
- **Files Skipped (unchanged):** {stats['files_skipped']}
- **Symbols Found:** {stats['symbols_found']}
- **References Found:** {stats['references_found']}
"""
            
            if stats['errors']:
                output += f"\n### Errors ({len(stats['errors'])})\n"
                for err in stats['errors'][:5]:
                    output += f"- {err}\n"
            
            return ToolResult(output=output)
            
        except Exception as e:
            return ToolResult(error=f"Error indexing codebase: {str(e)}")


def create_analysis_tools(workspace: str) -> List[BaseTool]:
    """
    Crea las herramientas de análisis para un workspace.
    
    Args:
        workspace: Directorio raíz del proyecto
        
    Returns:
        Lista de herramientas listas para usar
    """
    return [
        AnalyzeImpactTool(workspace=workspace),
        FindReferencesTool(workspace=workspace),
        GetEditContextTool(workspace=workspace),
        IndexCodebaseTool(workspace=workspace),
    ]


# Para uso directo desde el agente (sin SDK)
def analyze_impact_direct(workspace: str, symbol: str, change_type: str = "modify") -> str:
    """Función directa para analizar impacto"""
    tool = AnalyzeImpactTool(workspace=workspace)
    result = tool.execute(symbol=symbol, change_type=change_type)
    return result.output if not result.error else f"Error: {result.error}"


def find_references_direct(workspace: str, symbol: str) -> str:
    """Función directa para encontrar referencias"""
    tool = FindReferencesTool(workspace=workspace)
    result = tool.execute(symbol=symbol)
    return result.output if not result.error else f"Error: {result.error}"
