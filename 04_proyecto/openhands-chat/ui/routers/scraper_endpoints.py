"""
Endpoints API para el Web Scraper
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.web_scraper import get_scraper

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    url: str
    extract_links: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    extract_metadata: bool = True
    use_cache: bool = True


class ScrapeMultipleRequest(BaseModel):
    urls: List[str]
    extract_links: bool = True
    extract_images: bool = False
    extract_tables: bool = False


@router.post("/scrape")
async def scrape_url(request: ScrapeRequest):
    """
    Extrae datos de una URL.
    
    Retorna: título, texto, links, imágenes, tablas y metadata.
    """
    try:
        scraper = get_scraper()
        result = await scraper.scrape(
            url=request.url,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
            extract_tables=request.extract_tables,
            extract_metadata=request.extract_metadata,
            use_cache=request.use_cache
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/multiple")
async def scrape_multiple_urls(request: ScrapeMultipleRequest):
    """Scrape múltiples URLs en paralelo"""
    try:
        if len(request.urls) > 10:
            raise HTTPException(status_code=400, detail="Máximo 10 URLs a la vez")
        
        scraper = get_scraper()
        results = await scraper.scrape_multiple(
            urls=request.urls,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
            extract_tables=request.extract_tables
        )
        
        return {
            "results": [r.to_dict() for r in results],
            "total": len(results),
            "successful": sum(1 for r in results if r.success)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract-text")
async def extract_text_only(url: str):
    """Extrae solo el texto de una URL (más rápido)"""
    scraper = get_scraper()
    result = await scraper.scrape(
        url=url,
        extract_links=False,
        extract_images=False,
        extract_tables=False,
        extract_metadata=False
    )
    
    return {
        "url": url,
        "title": result.title,
        "text": result.text_content,
        "success": result.success,
        "error": result.error
    }


@router.get("/extract-links")
async def extract_links_only(url: str, external_only: bool = False):
    """Extrae solo los links de una URL"""
    scraper = get_scraper()
    result = await scraper.scrape(
        url=url,
        extract_links=True,
        extract_images=False,
        extract_tables=False,
        extract_metadata=False
    )
    
    links = result.links
    if external_only:
        links = [l for l in links if l.get('is_external')]
    
    return {
        "url": url,
        "links": links,
        "total": len(links),
        "success": result.success
    }


@router.delete("/cache")
async def clear_cache():
    """Limpia el cache del scraper"""
    scraper = get_scraper()
    scraper.clear_cache()
    return {"success": True, "message": "Cache limpiado"}


@router.get("/status")
async def get_status():
    """Estado del scraper"""
    scraper = get_scraper()
    return {
        "status": "active",
        "timeout": scraper.timeout,
        "max_retries": scraper.max_retries,
        "cache_size": len(scraper.cache)
    }
