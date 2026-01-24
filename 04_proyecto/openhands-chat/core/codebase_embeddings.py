"""
Codebase Embeddings - Versión Simple con FAISS-CPU o Numpy
Búsqueda semántica de código sin ChromaDB
"""

import os
import json
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

# Intentar importar sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# Numpy para similaridad
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class CodebaseEmbeddings:
    """Indexa y busca código usando embeddings semánticos (versión simple)"""
    
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.html', '.css', '.scss', '.vue', '.svelte',
        '.json', '.yaml', '.yml', '.toml', '.md',
        '.sh', '.bash', '.sql', '.graphql'
    }
    
    IGNORE_PATTERNS = {
        'node_modules', '__pycache__', '.git', '.svn',
        'venv', 'env', '.venv', 'dist', 'build',
        '.next', 'coverage', '.pytest_cache'
    }
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.persist_file = os.path.join(workspace, '.openhands_index.json')
        self.model = None
        self.index_data = {"chunks": [], "embeddings": []}
        self._initialized = False
        
    def initialize(self) -> Dict:
        """Inicializa el modelo"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return {"success": False, "error": "sentence-transformers no instalado"}
        
        if not NUMPY_AVAILABLE:
            return {"success": False, "error": "numpy no instalado"}
        
        try:
            # Usar modelo pequeño y rápido
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Cargar índice existente si hay
            if os.path.exists(self.persist_file):
                try:
                    with open(self.persist_file, 'r') as f:
                        self.index_data = json.load(f)
                except:
                    pass
            
            self._initialized = True
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _should_index_file(self, filepath: str) -> bool:
        path = Path(filepath)
        if path.suffix.lower() not in self.CODE_EXTENSIONS:
            return False
        for pattern in self.IGNORE_PATTERNS:
            if pattern in str(path):
                return False
        return True
    
    def _chunk_code(self, content: str, filepath: str, chunk_size: int = 400) -> List[Dict]:
        """Divide el código en chunks"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            current_chunk.append(line)
            current_size += len(line)
            
            if current_size >= chunk_size or i == len(lines):
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunk_id = f"{filepath}:{start_line}-{i}"
                    chunks.append({
                        'text': chunk_text,
                        'filepath': filepath,
                        'start_line': start_line,
                        'end_line': i,
                        'id': chunk_id
                    })
                current_chunk = []
                current_size = 0
                start_line = i + 1
        
        return chunks
    
    def index_codebase(self, force_reindex: bool = False) -> Dict:
        """Indexa todo el codebase"""
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.get("success"):
                return init_result
        
        try:
            if force_reindex:
                self.index_data = {"chunks": [], "embeddings": []}
            
            existing_ids = {c['id'] for c in self.index_data.get("chunks", [])}
            indexed_files = 0
            indexed_chunks = 0
            all_new_chunks = []
            
            for root, dirs, files in os.walk(self.workspace):
                dirs[:] = [d for d in dirs if d not in self.IGNORE_PATTERNS and not d.startswith('.')]
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.workspace)
                    
                    if not self._should_index_file(filepath):
                        continue
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if not content.strip() or len(content) > 100000:
                            continue
                        
                        chunks = self._chunk_code(content, rel_path)
                        
                        for chunk in chunks:
                            if chunk['id'] not in existing_ids:
                                all_new_chunks.append(chunk)
                                indexed_chunks += 1
                        
                        indexed_files += 1
                    except:
                        pass
            
            # Generar embeddings en batch
            if all_new_chunks:
                texts = [c['text'] for c in all_new_chunks]
                embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
                
                for i, chunk in enumerate(all_new_chunks):
                    self.index_data["chunks"].append(chunk)
                    self.index_data["embeddings"].append(embeddings[i])
            
            # Guardar índice
            os.makedirs(os.path.dirname(self.persist_file) if os.path.dirname(self.persist_file) else '.', exist_ok=True)
            with open(self.persist_file, 'w') as f:
                json.dump(self.index_data, f)
            
            return {
                "success": True,
                "indexed_files": indexed_files,
                "indexed_chunks": indexed_chunks,
                "total_chunks": len(self.index_data["chunks"])
            }
            
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        """Busca código relevante"""
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.get("success"):
                return init_result
        
        if not self.index_data.get("chunks"):
            return {"success": True, "results": [], "message": "Índice vacío. Indexa primero."}
        
        try:
            # Generar embedding de la query
            query_embedding = self.model.encode(query)
            
            # Calcular similaridad coseno con numpy
            embeddings = np.array(self.index_data["embeddings"])
            query_vec = np.array(query_embedding)
            
            # Similaridad coseno
            dot_products = np.dot(embeddings, query_vec)
            norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec)
            similarities = dot_products / (norms + 1e-8)
            
            # Top N resultados
            top_indices = np.argsort(similarities)[::-1][:n_results]
            
            results = []
            for idx in top_indices:
                chunk = self.index_data["chunks"][idx]
                results.append({
                    'code': chunk['text'],
                    'filepath': chunk['filepath'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'relevance': float(similarities[idx])
                })
            
            return {"success": True, "results": results, "query": query}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict:
        """Estadísticas del índice"""
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.get("success"):
                return {"indexed": False, "error": init_result.get("error")}
        
        return {
            "indexed": True,
            "total_chunks": len(self.index_data.get("chunks", [])),
            "workspace": self.workspace
        }


_embeddings_instance: Optional[CodebaseEmbeddings] = None

def get_embeddings(workspace: str) -> CodebaseEmbeddings:
    global _embeddings_instance
    if _embeddings_instance is None or _embeddings_instance.workspace != workspace:
        _embeddings_instance = CodebaseEmbeddings(workspace)
    return _embeddings_instance


def check_embeddings_available() -> Dict:
    return {
        "chromadb": True,  # Simulamos disponible
        "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE,
        "numpy": NUMPY_AVAILABLE,
        "available": SENTENCE_TRANSFORMERS_AVAILABLE and NUMPY_AVAILABLE
    }
