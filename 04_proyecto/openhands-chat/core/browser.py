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


def browser_click(selector: str = None, x: int = None, y: int = None) -> dict:
    """
    Hace clic en un elemento de la página por selector CSS o coordenadas.
    
    Args:
        selector: Selector CSS del elemento a clickear (opcional)
        x: Coordenada X para click por posición (opcional)
        y: Coordenada Y para click por posición (opcional)
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        if x is not None and y is not None:
            # Click por coordenadas (Computer Use style)
            page.mouse.click(x, y)
            page.wait_for_timeout(1000)
        elif selector:
            # Click por selector CSS
            page.click(selector, timeout=5000)
            page.wait_for_timeout(1000)
        else:
            return {
                'success': False,
                'error': 'Se requiere selector o coordenadas (x, y)'
            }
        
        return {
            'success': True,
            'url': page.url,
            'title': page.title(),
            'screenshot': take_screenshot(),
            'click_position': {'x': x, 'y': y} if x and y else None
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


# === FUNCIONES ADICIONALES COMPUTER USE ===

def browser_mouse_move(x: int, y: int) -> dict:
    """
    Mueve el mouse a una posición específica.
    
    Args:
        x: Coordenada X
        y: Coordenada Y
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        page.mouse.move(x, y)
        page.wait_for_timeout(200)
        
        return {
            'success': True,
            'position': {'x': x, 'y': y},
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_double_click(x: int = None, y: int = None, selector: str = None) -> dict:
    """
    Hace doble clic en una posición o elemento.
    
    Args:
        x: Coordenada X (opcional)
        y: Coordenada Y (opcional)
        selector: Selector CSS (opcional)
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        if x is not None and y is not None:
            page.mouse.dblclick(x, y)
        elif selector:
            page.dblclick(selector, timeout=5000)
        else:
            return {'success': False, 'error': 'Se requiere selector o coordenadas'}
        
        page.wait_for_timeout(1000)
        
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


def browser_drag(start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
    """
    Arrastra desde una posición a otra.
    
    Args:
        start_x, start_y: Posición inicial
        end_x, end_y: Posición final
    
    Returns:
        dict con resultado y screenshot
    """
    page = get_browser()
    
    try:
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(end_x, end_y)
        page.mouse.up()
        page.wait_for_timeout(500)
        
        return {
            'success': True,
            'from': {'x': start_x, 'y': start_y},
            'to': {'x': end_x, 'y': end_y},
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_key_press(key: str) -> dict:
    """
    Presiona una tecla (Enter, Tab, Escape, etc.)
    
    Args:
        key: Nombre de la tecla (Enter, Tab, Escape, ArrowUp, ArrowDown, etc.)
    
    Returns:
        dict con resultado
    """
    page = get_browser()
    
    try:
        page.keyboard.press(key)
        page.wait_for_timeout(500)
        
        return {
            'success': True,
            'key': key,
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_get_element_position(selector: str) -> dict:
    """
    Obtiene la posición de un elemento (útil para clicks por coordenadas).
    
    Args:
        selector: Selector CSS del elemento
    
    Returns:
        dict con posición x, y del centro del elemento
    """
    page = get_browser()
    
    try:
        element = page.query_selector(selector)
        if not element:
            return {'success': False, 'error': f'Elemento no encontrado: {selector}'}
        
        box = element.bounding_box()
        if not box:
            return {'success': False, 'error': 'No se pudo obtener posición del elemento'}
        
        center_x = int(box['x'] + box['width'] / 2)
        center_y = int(box['y'] + box['height'] / 2)
        
        return {
            'success': True,
            'selector': selector,
            'position': {'x': center_x, 'y': center_y},
            'bounds': box
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def browser_wait_for_element(selector: str, timeout: int = 5000) -> dict:
    """
    Espera a que un elemento aparezca en la página.
    
    Args:
        selector: Selector CSS del elemento
        timeout: Tiempo máximo de espera en ms
    
    Returns:
        dict con resultado
    """
    page = get_browser()
    
    try:
        page.wait_for_selector(selector, timeout=timeout)
        
        return {
            'success': True,
            'selector': selector,
            'screenshot': take_screenshot()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# === CLI PARA USO DESDE TERMINAL ===

def main():
    """
    Interfaz de línea de comandos para las herramientas de browser (Computer Use).
    Permite al agente usar el browser mediante comandos bash.
    
    Uso:
        python -m core.browser navigate https://google.com
        python -m core.browser state
        python -m core.browser click "button.submit"
        python -m core.browser click_xy 500 300
        python -m core.browser type "input#search" "texto a buscar"
        python -m core.browser scroll down
        python -m core.browser content
        python -m core.browser move 500 300
        python -m core.browser dblclick_xy 500 300
        python -m core.browser drag 100 100 300 300
        python -m core.browser key Enter
        python -m core.browser position "button.submit"
        python -m core.browser wait "div.loaded"
    """
    import sys
    import json
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python -m core.browser <comando> [args]"}))
        print("Comandos: navigate, state, click, click_xy, type, scroll, content, move, dblclick_xy, drag, key, position, wait")
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
            result = browser_click(selector=sys.argv[2])
        
        elif command == "click_xy":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Faltan coordenadas. Uso: click_xy <x> <y>"}))
                sys.exit(1)
            result = browser_click(x=int(sys.argv[2]), y=int(sys.argv[3]))
        
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
        
        elif command == "move":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Faltan coordenadas. Uso: move <x> <y>"}))
                sys.exit(1)
            result = browser_mouse_move(int(sys.argv[2]), int(sys.argv[3]))
        
        elif command == "dblclick_xy":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Faltan coordenadas. Uso: dblclick_xy <x> <y>"}))
                sys.exit(1)
            result = browser_double_click(x=int(sys.argv[2]), y=int(sys.argv[3]))
        
        elif command == "drag":
            if len(sys.argv) < 6:
                print(json.dumps({"error": "Faltan coordenadas. Uso: drag <x1> <y1> <x2> <y2>"}))
                sys.exit(1)
            result = browser_drag(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        
        elif command == "key":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Falta tecla. Uso: key <tecla> (Enter, Tab, Escape, etc.)"}))
                sys.exit(1)
            result = browser_key_press(sys.argv[2])
        
        elif command == "position":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Falta selector. Uso: position <selector>"}))
                sys.exit(1)
            result = browser_get_element_position(sys.argv[2])
        
        elif command == "wait":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Falta selector. Uso: wait <selector>"}))
                sys.exit(1)
            timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
            result = browser_wait_for_element(sys.argv[2], timeout)
        
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
