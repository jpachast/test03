/**
 * Code Server Module - VS Code integration
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let codeServerLoaded = false;
    
    async function startCodeServer() {
        const currentConversationId = window.currentConversationId;
        const loading = document.getElementById('codeLoadingRight');
        const frame = document.getElementById('codeServerFrameRight');
        
        if (!loading || !frame) return;
        
        loading.style.display = 'flex';
        loading.innerHTML = '<div class="loading-spinner"></div><p>Cargando VS Code...</p>';
        frame.style.display = 'none';
        
        const showFrameOnLoad = () => {
            frame.onload = () => {
                setTimeout(() => {
                    frame.style.display = 'block';
                    loading.style.display = 'none';
                    codeServerLoaded = true;
                    window.codeServerLoaded = true;
                }, 800);
            };
        };
        
        try {
            // Verificar si ya está corriendo
            const statusResp = await fetch('/api/code-server/status');
            const statusData = await statusResp.json();
            
            if (statusData.status === 'running' && statusData.port) {
                showFrameOnLoad();
                frame.src = '/code-server/';
                return;
            }
            
            // Si no está corriendo, iniciarlo
            const response = await fetch('/api/code-server/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: currentConversationId })
            });
            
            const data = await response.json();
            
            if (response.status === 403) {
                loading.innerHTML = '<p>⚠️ El editor de código no está disponible para el proyecto principal (test03)</p>';
                return;
            }
            
            if (response.status === 404) {
                loading.innerHTML = `
                    <p>📁 El proyecto no está clonado localmente</p>
                    <p style="font-size: 0.9em; color: #8b949e;">Haz Pull para clonar el repositorio</p>
                `;
                return;
            }
            
            if (data.status === 'started' || data.status === 'running') {
                showFrameOnLoad();
                frame.src = '/code-server/';
            } else {
                loading.innerHTML = `<p>❌ ${data.message || data.error || 'No se pudo iniciar el editor'}</p>`;
            }
        } catch (error) {
            loading.innerHTML = `<p>❌ Error: ${error.message}</p>`;
        }
    }
    
    async function stopCodeServer() {
        try {
            await fetch('/api/code-server/stop', { method: 'POST' });
            codeServerLoaded = false;
            window.codeServerLoaded = false;
            const frame = document.getElementById('codeServerFrameRight');
            if (frame) frame.src = 'about:blank';
        } catch (error) {
            console.error('Error deteniendo code-server:', error);
        }
    }
    
    function isLoaded() {
        return codeServerLoaded;
    }
    
    function setLoaded(value) {
        codeServerLoaded = value;
        window.codeServerLoaded = value;
    }
    
    // Exponer globalmente
    window.CodeServerModule = {
        start: startCodeServer,
        stop: stopCodeServer,
        isLoaded: isLoaded,
        setLoaded: setLoaded
    };
    
    window.startCodeServer = startCodeServer;
    window.stopCodeServer = stopCodeServer;
    
})();
