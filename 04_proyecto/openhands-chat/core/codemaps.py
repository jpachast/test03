"""
Codemaps - Grafo de dependencias visual usando AST

Características:
- Análisis AST de Python/JavaScript
- Extracción de imports, funciones, clases
- Grafo de dependencias entre archivos
- Visualización interactiva con D3.js
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeNode:
    """Nodo del grafo (archivo, función, clase)"""
    id: str
    name: str
    type: str  # file, function, class, import
    path: str
    line: int = 0
    size: int = 1
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "line": self.line,
            "size": self.size,
            "imports": self.imports,
            "functions": self.functions,
            "classes": self.classes
        }


@dataclass
class CodeEdge:
    """Arista del grafo (dependencia)"""
    source: str
    target: str
    type: str  # import, call, inheritance
    weight: int = 1
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "weight": self.weight
        }


class PythonASTAnalyzer:
    """Analiza código Python usando AST"""
    
    def analyze_file(self, file_path: str) -> Optional[CodeNode]:
        """Analiza un archivo Python"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = []
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                # Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                
                # Funciones
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                
                # Clases
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            rel_path = os.path.basename(file_path)
            
            return CodeNode(
                id=file_path,
                name=rel_path,
                type="file",
                path=file_path,
                size=len(content.split('\n')),
                imports=imports,
                functions=functions,
                classes=classes
            )
            
        except Exception as e:
            logger.warning(f"Error analizando {file_path}: {e}")
            return None


class JavaScriptAnalyzer:
    """Analiza código JavaScript/TypeScript con regex"""
    
    def analyze_file(self, file_path: str) -> Optional[CodeNode]:
        """Analiza un archivo JS/TS"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            imports = []
            functions = []
            classes = []
            
            # Imports ES6
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s*\([\'"]([^\'"]+)[\'"]\)',
                r'require\s*\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
            
            # Funciones
            func_patterns = [
                r'function\s+(\w+)\s*\(',
                r'const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>',
                r'const\s+(\w+)\s*=\s*function',
                r'(\w+)\s*:\s*(?:async\s*)?\([^)]*\)\s*=>'
            ]
            
            for pattern in func_patterns:
                matches = re.findall(pattern, content)
                functions.extend(matches)
            
            # Clases
            class_pattern = r'class\s+(\w+)'
            classes = re.findall(class_pattern, content)
            
            rel_path = os.path.basename(file_path)
            
            return CodeNode(
                id=file_path,
                name=rel_path,
                type="file",
                path=file_path,
                size=len(content.split('\n')),
                imports=list(set(imports)),
                functions=list(set(functions)),
                classes=list(set(classes))
            )
            
        except Exception as e:
            logger.warning(f"Error analizando {file_path}: {e}")
            return None


class CodemapGenerator:
    """Genera grafo de dependencias del código"""
    
    PYTHON_EXTENSIONS = {'.py'}
    JS_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}
    
    IGNORE_DIRS = {
        'node_modules', '__pycache__', '.git', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.next', 'coverage'
    }
    
    def __init__(self):
        self.py_analyzer = PythonASTAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.nodes: Dict[str, CodeNode] = {}
        self.edges: List[CodeEdge] = []
    
    def scan_directory(self, directory: str, max_files: int = 200) -> Dict[str, Any]:
        """
        Escanea un directorio y genera el grafo de dependencias.
        
        Returns:
            Dict con nodes y edges para visualización
        """
        self.nodes = {}
        self.edges = []
        
        directory = Path(directory)
        if not directory.exists():
            return {"error": "Directorio no existe", "nodes": [], "edges": []}
        
        files_processed = 0
        
        for root, dirs, files in os.walk(directory):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if files_processed >= max_files:
                    break
                
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                node = None
                
                if ext in self.PYTHON_EXTENSIONS:
                    node = self.py_analyzer.analyze_file(file_path)
                elif ext in self.JS_EXTENSIONS:
                    node = self.js_analyzer.analyze_file(file_path)
                
                if node:
                    # Usar path relativo como ID
                    rel_path = os.path.relpath(file_path, directory)
                    node.id = rel_path
                    node.path = rel_path
                    self.nodes[rel_path] = node
                    files_processed += 1
            
            if files_processed >= max_files:
                break
        
        # Generar edges basados en imports
        self._generate_edges(directory)
        
        return self._build_graph_data()
    
    def _generate_edges(self, base_dir: Path):
        """Genera aristas basadas en imports"""
        for node_id, node in self.nodes.items():
            for imp in node.imports:
                # Buscar el archivo que corresponde al import
                target_id = self._resolve_import(imp, node_id, base_dir)
                
                if target_id and target_id in self.nodes:
                    self.edges.append(CodeEdge(
                        source=node_id,
                        target=target_id,
                        type="import"
                    ))
    
    def _resolve_import(self, import_name: str, source_id: str, base_dir: Path) -> Optional[str]:
        """Resuelve un import a un archivo del proyecto"""
        # Convertir import a posible path
        possible_paths = [
            import_name.replace('.', '/') + '.py',
            import_name.replace('.', '/') + '.js',
            import_name.replace('.', '/') + '/index.js',
            import_name.replace('.', '/') + '/__init__.py',
            import_name + '.py',
            import_name + '.js',
        ]
        
        # Imports relativos
        if import_name.startswith('.'):
            source_dir = os.path.dirname(source_id)
            rel_import = import_name.lstrip('.')
            possible_paths.extend([
                os.path.join(source_dir, rel_import.replace('.', '/') + '.py'),
                os.path.join(source_dir, rel_import.replace('.', '/') + '.js'),
            ])
        
        for path in possible_paths:
            if path in self.nodes:
                return path
        
        return None
    
    def _build_graph_data(self) -> Dict[str, Any]:
        """Construye datos del grafo para D3.js"""
        nodes_list = []
        
        for node in self.nodes.values():
            # Determinar grupo por tipo de archivo
            ext = os.path.splitext(node.name)[1]
            if ext == '.py':
                group = 1
            elif ext in ['.js', '.jsx']:
                group = 2
            elif ext in ['.ts', '.tsx']:
                group = 3
            else:
                group = 4
            
            nodes_list.append({
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "group": group,
                "size": min(node.size, 500),  # Limitar tamaño visual
                "functions": len(node.functions),
                "classes": len(node.classes),
                "imports": len(node.imports),
                "details": {
                    "functions": node.functions[:10],  # Limitar
                    "classes": node.classes[:10],
                    "imports": node.imports[:10]
                }
            })
        
        edges_list = [edge.to_dict() for edge in self.edges]
        
        # Calcular métricas
        total_functions = sum(len(n.functions) for n in self.nodes.values())
        total_classes = sum(len(n.classes) for n in self.nodes.values())
        total_imports = sum(len(n.imports) for n in self.nodes.values())
        
        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "stats": {
                "total_files": len(self.nodes),
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_imports": total_imports,
                "total_edges": len(self.edges)
            }
        }
    
    def get_file_details(self, file_path: str, base_dir: str) -> Optional[Dict]:
        """Obtiene detalles de un archivo específico"""
        full_path = os.path.join(base_dir, file_path)
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.PYTHON_EXTENSIONS:
            node = self.py_analyzer.analyze_file(full_path)
        elif ext in self.JS_EXTENSIONS:
            node = self.js_analyzer.analyze_file(full_path)
        else:
            return None
        
        if node:
            return {
                "name": node.name,
                "path": file_path,
                "lines": node.size,
                "functions": node.functions,
                "classes": node.classes,
                "imports": node.imports
            }
        
        return None


# Instancia global
_generator: Optional[CodemapGenerator] = None


def get_generator() -> CodemapGenerator:
    """Obtiene o crea el generador"""
    global _generator
    if _generator is None:
        _generator = CodemapGenerator()
    return _generator
