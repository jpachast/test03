/**
 * SSE Reconnect - Reconexión automática de streaming
 * 
 * Maneja:
 * - Detección de conexión perdida
 * - Reconexión automática con backoff
 * - Polling de estado como fallback
 * - Timeout de inactividad
 */

(function() {
    'use strict';

    const CONFIG = {
        HEARTBEAT_TIMEOUT: 15000,     // 15s sin heartbeat = verificar
        AUTO_CHECK_INTERVAL: 5000,    // Verificar cada 5s si conexión perdida
        MAX_AUTO_CHECKS: 60,          // Máximo 60 verificaciones (5 min)
    };

    let lastHeartbeat = Date.now();
    let heartbeatChecker = null;
    let autoCheckInterval = null;
    let autoCheckCount = 0;
    let isStreaming = false;
    let currentConversationId = null;
    let lastMessageCount = 0;

    /**
     * Inicia el monitor de heartbeat con verificación automática
     */
    function startHeartbeatMonitor() {
        lastHeartbeat = Date.now();
        autoCheckCount = 0;
        
        if (heartbeatChecker) {
            clearInterval(heartbeatChecker);
        }
        if (autoCheckInterval) {
            clearInterval(autoCheckInterval);
        }

        heartbeatChecker = setInterval(() => {
            if (!isStreaming) return;

            const timeSinceLastHeartbeat = Date.now() - lastHeartbeat;
            
            if (timeSinceLastHeartbeat > CONFIG.HEARTBEAT_TIMEOUT) {
                console.warn('[SSE] No heartbeat en', timeSinceLastHeartbeat, 'ms - iniciando verificación automática');
                showConnectionWarning();
                startAutoCheck();
            }
        }, 5000);
    }

    /**
     * Inicia verificación automática periódica
     */
    function startAutoCheck() {
        if (autoCheckInterval) return; // Ya está corriendo
        
        autoCheckInterval = setInterval(async () => {
            if (!isStreaming || autoCheckCount >= CONFIG.MAX_AUTO_CHECKS) {
                stopAutoCheck();
                return;
            }
            
            autoCheckCount++;
            console.log('[SSE] Verificación automática', autoCheckCount);
            await checkStatus();
        }, CONFIG.AUTO_CHECK_INTERVAL);
    }

    /**
     * Detiene verificación automática
     */
    function stopAutoCheck() {
        if (autoCheckInterval) {
            clearInterval(autoCheckInterval);
            autoCheckInterval = null;
        }
    }

    /**
     * Registra recepción de heartbeat
     */
    function recordHeartbeat() {
        lastHeartbeat = Date.now();
        hideConnectionWarning();
    }

    /**
     * Muestra indicador discreto de verificación
     */
    function showConnectionWarning() {
        let warning = document.getElementById('sseConnectionWarning');
        
        if (!warning) {
            warning = document.createElement('div');
            warning.id = 'sseConnectionWarning';
            warning.style.cssText = `
                position: fixed;
                bottom: 80px;
                right: 20px;
                background: rgba(0,0,0,0.7);
                color: #aaa;
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 12px;
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            document.body.appendChild(warning);
        }
        
        warning.innerHTML = `
            <span style="animation: pulse 1s infinite;">🔄</span>
            <span>Verificando respuesta...</span>
        `;
        warning.style.display = 'flex';
    }

    /**
     * Oculta advertencia de conexión
     */
    function hideConnectionWarning() {
        const warning = document.getElementById('sseConnectionWarning');
        if (warning) {
            warning.style.display = 'none';
        }
    }

    /**
     * Verifica estado de la conversación actual (automático)
     */
    async function checkStatus() {
        if (!currentConversationId) {
            console.log('[SSE] No hay conversación activa');
            return;
        }

        try {
            const response = await fetch(`/api/conversations/${currentConversationId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > lastMessageCount) {
                // Hay nuevos mensajes
                const newMessages = data.messages.slice(lastMessageCount);
                const assistantMessage = newMessages.find(m => m.role === 'assistant');
                
                if (assistantMessage) {
                    console.log('[SSE] ✅ Respuesta del agente recuperada automáticamente');
                    
                    // Remover el indicador de "Iniciando..."
                    const progressDiv = document.querySelector('.streaming-progress');
                    if (progressDiv) progressDiv.remove();
                    
                    // Remover div de streaming si existe
                    const streamingDiv = document.querySelector('.message.assistant.streaming');
                    if (streamingDiv) streamingDiv.remove();
                    
                    // Mostrar la respuesta
                    if (window.addMessage) {
                        window.addMessage(assistantMessage.content, 'assistant');
                    }
                    
                    // Actualizar estado
                    if (window.setTaskStatus) {
                        window.setTaskStatus('completed', 'Tarea completada');
                    }
                    
                    hideConnectionWarning();
                    stopStreaming();
                    
                    // Toast sutil
                    showToast('Respuesta recibida', 'success');
                }
            }
        } catch (error) {
            console.error('[SSE] Error verificando estado:', error);
        }
    }

    /**
     * Muestra toast de notificación
     */
    function showToast(message, type = 'info') {
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            console.log('[TOAST]', message);
        }
    }

    /**
     * Inicia tracking de streaming
     */
    async function startStreaming(conversationId) {
        isStreaming = true;
        currentConversationId = conversationId;
        autoCheckCount = 0;
        
        // Guardar número de mensajes actual para detectar nuevos
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();
            lastMessageCount = data.messages ? data.messages.length : 0;
        } catch (e) {
            lastMessageCount = 0;
        }
        
        startHeartbeatMonitor();
        console.log('[SSE] Streaming iniciado para conversación:', conversationId, 'mensajes:', lastMessageCount);
    }

    /**
     * Detiene tracking de streaming
     */
    function stopStreaming() {
        isStreaming = false;
        
        if (heartbeatChecker) {
            clearInterval(heartbeatChecker);
            heartbeatChecker = null;
        }
        
        stopAutoCheck();
        hideConnectionWarning();
        console.log('[SSE] Streaming detenido');
    }

    /**
     * Hook para el evento de heartbeat del stream
     */
    function handleStreamEvent(event) {
        if (event.type === 'heartbeat') {
            recordHeartbeat();
        } else if (event.type === 'done' || event.type === 'error') {
            stopStreaming();
        } else {
            // Cualquier evento cuenta como actividad
            recordHeartbeat();
        }
    }

    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    `;
    document.head.appendChild(style);

    // API pública
    window.SSEReconnect = {
        startStreaming,
        stopStreaming,
        handleStreamEvent,
        recordHeartbeat,
        checkStatus,
        isActive: () => isStreaming
    };

    console.log('[SSEReconnect] Módulo cargado');
})();
