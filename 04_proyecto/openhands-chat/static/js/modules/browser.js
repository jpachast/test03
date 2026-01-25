/**
 * Browser Module - Browser Screenshots (OpenHands pattern)
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    // === NAVEGADOR (Browser Screenshots - como OpenHands) ===
    let currentBrowserUrl = '';
    let currentScreenshot = null;
    
    async function loadBrowserScreenshot() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) return;
        
        try {
            const resp = await fetch(`/api/browser/screenshot?conversation_id=${currentConversationId}`);
            const data = await resp.json();
            
            if (data.screenshot) {
                showBrowserScreenshot(data.url, data.screenshot);
            } else {
                showBrowserEmpty();
            }
        } catch (e) {
            console.log('No browser screenshot available');
            showBrowserEmpty();
        }
        window.browserLoaded = true;
    }
    
    function showBrowserScreenshot(url, screenshotBase64) {
        const urlInput = document.getElementById('browserUrl');
        const screenshot = document.getElementById('browserScreenshot');
        const empty = document.getElementById('browserEmpty');
        
        if (!urlInput || !screenshot || !empty) return;
        
        currentBrowserUrl = url;
        currentScreenshot = screenshotBase64;
        
        urlInput.value = url || '';
        
        // Mostrar screenshot
        const imgSrc = screenshotBase64.startsWith('data:image/')
            ? screenshotBase64
            : `data:image/png;base64,${screenshotBase64}`;
        screenshot.src = imgSrc;
        screenshot.style.display = 'block';
        empty.style.display = 'none';
    }
    
    function showBrowserEmpty() {
        const urlInput = document.getElementById('browserUrl');
        const screenshot = document.getElementById('browserScreenshot');
        const empty = document.getElementById('browserEmpty');
        
        if (!urlInput || !screenshot || !empty) return;
        
        urlInput.value = '';
        screenshot.style.display = 'none';
        empty.style.display = 'flex';
        empty.style.flexDirection = 'column';
        empty.style.alignItems = 'center';
        empty.style.justifyContent = 'center';
        empty.style.height = '100%';
    }
    
    function refreshBrowser() {
        window.browserLoaded = false;
        loadBrowserScreenshot();
    }
    
    // Función para actualizar screenshot desde el agente (vía WebSocket)
    function updateBrowserScreenshot(url, screenshot) {
        currentBrowserUrl = url;
        currentScreenshot = screenshot;
        if (window.currentView === 'browser') {
            showBrowserScreenshot(url, screenshot);
        }
    }
    
    function getCurrentUrl() {
        return currentBrowserUrl;
    }
    
    function getCurrentScreenshot() {
        return currentScreenshot;
    }
    
    // Exponer funciones globalmente
    window.BrowserModule = {
        load: loadBrowserScreenshot,
        showScreenshot: showBrowserScreenshot,
        showEmpty: showBrowserEmpty,
        refresh: refreshBrowser,
        update: updateBrowserScreenshot,
        getCurrentUrl: getCurrentUrl,
        getCurrentScreenshot: getCurrentScreenshot
    };
    
    // Alias para compatibilidad con código existente
    window.loadBrowserScreenshot = loadBrowserScreenshot;
    window.showBrowserScreenshot = showBrowserScreenshot;
    window.showBrowserEmpty = showBrowserEmpty;
    window.refreshBrowser = refreshBrowser;
    window.updateBrowserScreenshot = updateBrowserScreenshot;
    
})();
