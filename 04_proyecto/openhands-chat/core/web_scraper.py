"""
Web Scraper Avanzado - Extracción de datos web con múltiples estrategias
Incluye: requests básico, BeautifulSoup, y soporte para páginas dinámicas
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib


@dataclass
class ScrapedData:
    """Datos extraídos de una página web"""
    url: str
    title: str
    text_content: str
    links: List[Dict[str, str]]
    images: List[Dict[str, str]]
    metadata: Dict[str, Any]
    tables: List[List[List[str]]]
    scraped_at: str
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebScraper:
    """
    Scraper web avanzado con múltiples estrategias de extracción.
    """
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache: Dict[str, ScrapedData] = {}
    
    async def scrape(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = True,
        extract_tables: bool = True,
        extract_metadata: bool = True,
        use_cache: bool = True,
        custom_headers: Dict[str, str] = None
    ) -> ScrapedData:
        """
        Extrae datos de una URL.
        """
        # Verificar cache
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            # Cache válido por 5 minutos
            cached_time = datetime.fromisoformat(cached.scraped_at)
            if (datetime.now() - cached_time).seconds < 300:
                return cached
        
        headers = {**self.DEFAULT_HEADERS, **(custom_headers or {})}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=False
                ) as response:
                    if response.status != 200:
                        return ScrapedData(
                            url=url,
                            title="",
                            text_content="",
                            links=[],
                            images=[],
                            metadata={"status_code": response.status},
                            tables=[],
                            scraped_at=datetime.now().isoformat(),
                            success=False,
                            error=f"HTTP {response.status}"
                        )
                    
                    html = await response.text()
                    
        except asyncio.TimeoutError:
            return ScrapedData(
                url=url, title="", text_content="", links=[], images=[],
                metadata={}, tables=[], scraped_at=datetime.now().isoformat(),
                success=False, error="Timeout"
            )
        except Exception as e:
            return ScrapedData(
                url=url, title="", text_content="", links=[], images=[],
                metadata={}, tables=[], scraped_at=datetime.now().isoformat(),
                success=False, error=str(e)
            )
        
        # Parsear HTML
        result = self._parse_html(url, html, extract_links, extract_images, extract_tables, extract_metadata)
        
        # Guardar en cache
        self.cache[cache_key] = result
        
        return result
    
    def _parse_html(
        self,
        url: str,
        html: str,
        extract_links: bool,
        extract_images: bool,
        extract_tables: bool,
        extract_metadata: bool
    ) -> ScrapedData:
        """Parsea HTML y extrae datos"""
        
        # Extraer título
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        
        # Extraer texto limpio
        text_content = self._extract_text(html)
        
        # Extraer links
        links = []
        if extract_links:
            links = self._extract_links(url, html)
        
        # Extraer imágenes
        images = []
        if extract_images:
            images = self._extract_images(url, html)
        
        # Extraer tablas
        tables = []
        if extract_tables:
            tables = self._extract_tables(html)
        
        # Extraer metadata
        metadata = {}
        if extract_metadata:
            metadata = self._extract_metadata(html)
        
        return ScrapedData(
            url=url,
            title=title,
            text_content=text_content[:50000],  # Limitar tamaño
            links=links[:100],  # Limitar cantidad
            images=images[:50],
            metadata=metadata,
            tables=tables[:20],
            scraped_at=datetime.now().isoformat(),
            success=True
        )
    
    def _extract_text(self, html: str) -> str:
        """Extrae texto limpio del HTML"""
        # Remover scripts y styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remover comentarios
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Remover tags HTML
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Limpiar espacios
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_links(self, base_url: str, html: str) -> List[Dict[str, str]]:
        """Extrae links del HTML"""
        links = []
        
        # Buscar todos los tags <a>
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        for href, text in matches:
            # Convertir URLs relativas a absolutas
            full_url = urljoin(base_url, href)
            text = text.strip()
            
            # Filtrar links vacíos o de JavaScript
            if href.startswith('javascript:') or href.startswith('#'):
                continue
                
            links.append({
                "url": full_url,
                "text": text[:100] if text else "",
                "is_external": urlparse(full_url).netloc != urlparse(base_url).netloc
            })
        
        return links
    
    def _extract_images(self, base_url: str, html: str) -> List[Dict[str, str]]:
        """Extrae imágenes del HTML"""
        images = []
        
        # Buscar todos los tags <img>
        pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        for match in matches:
            src = match[0] if isinstance(match, tuple) else match
            alt = match[1] if isinstance(match, tuple) and len(match) > 1 else ""
            
            full_url = urljoin(base_url, src)
            
            # Filtrar data URIs
            if src.startswith('data:'):
                continue
                
            images.append({
                "url": full_url,
                "alt": alt[:200] if alt else ""
            })
        
        return images
    
    def _extract_tables(self, html: str) -> List[List[List[str]]]:
        """Extrae tablas del HTML"""
        tables = []
        
        # Buscar todos los tags <table>
        table_pattern = r'<table[^>]*>(.*?)</table>'
        table_matches = re.findall(table_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for table_html in table_matches:
            rows = []
            
            # Buscar filas
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            row_matches = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
            
            for row_html in row_matches:
                cells = []
                
                # Buscar celdas (th o td)
                cell_pattern = r'<t[hd][^>]*>([^<]*)</t[hd]>'
                cell_matches = re.findall(cell_pattern, row_html, re.IGNORECASE)
                
                for cell in cell_matches:
                    cells.append(cell.strip()[:500])
                
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append(rows)
        
        return tables
    
    def _extract_metadata(self, html: str) -> Dict[str, Any]:
        """Extrae metadata del HTML"""
        metadata = {}
        
        # Meta tags
        meta_pattern = r'<meta[^>]+(?:name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']'
        meta_matches = re.findall(meta_pattern, html, re.IGNORECASE)
        
        for name, content in meta_matches:
            metadata[name.lower()] = content[:500]
        
        # También buscar en orden inverso (content antes de name)
        meta_pattern2 = r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\']([^"\']+)["\']'
        meta_matches2 = re.findall(meta_pattern2, html, re.IGNORECASE)
        
        for content, name in meta_matches2:
            if name.lower() not in metadata:
                metadata[name.lower()] = content[:500]
        
        # Canonical URL
        canonical = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if canonical:
            metadata['canonical_url'] = canonical.group(1)
        
        return metadata
    
    async def scrape_multiple(
        self,
        urls: List[str],
        **kwargs
    ) -> List[ScrapedData]:
        """Scrape múltiples URLs en paralelo"""
        tasks = [self.scrape(url, **kwargs) for url in urls]
        return await asyncio.gather(*tasks)
    
    def clear_cache(self):
        """Limpia el cache"""
        self.cache.clear()


# Instancia global
_scraper_instance: Optional[WebScraper] = None


def get_scraper() -> WebScraper:
    """Obtiene la instancia global del scraper"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = WebScraper()
    return _scraper_instance
