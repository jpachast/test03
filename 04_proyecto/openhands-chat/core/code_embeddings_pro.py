"""
Code Embeddings Profesional con ChromaDB
Búsqueda semántica de código nivel Cursor/Devin
"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import ast
import re


class CodeEmbeddingsPro:
    """Sistema de embeddings de código profesional"""
    
    def __init__(self, workspace: str = "/workspace/project/test03"):
        self.workspace = workspace
        self.db_path = os.path.join(workspace, ".openhands_embeddings")
        
        # LAZY LOAD: No inicializar ChromaDB hasta que se necesite
        self._client = None
        self._collection = None

    @property
    def client(self):
        """Lazy load ChromaDB client"""
        if self._client is None:
            os.makedirs(self.db_path, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def collection(self):
        """Lazy load collection"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="code_chunks",
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
        
        # Extensiones soportadas
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.css': 'css',
            '.html': 'html',
            '.json': 'json',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sh': 'bash',
            '.sql': 'sql'
        }
        
        # Patrones a ignorar
        self.ignore_patterns = [
            '__pycache__', 'node_modules', '.git', '.venv', 'venv',
            'dist', 'build', '.eggs', '*.egg-info', '.tox',
            '.openhands_embeddings', '.openhands_checkpoints'
        ]
    
    def should_ignore(self, path: str) -> bool:
        """Verifica si un path debe ser ignorado"""
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        return False
    
    def get_file_hash(self, filepath: str) -> str:
        """Genera hash del contenido del archivo"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def chunk_python_code(self, content: str, filepath: str) -> List[Dict]:
        """Divide código Python en chunks semánticos (funciones, clases)"""
        chunks = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Extraer función completa
                    start = node.lineno - 1
                    end = node.end_lineno if hasattr(node, 'end_lineno') else start + 20
                    func_code = '\n'.join(lines[start:end])
                    
                    # Extraer docstring si existe
                    docstring = ast.get_docstring(node) or ""
                    
                    chunks.append({
                        'type': 'function',
                        'name': node.name,
                        'code': func_code,
                        'docstring': docstring,
                        'start_line': start + 1,
                        'end_line': end,
                        'filepath': filepath
                    })
                    
                elif isinstance(node, ast.ClassDef):
                    # Extraer clase completa
                    start = node.lineno - 1
                    end = node.end_lineno if hasattr(node, 'end_lineno') else start + 50
                    class_code = '\n'.join(lines[start:end])
                    
                    docstring = ast.get_docstring(node) or ""
                    
                    # Extraer métodos de la clase
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    
                    chunks.append({
                        'type': 'class',
                        'name': node.name,
                        'code': class_code,
                        'docstring': docstring,
                        'methods': methods,
                        'start_line': start + 1,
                        'end_line': end,
                        'filepath': filepath
                    })
                    
        except SyntaxError:
            # Si hay error de sintaxis, dividir por líneas
            chunk_size = 50
            for i in range(0, len(content.split('\n')), chunk_size):
                chunk_lines = content.split('\n')[i:i+chunk_size]
                chunks.append({
                    'type': 'block',
                    'name': f'block_{i}',
                    'code': '\n'.join(chunk_lines),
                    'start_line': i + 1,
                    'end_line': i + len(chunk_lines),
                    'filepath': filepath
                })
        
        return chunks
    
    def chunk_generic_code(self, content: str, filepath: str, language: str) -> List[Dict]:
        """Divide código genérico en chunks"""
        chunks = []
        lines = content.split('\n')
        chunk_size = 40  # líneas por chunk
        overlap = 10     # líneas de overlap
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            if not chunk_lines or all(not l.strip() for l in chunk_lines):
                continue
                
            chunks.append({
                'type': 'block',
                'name': f'{language}_block_{i}',
                'code': '\n'.join(chunk_lines),
                'start_line': i + 1,
                'end_line': i + len(chunk_lines),
                'filepath': filepath,
                'language': language
            })
        
        return chunks
    
    def create_embedding_text(self, chunk: Dict) -> str:
        """Crea texto optimizado para embedding"""
        parts = []
        
        # Tipo y nombre
        if chunk.get('type') and chunk.get('name'):
            parts.append(f"{chunk['type']}: {chunk['name']}")
        
        # Docstring si existe
        if chunk.get('docstring'):
            parts.append(f"Description: {chunk['docstring']}")
        
        # Métodos si es clase
        if chunk.get('methods'):
            parts.append(f"Methods: {', '.join(chunk['methods'])}")
        
        # Código
        parts.append(chunk.get('code', ''))
        
        return '\n'.join(parts)
    
    def index_file(self, filepath: str) -> int:
        """Indexa un archivo individual"""
        if self.should_ignore(filepath):
            return 0
            
        ext = Path(filepath).suffix.lower()
        if ext not in self.supported_extensions:
            return 0
        
        language = self.supported_extensions[ext]
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error leyendo {filepath}: {e}")
            return 0
        
        if not content.strip():
            return 0
        
        # Dividir en chunks según el lenguaje
        if language == 'python':
            chunks = self.chunk_python_code(content, filepath)
        else:
            chunks = self.chunk_generic_code(content, filepath, language)
        
        if not chunks:
            return 0
        
        # Preparar datos para ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        file_hash = self.get_file_hash(filepath)
        rel_path = os.path.relpath(filepath, self.workspace)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{rel_path}:{chunk.get('name', i)}:{file_hash[:8]}"
            
            ids.append(chunk_id)
            documents.append(self.create_embedding_text(chunk))
            metadatas.append({
                'filepath': rel_path,
                'type': chunk.get('type', 'block'),
                'name': chunk.get('name', ''),
                'start_line': chunk.get('start_line', 0),
                'end_line': chunk.get('end_line', 0),
                'language': language,
                'file_hash': file_hash
            })
        
        # Eliminar chunks antiguos del mismo archivo
        try:
            existing = self.collection.get(where={"filepath": rel_path})
            if existing['ids']:
                self.collection.delete(ids=existing['ids'])
        except:
            pass
        
        # Añadir nuevos chunks
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def index_workspace(self) -> Dict[str, Any]:
        """Indexa todo el workspace"""
        stats = {
            'files_indexed': 0,
            'chunks_created': 0,
            'errors': []
        }
        
        for root, dirs, files in os.walk(self.workspace):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if not self.should_ignore(d)]
            
            for file in files:
                filepath = os.path.join(root, file)
                if self.should_ignore(filepath):
                    continue
                
                try:
                    chunks = self.index_file(filepath)
                    if chunks > 0:
                        stats['files_indexed'] += 1
                        stats['chunks_created'] += chunks
                except Exception as e:
                    stats['errors'].append(f"{filepath}: {str(e)}")
        
        return stats
    
    def search(self, query: str, n_results: int = 10, filter_language: Optional[str] = None) -> List[Dict]:
        """Búsqueda semántica de código"""
        where = None
        if filter_language:
            where = {"language": filter_language}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                formatted_results.append({
                    'id': id,
                    'filepath': results['metadatas'][0][i].get('filepath'),
                    'type': results['metadatas'][0][i].get('type'),
                    'name': results['metadatas'][0][i].get('name'),
                    'start_line': results['metadatas'][0][i].get('start_line'),
                    'end_line': results['metadatas'][0][i].get('end_line'),
                    'language': results['metadatas'][0][i].get('language'),
                    'code_preview': results['documents'][0][i][:500] if results['documents'][0][i] else '',
                    'relevance': 1 - results['distances'][0][i] if results['distances'][0][i] else 0
                })
        
        return formatted_results
    
    def find_similar(self, code: str, n_results: int = 5) -> List[Dict]:
        """Encuentra código similar"""
        return self.search(code, n_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del índice"""
        count = self.collection.count()
        
        # Contar por lenguaje
        languages = {}
        try:
            all_data = self.collection.get(include=["metadatas"])
            for meta in all_data['metadatas']:
                lang = meta.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
        except:
            pass
        
        return {
            'total_chunks': count,
            'by_language': languages,
            'db_path': self.db_path
        }


# Instancia global
_embeddings_instance = None

def get_embeddings(workspace: str = "/workspace/project/test03") -> CodeEmbeddingsPro:
    """Obtiene o crea instancia de embeddings"""
    global _embeddings_instance
    if _embeddings_instance is None or _embeddings_instance.workspace != workspace:
        _embeddings_instance = CodeEmbeddingsPro(workspace)
    return _embeddings_instance
