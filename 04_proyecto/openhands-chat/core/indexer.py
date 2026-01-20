"""
Code Indexer - Indexa código para análisis de impacto

Arquitectura similar a Cursor/Devin:
1. Parsea código con tree-sitter (AST)
2. Extrae símbolos (clases, funciones, variables, CSS)
3. Mapea referencias y dependencias
4. Permite búsquedas semánticas

Uso:
    indexer = CodeIndexer("/path/to/project")
    indexer.index()  # Indexa todo el proyecto
    
    # Buscar referencias
    refs = indexer.find_references(".tool-btn")
    # Returns: [{"file": "index.css", "line": 45, "type": "definition"}, ...]
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Intentar importar tree-sitter
try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_html as tshtml
    import tree_sitter_css as tscss
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Symbol:
    """Representa un símbolo en el código (clase, función, variable, selector CSS)"""
    name: str
    type: str  # "class", "function", "variable", "css_class", "css_id", "html_element"
    file: str
    line: int
    column: int = 0
    end_line: int = 0
    scope: str = ""  # Scope padre (ej: "MyClass" para métodos)
    content: str = ""  # Contenido/definición
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class Reference:
    """Representa una referencia a un símbolo"""
    symbol_name: str
    file: str
    line: int
    column: int = 0
    context: str = ""  # Línea de código donde aparece
    ref_type: str = "usage"  # "definition", "usage", "import"
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileIndex:
    """Índice de un archivo individual"""
    path: str
    hash: str  # Hash del contenido para detectar cambios
    language: str
    symbols: List[Symbol] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    last_indexed: str = ""
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "hash": self.hash,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "references": [r.to_dict() for r in self.references],
            "imports": self.imports,
            "last_indexed": self.last_indexed
        }


class CodeIndexer:
    """
    Indexador de código que extrae símbolos y referencias.
    
    Soporta:
    - Python (.py)
    - JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
    - HTML (.html)
    - CSS (.css, .scss, .less)
    - JSON (.json)
    """
    
    # Extensiones soportadas y su lenguaje
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".less": "less",
        ".json": "json",
    }
    
    # Patrones para ignorar
    IGNORE_PATTERNS = {
        "node_modules", "__pycache__", ".git", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache"
    }
    
    def __init__(self, workspace: str):
        """
        Inicializa el indexador.
        
        Args:
            workspace: Directorio raíz del proyecto
        """
        self.workspace = Path(workspace)
        self.index: Dict[str, FileIndex] = {}
        self.symbol_table: Dict[str, List[Symbol]] = {}  # symbol_name -> [Symbol]
        self.reference_table: Dict[str, List[Reference]] = {}  # symbol_name -> [Reference]
        
        # Inicializar parsers de tree-sitter si están disponibles
        self._init_parsers()
    
    def _init_parsers(self):
        """Inicializa los parsers de tree-sitter"""
        self.parsers = {}
        
        if not TREE_SITTER_AVAILABLE:
            return
        
        try:
            # Python parser
            self.parsers["python"] = Parser(Language(tspython.language()))
        except:
            pass
            
        try:
            # JavaScript parser
            self.parsers["javascript"] = Parser(Language(tsjavascript.language()))
        except:
            pass
            
        try:
            # HTML parser
            self.parsers["html"] = Parser(Language(tshtml.language()))
        except:
            pass
            
        try:
            # CSS parser
            self.parsers["css"] = Parser(Language(tscss.language()))
        except:
            pass
    
    def _should_ignore(self, path: Path) -> bool:
        """Verifica si un path debe ser ignorado"""
        parts = path.parts
        return any(p in self.IGNORE_PATTERNS for p in parts)
    
    def _get_file_hash(self, content: str) -> str:
        """Genera hash del contenido para detectar cambios"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_language(self, path: Path) -> Optional[str]:
        """Obtiene el lenguaje basado en la extensión"""
        return self.LANGUAGE_MAP.get(path.suffix.lower())
    
    def index(self, incremental: bool = True) -> Dict[str, Any]:
        """
        Indexa todo el proyecto.
        
        Args:
            incremental: Si True, solo re-indexa archivos modificados
            
        Returns:
            Resumen del indexado
        """
        stats = {
            "files_scanned": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "symbols_found": 0,
            "references_found": 0,
            "errors": []
        }
        
        # Recorrer todos los archivos
        for path in self.workspace.rglob("*"):
            if path.is_dir() or self._should_ignore(path):
                continue
                
            language = self._get_language(path)
            if not language:
                continue
            
            stats["files_scanned"] += 1
            
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                file_hash = self._get_file_hash(content)
                rel_path = str(path.relative_to(self.workspace))
                
                # Verificar si necesita re-indexar
                if incremental and rel_path in self.index:
                    if self.index[rel_path].hash == file_hash:
                        stats["files_skipped"] += 1
                        continue
                
                # Indexar archivo
                file_index = self._index_file(path, content, language)
                self.index[rel_path] = file_index
                
                # Actualizar tablas globales
                for symbol in file_index.symbols:
                    if symbol.name not in self.symbol_table:
                        self.symbol_table[symbol.name] = []
                    self.symbol_table[symbol.name].append(symbol)
                    stats["symbols_found"] += 1
                
                for ref in file_index.references:
                    if ref.symbol_name not in self.reference_table:
                        self.reference_table[ref.symbol_name] = []
                    self.reference_table[ref.symbol_name].append(ref)
                    stats["references_found"] += 1
                
                stats["files_indexed"] += 1
                
            except Exception as e:
                stats["errors"].append(f"{path}: {str(e)}")
        
        return stats
    
    def _index_file(self, path: Path, content: str, language: str) -> FileIndex:
        """Indexa un archivo individual"""
        rel_path = str(path.relative_to(self.workspace))
        file_hash = self._get_file_hash(content)
        
        file_index = FileIndex(
            path=rel_path,
            hash=file_hash,
            language=language,
            last_indexed=datetime.now().isoformat()
        )
        
        # Usar parser apropiado según el lenguaje
        if language == "css" or language == "scss":
            self._index_css(content, file_index)
        elif language == "html":
            self._index_html(content, file_index)
        elif language == "python":
            self._index_python(content, file_index)
        elif language in ("javascript", "typescript"):
            self._index_javascript(content, file_index)
        elif language == "json":
            self._index_json(content, file_index)
        
        return file_index
    
    def _index_css(self, content: str, file_index: FileIndex):
        """Indexa archivo CSS - extrae clases, IDs, selectores"""
        lines = content.split("\n")
        
        # Regex para selectores CSS
        class_pattern = re.compile(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)')
        id_pattern = re.compile(r'#([a-zA-Z_-][a-zA-Z0-9_-]*)')
        
        # Buscar definiciones de clases e IDs
        in_rule = False
        current_selectors = []
        
        for line_num, line in enumerate(lines, 1):
            # Buscar clases
            for match in class_pattern.finditer(line):
                class_name = f".{match.group(1)}"
                symbol = Symbol(
                    name=class_name,
                    type="css_class",
                    file=file_index.path,
                    line=line_num,
                    column=match.start(),
                    content=line.strip()
                )
                file_index.symbols.append(symbol)
            
            # Buscar IDs
            for match in id_pattern.finditer(line):
                id_name = f"#{match.group(1)}"
                symbol = Symbol(
                    name=id_name,
                    type="css_id",
                    file=file_index.path,
                    line=line_num,
                    column=match.start(),
                    content=line.strip()
                )
                file_index.symbols.append(symbol)
    
    def _index_html(self, content: str, file_index: FileIndex):
        """Indexa archivo HTML - extrae clases, IDs usados"""
        lines = content.split("\n")
        
        # Regex para atributos class e id
        class_attr_pattern = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')
        id_attr_pattern = re.compile(r'id\s*=\s*["\']([^"\']+)["\']')
        
        for line_num, line in enumerate(lines, 1):
            # Buscar clases usadas
            for match in class_attr_pattern.finditer(line):
                classes = match.group(1).split()
                for cls in classes:
                    ref = Reference(
                        symbol_name=f".{cls}",
                        file=file_index.path,
                        line=line_num,
                        column=match.start(),
                        context=line.strip()[:100],
                        ref_type="usage"
                    )
                    file_index.references.append(ref)
            
            # Buscar IDs usados
            for match in id_attr_pattern.finditer(line):
                ref = Reference(
                    symbol_name=f"#{match.group(1)}",
                    file=file_index.path,
                    line=line_num,
                    column=match.start(),
                    context=line.strip()[:100],
                    ref_type="usage"
                )
                file_index.references.append(ref)
    
    def _index_python(self, content: str, file_index: FileIndex):
        """Indexa archivo Python - extrae clases, funciones, imports"""
        lines = content.split("\n")
        
        # Patrones simples (fallback si no hay tree-sitter)
        class_pattern = re.compile(r'^class\s+(\w+)')
        func_pattern = re.compile(r'^(\s*)def\s+(\w+)')
        import_pattern = re.compile(r'^(?:from\s+(\S+)\s+)?import\s+(.+)')
        
        current_class = None
        
        for line_num, line in enumerate(lines, 1):
            # Clases
            match = class_pattern.match(line)
            if match:
                current_class = match.group(1)
                symbol = Symbol(
                    name=current_class,
                    type="class",
                    file=file_index.path,
                    line=line_num,
                    content=line.strip()
                )
                file_index.symbols.append(symbol)
                continue
            
            # Funciones
            match = func_pattern.match(line)
            if match:
                indent = len(match.group(1))
                func_name = match.group(2)
                scope = current_class if indent > 0 and current_class else ""
                symbol = Symbol(
                    name=func_name,
                    type="function" if not scope else "method",
                    file=file_index.path,
                    line=line_num,
                    scope=scope,
                    content=line.strip()
                )
                file_index.symbols.append(symbol)
                continue
            
            # Imports
            match = import_pattern.match(line)
            if match:
                module = match.group(1) or ""
                imports = match.group(2)
                file_index.imports.append(f"{module}:{imports}" if module else imports)
            
            # Reset class si volvemos a nivel 0
            if line and not line[0].isspace():
                if not class_pattern.match(line):
                    current_class = None
    
    def _index_javascript(self, content: str, file_index: FileIndex):
        """Indexa archivo JavaScript - extrae clases, funciones, imports"""
        lines = content.split("\n")
        
        # Patrones
        class_pattern = re.compile(r'class\s+(\w+)')
        func_pattern = re.compile(r'(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))')
        const_pattern = re.compile(r'(?:const|let|var)\s+(\w+)')
        import_pattern = re.compile(r"import\s+.+\s+from\s+['\"](.+)['\"]")
        
        for line_num, line in enumerate(lines, 1):
            # Clases
            match = class_pattern.search(line)
            if match:
                symbol = Symbol(
                    name=match.group(1),
                    type="class",
                    file=file_index.path,
                    line=line_num,
                    content=line.strip()
                )
                file_index.symbols.append(symbol)
            
            # Funciones
            match = func_pattern.search(line)
            if match:
                func_name = match.group(1) or match.group(2)
                if func_name:
                    symbol = Symbol(
                        name=func_name,
                        type="function",
                        file=file_index.path,
                        line=line_num,
                        content=line.strip()
                    )
                    file_index.symbols.append(symbol)
            
            # Imports
            match = import_pattern.search(line)
            if match:
                file_index.imports.append(match.group(1))
    
    def _index_json(self, content: str, file_index: FileIndex):
        """Indexa archivo JSON - extrae keys de primer nivel"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                for key in data.keys():
                    symbol = Symbol(
                        name=key,
                        type="json_key",
                        file=file_index.path,
                        line=1,
                        content=f'"{key}": ...'
                    )
                    file_index.symbols.append(symbol)
        except json.JSONDecodeError:
            pass
    
    def find_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Busca todas las referencias a un símbolo.
        
        Args:
            symbol_name: Nombre del símbolo (ej: ".tool-btn", "MyClass", "my_function")
            
        Returns:
            Lista de referencias con archivo, línea, tipo, contexto
        """
        results = []
        
        # Buscar en tabla de símbolos (definiciones)
        if symbol_name in self.symbol_table:
            for symbol in self.symbol_table[symbol_name]:
                results.append({
                    "file": symbol.file,
                    "line": symbol.line,
                    "type": "definition",
                    "symbol_type": symbol.type,
                    "context": symbol.content,
                    "scope": symbol.scope
                })
        
        # Buscar en tabla de referencias (usos)
        if symbol_name in self.reference_table:
            for ref in self.reference_table[symbol_name]:
                results.append({
                    "file": ref.file,
                    "line": ref.line,
                    "type": ref.ref_type,
                    "context": ref.context
                })
        
        # Si no encontramos nada, hacer búsqueda por grep como fallback
        if not results:
            results = self._grep_fallback(symbol_name)
        
        return results
    
    def _grep_fallback(self, pattern: str) -> List[Dict[str, Any]]:
        """Búsqueda por grep cuando el índice no tiene el símbolo"""
        results = []
        
        # Escapar caracteres especiales de regex excepto para selectores CSS
        if not pattern.startswith(".") and not pattern.startswith("#"):
            search_pattern = re.escape(pattern)
        else:
            search_pattern = re.escape(pattern)
        
        regex = re.compile(search_pattern)
        
        for path in self.workspace.rglob("*"):
            if path.is_dir() or self._should_ignore(path):
                continue
            
            if not self._get_language(path):
                continue
            
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")
                
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        rel_path = str(path.relative_to(self.workspace))
                        results.append({
                            "file": rel_path,
                            "line": line_num,
                            "type": "grep_match",
                            "context": line.strip()[:100]
                        })
            except:
                pass
        
        return results
    
    def analyze_impact(self, file_path: str, symbol_name: str) -> Dict[str, Any]:
        """
        Analiza el impacto de modificar un símbolo.
        
        Args:
            file_path: Archivo donde está el símbolo
            symbol_name: Nombre del símbolo a modificar
            
        Returns:
            Análisis de impacto con archivos afectados
        """
        refs = self.find_references(symbol_name)
        
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
        
        if num_files == 1:
            risk = "low"
        elif num_files <= 3:
            risk = "medium"
        else:
            risk = "high"
        
        return {
            "symbol": symbol_name,
            "total_references": num_refs,
            "files_affected": num_files,
            "risk_level": risk,
            "details": files_affected,
            "recommendation": self._get_recommendation(symbol_name, files_affected)
        }
    
    def _get_recommendation(self, symbol_name: str, files_affected: Dict) -> str:
        """Genera recomendación basada en el análisis"""
        num_files = len(files_affected)
        
        if num_files == 0:
            return f"Symbol '{symbol_name}' not found. Safe to create."
        elif num_files == 1:
            return f"Symbol used in 1 file. Safe to modify."
        else:
            return (
                f"⚠️ Symbol '{symbol_name}' is used in {num_files} files. "
                f"Consider creating a more specific selector/name to avoid unintended changes."
            )
    
    def get_file_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Obtiene todos los símbolos de un archivo"""
        if file_path in self.index:
            return [s.to_dict() for s in self.index[file_path].symbols]
        return []
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del índice"""
        return {
            "total_files": len(self.index),
            "total_symbols": sum(len(s) for s in self.symbol_table.values()),
            "total_references": sum(len(r) for r in self.reference_table.values()),
            "languages": list(set(f.language for f in self.index.values())),
            "symbol_types": self._count_symbol_types()
        }
    
    def _count_symbol_types(self) -> Dict[str, int]:
        """Cuenta símbolos por tipo"""
        counts = {}
        for symbols in self.symbol_table.values():
            for s in symbols:
                counts[s.type] = counts.get(s.type, 0) + 1
        return counts
    
    def to_json(self) -> str:
        """Serializa el índice a JSON"""
        data = {
            "workspace": str(self.workspace),
            "files": {k: v.to_dict() for k, v in self.index.items()},
            "summary": self.get_summary()
        }
        return json.dumps(data, indent=2)
    
    def save(self, path: str = None):
        """Guarda el índice a disco"""
        if path is None:
            path = self.workspace / ".code_index.json"
        
        Path(path).write_text(self.to_json())
    
    def load(self, path: str = None) -> bool:
        """Carga el índice desde disco"""
        if path is None:
            path = self.workspace / ".code_index.json"
        
        try:
            data = json.loads(Path(path).read_text())
            # Reconstruir índice
            for file_path, file_data in data.get("files", {}).items():
                symbols = [Symbol(**s) for s in file_data.get("symbols", [])]
                refs = [Reference(**r) for r in file_data.get("references", [])]
                
                file_index = FileIndex(
                    path=file_data["path"],
                    hash=file_data["hash"],
                    language=file_data["language"],
                    symbols=symbols,
                    references=refs,
                    imports=file_data.get("imports", []),
                    last_indexed=file_data.get("last_indexed", "")
                )
                self.index[file_path] = file_index
                
                # Reconstruir tablas
                for symbol in symbols:
                    if symbol.name not in self.symbol_table:
                        self.symbol_table[symbol.name] = []
                    self.symbol_table[symbol.name].append(symbol)
                
                for ref in refs:
                    if ref.symbol_name not in self.reference_table:
                        self.reference_table[ref.symbol_name] = []
                    self.reference_table[ref.symbol_name].append(ref)
            
            return True
        except:
            return False


# Instancia global para acceso desde herramientas
_global_indexer: Optional[CodeIndexer] = None


def get_indexer(workspace: str = None) -> CodeIndexer:
    """Obtiene o crea el indexador global"""
    global _global_indexer
    
    if _global_indexer is None and workspace:
        _global_indexer = CodeIndexer(workspace)
    
    return _global_indexer


def set_indexer(indexer: CodeIndexer):
    """Establece el indexador global"""
    global _global_indexer
    _global_indexer = indexer
