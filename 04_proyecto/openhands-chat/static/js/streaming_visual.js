/**
 * streaming_visual.js v3.0 - Streaming REAL completo para OpenHands Chat
 * 
 * Garantiza que TODAS las respuestas se muestren con efecto de streaming:
 * 1. Tokens reales del LLM (cuando genera texto)
 * 2. Efecto visual de escritura (cuando usa herramientas)
 */
(function() {
    'use strict';
    
    const CONFIG = {
        charDelay: 2,        // ms por iteración
        charsPerChunk: 8,    // caracteres por chunk
        minLength: 80,       // mínimo para aplicar efecto
        debug: false
    };
    
    let activeStreaming = null;
    
    function log(...args) {
        if (CONFIG.debug) console.log('[STREAM]', ...args);
    }
    
    // Efecto de streaming visual
    window.applyStreamingEffect = function(element, text, isMarkdown = true) {
        if (!element || !text) return Promise.resolve();
        
        const contentEl = element.querySelector('.message-content') || element;
        
        if (text.length < CONFIG.minLength) {
            contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(text) : text;
            return Promise.resolve();
        }
        
        // Cancelar streaming anterior si existe
        if (activeStreaming) {
            activeStreaming.cancel = true;
        }
        
        const state = { cancel: false };
        activeStreaming = state;
        
        return new Promise(resolve => {
            let i = 0;
            contentEl.innerHTML = '';
            element.classList.add('streaming');
            
            const typeNext = () => {
                if (state.cancel || i >= text.length) {
                    contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(text) : text;
                    element.classList.remove('streaming');
                    activeStreaming = null;
                    resolve();
                    return;
                }
                
                i += CONFIG.charsPerChunk;
                const partial = text.substring(0, i);
                contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(partial) : partial;
                
                // Scroll
                const chat = document.getElementById('chatMessages');
                if (chat) chat.scrollTop = chat.scrollHeight;
                
                requestAnimationFrame(() => setTimeout(typeNext, CONFIG.charDelay));
            };
            
            typeNext();
        });
    };
    
    // Observador para mensajes que llegan de golpe
    function setupObserver() {
        const chatMessages = document.getElementById('chatMessages') || 
                            document.querySelector('.chat-messages');
        if (!chatMessages) {
            setTimeout(setupObserver, 500);
            return;
        }
        
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    if (!node.classList?.contains('message')) return;
                    if (!node.classList?.contains('assistant')) return;
                    if (node.classList?.contains('streaming-applied')) return;
                    if (node.classList?.contains('streaming')) return;
                    if (node.classList?.contains('streaming-progress')) return;
                    
                    const content = node.querySelector('.message-content');
                    if (!content) return;
                    
                    const text = content.innerHTML;
                    if (text.length < CONFIG.minLength) return;
                    
                    // Marcar para no procesar de nuevo
                    node.classList.add('streaming-applied');
                    
                    log('Applying visual streaming to message');
                    
                    // Aplicar efecto
                    content.innerHTML = '';
                    node.classList.add('streaming');
                    
                    let i = 0;
                    const animate = () => {
                        if (i >= text.length) {
                            content.innerHTML = text;
                            node.classList.remove('streaming');
                            return;
                        }
                        
                        i += CONFIG.charsPerChunk;
                        content.innerHTML = text.substring(0, i);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        
                        requestAnimationFrame(() => setTimeout(animate, CONFIG.charDelay));
                    };
                    
                    animate();
                });
            });
        });
        
        observer.observe(chatMessages, { childList: true, subtree: true });
        log('Observer active');
    }
    
    // Estilos de cursor de streaming
    function addStyles() {
        if (document.getElementById('streaming-styles-v3')) return;
        
        const style = document.createElement('style');
        style.id = 'streaming-styles-v3';
        style.textContent = `
            @keyframes cursor-blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
            .message.streaming .message-content::after {
                content: '▊';
                animation: cursor-blink 0.6s infinite;
                color: #4CAF50;
                margin-left: 2px;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Inicializar
    function init() {
        addStyles();
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupObserver);
        } else {
            setupObserver();
        }
        console.log('🚀 [STREAMING] v3.0 loaded');
    }
    
    init();
})();
