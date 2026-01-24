"""
MCP Client - Model Context Protocol Implementation
Conecta con servidores MCP para extender las capacidades del agente
"""

import asyncio
import json
import subprocess
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading
import queue


@dataclass
class MCPServer:
    """Representa un servidor MCP"""
    id: str
    name: str
    description: str
    command: str
    args: List[str]
    env: Dict[str, str] = None
    status: str = "disconnected"
    process: subprocess.Popen = None
    tools: List[Dict] = None


class MCPClient:
    """Cliente para conectar con servidores MCP"""
    
    # Servidores MCP disponibles
    AVAILABLE_SERVERS = {
        "filesystem": MCPServer(
            id="filesystem",
            name="Filesystem MCP",
            description="Acceso a archivos del sistema",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
        ),
        "github": MCPServer(
            id="github",
            name="GitHub MCP", 
            description="Issues, PRs, Repositorios",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN", "")}
        ),
        "memory": MCPServer(
            id="memory",
            name="Memory MCP",
            description="Memoria persistente para el agente",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"]
        ),
        "brave-search": MCPServer(
            id="brave-search",
            name="Brave Search MCP",
            description="Búsqueda web con Brave",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
        ),
        "sqlite": MCPServer(
            id="sqlite",
            name="SQLite MCP",
            description="Consultas a bases de datos SQLite",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sqlite"]
        ),
        "puppeteer": MCPServer(
            id="puppeteer",
            name="Puppeteer MCP",
            description="Automatización de navegador",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"]
        )
    }
    
    def __init__(self):
        self.connected_servers: Dict[str, MCPServer] = {}
        self.message_id = 0
        self._lock = threading.Lock()
    
    def _get_next_id(self) -> int:
        """Obtiene el siguiente ID de mensaje"""
        with self._lock:
            self.message_id += 1
            return self.message_id
    
    def list_available_servers(self) -> List[Dict]:
        """Lista todos los servidores MCP disponibles"""
        servers = []
        for server_id, server in self.AVAILABLE_SERVERS.items():
            servers.append({
                "id": server.id,
                "name": server.name,
                "description": server.description,
                "status": self.connected_servers.get(server_id, server).status,
                "requires_env": bool(server.env),
                "env_vars": list(server.env.keys()) if server.env else []
            })
        return servers
    
    def get_status(self) -> Dict:
        """Estado general del cliente MCP"""
        return {
            "enabled": True,
            "connected_servers": list(self.connected_servers.keys()),
            "available_servers": list(self.AVAILABLE_SERVERS.keys()),
            "total_tools": sum(
                len(s.tools or []) 
                for s in self.connected_servers.values()
            )
        }
    
    async def connect_server(self, server_id: str) -> Dict:
        """Conecta a un servidor MCP"""
        if server_id not in self.AVAILABLE_SERVERS:
            return {"success": False, "error": f"Servidor '{server_id}' no encontrado"}
        
        if server_id in self.connected_servers:
            return {"success": True, "message": "Ya conectado", "server": server_id}
        
        server = self.AVAILABLE_SERVERS[server_id]
        
        # Verificar variables de entorno requeridas
        if server.env:
            missing = [k for k, v in server.env.items() if not v]
            if missing:
                return {
                    "success": False, 
                    "error": f"Variables de entorno faltantes: {', '.join(missing)}"
                }
        
        try:
            # Verificar que npx esté disponible
            npx_check = subprocess.run(["which", "npx"], capture_output=True)
            if npx_check.returncode != 0:
                # Intentar instalar node/npm
                return {
                    "success": False,
                    "error": "npx no disponible. Instala Node.js para usar MCP servers."
                }
            
            # Preparar entorno
            env = os.environ.copy()
            if server.env:
                env.update(server.env)
            
            # Iniciar proceso del servidor
            process = subprocess.Popen(
                [server.command] + server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )
            
            # Enviar mensaje de inicialización
            init_message = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "OpenHands Chat",
                        "version": "1.0.0"
                    }
                }
            }
            
            process.stdin.write(json.dumps(init_message) + "\n")
            process.stdin.flush()
            
            # Leer respuesta (con timeout)
            try:
                # Esperar respuesta
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line)
                    
                    # Listar herramientas
                    tools_message = {
                        "jsonrpc": "2.0",
                        "id": self._get_next_id(),
                        "method": "tools/list",
                        "params": {}
                    }
                    process.stdin.write(json.dumps(tools_message) + "\n")
                    process.stdin.flush()
                    
                    tools_line = process.stdout.readline()
                    tools_response = json.loads(tools_line) if tools_line else {}
                    
                    # Guardar servidor conectado
                    server.process = process
                    server.status = "connected"
                    server.tools = tools_response.get("result", {}).get("tools", [])
                    self.connected_servers[server_id] = server
                    
                    return {
                        "success": True,
                        "server": server_id,
                        "tools": len(server.tools),
                        "message": f"Conectado a {server.name}"
                    }
            except Exception as e:
                process.terminate()
                return {"success": False, "error": f"Error de comunicación: {str(e)}"}
            
        except FileNotFoundError:
            return {"success": False, "error": "npx no encontrado. Instala Node.js"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def disconnect_server(self, server_id: str) -> Dict:
        """Desconecta un servidor MCP"""
        if server_id not in self.connected_servers:
            return {"success": False, "error": "Servidor no conectado"}
        
        try:
            server = self.connected_servers[server_id]
            if server.process:
                server.process.terminate()
                server.process.wait(timeout=5)
            
            server.status = "disconnected"
            server.tools = None
            del self.connected_servers[server_id]
            
            return {"success": True, "message": f"Desconectado de {server.name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict) -> Dict:
        """Llama a una herramienta de un servidor MCP"""
        if server_id not in self.connected_servers:
            return {"success": False, "error": "Servidor no conectado"}
        
        server = self.connected_servers[server_id]
        
        try:
            # Enviar llamada a herramienta
            call_message = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            server.process.stdin.write(json.dumps(call_message) + "\n")
            server.process.stdin.flush()
            
            # Leer respuesta
            response_line = server.process.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                result = response.get("result", {})
                
                return {
                    "success": True,
                    "result": result,
                    "tool": tool_name
                }
            
            return {"success": False, "error": "Sin respuesta del servidor"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_server_tools(self, server_id: str) -> List[Dict]:
        """Obtiene las herramientas de un servidor conectado"""
        if server_id not in self.connected_servers:
            return []
        return self.connected_servers[server_id].tools or []
    
    def cleanup(self):
        """Limpia todas las conexiones"""
        for server_id in list(self.connected_servers.keys()):
            try:
                server = self.connected_servers[server_id]
                if server.process:
                    server.process.terminate()
            except:
                pass
        self.connected_servers.clear()


# Singleton
_mcp_client: Optional[MCPClient] = None

def get_mcp_client() -> MCPClient:
    """Obtiene la instancia del cliente MCP"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


def check_mcp_available() -> Dict:
    """Verifica si MCP está disponible"""
    # Verificar npx
    try:
        result = subprocess.run(["which", "npx"], capture_output=True)
        npx_available = result.returncode == 0
    except:
        npx_available = False
    
    return {
        "npx_available": npx_available,
        "node_required": not npx_available,
        "available": npx_available
    }
