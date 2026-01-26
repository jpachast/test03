/**
 * streaming_visual.js v3.1 - Streaming REAL completo para OpenHands Chat
 * Fix: Compatible con mensajes con y sin .message-content wrapper
 */
(function() {
    'use strict';

    const CONFIG = {
        charDelay: 2,
        charsPerChunk: 8,
        minLength: 80,
        debug: true
    };

    function log(...args) {
        if (CONFIG.debug) console.log('[STREAM]', ...args);
    }

    // Efecto de streaming visual
    window.applyStreamingEffect = function(element, text, isMarkdown = true) {
        if (!element || !text) return Promise.resolve();
        
        // Buscar contenedor o usar el elemento directamente
        const contentEl = element.querySelector('.message-content') || element;

        if (text.length < CONFIG.minLength) {
            contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(text) : text;
            return Promise.resolve();
        }

        return new Promise(resolve => {
            let i = 0;
            element.classList.add('streaming');

            const typeNext = () => {
                if (i >= text.length) {
                    contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(text) : text;
                    element.classList.remove('streaming');
                    resolve();
                    return;
                }

                i += CONFIG.charsPerChunk;
                const partial = text.substring(0, i);
                contentEl.innerHTML = isMarkdown && window.marked ? marked.parse(partial) : partial;

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
            log('Chat container not found, retrying...');
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

                    // Obtener texto - puede estar en .message-content o directamente en el nodo
                    const contentEl = node.querySelector('.message-content') || node;
                    const text = contentEl.innerHTML || '';
                    
                    // Ignorar si es muy corto
                    if (text.length < CONFIG.minLength) {
                        log('Message too short, skipping:', text.length);
                        return;
                    }

                    log('Applying streaming effect to message:', text.length, 'chars');
                    node.classList.add('streaming-applied');

                    // Guardar texto y limpiar
                    const originalText = text;
                    contentEl.innerHTML = '';
                    node.classList.add('streaming');

                    let i = 0;
                    const animate = () => {
                        if (i >= originalText.length) {
                            contentEl.innerHTML = originalText;
                            node.classList.remove('streaming');
                            return;
                        }

                        i += CONFIG.charsPerChunk;
                        contentEl.innerHTML = originalText.substring(0, i);
                        chatMessages.scrollTop = chatMessages.scrollHeight;

                        requestAnimationFrame(() => setTimeout(animate, CONFIG.charDelay));
                    };

                    animate();
                });
            });
        });

        observer.observe(chatMessages, { childList: true, subtree: true });
        log('Observer active on:', chatMessages.id || chatMessages.className);
    }

    // Estilos de cursor
    function addStyles() {
        if (document.getElementById('streaming-styles-v3')) return;

        const style = document.createElement('style');
        style.id = 'streaming-styles-v3';
        style.textContent = `
            @keyframes cursor-blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
            .message.streaming::after {
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
        console.log('🚀 [STREAMING] v3.1 loaded');
    }

    init();
})();
