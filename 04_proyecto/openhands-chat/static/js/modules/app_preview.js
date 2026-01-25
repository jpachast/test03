/**
 * App Preview Module - Port Forwarding (OpenHands Cloud pattern)
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    // === APLICACIÓN (Port Forwarding dinámico como OpenHands Cloud) ===
    let appServerPort = null;
    let appServerPollingActive = false;
    
    async function checkAppServer() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) return false;
        
        console.log('checkAppServer called, conversationId:', currentConversationId);
        try {
            const url = '/api/app-server/active-port?conversation_id=' + currentConversationId;
            console.log('Fetching:', url);
            const resp = await fetch(url);
            const data = await resp.json();
            console.log('checkAppServer response:', data);
            
            if (data.status === 'active' && data.port) {
                console.log('Server active on port', data.port);
                showAppInIframe(data.port);
                return true;
            } else {
                console.log('No active server, showing placeholder');
                hideAppIframe();
            }
        } catch (e) {
            console.log('checkAppServer error:', e);
            hideAppIframe();
        }
        return false;
    }
    
    function hideAppIframe() {
        const placeholder = document.getElementById('appPlaceholder');
        const activeContainer = document.getElementById('appActiveContainer');
        const frame = document.getElementById('appFrame');
        const urlInput = document.getElementById('appUrl');
        
        if (!placeholder || !frame || !urlInput) return;
        
        if (appServerPort !== null) {
            appServerPort = null;
            placeholder.style.display = 'flex';
            if (activeContainer) activeContainer.style.display = 'none';
            frame.src = 'about:blank';
            urlInput.value = 'http://localhost:PORT';
            console.log('App server stopped - showing placeholder');
        }
    }
    
    function setupAppFrameHandlers() {
        const frame = document.getElementById('appFrame');
        if (!frame) return;
        
        frame.onload = function() {
            console.log('App iframe loaded successfully');
            frame.dataset.loaded = 'true';
        };
        
        frame.onerror = function() {
            console.log('App iframe error - will retry on next poll');
            frame.dataset.loaded = 'false';
        };
        
        window.addEventListener('hashchange', (e) => {
            window.scrollTo(0, 0);
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        });
        
        let scrollLocked = false;
        window.addEventListener('scroll', (e) => {
            if (!scrollLocked && (window.scrollY > 0 || document.documentElement.scrollTop > 0)) {
                scrollLocked = true;
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
                setTimeout(() => { scrollLocked = false; }, 100);
            }
        });
    }
    
    function showAppInIframe(port) {
        const currentConversationId = window.currentConversationId;
        const placeholder = document.getElementById('appPlaceholder');
        const activeContainer = document.getElementById('appActiveContainer');
        const frame = document.getElementById('appFrame');
        const urlInput = document.getElementById('appUrl');
        const copyBtn = document.getElementById('copyUrlBtn');
        
        if (!placeholder || !frame || !urlInput) return;
        
        if (appServerPort !== port) {
            appServerPort = port;
            
            placeholder.style.display = 'none';
            if (activeContainer) {
                activeContainer.style.display = 'flex';
            }
            
            loadAppWithFetchSrcdoc(frame);
            
            if (window.location.hostname !== 'localhost') {
                const externalUrl = `${window.location.origin}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
                urlInput.value = externalUrl;
            } else {
                urlInput.value = `http://localhost:${port}`;
            }
            
            if (copyBtn) copyBtn.style.display = 'inline-block';
            const openNewTabBtn = document.getElementById('openNewTabBtn');
            if (openNewTabBtn) openNewTabBtn.style.display = 'inline-block';
            console.log(`App server detected on port ${port}`);
        }
    }
    
    async function loadAppWithFetchSrcdoc(frame, retries = 2) {
        const currentConversationId = window.currentConversationId;
        const url = `/api/app-server/app-preview/?conversation_id=${currentConversationId}&_t=${Date.now()}`;
        console.log('Loading app via fetch + srcdoc:', url);
        
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                const response = await fetch(url, { 
                    cache: 'no-store',
                    headers: { 'Accept': 'text/html' }
                });
                
                if (!response.ok) {
                    console.warn(`Fetch attempt ${attempt} failed: ${response.status}`);
                    continue;
                }
                
                const html = await response.text();
                
                if (html.length === 0) {
                    console.warn(`Fetch attempt ${attempt} empty (0 bytes)`);
                    continue;
                }
                
                console.log(`Fetched ${html.length} bytes on attempt ${attempt}`);
                const cleanHtml = html.replace(/<base[^>]*>/gi, '');
                frame.srcdoc = cleanHtml;
                frame.style.display = 'block';
                return;
                
            } catch (err) {
                console.warn(`Fetch attempt ${attempt} error:`, err);
            }
        }
        
        console.log('Fetch failed, falling back to iframe.src:', url);
        frame.src = url;
        frame.style.display = 'block';
    }
    
    function refreshApp() {
        const frame = document.getElementById('appFrame');
        if (appServerPort) {
            loadAppWithFetchSrcdoc(frame);
        } else {
            checkAppServer();
        }
    }
    
    function copyExternalUrl() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) {
            if (window.showNotification) {
                window.showNotification('No hay conversación activa', 'error');
            }
            return;
        }
        
        const baseUrl = window.location.origin;
        const externalUrl = `${baseUrl}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
        
        navigator.clipboard.writeText(externalUrl).then(() => {
            if (window.showNotification) {
                window.showNotification('✅ URL copiada al portapapeles', 'success');
            }
            
            const btn = document.getElementById('copyUrlBtn');
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓';
                setTimeout(() => { btn.textContent = originalText; }, 1500);
            }
        }).catch(err => {
            const textArea = document.createElement('textarea');
            textArea.value = externalUrl;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            if (window.showNotification) {
                window.showNotification('✅ URL copiada', 'success');
            }
        });
    }
    
    function openAppInNewTab() {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) {
            if (window.showNotification) {
                window.showNotification('No hay conversación activa', 'error');
            }
            return;
        }
        const baseUrl = window.location.origin;
        const externalUrl = `${baseUrl}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
        window.open(externalUrl, '_blank');
    }
    
    function startAppServerPolling() {
        if (appServerPollingActive) return;
        appServerPollingActive = true;
        
        setInterval(async () => {
            if (window.currentView === 'app' && document.visibilityState === 'visible') {
                await checkAppServer();
            }
        }, 3000);
    }
    
    function getActivePort() {
        return appServerPort;
    }
    
    // Exponer funciones globalmente
    window.AppPreviewModule = {
        check: checkAppServer,
        hide: hideAppIframe,
        setup: setupAppFrameHandlers,
        show: showAppInIframe,
        load: loadAppWithFetchSrcdoc,
        refresh: refreshApp,
        copyUrl: copyExternalUrl,
        openNewTab: openAppInNewTab,
        startPolling: startAppServerPolling,
        getActivePort: getActivePort
    };
    
    // Alias para compatibilidad
    window.checkAppServer = checkAppServer;
    window.hideAppIframe = hideAppIframe;
    window.setupAppFrameHandlers = setupAppFrameHandlers;
    window.showAppInIframe = showAppInIframe;
    window.loadAppWithFetchSrcdoc = loadAppWithFetchSrcdoc;
    window.refreshApp = refreshApp;
    window.copyExternalUrl = copyExternalUrl;
    window.openAppInNewTab = openAppInNewTab;
    window.startAppServerPolling = startAppServerPolling;
    
})();
