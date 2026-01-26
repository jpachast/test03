"""
Herramientas de Browser para el Agente (usando Playwright)

Este módulo proporciona herramientas de navegación web para el agente,
similar a las que tiene OpenHands Cloud.

Los screenshots se guardan automáticamente y se envían a la UI.
"""

import base64
import asyncio
import subprocess
from typing import Optional
from pathlib import Path

# Singleton del browser
_browser_instance = None
_browser_context = None
_current_page = None
_playwright_instance = None
_playwright_verified = False  # OPTIMIZACIÓN: Solo verificar instalación una vez


def _ensure_playwright_installed():
    """Asegura que Playwright y sus browsers estén instalados (solo primera vez)"""
    global _playwright_verified
    
    # OPTIMIZACIÓN: Skip si ya verificamos
    if _playwright_verified:
        return True
    
    try:
        from playwright.sync_api import sync_playwright
        # Verificar si chromium está instalado
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                _playwright_verified = True
                return True
            except Exception:
                print("  📦 Instalando browsers de Playwright...")
                subprocess.run(
                    ["python3", "-m", "playwright", "install", "chromium"],
                    capture_output=True
                )
                _playwright_verified = True
                return True
    except ImportError:
        print("  ⚠️ Playwright no instalado, instalando...")
        subprocess.run(
            ["pip", "install", "playwright"],
            capture_output=True
        )
        subprocess.run(
            ["python3", "-m", "playwright", "install", "chromium"],
            capture_output=True
        )
        _playwright_verified = True
        return True


def get_browser():
    """Obtiene o crea una instancia del browser"""
    global _browser_instance, _browser_context, _current_page, _playwright_instance
    
    if _browser_instance is None:
        _ensure_playwright_installed()
        from playwright.sync_api import sync_playwright
        _playwright_instance = sync_playwright().start()
        _browser_instance = _playwright_instance.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        _browser_context = _browser_instance.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        _current_page = _browser_context.new_page()
    
    return _current_page


def close_browser():
    """Cierra el browser"""
    global _browser_instance, _browser_context, _current_page, _playwright_instance
    
    if _browser_instance:
        _browser_instance.close()
        _browser_instance = None
        _browser_context = None
        _current_page = None
    
    if _playwright_instance:
        _playwright_instance.stop()
        _playwright_instance = None


def take_screenshot() -> str:
    """Toma un screenshot de la página actual y lo retorna como base64"""
    page = get_browser()
    screenshot_bytes = page.screenshot(full_page=False)
    return base64.b64encode(screenshot_bytes).decode('utf-8')


def browser_navigate(url: str) -> dict:
    """
    Navega a una URL específica.
    
    Args:
        url: URL a la que navegar (debe incluir http:// o https://)
    
    Returns:
        dict con url, title y screenshot en base64
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    page = get_browser()
    
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(1000)  # Esperar a que cargue contenido dinámico
        
        return {
            'success': True,
            'url': page.url,
            'title': page.title(),
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url
        }


def browser_get_state() -> dict:
    """
    Obtiene el estado actual del browser incluyendo screenshot.
    
    Returns:
        dict con url, title, elementos interactivos y screenshot
    """
    page = get_browser()
    
    try:
        # Obtener elementos interactivos
        elements = []
        interactive_selectors = [
            'a[href]', 'button', 'input', 'select', 'textarea',
            '[role="button"]', '[onclick]'
        ]
        
        for selector in interactive_selectors:
            try:
                for el in page.query_selector_all(selector)[:20]:  # Limitar a 20 por tipo
                    text = el.inner_text()[:50] if el.inner_text() else ''
                    tag = el.evaluate('el => el.tagName.toLowerCase()')
                    elements.append({
                        'tag': tag,
                        'text': text.strip()
                    })
            except:
                pass
        
        return {
            'success': True,
            'url': page.url,
            'title': page.title(),
            'elements': elements[:50],  # Limitar total
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_click(selector: str) -> dict:
    """
    Hace clic en un elemento de la página.
    
    Args:
        selector: Selector CSS del elemento a clickear
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        page.click(selector, timeout=5000)
        page.wait_for_timeout(1000)
        
        return {
            'success': True,
            'url': page.url,
            'title': page.title(),
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_type(selector: str, text: str) -> dict:
    """
    Escribe texto en un campo de la página.
    
    Args:
        selector: Selector CSS del campo
        text: Texto a escribir
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        page.fill(selector, text, timeout=5000)
        
        return {
            'success': True,
            'url': page.url,
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_scroll(direction: str = 'down') -> dict:
    """
    Hace scroll en la página.
    
    Args:
        direction: 'up' o 'down'
    
    Returns:
        dict con screenshot actualizado
    """
    page = get_browser()
    
    try:
        if direction == 'down':
            page.evaluate('window.scrollBy(0, 500)')
        else:
            page.evaluate('window.scrollBy(0, -500)')
        
        page.wait_for_timeout(500)
        
        return {
            'success': True,
            'url': page.url,
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_get_content() -> dict:
    """
    Obtiene el contenido de texto de la página actual.
    
    Returns:
        dict con el contenido de texto de la página
    """
    page = get_browser()
    
    try:
        # Obtener texto limpio de la página
        content = page.evaluate('''() => {
            // Remover scripts, styles, etc.
            const clone = document.body.cloneNode(true);
            const scripts = clone.querySelectorAll('script, style, noscript');
            scripts.forEach(s => s.remove());
            return clone.innerText;
        }''')
        
        return {
            'success': True,
            'url': page.url,
            'title': page.title(),
            'content': content[:5000]  # Limitar a 5000 caracteres
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# === CLI PARA USO DESDE TERMINAL ===

def main():
    """
    Interfaz de línea de comandos para las herramientas de browser.
    Permite al agente usar el browser mediante comandos bash.
    
    Uso:
        python -m core.browser navigate https://google.com
        python -m core.browser state
        python -m core.browser click "button.submit"
        python -m core.browser type "input#search" "texto a buscar"
        python -m core.browser scroll down
        python -m core.browser content
    """
    import sys
    import json
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python -m core.browser <comando> [args]"}))
        print("Comandos: navigate, state, click, type, scroll, content")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "navigate":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Falta URL. Uso: navigate <url>"}))
                sys.exit(1)
            result = browser_navigate(sys.argv[2])
        
        elif command == "state":
            result = browser_get_state()
        
        elif command == "click":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Falta selector. Uso: click <selector>"}))
                sys.exit(1)
            result = browser_click(sys.argv[2])
        
        elif command == "type":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Faltan args. Uso: type <selector> <texto>"}))
                sys.exit(1)
            result = browser_type(sys.argv[2], sys.argv[3])
        
        elif command == "scroll":
            direction = sys.argv[2] if len(sys.argv) > 2 else "down"
            result = browser_scroll(direction)
        
        elif command == "content":
            result = browser_get_content()
        
        elif command == "close":
            close_browser()
            result = {"success": True, "message": "Browser cerrado"}
        
        else:
            result = {"error": f"Comando desconocido: {command}"}
        
        # Imprimir resultado como JSON (el agente puede parsearlo)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
