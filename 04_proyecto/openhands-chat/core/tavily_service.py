"""
Servicio de Tavily para búsquedas web
Con tracking de consumo de créditos
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Intentar importar tavily
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("[Tavily] tavily-python no instalado. Ejecuta: pip install tavily-python")


class TavilyService:
    """Servicio de búsqueda web con Tavily y tracking de uso"""
    
    # Límites del plan Free
    FREE_MONTHLY_LIMIT = 1000
    
    def __init__(self, db=None):
        self.db = db
        self.client = None
        self.usage_file = Path(__file__).parent.parent / "data" / "tavily_usage.json"
        self._init_client()
    
    def _init_client(self):
        """Inicializar cliente de Tavily"""
        if not TAVILY_AVAILABLE:
            return
        
        api_key = None
        
        # 1. Intentar desde variable de entorno
        api_key = os.environ.get('TAVILY_API_KEY', '')
        
        # 2. Intentar desde base de datos
        if not api_key and self.db:
            api_key = self.db.get_tavily_api_key()
        
        if api_key:
            try:
                self.client = TavilyClient(api_key=api_key)
                print(f"[Tavily] ✅ Cliente inicializado")
            except Exception as e:
                print(f"[Tavily] ❌ Error inicializando cliente: {e}")
    
    def is_available(self) -> bool:
        """Verificar si Tavily está disponible"""
        return self.client is not None
    
    def _get_usage(self) -> dict:
        """Obtener datos de uso actuales"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Verificar si es el mismo mes
                    current_month = datetime.now().strftime('%Y-%m')
                    if data.get('month') == current_month:
                        return data
            # Nuevo mes o archivo no existe
            return {
                'month': datetime.now().strftime('%Y-%m'),
                'credits_used': 0,
                'searches': []
            }
        except:
            return {
                'month': datetime.now().strftime('%Y-%m'),
                'credits_used': 0,
                'searches': []
            }
    
    def _save_usage(self, data: dict):
        """Guardar datos de uso"""
        try:
            self.usage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Tavily] Error guardando uso: {e}")
    
    def _track_search(self, query: str, credits: int = 1):
        """Registrar una búsqueda"""
        usage = self._get_usage()
        usage['credits_used'] += credits
        usage['searches'].append({
            'query': query[:100],
            'credits': credits,
            'timestamp': datetime.now().isoformat()
        })
        # Mantener solo las últimas 100 búsquedas
        if len(usage['searches']) > 100:
            usage['searches'] = usage['searches'][-100:]
        self._save_usage(usage)
    
    def get_usage_stats(self) -> dict:
        """Obtener estadísticas de uso"""
        usage = self._get_usage()
        credits_used = usage.get('credits_used', 0)
        credits_remaining = max(0, self.FREE_MONTHLY_LIMIT - credits_used)
        
        return {
            'month': usage.get('month', datetime.now().strftime('%Y-%m')),
            'plan': 'Free',
            'limit': self.FREE_MONTHLY_LIMIT,
            'credits_used': credits_used,
            'credits_remaining': credits_remaining,
            'percentage_used': round((credits_used / self.FREE_MONTHLY_LIMIT) * 100, 1),
            'is_available': self.is_available(),
            'recent_searches': len(usage.get('searches', []))
        }
    
    def search(self, query: str, search_depth: str = "basic", 
               max_results: int = 5, include_answer: bool = True) -> dict:
        """
        Realizar búsqueda web con Tavily
        
        Args:
            query: Consulta de búsqueda
            search_depth: basic (1 credito) o advanced (2 creditos)
            max_results: Número máximo de resultados
            include_answer: Incluir respuesta generada por IA
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Tavily no configurado. Agrega tu API key en Configuración.',
                'results': []
            }
        
        # Verificar límite
        usage = self._get_usage()
        credits_needed = 2 if search_depth == "advanced" else 1
        
        if usage['credits_used'] + credits_needed > self.FREE_MONTHLY_LIMIT:
            return {
                'success': False,
                'error': f'Límite mensual alcanzado ({self.FREE_MONTHLY_LIMIT} créditos). Actualiza a plan de pago en tavily.com',
                'results': [],
                'usage': self.get_usage_stats()
            }
        
        try:
            # Realizar búsqueda
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer
            )
            
            # Registrar uso
            self._track_search(query, credits_needed)
            
            # Formatear resultados
            results = []
            for item in response.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', ''),
                    'score': item.get('score', 0)
                })
            
            return {
                'success': True,
                'query': query,
                'answer': response.get('answer', ''),
                'results': results,
                'usage': self.get_usage_stats()
            }
            
        except Exception as e:
            error_msg = str(e)
            if 'Invalid API' in error_msg or 'api_key' in error_msg.lower():
                return {
                    'success': False,
                    'error': 'API key de Tavily inválida. Verifica tu clave en Configuración.',
                    'results': []
                }
            return {
                'success': False,
                'error': f'Error en búsqueda: {error_msg}',
                'results': []
            }
    
    def extract(self, urls: list) -> dict:
        """Extraer contenido de URLs específicas"""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Tavily no está configurado',
                'results': []
            }
        
        try:
            response = self.client.extract(urls=urls)
            self._track_search(f"extract: {urls[0][:50]}...", 1)
            
            return {
                'success': True,
                'results': response.get('results', []),
                'usage': self.get_usage_stats()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }


# Singleton global
_tavily_service = None

def get_tavily_service(db=None) -> TavilyService:
    """Obtener instancia singleton del servicio Tavily"""
    global _tavily_service
    if _tavily_service is None:
        _tavily_service = TavilyService(db)
    return _tavily_service

def reinit_tavily_service(db=None):
    """Reinicializar servicio (después de cambiar API key)"""
    global _tavily_service
    _tavily_service = TavilyService(db)
    return _tavily_service
