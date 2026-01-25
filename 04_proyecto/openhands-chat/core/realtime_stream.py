#!/usr/bin/env python3
"""
Realtime Streaming - Streaming de tokens en tiempo real.

Implementa streaming directo con litellm para mostrar tokens
conforme el LLM los genera, sin esperar la respuesta completa.

Uso:
    from core.realtime_stream import stream_response
    
    async for token in stream_response("Hola", model="anthropic/claude-sonnet-4-20250514"):
        print(token, end="", flush=True)
"""

import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def stream_response(
    message: str,
    model: str = None,
    api_key: str = None,
    system_prompt: str = None,
    conversation_history: list = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> AsyncGenerator[dict, None]:
    """
    Stream de tokens en tiempo real usando litellm.
    
    Yields dictionaries con:
    - {"type": "token", "content": "..."}
    - {"type": "done", "content": "full response"}
    - {"type": "error", "error": "..."}
    """
    try:
        import litellm
        
        # Cargar configuración si no se proporciona
        if not model or not api_key:
            try:
                from config.database import Database
                db = Database()
                model = model or db.get_setting('llm_model', 'anthropic/claude-sonnet-4-20250514')
                api_key = api_key or db.get_llm_api_key()
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
                model = model or "anthropic/claude-sonnet-4-20250514"
        
        # Construir mensajes
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        # Configurar litellm
        litellm.drop_params = True
        
        # Crear stream
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        full_response = ""
        
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and hasattr(delta, 'content') and delta.content:
                    token = delta.content
                    full_response += token
                    yield {"type": "token", "content": token}
        
        yield {"type": "done", "content": full_response}
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield {"type": "error", "error": str(e)}


async def stream_with_tools(
    message: str,
    workspace: str = None,
    model: str = None,
    api_key: str = None,
    system_prompt: str = None,
    conversation_history: list = None,
    enable_tools: bool = True
) -> AsyncGenerator[dict, None]:
    """
    Stream con soporte para tools (ejecución de comandos, etc).
    
    Para respuestas simples usa streaming directo.
    Para respuestas con tools, delega al SDK de OpenHands.
    """
    # Por ahora, usar streaming directo para respuestas simples
    # TODO: Integrar con SDK para tools si es necesario
    
    async for event in stream_response(
        message=message,
        model=model,
        api_key=api_key,
        system_prompt=system_prompt,
        conversation_history=conversation_history
    ):
        yield event


class RealtimeStreamManager:
    """Gestor de streaming en tiempo real"""
    
    def __init__(self):
        self._active_streams = {}
    
    async def start_stream(
        self,
        stream_id: str,
        message: str,
        **kwargs
    ) -> AsyncGenerator[dict, None]:
        """Inicia un nuevo stream"""
        self._active_streams[stream_id] = True
        
        try:
            async for event in stream_response(message, **kwargs):
                if not self._active_streams.get(stream_id):
                    yield {"type": "cancelled", "reason": "Stream cancelled by user"}
                    break
                yield event
        finally:
            self._active_streams.pop(stream_id, None)
    
    def cancel_stream(self, stream_id: str):
        """Cancela un stream activo"""
        if stream_id in self._active_streams:
            self._active_streams[stream_id] = False
    
    def is_streaming(self, stream_id: str) -> bool:
        """Verifica si un stream está activo"""
        return self._active_streams.get(stream_id, False)


# Instancia global
_stream_manager = RealtimeStreamManager()


def get_stream_manager() -> RealtimeStreamManager:
    """Obtiene el gestor de streaming"""
    return _stream_manager


# CLI para testing
async def test_stream():
    """Test de streaming"""
    print("Testing realtime stream...")
    print("-" * 50)
    
    async for event in stream_response("Cuéntame un chiste corto sobre Python"):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            print("\n" + "-" * 50)
            print(f"Total characters: {len(event['content'])}")
        elif event["type"] == "error":
            print(f"\nError: {event['error']}")


if __name__ == "__main__":
    asyncio.run(test_stream())
