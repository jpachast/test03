"""
Error Handler - Translates API errors to user-friendly messages
"""
from typing import Optional


def translate_error_message(error_detail: str) -> str:
    """
    Traduce errores de API a mensajes amigables para el usuario.
    
    Args:
        error_detail: Mensaje de error original
        
    Returns:
        Mensaje traducido y amigable
    """
    if not error_detail:
        return "Error desconocido"
    
    error_lower = str(error_detail).lower()
    
    # Errores de crédito/billing
    if 'credit balance is too low' in error_lower or 'insufficient' in error_lower:
        return "⚠️ SIN CRÉDITO: Tu cuenta de Anthropic no tiene saldo suficiente. Por favor recarga créditos en console.anthropic.com"
    
    # Rate limiting
    if 'rate limit' in error_lower or 'too many requests' in error_lower:
        return "⚠️ LÍMITE DE VELOCIDAD: Demasiadas solicitudes. Espera unos segundos e intenta de nuevo."
    
    # API Key inválida
    if 'invalid_api_key' in error_lower or 'authentication' in error_lower or 'unauthorized' in error_lower:
        return "⚠️ API KEY INVÁLIDA: La clave de API no es válida. Revisa la configuración en Settings."
    
    # Timeout
    if 'timeout' in error_lower or 'timed out' in error_lower:
        return "⚠️ TIMEOUT: La solicitud tardó demasiado. Intenta de nuevo."
    
    # Conexión
    if 'connection' in error_lower or 'network' in error_lower or 'unreachable' in error_lower:
        return "⚠️ ERROR DE CONEXIÓN: No se pudo conectar con el servidor de IA."
    
    # Modelo no disponible
    if 'model' in error_lower and ('not found' in error_lower or 'unavailable' in error_lower):
        return "⚠️ MODELO NO DISPONIBLE: El modelo seleccionado no está disponible. Prueba con otro modelo."
    
    # Context length
    if 'context length' in error_lower or 'too long' in error_lower or 'max tokens' in error_lower:
        return "⚠️ MENSAJE MUY LARGO: El mensaje excede el límite. Intenta con un mensaje más corto."
    
    # Content filtering
    if 'content' in error_lower and ('filter' in error_lower or 'blocked' in error_lower or 'policy' in error_lower):
        return "⚠️ CONTENIDO BLOQUEADO: El mensaje fue bloqueado por políticas de contenido."
    
    # Server errors
    if 'internal server error' in error_lower or '500' in error_lower:
        return "⚠️ ERROR DEL SERVIDOR: Error interno. Intenta de nuevo en unos momentos."
    
    if 'service unavailable' in error_lower or '503' in error_lower:
        return "⚠️ SERVICIO NO DISPONIBLE: El servidor está sobrecargado. Intenta más tarde."
    
    # Default: mostrar los primeros 200 caracteres
    return str(error_detail)[:200]


def get_error_type(error_detail: str) -> str:
    """
    Determina el tipo de error para categorización.
    
    Args:
        error_detail: Mensaje de error
        
    Returns:
        Tipo de error: 'billing', 'auth', 'rate_limit', 'connection', 'server', 'unknown'
    """
    if not error_detail:
        return 'unknown'
    
    error_lower = str(error_detail).lower()
    
    if 'credit' in error_lower or 'billing' in error_lower or 'insufficient' in error_lower:
        return 'billing'
    if 'api_key' in error_lower or 'auth' in error_lower or 'unauthorized' in error_lower:
        return 'auth'
    if 'rate limit' in error_lower:
        return 'rate_limit'
    if 'connection' in error_lower or 'network' in error_lower or 'timeout' in error_lower:
        return 'connection'
    if 'server' in error_lower or '50' in error_lower:
        return 'server'
    
    return 'unknown'


def is_retryable_error(error_detail: str) -> bool:
    """
    Determina si el error es reintentable.
    
    Args:
        error_detail: Mensaje de error
        
    Returns:
        True si se puede reintentar, False si no
    """
    error_type = get_error_type(error_detail)
    # Errores reintentables
    return error_type in ['rate_limit', 'connection', 'server']
