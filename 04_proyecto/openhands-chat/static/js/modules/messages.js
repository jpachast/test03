/**
 * Messages Module - Chat message handling
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    async function loadMessages(conversationId) {
        if (!conversationId) return;
        
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                chatMessages.innerHTML = '';
                data.messages.forEach(msg => {
                    addMessage(msg.content, msg.role);
                });
            } else {
                chatMessages.innerHTML = '<div class="message system">👋 ¡Hola! Soy tu asistente de desarrollo. ¿En qué puedo ayudarte?</div>';
            }
        } catch (error) {
            console.error('Error cargando mensajes:', error);
        }
    }
    
    function formatMessage(text) {
        if (!text) return '';
        
        // Transformar URLs localhost
        if (window.transformLocalhostUrlsInText) {
            text = window.transformLocalhostUrlsInText(text);
        }
        
        try {
            if (typeof marked !== 'undefined') {
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    highlight: function(code, lang) {
                        if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                            try {
                                return hljs.highlight(code, { language: lang }).value;
                            } catch (e) {}
                        }
                        if (typeof hljs !== 'undefined') {
                            try {
                                return hljs.highlightAuto(code).value;
                            } catch (e) {}
                        }
                        return code;
                    }
                });
                
                const renderer = new marked.Renderer();
                renderer.link = function(token) {
                    let href, title, text;
                    if (typeof token === 'object' && token !== null) {
                        href = token.href;
                        title = token.title;
                        text = token.text;
                    } else {
                        href = arguments[0];
                        title = arguments[1];
                        text = arguments[2];
                    }
                    const titleAttr = title ? ` title="${title}"` : '';
                    return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:underline">${text}</a>`;
                };
                
                marked.setOptions({ renderer });
                
                const html = marked.parse(text);
                
                setTimeout(() => {
                    document.querySelectorAll('pre code:not(.hljs)').forEach((block) => {
                        if (typeof hljs !== 'undefined') {
                            hljs.highlightElement(block);
                        }
                    });
                }, 0);
                
                return html;
            }
        } catch (e) {
            console.error('Error rendering markdown:', e);
        }
        
        // Fallback básico
        text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        text = text.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\n\n/g, '</p><p>');
        text = text.replace(/\n/g, '<br>');
        return '<p>' + text + '</p>';
    }
    
    function addMessage(content, type = 'user') {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const div = document.createElement('div');
        div.className = `message ${type}`;
        
        if (type === 'assistant') {
            div.innerHTML = '🤖 ' + formatMessage(content);
            
            // Detectar y renderizar bloques de diff como side-by-side
            setTimeout(() => {
                if (window.DiffSideBySide) {
                    window.DiffSideBySide.detect(div);
                }
            }, 100);
        } else if (type === 'user') {
            div.innerHTML = content;
        } else {
            div.innerHTML = content;
        }
        
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addMessageWithImages(content, type, images = []) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const div = document.createElement('div');
        div.className = `message ${type}`;
        
        let html = '';
        
        if (images.length > 0) {
            html += '<div class="message-images">';
            images.forEach(img => {
                html += `<img src="${img.dataUrl}" alt="${img.name}" class="message-image" onclick="showImageFullscreen('${img.dataUrl}')">`;
            });
            html += '</div>';
        }
        
        if (content) {
            if (type === 'assistant') {
                html += '🤖 ' + formatMessage(content);
            } else {
                html += content;
            }
        }
        
        div.innerHTML = html;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function showImageFullscreen(src) {
        const overlay = document.createElement('div');
        overlay.className = 'image-fullscreen-overlay';
        overlay.innerHTML = `
            <img src="${src}" class="fullscreen-image">
            <button class="close-fullscreen" onclick="this.parentElement.remove()">×</button>
        `;
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };
        document.body.appendChild(overlay);
    }
    
    // Exponer globalmente
    window.MessagesModule = {
        load: loadMessages,
        format: formatMessage,
        add: addMessage,
        addWithImages: addMessageWithImages,
        showFullscreen: showImageFullscreen
    };
    
    window.loadMessages = loadMessages;
    window.formatMessage = formatMessage;
    window.addMessage = addMessage;
    window.addMessageWithImages = addMessageWithImages;
    window.showImageFullscreen = showImageFullscreen;
    
})();
