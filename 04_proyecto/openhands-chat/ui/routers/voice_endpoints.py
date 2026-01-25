"""
Endpoints API para Voice Input
Transcripción de voz con Whisper (Groq/OpenAI)
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.voice_input import VoiceInput

router = APIRouter(tags=["voice"])

# Instancia global
_voice_input: Optional[VoiceInput] = None


def get_voice_input() -> VoiceInput:
    """Obtiene o crea la instancia de VoiceInput"""
    global _voice_input
    if _voice_input is None:
        _voice_input = VoiceInput()
    return _voice_input


@router.get("/api/voice/status")
@router.get("/api/features/voice/status")
async def get_voice_status():
    """
    Obtiene el estado de Voice Input.
    
    Returns:
        Estado de configuración de Whisper (Groq/OpenAI)
    """
    voice = get_voice_input()
    status = voice.get_status()
    
    return {
        "success": True,
        "voice_input": status,
        "backends": {
            "web_speech": {
                "name": "Web Speech API",
                "available": True,
                "key_configured": True,
                "description": "Reconocimiento de voz del navegador (gratis)",
                "free": True
            },
            "groq_whisper": {
                "name": "Groq Whisper",
                "available": status.get("groq_configured", False),
                "key_configured": status.get("groq_configured", False),
                "description": "Whisper ultra-rápido (tier gratuito)",
                "free": True
            },
            "openai_whisper": {
                "name": "OpenAI Whisper",
                "available": status.get("openai_configured", False),
                "key_configured": status.get("openai_configured", False),
                "description": "Alta precisión ($0.006/min)",
                "free": False
            }
        }
    }


@router.post("/api/voice/transcribe")
@router.post("/api/features/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    backend: str = Form("groq_whisper")
):
    """
    Transcribe audio a texto usando Whisper.
    
    Args:
        audio: Archivo de audio (webm, mp3, wav, etc.)
        backend: Backend a usar (groq_whisper, openai_whisper)
    
    Returns:
        Texto transcrito
    """
    voice = get_voice_input()
    
    # Validar backend
    if backend not in ["groq_whisper", "openai_whisper", "web_speech"]:
        raise HTTPException(
            status_code=400,
            detail=f"Backend no válido: {backend}. Usa: groq_whisper, openai_whisper"
        )
    
    # Web Speech se maneja en el frontend
    if backend == "web_speech":
        return {
            "success": False,
            "error": "Web Speech API se procesa en el navegador",
            "suggestion": "Usa groq_whisper o openai_whisper para transcripción server-side"
        }
    
    # Leer audio
    try:
        audio_data = await audio.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Archivo de audio vacío")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo audio: {str(e)}")
    
    # Determinar formato
    filename = audio.filename or "audio.webm"
    format = filename.split('.')[-1] if '.' in filename else "webm"
    
    # Transcribir
    result = await voice.transcribe(audio_data, format)
    
    if result.get("success"):
        return {
            "success": True,
            "text": result.get("text", ""),
            "backend": result.get("backend", backend),
            "format": format
        }
    else:
        error = result.get("error", "Error de transcripción")
        suggestion = None
        
        # Sugerencias según el error
        if "API key" in error or "key no configurada" in error.lower():
            suggestion = "Configura GROQ_API_KEY en Settings → API Keys (gratis en console.groq.com)"
        elif "insufficient_quota" in error.lower() or "créditos" in error.lower():
            suggestion = "Usa Groq Whisper (gratis) en lugar de OpenAI"
        
        return {
            "success": False,
            "error": error,
            "suggestion": suggestion
        }


@router.post("/api/voice/test")
@router.post("/api/features/voice/test")
async def test_voice_connection():
    """
    Prueba la conexión con los backends de voz.
    
    Returns:
        Estado de conexión de cada backend
    """
    voice = get_voice_input()
    status = voice.get_status()
    
    results = {
        "groq": {
            "configured": status.get("groq_configured", False),
            "status": "✅ Listo" if status.get("groq_configured") else "⚠️ Requiere API key"
        },
        "openai": {
            "configured": status.get("openai_configured", False),
            "status": "✅ Listo" if status.get("openai_configured") else "⚠️ Requiere API key"
        },
        "web_speech": {
            "configured": True,
            "status": "✅ Disponible en navegador"
        }
    }
    
    return {
        "success": True,
        "backends": results,
        "recommended": "groq" if status.get("groq_configured") else "web_speech"
    }
