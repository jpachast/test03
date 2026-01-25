/**
 * URL Utils Module - URL transformation utilities (OpenHands pattern)
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    /**
     * Transforma URLs localhost al hostname actual
     * Similar a transformVSCodeUrl de OpenHands
     * @param {string} url - URL original (puede ser localhost)
     * @returns {string} URL transformada con el hostname correcto
     */
    function transformLocalhostUrl(url) {
        if (!url) return null;
        try {
            const urlObj = new URL(url);
            if (urlObj.hostname === 'localhost' && window.location.hostname !== 'localhost') {
                urlObj.hostname = window.location.hostname;
                return urlObj.toString();
            }
            return url;
        } catch {
            return url;
        }
    }
    
    /**
     * Obtiene la URL externa completa para un puerto de app
     * @param {number} port - Puerto del servidor
     * @returns {string} URL externa accesible
     */
    function getExternalAppUrl(port) {
        const currentConversationId = window.currentConversationId;
        if (!currentConversationId) return null;
        return `${window.location.origin}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
    }
    
    /**
     * Transforma URLs localhost en el texto a URLs externas accesibles
     * Patrón OpenHands: detecta http://localhost:PORT y lo convierte
     * @param {string} text - Texto con posibles URLs localhost
     * @returns {string} Texto con URLs transformadas
     */
    function transformLocalhostUrlsInText(text) {
        if (!text) return text;
        
        const localhostRegex = /http:\/\/localhost:(\d+)/g;
        
        if (window.location.hostname === 'localhost') {
            return text;
        }
        
        const currentConversationId = window.currentConversationId;
        return text.replace(localhostRegex, (match, port) => {
            if (currentConversationId) {
                return `${window.location.origin}/api/app-server/app-preview/?conversation_id=${currentConversationId}`;
            }
            return `http://${window.location.hostname}:${port}`;
        });
    }
    
    // Exponer globalmente
    window.UrlUtilsModule = {
        transformUrl: transformLocalhostUrl,
        getExternalUrl: getExternalAppUrl,
        transformInText: transformLocalhostUrlsInText
    };
    
    window.transformLocalhostUrl = transformLocalhostUrl;
    window.getExternalAppUrl = getExternalAppUrl;
    window.transformLocalhostUrlsInText = transformLocalhostUrlsInText;
    
})();
