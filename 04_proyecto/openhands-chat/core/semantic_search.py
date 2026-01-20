"""
Semantic Search - Búsqueda semántica de código con ChromaDB

Arquitectura similar a Cursor:
1. Divide código en chunks semánticos (funciones, clases, bloques)
2. Genera embeddings con sentence-transformers
3. Almacena en ChromaDB (vector database)
4. Permite búsquedas como "¿dónde está la autenticación?"

Uso:
    semantic = SemanticSearch("/path/to/project")
    semantic.index()  # Indexa todo el proyecto
    
    # Búsqueda semántica
    results = semantic.search("¿dónde se maneja la autenticación?")
    # Returns: [{"file": "auth.py", "line": 45, "content": "...", "score": 0.89}]
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

# Intentar importar ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[SEMANTIC] ChromaDB no disponible, instalar con: pip install chromadb")

# Intentar importar sentence-transformers para embeddings locales
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[SEMANTIC] sentence-transformers no disponible")


@dataclass
class CodeChunk:
    """Un chunk de código semántico"""
    id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str  # "function", "class", "block", "file"
    name: str  # Nombre del símbolo (función, clase, etc.)
    language: str
    hash: str  # Hash del contenido para detectar cambios


class SemanticSearch:
    """
    Motor de búsqueda semántica para código.
    
    Usa ChromaDB como vector store y sentence-transformers 
    para generar embeddings localmente (sin API externa).
    """
    
    # Extensiones soportadas
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", 
        ".json", ".md", ".yaml", ".yml", ".sh", ".sql"
    }
    
    # Patrones a ignorar
    IGNORE_PATTERNS = {
        "node_modules", "__pycache__", ".git", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
        ".code_index.json", ".chroma"
    }
    
    # Modelo de embeddings (pequeño y rápido)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dims, ~80MB
    
    def __init__(self, workspace: str, persist_dir: str = None):
        """
        Inicializa el motor de búsqueda semántica.
        
        Args:
            workspace: Directorio raíz del proyecto
            persist_dir: Directorio para persistir la base de datos
        """
        self.workspace = Path(workspace)
        self.persist_dir = persist_dir or str(self.workspace / ".chroma")
        
        # Estado
        self._initialized = False
        self._client = None
        self._collection = None
        self._embedder = None
        self._file_hashes: Dict[str, str] = {}  # Para Merkle tree
        
    def _ensure_initialized(self):
        """Inicializa ChromaDB y el modelo de embeddings (lazy loading)"""
        if self._initialized:
            return True
            
        if not CHROMADB_AVAILABLE:
            print("[SEMANTIC] ChromaDB no disponible")
            return False
        
        try:
            # Inicializar ChromaDB con persistencia
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Crear o obtener colección
            collection_name = f"code_{hashlib.md5(str(self.workspace).encode()).hexdigest()[:8]}"
            
            # Usar embeddings de ChromaDB por defecto (no requiere modelo externo)
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"workspace": str(self.workspace)}
            )
            
            # Intentar cargar modelo de embeddings local
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self._embedder = SentenceTransformer(self.EMBEDDING_MODEL)
                    print(f"[SEMANTIC] Modelo de embeddings cargado: {self.EMBEDDING_MODEL}")
                except Exception as e:
                    print(f"[SEMANTIC] No se pudo cargar modelo local: {e}")
                    self._embedder = None
            
            self._initialized = True
            print(f"[SEMANTIC] Inicializado. Colección: {collection_name}")
            return True
            
        except Exception as e:
            print(f"[SEMANTIC] Error inicializando: {e}")
            return False
    
    def _should_ignore(self, path: Path) -> bool:
        """Verifica si un path debe ser ignorado"""
        parts = path.parts
        return any(p in self.IGNORE_PATTERNS for p in parts)
    
    def _get_file_hash(self, content: str) -> str:
        """Genera hash del contenido (para Merkle tree)"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _chunk_python(self, content: str, file_path: str) -> List[CodeChunk]:
        """Divide código Python en chunks semánticos"""
        chunks = []
        lines = content.split('\n')
        
        # Regex para detectar funciones y clases
        func_pattern = re.compile(r'^(\s*)def\s+(\w+)\s*\(')
        class_pattern = re.compile(r'^(\s*)class\s+(\w+)')
        
        current_chunk = []
        current_type = "block"
        current_name = "module"
        current_start = 1
        current_indent = 0
        
        for i, line in enumerate(lines, 1):
            func_match = func_pattern.match(line)
            class_match = class_pattern.match(line)
            
            if func_match or class_match:
                # Guardar chunk anterior si existe
                if current_chunk:
                    chunk_content = '\n'.join(current_chunk)
                    if len(chunk_content.strip()) > 10:  # Ignorar chunks muy pequeños
                        chunks.append(CodeChunk(
                            id=f"{file_path}:{current_start}-{i-1}",
                            file_path=file_path,
                            start_line=current_start,
                            end_line=i-1,
                            content=chunk_content,
                            chunk_type=current_type,
                            name=current_name,
                            language="python",
                            hash=self._get_file_hash(chunk_content)
                        ))
                
                # Nuevo chunk
                current_chunk = [line]
                current_start = i
                
                if func_match:
                    current_type = "function"
                    current_name = func_match.group(2)
                    current_indent = len(func_match.group(1))
                else:
                    current_type = "class"
                    current_name = class_match.group(2)
                    current_indent = len(class_match.group(1))
            else:
                current_chunk.append(line)
        
        # Último chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if len(chunk_content.strip()) > 10:
                chunks.append(CodeChunk(
                    id=f"{file_path}:{current_start}-{len(lines)}",
                    file_path=file_path,
                    start_line=current_start,
                    end_line=len(lines),
                    content=chunk_content,
                    chunk_type=current_type,
                    name=current_name,
                    language="python",
                    hash=self._get_file_hash(chunk_content)
                ))
        
        return chunks
    
    def _chunk_javascript(self, content: str, file_path: str) -> List[CodeChunk]:
        """Divide código JavaScript/TypeScript en chunks semánticos"""
        chunks = []
        lines = content.split('\n')
        
        # Regex para detectar funciones
        func_patterns = [
            re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)'),
            re.compile(r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\('),
            re.compile(r'^\s*(?:export\s+)?(?:class|interface)\s+(\w+)'),
        ]
        
        current_chunk = []
        current_type = "block"
        current_name = "module"
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            is_definition = False
            for pattern in func_patterns:
                match = pattern.match(line)
                if match:
                    is_definition = True
                    # Guardar chunk anterior
                    if current_chunk:
                        chunk_content = '\n'.join(current_chunk)
                        if len(chunk_content.strip()) > 10:
                            chunks.append(CodeChunk(
                                id=f"{file_path}:{current_start}-{i-1}",
                                file_path=file_path,
                                start_line=current_start,
                                end_line=i-1,
                                content=chunk_content,
                                chunk_type=current_type,
                                name=current_name,
                                language="javascript",
                                hash=self._get_file_hash(chunk_content)
                            ))
                    
                    current_chunk = [line]
                    current_start = i
                    current_name = match.group(1)
                    current_type = "function" if "function" in line or "=>" in line or "const" in line else "class"
                    break
            
            if not is_definition:
                current_chunk.append(line)
        
        # Último chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if len(chunk_content.strip()) > 10:
                chunks.append(CodeChunk(
                    id=f"{file_path}:{current_start}-{len(lines)}",
                    file_path=file_path,
                    start_line=current_start,
                    end_line=len(lines),
                    content=chunk_content,
                    chunk_type=current_type,
                    name=current_name,
                    language="javascript",
                    hash=self._get_file_hash(chunk_content)
                ))
        
        return chunks
    
    def _chunk_generic(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Divide archivos genéricos en chunks por tamaño"""
        chunks = []
        lines = content.split('\n')
        
        # Chunks de ~50 líneas con overlap de 10
        chunk_size = 50
        overlap = 10
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) > 10:
                chunks.append(CodeChunk(
                    id=f"{file_path}:{i+1}-{min(i+chunk_size, len(lines))}",
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=min(i + chunk_size, len(lines)),
                    content=chunk_content,
                    chunk_type="block",
                    name=f"block_{i//chunk_size}",
                    language=language,
                    hash=self._get_file_hash(chunk_content)
                ))
        
        return chunks
    
    def _chunk_file(self, file_path: Path, content: str) -> List[CodeChunk]:
        """Divide un archivo en chunks semánticos según su tipo"""
        rel_path = str(file_path.relative_to(self.workspace))
        ext = file_path.suffix.lower()
        
        if ext == ".py":
            return self._chunk_python(content, rel_path)
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            return self._chunk_javascript(content, rel_path)
        else:
            lang = ext.lstrip(".")
            return self._chunk_generic(content, rel_path, lang)
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding para un texto"""
        if self._embedder:
            try:
                return self._embedder.encode(text).tolist()
            except:
                pass
        return None
    
    def index(self, incremental: bool = True) -> Dict[str, Any]:
        """
        Indexa el proyecto completo.
        
        Args:
            incremental: Si True, solo re-indexa archivos modificados (Merkle tree)
            
        Returns:
            Estadísticas del indexado
        """
        if not self._ensure_initialized():
            return {"error": "No se pudo inicializar ChromaDB"}
        
        stats = {
            "files_scanned": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "chunks_added": 0,
            "chunks_updated": 0,
            "errors": []
        }
        
        # Cargar hashes anteriores para Merkle tree
        hash_file = self.workspace / ".semantic_hashes.json"
        if incremental and hash_file.exists():
            try:
                self._file_hashes = json.loads(hash_file.read_text())
            except:
                self._file_hashes = {}
        
        all_chunks = []
        new_hashes = {}
        
        # Escanear archivos
        for path in self.workspace.rglob("*"):
            if path.is_dir() or self._should_ignore(path):
                continue
            
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            stats["files_scanned"] += 1
            rel_path = str(path.relative_to(self.workspace))
            
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                file_hash = self._get_file_hash(content)
                new_hashes[rel_path] = file_hash
                
                # Merkle tree: skip si no cambió
                if incremental and self._file_hashes.get(rel_path) == file_hash:
                    stats["files_skipped"] += 1
                    continue
                
                # Dividir en chunks
                chunks = self._chunk_file(path, content)
                all_chunks.extend(chunks)
                stats["files_indexed"] += 1
                
            except Exception as e:
                stats["errors"].append(f"{rel_path}: {str(e)}")
        
        # Agregar chunks a ChromaDB
        if all_chunks:
            ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            for chunk in all_chunks:
                ids.append(chunk.id)
                
                # Documento: combinación de nombre + contenido para mejor búsqueda
                doc = f"{chunk.chunk_type} {chunk.name}:\n{chunk.content[:1000]}"
                documents.append(doc)
                
                metadatas.append({
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name,
                    "language": chunk.language
                })
                
                # Generar embedding si tenemos modelo local
                if self._embedder:
                    emb = self._generate_embedding(doc)
                    if emb:
                        embeddings.append(emb)
            
            try:
                # Primero eliminar chunks existentes de archivos modificados
                files_to_update = set(c.file_path for c in all_chunks)
                for file_path in files_to_update:
                    try:
                        self._collection.delete(
                            where={"file_path": file_path}
                        )
                    except:
                        pass
                
                # Agregar nuevos chunks
                if embeddings and len(embeddings) == len(ids):
                    self._collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                else:
                    self._collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                
                stats["chunks_added"] = len(all_chunks)
                
            except Exception as e:
                stats["errors"].append(f"Error agregando chunks: {str(e)}")
        
        # Guardar hashes para próximo indexado incremental
        self._file_hashes = new_hashes
        hash_file.write_text(json.dumps(new_hashes, indent=2))
        
        return stats
    
    def search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica en el código.
        
        Args:
            query: Pregunta en lenguaje natural (ej: "¿dónde está la autenticación?")
            n_results: Número máximo de resultados
            
        Returns:
            Lista de chunks relevantes con scores
        """
        if not self._ensure_initialized():
            return []
        
        try:
            # Generar embedding de la query si tenemos modelo
            query_embedding = None
            if self._embedder:
                query_embedding = self._generate_embedding(query)
            
            # Buscar
            if query_embedding:
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
            
            # Formatear resultados
            formatted = []
            if results and results.get("ids") and results["ids"][0]:
                for i, id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    
                    # Convertir distancia a score (1 = mejor, 0 = peor)
                    score = 1 / (1 + distance) if distance else 1
                    
                    formatted.append({
                        "id": id,
                        "file": metadata.get("file_path", ""),
                        "start_line": metadata.get("start_line", 0),
                        "end_line": metadata.get("end_line", 0),
                        "type": metadata.get("chunk_type", ""),
                        "name": metadata.get("name", ""),
                        "language": metadata.get("language", ""),
                        "score": round(score, 3),
                        "content": results["documents"][0][i][:500] if results.get("documents") else ""
                    })
            
            return formatted
            
        except Exception as e:
            print(f"[SEMANTIC] Error en búsqueda: {e}")
            return []
    
    def find_similar(self, file_path: str, line: int, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Encuentra código similar a un fragmento específico.
        
        Args:
            file_path: Ruta del archivo
            line: Número de línea
            n_results: Número de resultados
            
        Returns:
            Chunks de código similares
        """
        if not self._ensure_initialized():
            return []
        
        # Leer el código fuente
        full_path = self.workspace / file_path
        if not full_path.exists():
            return []
        
        try:
            content = full_path.read_text()
            lines = content.split('\n')
            
            # Obtener contexto (±10 líneas)
            start = max(0, line - 10)
            end = min(len(lines), line + 10)
            context = '\n'.join(lines[start:end])
            
            # Buscar similares
            return self.search(context, n_results)
            
        except Exception as e:
            print(f"[SEMANTIC] Error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del índice"""
        if not self._ensure_initialized():
            return {"initialized": False}
        
        try:
            count = self._collection.count()
            return {
                "initialized": True,
                "total_chunks": count,
                "workspace": str(self.workspace),
                "persist_dir": self.persist_dir,
                "has_local_embeddings": self._embedder is not None
            }
        except:
            return {"initialized": True, "error": "No se pudo obtener stats"}
    
    def clear(self):
        """Limpia el índice completamente"""
        if self._client and self._collection:
            try:
                collection_name = self._collection.name
                self._client.delete_collection(collection_name)
                self._collection = self._client.create_collection(
                    name=collection_name,
                    metadata={"workspace": str(self.workspace)}
                )
                self._file_hashes = {}
                
                # Limpiar archivo de hashes
                hash_file = self.workspace / ".semantic_hashes.json"
                if hash_file.exists():
                    hash_file.unlink()
                    
            except Exception as e:
                print(f"[SEMANTIC] Error limpiando: {e}")


# Instancia global
_global_semantic: Optional[SemanticSearch] = None


def get_semantic_search(workspace: str = None) -> Optional[SemanticSearch]:
    """Obtiene o crea el motor de búsqueda semántica global"""
    global _global_semantic
    
    if _global_semantic is None and workspace:
        _global_semantic = SemanticSearch(workspace)
    
    return _global_semantic


def set_semantic_search(semantic: SemanticSearch):
    """Establece el motor de búsqueda semántica global"""
    global _global_semantic
    _global_semantic = semantic
