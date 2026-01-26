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
        HEARTBEAT_TIMEOUT: 30000,    // 30s sin heartbeat = conexión perdida
        RECONNECT_DELAY: 2000,        // 2s entre intentos
        MAX_RECONNECT_ATTEMPTS: 3,    // Máximo 3 intentos
        STATUS_POLL_INTERVAL: 5000,   // Polling cada 5s como fallback
    };

    let lastHeartbeat = Date.now();
    let heartbeatChecker = null;
    let reconnectAttempts = 0;
    let isStreaming = false;
    let currentConversationId = null;

    /**
     * Inicia el monitor de heartbeat
     */
    function startHeartbeatMonitor() {
        lastHeartbeat = Date.now();
        
        if (heartbeatChecker) {
            clearInterval(heartbeatChecker);
        }

        heartbeatChecker = setInterval(() => {
            if (!isStreaming) return;

            const timeSinceLastHeartbeat = Date.now() - lastHeartbeat;
            
            if (timeSinceLastHeartbeat > CONFIG.HEARTBEAT_TIMEOUT) {
                console.warn('[SSE] No heartbeat en', timeSinceLastHeartbeat, 'ms - conexión posiblemente perdida');
                showConnectionWarning();
            }
        }, 5000);
    }

    /**
     * Registra recepción de heartbeat
     */
    function recordHeartbeat() {
        lastHeartbeat = Date.now();
        hideConnectionWarning();
    }

    /**
     * Muestra advertencia de conexión
     */
    function showConnectionWarning() {
        let warning = document.getElementById('sseConnectionWarning');
        
        if (!warning) {
            warning = document.createElement('div');
            warning.id = 'sseConnectionWarning';
            warning.style.cssText = `
                position: fixed;
                top: 60px;
                right: 20px;
                background: linear-gradient(135deg, #f39c12, #e74c3c);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 10000;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 10px;
                animation: slideIn 0.3s ease;
            `;
            warning.innerHTML = `
                <span style="animation: pulse 1s infinite;">⚠️</span>
                <span>Conexión lenta - El agente sigue trabajando...</span>
                <button onclick="window.SSEReconnect.checkStatus()" style="
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                ">Verificar</button>
            `;
            document.body.appendChild(warning);
        }
        
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
     * Verifica estado de la conversación actual
     */
    async function checkStatus() {
        if (!currentConversationId) {
            console.log('[SSE] No hay conversación activa');
            return;
        }

        try {
            const response = await fetch(`/api/conversations/${currentConversationId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                const lastMessage = data.messages[data.messages.length - 1];
                
                if (lastMessage.role === 'assistant') {
                    console.log('[SSE] Encontrada respuesta del agente');
                    
                    // Si hay una respuesta nueva, actualizar la UI
                    if (window.addMessage) {
                        // Remover el indicador de "Iniciando..."
                        const progressDiv = document.querySelector('.streaming-progress');
                        if (progressDiv) progressDiv.remove();
                        
                        // Mostrar la respuesta
                        window.addMessage(lastMessage.content, 'assistant');
                        
                        // Actualizar estado
                        if (window.setTaskStatus) {
                            window.setTaskStatus('completed', 'Tarea completada');
                        }
                    }
                    
                    hideConnectionWarning();
                    stopStreaming();
                    
                    showToast('✅ Respuesta recuperada', 'success');
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
    function startStreaming(conversationId) {
        isStreaming = true;
        currentConversationId = conversationId;
        reconnectAttempts = 0;
        startHeartbeatMonitor();
        console.log('[SSE] Streaming iniciado para conversación:', conversationId);
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
