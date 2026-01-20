"""
Smart Browser - Browser mejorado con características TOP

Mejoras sobre el browser básico:
1. Retry inteligente con selectores alternativos
2. Cookie/Session sharing (persistencia)
3. Goal-driven adaptation (detecta cambios y se adapta)
4. Anti-detection básico
5. Extracción de contenido mejorada

Uso:
    browser = SmartBrowser()
    browser.navigate("https://example.com")
    
    # Con retry inteligente
    browser.smart_click("Add to Cart", retries=3)
    
    # Guardar/cargar sesión
    browser.save_session("mi_sesion")
    browser.load_session("mi_sesion")
"""

import os
import re
import json
import base64
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Intentar importar Playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class SelectorStrategy:
    """Estrategia de selector para retry inteligente"""
    primary: str  # Selector principal
    alternatives: List[str] = field(default_factory=list)  # Selectores alternativos
    by_text: Optional[str] = None  # Buscar por texto
    by_role: Optional[str] = None  # Buscar por role ARIA


@dataclass
class BrowserSession:
    """Sesión de browser que puede ser guardada/restaurada"""
    name: str
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_storage: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_url: str = ""


class SmartBrowser:
    """
    Browser inteligente con capacidades avanzadas.
    
    Features:
    - Retry inteligente con múltiples estrategias de selector
    - Persistencia de sesiones (cookies, localStorage)
    - Detección de cambios en página
    - Anti-bot básico
    - Extracción de contenido mejorada
    """
    
    # Directorio para guardar sesiones
    SESSIONS_DIR = ".browser_sessions"
    
    # User agents rotativos (anti-detection básico)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    def __init__(self, workspace: str = None, headless: bool = True):
        """
        Inicializa el browser inteligente.
        
        Args:
            workspace: Directorio para guardar sesiones
            headless: Si True, ejecuta sin interfaz gráfica
        """
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.sessions_dir = self.workspace / self.SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # Estado para detección de cambios
        self._last_page_hash: str = ""
        self._retry_count: int = 0
        self._max_retries: int = 3
        
    def _ensure_browser(self):
        """Inicializa el browser si no está corriendo"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright no está instalado. Instalar con: pip install playwright && playwright install chromium")
        
        if self._browser is None:
            import random
            
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # Contexto con user agent aleatorio
            user_agent = random.choice(self.USER_AGENTS)
            self._context = self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=user_agent,
                locale='es-ES',
                timezone_id='America/Lima'
            )
            
            # Anti-detection: ocultar webdriver
            self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self._page = self._context.new_page()
            
            # Configurar timeouts
            self._page.set_default_timeout(30000)
            self._page.set_default_navigation_timeout(60000)
    
    def close(self):
        """Cierra el browser"""
        if self._browser:
            self._browser.close()
            self._browser = None
            self._context = None
            self._page = None
        
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
    
    def navigate(self, url: str, wait_for: str = "domcontentloaded") -> Dict[str, Any]:
        """
        Navega a una URL con retry inteligente.
        
        Args:
            url: URL a visitar
            wait_for: Evento a esperar (load, domcontentloaded, networkidle)
            
        Returns:
            Estado de la navegación
        """
        self._ensure_browser()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        retries = 0
        last_error = None
        
        while retries < self._max_retries:
            try:
                self._page.goto(url, wait_until=wait_for)
                self._page.wait_for_timeout(1000)  # Contenido dinámico
                
                self._last_page_hash = self._get_page_hash()
                
                return {
                    "success": True,
                    "url": self._page.url,
                    "title": self._page.title(),
                    "screenshot": self._take_screenshot()
                }
                
            except Exception as e:
                last_error = str(e)
                retries += 1
                
                if retries < self._max_retries:
                    # Esperar antes de retry (exponential backoff)
                    time.sleep(2 ** retries)
                    
                    # Intentar con diferente wait_for
                    if wait_for == "networkidle":
                        wait_for = "domcontentloaded"
                    elif wait_for == "domcontentloaded":
                        wait_for = "load"
        
        return {
            "success": False,
            "error": last_error,
            "retries": retries
        }
    
    def smart_click(self, target: str, retries: int = 3) -> Dict[str, Any]:
        """
        Click inteligente con múltiples estrategias de selector.
        
        Args:
            target: Texto del elemento, selector CSS, o descripción
            retries: Número de reintentos
            
        Returns:
            Resultado del click
        """
        self._ensure_browser()
        
        # Generar estrategias de selector
        strategies = self._generate_selector_strategies(target)
        
        last_error = None
        for attempt in range(retries):
            for strategy in strategies:
                try:
                    # Probar selector primario
                    if self._try_click(strategy.primary):
                        return self._get_state_after_action("click", target)
                    
                    # Probar por texto
                    if strategy.by_text:
                        try:
                            self._page.get_by_text(strategy.by_text).first.click(timeout=3000)
                            return self._get_state_after_action("click", target)
                        except:
                            pass
                    
                    # Probar por role
                    if strategy.by_role:
                        try:
                            self._page.get_by_role(strategy.by_role, name=target).click(timeout=3000)
                            return self._get_state_after_action("click", target)
                        except:
                            pass
                    
                    # Probar selectores alternativos
                    for alt_selector in strategy.alternatives:
                        if self._try_click(alt_selector):
                            return self._get_state_after_action("click", target)
                    
                except Exception as e:
                    last_error = str(e)
            
            # Esperar antes del siguiente intento completo
            if attempt < retries - 1:
                time.sleep(1)
        
        return {
            "success": False,
            "error": f"No se pudo hacer click en '{target}'. Último error: {last_error}",
            "strategies_tried": len(strategies)
        }
    
    def _try_click(self, selector: str) -> bool:
        """Intenta hacer click con un selector específico"""
        try:
            if self._page.locator(selector).count() > 0:
                self._page.click(selector, timeout=3000)
                self._page.wait_for_timeout(500)
                return True
        except:
            pass
        return False
    
    def _generate_selector_strategies(self, target: str) -> List[SelectorStrategy]:
        """
        Genera múltiples estrategias de selector para un target.
        
        Intenta diferentes formas de encontrar el elemento.
        """
        strategies = []
        
        # Si parece un selector CSS válido
        if target.startswith(('.', '#', '[')) or '>' in target:
            strategies.append(SelectorStrategy(
                primary=target,
                alternatives=[
                    f"*{target}",  # Más permisivo
                    f"body {target}"
                ]
            ))
        
        # Estrategia por texto
        strategies.append(SelectorStrategy(
            primary=f"text={target}",
            by_text=target,
            alternatives=[
                f"text='{target}'",
                f"//*[contains(text(), '{target}')]",
                f"*:has-text('{target}')"
            ]
        ))
        
        # Estrategia por atributos comunes
        safe_target = target.replace("'", "\\'")
        strategies.append(SelectorStrategy(
            primary=f"[aria-label='{safe_target}']",
            alternatives=[
                f"[title='{safe_target}']",
                f"[placeholder='{safe_target}']",
                f"button:has-text('{safe_target}')",
                f"a:has-text('{safe_target}')"
            ]
        ))
        
        # Estrategia por role
        for role in ["button", "link", "menuitem", "tab"]:
            strategies.append(SelectorStrategy(
                primary=f"[role='{role}']:has-text('{safe_target}')",
                by_role=role
            ))
        
        return strategies
    
    def smart_type(self, target: str, text: str) -> Dict[str, Any]:
        """
        Escribe texto con retry inteligente.
        
        Args:
            target: Selector o descripción del campo
            text: Texto a escribir
        """
        self._ensure_browser()
        
        # Estrategias para encontrar el input
        selectors = [
            target,
            f"input[name='{target}']",
            f"input[placeholder*='{target}']",
            f"[aria-label*='{target}']",
            f"label:has-text('{target}') + input",
            f"label:has-text('{target}') input"
        ]
        
        for selector in selectors:
            try:
                if self._page.locator(selector).count() > 0:
                    self._page.fill(selector, text, timeout=5000)
                    return self._get_state_after_action("type", f"{target}={text[:20]}...")
            except:
                pass
        
        return {
            "success": False,
            "error": f"No se encontró campo '{target}'"
        }
    
    def extract_content(self, format: str = "markdown") -> Dict[str, Any]:
        """
        Extrae contenido de la página en formato limpio.
        
        Args:
            format: "markdown", "text", "structured"
            
        Returns:
            Contenido extraído
        """
        self._ensure_browser()
        
        try:
            if format == "structured":
                return self._extract_structured()
            elif format == "markdown":
                return self._extract_markdown()
            else:
                return self._extract_text()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text(self) -> Dict[str, Any]:
        """Extrae texto limpio de la página"""
        content = self._page.evaluate('''() => {
            const clone = document.body.cloneNode(true);
            ['script', 'style', 'noscript', 'iframe', 'svg'].forEach(tag => {
                clone.querySelectorAll(tag).forEach(el => el.remove());
            });
            return clone.innerText;
        }''')
        
        # Limpiar espacios excesivos
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return {
            "success": True,
            "url": self._page.url,
            "title": self._page.title(),
            "content": content[:10000],
            "format": "text"
        }
    
    def _extract_markdown(self) -> Dict[str, Any]:
        """Extrae contenido como Markdown aproximado"""
        content = self._page.evaluate('''() => {
            function toMarkdown(element) {
                let md = '';
                
                element.childNodes.forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        md += node.textContent;
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        const tag = node.tagName.toLowerCase();
                        
                        if (['script', 'style', 'noscript'].includes(tag)) return;
                        
                        switch(tag) {
                            case 'h1': md += '# ' + node.textContent + '\\n\\n'; break;
                            case 'h2': md += '## ' + node.textContent + '\\n\\n'; break;
                            case 'h3': md += '### ' + node.textContent + '\\n\\n'; break;
                            case 'p': md += node.textContent + '\\n\\n'; break;
                            case 'a': 
                                const href = node.getAttribute('href');
                                md += '[' + node.textContent + '](' + (href || '') + ')';
                                break;
                            case 'li': md += '- ' + node.textContent + '\\n'; break;
                            case 'code': md += '`' + node.textContent + '`'; break;
                            case 'pre': md += '```\\n' + node.textContent + '\\n```\\n'; break;
                            case 'br': md += '\\n'; break;
                            default: md += toMarkdown(node);
                        }
                    }
                });
                
                return md;
            }
            
            return toMarkdown(document.body);
        }''')
        
        return {
            "success": True,
            "url": self._page.url,
            "title": self._page.title(),
            "content": content[:10000],
            "format": "markdown"
        }
    
    def _extract_structured(self) -> Dict[str, Any]:
        """Extrae contenido estructurado (headings, links, etc.)"""
        data = self._page.evaluate('''() => {
            const result = {
                headings: [],
                links: [],
                forms: [],
                tables: [],
                images: []
            };
            
            // Headings
            document.querySelectorAll('h1, h2, h3').forEach(h => {
                result.headings.push({
                    level: parseInt(h.tagName[1]),
                    text: h.textContent.trim().substring(0, 200)
                });
            });
            
            // Links
            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.getAttribute('href');
                if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                    result.links.push({
                        text: a.textContent.trim().substring(0, 100),
                        href: href.substring(0, 500)
                    });
                }
            });
            
            // Forms
            document.querySelectorAll('form').forEach(form => {
                const inputs = [];
                form.querySelectorAll('input, select, textarea').forEach(input => {
                    inputs.push({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        placeholder: input.placeholder
                    });
                });
                result.forms.push({
                    action: form.action,
                    method: form.method,
                    inputs: inputs.slice(0, 10)
                });
            });
            
            // Images
            document.querySelectorAll('img[src]').forEach(img => {
                result.images.push({
                    src: img.src.substring(0, 500),
                    alt: img.alt
                });
            });
            
            return result;
        }''')
        
        return {
            "success": True,
            "url": self._page.url,
            "title": self._page.title(),
            "data": data,
            "format": "structured"
        }
    
    def save_session(self, name: str) -> Dict[str, Any]:
        """
        Guarda la sesión actual (cookies, storage) para uso posterior.
        
        Args:
            name: Nombre para identificar la sesión
        """
        self._ensure_browser()
        
        try:
            # Obtener cookies
            cookies = self._context.cookies()
            
            # Obtener storage
            local_storage = self._page.evaluate('''() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }''')
            
            session_storage = self._page.evaluate('''() => {
                const items = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    items[key] = sessionStorage.getItem(key);
                }
                return items;
            }''')
            
            # Crear objeto de sesión
            session = BrowserSession(
                name=name,
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                last_url=self._page.url
            )
            
            # Guardar a archivo
            session_file = self.sessions_dir / f"{name}.json"
            session_file.write_text(json.dumps({
                "name": session.name,
                "cookies": session.cookies,
                "local_storage": session.local_storage,
                "session_storage": session.session_storage,
                "created_at": session.created_at,
                "last_url": session.last_url
            }, indent=2))
            
            return {
                "success": True,
                "session_name": name,
                "cookies_saved": len(cookies),
                "file": str(session_file)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def load_session(self, name: str) -> Dict[str, Any]:
        """
        Carga una sesión guardada previamente.
        
        Args:
            name: Nombre de la sesión a cargar
        """
        self._ensure_browser()
        
        session_file = self.sessions_dir / f"{name}.json"
        
        if not session_file.exists():
            return {"success": False, "error": f"Sesión '{name}' no encontrada"}
        
        try:
            data = json.loads(session_file.read_text())
            
            # Cargar cookies
            if data.get("cookies"):
                self._context.add_cookies(data["cookies"])
            
            # Navegar a la última URL si existe
            if data.get("last_url"):
                self._page.goto(data["last_url"])
            
            # Cargar storage después de navegar
            if data.get("local_storage"):
                for key, value in data["local_storage"].items():
                    self._page.evaluate(f"localStorage.setItem('{key}', '{value}')")
            
            if data.get("session_storage"):
                for key, value in data["session_storage"].items():
                    self._page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
            
            return {
                "success": True,
                "session_name": name,
                "cookies_loaded": len(data.get("cookies", [])),
                "url": data.get("last_url")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_sessions(self) -> List[str]:
        """Lista sesiones guardadas"""
        return [f.stem for f in self.sessions_dir.glob("*.json")]
    
    def delete_session(self, name: str) -> bool:
        """Elimina una sesión guardada"""
        session_file = self.sessions_dir / f"{name}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    
    def detect_page_change(self) -> bool:
        """
        Detecta si la página ha cambiado desde la última vez.
        
        Útil para detectar navegación exitosa, carga de contenido dinámico, etc.
        """
        current_hash = self._get_page_hash()
        changed = current_hash != self._last_page_hash
        self._last_page_hash = current_hash
        return changed
    
    def _get_page_hash(self) -> str:
        """Genera un hash del contenido actual de la página"""
        try:
            content = self._page.content()
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return ""
    
    def _take_screenshot(self) -> str:
        """Toma screenshot y retorna como base64"""
        try:
            screenshot_bytes = self._page.screenshot(full_page=False)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except:
            return ""
    
    def _get_state_after_action(self, action: str, target: str) -> Dict[str, Any]:
        """Estado común después de una acción"""
        return {
            "success": True,
            "action": action,
            "target": target,
            "url": self._page.url,
            "title": self._page.title(),
            "page_changed": self.detect_page_change(),
            "screenshot": self._take_screenshot()
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Obtiene el estado actual del browser"""
        self._ensure_browser()
        
        try:
            # Obtener elementos interactivos con índices
            elements = self._page.evaluate('''() => {
                const result = [];
                const selectors = 'a, button, input, select, textarea, [role="button"], [onclick]';
                
                document.querySelectorAll(selectors).forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        result.push({
                            index: index,
                            tag: el.tagName.toLowerCase(),
                            text: (el.textContent || el.value || el.placeholder || '').trim().substring(0, 50),
                            type: el.type || '',
                            href: el.href || ''
                        });
                    }
                });
                
                return result.slice(0, 50);
            }''')
            
            return {
                "success": True,
                "url": self._page.url,
                "title": self._page.title(),
                "elements": elements,
                "screenshot": self._take_screenshot()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Instancia global
_smart_browser: Optional[SmartBrowser] = None


def get_smart_browser(workspace: str = None) -> SmartBrowser:
    """Obtiene o crea el browser inteligente global"""
    global _smart_browser
    
    if _smart_browser is None:
        _smart_browser = SmartBrowser(workspace)
    
    return _smart_browser


def close_smart_browser():
    """Cierra el browser inteligente global"""
    global _smart_browser
    
    if _smart_browser:
        _smart_browser.close()
        _smart_browser = None
