"""
Voice Input - Solo Whisper (Groq/OpenAI)
"""

import os
import tempfile
from typing import Dict, Optional
import httpx


def _get_key_from_db(key_name: str) -> str:
    """Obtiene una API key de la base de datos"""
    try:
        from config.database import Database
        db = Database()
        return db.get_setting(key_name, "") or ""
    except:
        return ""


class VoiceInput:
    """Transcripción de voz con Whisper"""
    
    def __init__(self, groq_api_key: str = None, openai_api_key: str = None):
        # Prioridad: parámetro > env > database
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY") or _get_key_from_db("groq_api_key")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY") or _get_key_from_db("openai_api_key")
    
    def get_status(self) -> Dict:
        """Estado de Whisper"""
        groq_configured = bool(self.groq_api_key)
        openai_configured = bool(self.openai_api_key)
        
        return {
            "enabled": groq_configured or openai_configured,
            "groq_configured": groq_configured,
            "openai_configured": openai_configured,
            "active_backend": "groq" if groq_configured else ("openai" if openai_configured else None),
            "needs_api_key": not (groq_configured or openai_configured),
            "message": self._get_status_message(groq_configured, openai_configured)
        }
    
    def _get_status_message(self, groq: bool, openai: bool) -> str:
        if groq:
            return "✅ Whisper activo (Groq - Gratis)"
        elif openai:
            return "✅ Whisper activo (OpenAI)"
        else:
            return "⚠️ Configura GROQ_API_KEY (gratis) para activar"
    
    async def transcribe(self, audio_data: bytes, format: str = "webm") -> Dict:
        """Transcribe audio con Whisper"""
        # Prioridad: Groq (gratis) > OpenAI
        if self.groq_api_key:
            return await self._transcribe_groq(audio_data, format)
        elif self.openai_api_key:
            return await self._transcribe_openai(audio_data, format)
        else:
            return {
                "success": False,
                "error": "API key no configurada",
                "help": "Configura GROQ_API_KEY en Settings → API Keys"
            }
    
    async def _transcribe_groq(self, audio_data: bytes, format: str) -> Dict:
        """Transcribe con Groq Whisper (gratis)"""
        try:
            suffix = f".{format}" if not format.startswith('.') else format
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(temp_path, 'rb') as audio_file:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.groq_api_key}"},
                        files={"file": (f"audio{suffix}", audio_file, f"audio/{format}")},
                        data={"model": "whisper-large-v3", "language": "es"}
                    )
            
            os.unlink(temp_path)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "text": response.json().get("text", ""),
                    "backend": "groq"
                }
            else:
                error = response.json().get("error", {}).get("message", response.text)
                return {"success": False, "error": error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _transcribe_openai(self, audio_data: bytes, format: str) -> Dict:
        """Transcribe con OpenAI Whisper"""
        try:
            suffix = f".{format}" if not format.startswith('.') else format
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(temp_path, 'rb') as audio_file:
                    response = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        files={"file": (f"audio{suffix}", audio_file, f"audio/{format}")},
                        data={"model": "whisper-1", "language": "es"}
                    )
            
            os.unlink(temp_path)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "text": response.json().get("text", ""),
                    "backend": "openai"
                }
            else:
                error = response.json().get("error", {}).get("message", response.text)
                # Mensaje amigable
                if "insufficient_quota" in str(error):
                    error = "Sin créditos en OpenAI. Usa Groq (gratis)."
                return {"success": False, "error": error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
