#!/usr/bin/env python3
"""
Production Deploy - Deploy a producción con dominio y SSL.

Permite configurar y desplegar aplicaciones con:
- Dominio personalizado
- SSL automático via Let's Encrypt
- Nginx como reverse proxy
- Docker containers

Uso CLI:
    python -m core.production_deploy status
    python -m core.production_deploy setup-domain <domain>
    python -m core.production_deploy setup-ssl <domain>
    python -m core.production_deploy deploy
    python -m core.production_deploy verify <domain>
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeployConfig:
    """Configuración de deploy"""
    domain: str = ""
    ssl_enabled: bool = False
    ssl_email: str = ""
    server_ip: str = ""
    container_name: str = "openhands-chat"
    internal_port: int = 12000
    external_port: int = 80
    ssl_port: int = 443


@dataclass
class DeployResult:
    """Resultado de operación de deploy"""
    success: bool
    message: str
    domain: str = ""
    ssl_status: str = ""
    url: str = ""
    error: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "domain": self.domain,
            "ssl_status": self.ssl_status,
            "url": self.url,
            "error": self.error,
            "details": self.details
        }


class ProductionDeployManager:
    """
    Gestor de deploy a producción.
    
    Maneja:
    - Configuración de dominio
    - Certificados SSL via Let's Encrypt
    - Nginx como reverse proxy
    - Deploy de containers Docker
    """
    
    def __init__(self):
        self.config = self._load_config()
        self._ssh_client = None
    
    def _load_config(self) -> DeployConfig:
        """Carga configuración desde BD o defaults"""
        try:
            from config.database import Database
            db = Database()
            return DeployConfig(
                domain=db.get_setting('deploy_domain', ''),
                ssl_enabled=db.get_setting('deploy_ssl_enabled', 'false') == 'true',
                ssl_email=db.get_setting('deploy_ssl_email', ''),
                server_ip=db.get_setting('hetzner_server_ip', '178.156.193.106'),
                container_name=db.get_setting('deploy_container', 'openhands-chat'),
            )
        except Exception as e:
            logger.warning(f"Could not load config from DB: {e}")
            return DeployConfig(server_ip='178.156.193.106')
    
    def _save_config(self):
        """Guarda configuración en BD"""
        try:
            from config.database import Database
            db = Database()
            db.set_setting('deploy_domain', self.config.domain)
            db.set_setting('deploy_ssl_enabled', 'true' if self.config.ssl_enabled else 'false')
            db.set_setting('deploy_ssl_email', self.config.ssl_email)
            db.set_setting('hetzner_server_ip', self.config.server_ip)
        except Exception as e:
            logger.warning(f"Could not save config to DB: {e}")
    
    def _get_ssh_client(self):
        """Obtiene cliente SSH al servidor"""
        if self._ssh_client is None:
            try:
                import paramiko
                self._ssh_client = paramiko.SSHClient()
                self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Cargar credenciales
                try:
                    from config.database import Database
                    db = Database()
                    password = db.get_setting('hetzner_ssh_password', 'kCJHc3sVMwNv')
                except:
                    password = 'kCJHc3sVMwNv'
                
                self._ssh_client.connect(
                    self.config.server_ip,
                    username='root',
                    password=password,
                    timeout=15
                )
            except Exception as e:
                raise RuntimeError(f"SSH connection failed: {e}")
        return self._ssh_client
    
    def _run_remote(self, cmd: str, timeout: int = 30) -> tuple:
        """Ejecuta comando remoto via SSH"""
        ssh = self._get_ssh_client()
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code
    
    def get_status(self) -> DeployResult:
        """Obtiene estado actual del deploy"""
        try:
            details = {
                "server_ip": self.config.server_ip,
                "domain": self.config.domain or "(no configurado)",
                "ssl_enabled": self.config.ssl_enabled,
                "container": self.config.container_name,
                "timestamp": datetime.now().isoformat()
            }
            
            # Verificar servidor
            try:
                out, err, code = self._run_remote("docker ps --format '{{.Names}}' | grep -q openhands-chat && echo 'running' || echo 'stopped'")
                details["container_status"] = out.strip()
            except Exception as e:
                details["container_status"] = f"error: {e}"
            
            # Verificar nginx
            try:
                out, err, code = self._run_remote("systemctl is-active nginx 2>/dev/null || echo 'not-installed'")
                details["nginx_status"] = out.strip()
            except:
                details["nginx_status"] = "unknown"
            
            # Verificar SSL
            if self.config.domain:
                try:
                    out, err, code = self._run_remote(f"ls /etc/letsencrypt/live/{self.config.domain}/fullchain.pem 2>/dev/null && echo 'valid' || echo 'not-found'")
                    details["ssl_certificate"] = out.strip()
                except:
                    details["ssl_certificate"] = "unknown"
            
            url = f"https://{self.config.domain}" if self.config.ssl_enabled and self.config.domain else f"http://{self.config.server_ip}"
            
            return DeployResult(
                success=True,
                message="Estado de producción obtenido",
                domain=self.config.domain,
                ssl_status="enabled" if self.config.ssl_enabled else "disabled",
                url=url,
                details=details
            )
        except Exception as e:
            return DeployResult(
                success=False,
                message="Error obteniendo estado",
                error=str(e)
            )
    
    def setup_domain(self, domain: str) -> DeployResult:
        """Configura un dominio para el servidor"""
        try:
            if not domain:
                return DeployResult(success=False, message="Dominio requerido", error="empty_domain")
            
            self.config.domain = domain
            
            # Crear configuración nginx
            nginx_config = f"""
server {{
    listen 80;
    server_name {domain};
    
    location / {{
        proxy_pass http://127.0.0.1:{self.config.internal_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }}
}}
"""
            
            # Instalar nginx si no existe
            self._run_remote("apt-get update && apt-get install -y nginx", timeout=120)
            
            # Guardar configuración
            config_path = f"/etc/nginx/sites-available/{domain}"
            self._run_remote(f"cat > {config_path} << 'NGINX_EOF'\n{nginx_config}\nNGINX_EOF")
            
            # Habilitar sitio
            self._run_remote(f"ln -sf {config_path} /etc/nginx/sites-enabled/")
            self._run_remote("rm -f /etc/nginx/sites-enabled/default")
            
            # Recargar nginx
            out, err, code = self._run_remote("nginx -t && systemctl reload nginx")
            if code != 0:
                return DeployResult(
                    success=False,
                    message="Error en configuración nginx",
                    error=err
                )
            
            self._save_config()
            
            return DeployResult(
                success=True,
                message=f"Dominio {domain} configurado correctamente",
                domain=domain,
                url=f"http://{domain}",
                details={
                    "nginx_config": config_path,
                    "next_step": f"Ejecuta: python -m core.production_deploy setup-ssl {domain}"
                }
            )
        except Exception as e:
            return DeployResult(
                success=False,
                message="Error configurando dominio",
                error=str(e)
            )
    
    def setup_ssl(self, domain: str, email: str = "") -> DeployResult:
        """Configura SSL con Let's Encrypt"""
        try:
            if not domain:
                domain = self.config.domain
            if not domain:
                return DeployResult(success=False, message="Dominio requerido", error="no_domain")
            
            if not email:
                email = self.config.ssl_email or f"admin@{domain}"
            
            # Instalar certbot
            self._run_remote("apt-get update && apt-get install -y certbot python3-certbot-nginx", timeout=120)
            
            # Obtener certificado
            cmd = f"certbot --nginx -d {domain} --non-interactive --agree-tos --email {email} --redirect"
            out, err, code = self._run_remote(cmd, timeout=180)
            
            if code != 0:
                # Intentar con staging para testing
                if "too many certificates" in err.lower() or "rate limit" in err.lower():
                    return DeployResult(
                        success=False,
                        message="Rate limit de Let's Encrypt alcanzado",
                        error=err,
                        details={"suggestion": "Espera unas horas o usa --staging para pruebas"}
                    )
                return DeployResult(
                    success=False,
                    message="Error obteniendo certificado SSL",
                    error=err
                )
            
            self.config.ssl_enabled = True
            self.config.ssl_email = email
            self._save_config()
            
            return DeployResult(
                success=True,
                message=f"SSL configurado para {domain}",
                domain=domain,
                ssl_status="enabled",
                url=f"https://{domain}",
                details={
                    "certificate_path": f"/etc/letsencrypt/live/{domain}/",
                    "auto_renewal": "Certbot configura renovación automática"
                }
            )
        except Exception as e:
            return DeployResult(
                success=False,
                message="Error configurando SSL",
                error=str(e)
            )
    
    def deploy(self, rebuild: bool = False) -> DeployResult:
        """Despliega la aplicación a producción"""
        try:
            details = {"steps": []}
            
            # 1. Pull últimos cambios
            out, err, code = self._run_remote(
                "cd /opt/openhands-chat && git pull origin main 2>&1",
                timeout=60
            )
            details["steps"].append({"git_pull": out.strip() or "ok"})
            
            # 2. Rebuild si es necesario
            if rebuild:
                out, err, code = self._run_remote(
                    "cd /opt/openhands-chat/04_proyecto/openhands-chat && docker-compose build --no-cache",
                    timeout=600
                )
                details["steps"].append({"docker_build": "completed" if code == 0 else err})
            
            # 3. Restart container
            out, err, code = self._run_remote(
                "docker restart openhands-chat",
                timeout=30
            )
            details["steps"].append({"container_restart": "ok" if code == 0 else err})
            
            # 4. Verificar que está corriendo
            import time
            time.sleep(5)
            out, err, code = self._run_remote("docker ps | grep openhands-chat | grep -q Up && echo 'running'")
            
            if "running" not in out:
                return DeployResult(
                    success=False,
                    message="Container no está corriendo después del deploy",
                    error=err,
                    details=details
                )
            
            url = f"https://{self.config.domain}" if self.config.ssl_enabled and self.config.domain else f"http://{self.config.server_ip}"
            
            return DeployResult(
                success=True,
                message="Deploy a producción completado",
                domain=self.config.domain,
                ssl_status="enabled" if self.config.ssl_enabled else "disabled",
                url=url,
                details=details
            )
        except Exception as e:
            return DeployResult(
                success=False,
                message="Error en deploy",
                error=str(e)
            )
    
    def verify(self, domain: str = "") -> DeployResult:
        """Verifica que el dominio y SSL funcionan correctamente"""
        try:
            import httpx
            
            if not domain:
                domain = self.config.domain
            if not domain:
                domain = self.config.server_ip
            
            results = {}
            
            # Test HTTP
            try:
                with httpx.Client(timeout=10, follow_redirects=True) as client:
                    resp = client.get(f"http://{domain}")
                    results["http"] = {
                        "status": resp.status_code,
                        "redirected": str(resp.url) != f"http://{domain}",
                        "final_url": str(resp.url)
                    }
            except Exception as e:
                results["http"] = {"error": str(e)}
            
            # Test HTTPS
            try:
                with httpx.Client(timeout=10, verify=True) as client:
                    resp = client.get(f"https://{domain}")
                    results["https"] = {
                        "status": resp.status_code,
                        "ssl_valid": True
                    }
            except httpx.ConnectError:
                results["https"] = {"ssl_valid": False, "error": "SSL not configured or invalid"}
            except Exception as e:
                results["https"] = {"error": str(e)}
            
            # Test API
            try:
                base = f"https://{domain}" if results.get("https", {}).get("ssl_valid") else f"http://{domain}"
                with httpx.Client(timeout=10, follow_redirects=True) as client:
                    resp = client.get(f"{base}/api/health")
                    results["api"] = {"status": resp.status_code}
            except Exception as e:
                results["api"] = {"error": str(e)}
            
            all_ok = (
                results.get("http", {}).get("status") in [200, 301, 302] and
                results.get("api", {}).get("status") == 200
            )
            
            return DeployResult(
                success=all_ok,
                message="Verificación completada" if all_ok else "Algunos checks fallaron",
                domain=domain,
                ssl_status="valid" if results.get("https", {}).get("ssl_valid") else "invalid",
                url=f"https://{domain}" if results.get("https", {}).get("ssl_valid") else f"http://{domain}",
                details=results
            )
        except Exception as e:
            return DeployResult(
                success=False,
                message="Error en verificación",
                error=str(e)
            )
    
    def close(self):
        """Cierra conexiones"""
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None


def main():
    """CLI principal"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = ProductionDeployManager()
    
    try:
        if command == "status":
            result = manager.get_status()
        
        elif command == "setup-domain":
            if len(sys.argv) < 3:
                print("Uso: python -m core.production_deploy setup-domain <domain>")
                sys.exit(1)
            domain = sys.argv[2]
            result = manager.setup_domain(domain)
        
        elif command == "setup-ssl":
            domain = sys.argv[2] if len(sys.argv) > 2 else ""
            email = sys.argv[3] if len(sys.argv) > 3 else ""
            result = manager.setup_ssl(domain, email)
        
        elif command == "deploy":
            rebuild = "--rebuild" in sys.argv
            result = manager.deploy(rebuild=rebuild)
        
        elif command == "verify":
            domain = sys.argv[2] if len(sys.argv) > 2 else ""
            result = manager.verify(domain)
        
        else:
            print(f"Comando desconocido: {command}")
            print(__doc__)
            sys.exit(1)
        
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0 if result.success else 1)
    
    finally:
        manager.close()


if __name__ == "__main__":
    main()
