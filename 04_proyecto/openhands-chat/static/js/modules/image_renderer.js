/**
 * Image Renderer Module - Renderiza imágenes en respuestas del chat
 * Detecta URLs de imágenes, base64, y análisis de visión
 */
(function() {
    'use strict';
    
    const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'];
    const BASE64_PATTERN = /data:image\/[^;]+;base64,[A-Za-z0-9+/=]+/g;
    const URL_PATTERN = /(https?:\/\/[^\s<>"']+\.(png|jpg|jpeg|gif|webp|svg|bmp)(\?[^\s<>"']*)?)/gi;
    
    // Estilos para las imágenes renderizadas
    function injectStyles() {
        if (document.getElementById('image-renderer-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'image-renderer-styles';
        styles.textContent = `
            .chat-image-container {
                margin: 10px 0;
                padding: 10px;
                background: #1e1e2e;
                border-radius: 8px;
                border: 1px solid #333;
            }
            
            .chat-image-wrapper {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                justify-content: flex-start;
            }
            
            .chat-image-item {
                position: relative;
                max-width: 300px;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .chat-image-item:hover {
                transform: scale(1.02);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            .chat-image-item img {
                width: 100%;
                height: auto;
                display: block;
                max-height: 250px;
                object-fit: contain;
                background: #2a2a3a;
            }
            
            .chat-image-caption {
                padding: 8px;
                background: #2a2a3a;
                font-size: 12px;
                color: #888;
                text-align: center;
                border-top: 1px solid #333;
            }
            
            .chat-image-actions {
                position: absolute;
                top: 5px;
                right: 5px;
                display: flex;
                gap: 5px;
                opacity: 0;
                transition: opacity 0.2s;
            }
            
            .chat-image-item:hover .chat-image-actions {
                opacity: 1;
            }
            
            .chat-image-btn {
                background: rgba(0,0,0,0.7);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .chat-image-btn:hover {
                background: rgba(0,0,0,0.9);
            }
            
            /* Modal fullscreen */
            .image-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                cursor: zoom-out;
            }
            
            .image-modal-content {
                max-width: 90vw;
                max-height: 90vh;
                object-fit: contain;
            }
            
            .image-modal-close {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                font-size: 24px;
                cursor: pointer;
                z-index: 10001;
            }
            
            /* Análisis de visión */
            .vision-analysis-container {
                margin: 10px 0;
                padding: 15px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 10px;
                border: 1px solid #0f3460;
            }
            
            .vision-analysis-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
                color: #e94560;
                font-weight: bold;
            }
            
            .vision-analysis-image {
                max-width: 200px;
                max-height: 150px;
                border-radius: 8px;
                float: left;
                margin-right: 15px;
                margin-bottom: 10px;
            }
            
            .vision-analysis-text {
                color: #ddd;
                line-height: 1.6;
            }
            
            /* Screenshot del navegador */
            .browser-screenshot-container {
                margin: 10px 0;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #444;
            }
            
            .browser-screenshot-header {
                background: #333;
                padding: 8px 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .browser-screenshot-url {
                font-size: 12px;
                color: #888;
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .browser-screenshot-img {
                width: 100%;
                max-height: 400px;
                object-fit: contain;
                background: #1a1a1a;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Detectar imágenes en texto
    function detectImages(text) {
        const images = [];
        
        // Detectar URLs de imágenes
        const urlMatches = text.match(URL_PATTERN) || [];
        urlMatches.forEach(url => {
            images.push({ type: 'url', src: url, caption: url.split('/').pop() });
        });
        
        // Detectar base64
        const base64Matches = text.match(BASE64_PATTERN) || [];
        base64Matches.forEach(data => {
            images.push({ type: 'base64', src: data, caption: 'Imagen embebida' });
        });
        
        return images;
    }
    
    // Detectar análisis de visión en respuesta
    function detectVisionAnalysis(element) {
        const text = element.textContent || '';
        
        // Patrones que indican análisis de imagen
        const visionPatterns = [
            /(?:analizando|analicé|análisis de) (?:la |esta )?imagen/i,
            /(?:veo|puedo ver|observo) (?:en la imagen|que la imagen)/i,
            /la imagen (?:muestra|contiene|presenta)/i,
            /en (?:la |esta )?(?:imagen|foto|captura)/i,
            /descripción de la imagen/i,
            /\[imagen\]/i,
            /📸|🖼️|📷/
        ];
        
        return visionPatterns.some(pattern => pattern.test(text));
    }
    
    // Renderizar imágenes detectadas
    function renderImages(element) {
        if (!element) return;
        
        injectStyles();
        
        const text = element.innerHTML;
        const images = detectImages(text);
        
        if (images.length === 0) return;
        
        // Crear contenedor de imágenes
        const container = document.createElement('div');
        container.className = 'chat-image-container';
        
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-image-wrapper';
        
        images.forEach((img, index) => {
            const item = document.createElement('div');
            item.className = 'chat-image-item';
            
            const imgEl = document.createElement('img');
            imgEl.src = img.src;
            imgEl.alt = img.caption;
            imgEl.loading = 'lazy';
            imgEl.onclick = () => showFullscreen(img.src);
            
            const caption = document.createElement('div');
            caption.className = 'chat-image-caption';
            caption.textContent = img.caption;
            
            const actions = document.createElement('div');
            actions.className = 'chat-image-actions';
            actions.innerHTML = `
                <button class="chat-image-btn" onclick="event.stopPropagation(); window.ImageRenderer.download('${img.src}', '${img.caption}')">⬇️</button>
                <button class="chat-image-btn" onclick="event.stopPropagation(); window.ImageRenderer.copy('${img.src}')">📋</button>
            `;
            
            item.appendChild(imgEl);
            item.appendChild(caption);
            item.appendChild(actions);
            wrapper.appendChild(item);
        });
        
        container.appendChild(wrapper);
        
        // Insertar después del contenido de texto
        element.appendChild(container);
    }
    
    // Renderizar screenshot de navegador
    function renderBrowserScreenshot(element, screenshotData, url) {
        injectStyles();
        
        const container = document.createElement('div');
        container.className = 'browser-screenshot-container';
        container.innerHTML = `
            <div class="browser-screenshot-header">
                <span>🌐</span>
                <span class="browser-screenshot-url">${url || 'Captura de pantalla'}</span>
                <button class="chat-image-btn" onclick="window.ImageRenderer.showFullscreen('${screenshotData}')">🔍</button>
            </div>
            <img src="${screenshotData}" class="browser-screenshot-img" onclick="window.ImageRenderer.showFullscreen('${screenshotData}')">
        `;
        
        element.appendChild(container);
    }
    
    // Mostrar imagen en fullscreen
    function showFullscreen(src) {
        const overlay = document.createElement('div');
        overlay.className = 'image-modal-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };
        
        const img = document.createElement('img');
        img.src = src;
        img.className = 'image-modal-content';
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'image-modal-close';
        closeBtn.textContent = '×';
        closeBtn.onclick = () => overlay.remove();
        
        overlay.appendChild(img);
        overlay.appendChild(closeBtn);
        document.body.appendChild(overlay);
        
        // Cerrar con Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                overlay.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }
    
    // Descargar imagen
    function downloadImage(src, filename) {
        const link = document.createElement('a');
        link.href = src;
        link.download = filename || 'imagen.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        if (window.showToast) {
            window.showToast('Imagen descargada', 'success');
        }
    }
    
    // Copiar imagen al portapapeles
    async function copyImage(src) {
        try {
            const response = await fetch(src);
            const blob = await response.blob();
            await navigator.clipboard.write([
                new ClipboardItem({ [blob.type]: blob })
            ]);
            
            if (window.showToast) {
                window.showToast('Imagen copiada al portapapeles', 'success');
            }
        } catch (e) {
            console.error('Error copiando imagen:', e);
            if (window.showToast) {
                window.showToast('Error al copiar imagen', 'error');
            }
        }
    }
    
    // Detectar y renderizar imágenes en mensajes del asistente
    function detectAndRender(element) {
        if (!element) return;
        
        injectStyles();
        
        // Buscar imágenes en el contenido
        const images = element.querySelectorAll('img:not(.chat-rendered)');
        images.forEach(img => {
            img.classList.add('chat-rendered');
            img.style.maxWidth = '300px';
            img.style.maxHeight = '250px';
            img.style.borderRadius = '8px';
            img.style.cursor = 'pointer';
            img.onclick = () => showFullscreen(img.src);
        });
        
        // Detectar URLs de imágenes en texto y convertirlas
        const text = element.innerHTML;
        const urlMatches = text.match(URL_PATTERN) || [];
        
        urlMatches.forEach(url => {
            // Verificar que no esté ya en un tag img
            if (!text.includes(`src="${url}"`) && !text.includes(`src='${url}'`)) {
                const imgTag = `<div class="chat-image-item" style="display:inline-block;margin:5px;">
                    <img src="${url}" style="max-width:250px;max-height:200px;border-radius:8px;cursor:pointer;" 
                         onclick="window.ImageRenderer.showFullscreen('${url}')" loading="lazy">
                </div>`;
                element.innerHTML = element.innerHTML.replace(url, imgTag);
            }
        });
    }
    
    // Inicializar
    function init() {
        injectStyles();
        console.log('[ImageRenderer] Módulo inicializado');
        
        // Observador para detectar nuevos mensajes
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1 && node.classList && node.classList.contains('message')) {
                            setTimeout(() => {
                                detectAndRender(node);
                            }, 300);
                        }
                    });
                });
            });
            
            observer.observe(chatMessages, { childList: true, subtree: true });
            console.log('[ImageRenderer] Observer configurado');
        }
    }
    
    // Inicializar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 1000);
    }
    
    // Exponer API global
    window.ImageRenderer = {
        detect: detectImages,
        render: renderImages,
        detectAndRender: detectAndRender,
        renderScreenshot: renderBrowserScreenshot,
        showFullscreen: showFullscreen,
        download: downloadImage,
        copy: copyImage,
        init: init
    };
    
})();
