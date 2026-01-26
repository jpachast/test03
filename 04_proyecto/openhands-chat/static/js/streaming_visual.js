
// streaming_visual.js - Efecto de escritura para respuestas
(function() {
    // Interceptar cuando se muestra la respuesta final
    const originalScrollIntoView = Element.prototype.scrollIntoView;
    
    // Función para aplicar streaming visual
    window.applyStreamingEffect = async function(element, text) {
        const contentEl = element.querySelector('.message-content') || element;
        contentEl.innerHTML = '';
        
        let accumulated = '';
        const step = 4;
        for (let i = 0; i < text.length; i += step) {
            accumulated += text.substr(i, step);
            contentEl.innerHTML = marked ? marked.parse(accumulated) : accumulated;
            element.scrollIntoView({ behavior: 'smooth', block: 'end' });
            await new Promise(r => setTimeout(r, 8));
        }
    };
    
    // Observar nuevos mensajes del asistente
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && 
                    node.classList && 
                    node.classList.contains('message') && 
                    node.classList.contains('assistant') &&
                    !node.classList.contains('streaming-applied')) {
                    
                    const content = node.querySelector('.message-content');
                    if (content && content.innerHTML.length > 100) {
                        const text = content.innerHTML;
                        node.classList.add('streaming-applied');
                        
                        // Aplicar efecto
                        content.innerHTML = '';
                        (async () => {
                            let acc = '';
                            const step = 5;
                            for (let i = 0; i < text.length; i += step) {
                                acc += text.substr(i, step);
                                content.innerHTML = acc;
                                await new Promise(r => setTimeout(r, 6));
                            }
                        })();
                    }
                }
            });
        });
    });
    
    // Iniciar observación cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const chatMessages = document.querySelector('.chat-messages');
            if (chatMessages) {
                observer.observe(chatMessages, { childList: true, subtree: true });
                console.log('[STREAMING] Visual streaming observer active');
            }
        });
    } else {
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            observer.observe(chatMessages, { childList: true, subtree: true });
            console.log('[STREAMING] Visual streaming observer active');
        }
    }
})();
