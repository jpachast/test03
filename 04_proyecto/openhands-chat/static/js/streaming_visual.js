// streaming_visual.js - Efecto de escritura para respuestas
(function() {
    console.log('[STREAMING] Inicializando streaming_visual.js...');

    // Funcion para aplicar streaming visual
    window.applyStreamingEffect = async function(element, text) {
        const contentEl = element.querySelector('.message-content') || element;
        contentEl.innerHTML = '';

        let accumulated = '';
        const step = 3;
        const delay = 5;

        for (let i = 0; i < text.length; i += step) {
            accumulated += text.substr(i, step);
            contentEl.innerHTML = window.marked ? window.marked.parse(accumulated) : accumulated;
            element.scrollIntoView({ behavior: 'smooth', block: 'end' });
            await new Promise(r => setTimeout(r, delay));
        }
        contentEl.innerHTML = window.marked ? window.marked.parse(text) : text;
    };

    // Observar nuevos mensajes del asistente
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType !== 1) return;
                
                const isAssistant = node.classList && 
                    (node.classList.contains('assistant') || 
                     (node.classList.contains('message') && node.innerHTML && node.innerHTML.includes('🤖')));
                
                if (!isAssistant) return;
                if (node.classList.contains('streaming-applied')) return;
                if (node.classList.contains('streaming')) return;
                if (node.classList.contains('streaming-progress')) return;

                const content = node.querySelector('.message-content') || node;
                const text = content.innerHTML || content.textContent || '';
                
                if (text.length < 50) return;
                
                console.log('[STREAMING] Aplicando efecto a mensaje de', text.length, 'chars');
                node.classList.add('streaming-applied');

                const originalText = text;
                content.innerHTML = '';

                (async () => {
                    let acc = '';
                    const step = 4;
                    const delay = 4;
                    for (let i = 0; i < originalText.length; i += step) {
                        acc += originalText.substr(i, step);
                        content.innerHTML = acc;
                        await new Promise(r => setTimeout(r, delay));
                    }
                    content.innerHTML = originalText;
                })();
            });
        });
    });

    function startObserver() {
        const chatMessages = document.getElementById('chatMessages') || 
                           document.querySelector('.chat-messages');
        
        if (chatMessages) {
            observer.observe(chatMessages, { childList: true, subtree: true });
            console.log('[STREAMING] Observer activo en:', chatMessages.id || chatMessages.className);
        } else {
            console.log('[STREAMING] Reintentando en 500ms...');
            setTimeout(startObserver, 500);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startObserver);
    } else {
        startObserver();
    }
})();
