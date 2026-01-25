/**
 * Attachments Module - Soporte para archivos adjuntos
 * PDFs, documentos, imágenes, código y más
 */
(function() {
    'use strict';
    
    // Tipos de archivo soportados
    const FILE_TYPES = {
        pdf: { icon: '📄', color: '#e74c3c', name: 'PDF' },
        doc: { icon: '📝', color: '#2980b9', name: 'Word' },
        docx: { icon: '📝', color: '#2980b9', name: 'Word' },
        xls: { icon: '📊', color: '#27ae60', name: 'Excel' },
        xlsx: { icon: '📊', color: '#27ae60', name: 'Excel' },
        ppt: { icon: '📽️', color: '#e67e22', name: 'PowerPoint' },
        pptx: { icon: '📽️', color: '#e67e22', name: 'PowerPoint' },
        txt: { icon: '📃', color: '#95a5a6', name: 'Texto' },
        md: { icon: '📋', color: '#9b59b6', name: 'Markdown' },
        json: { icon: '{ }', color: '#f39c12', name: 'JSON' },
        xml: { icon: '🏷️', color: '#1abc9c', name: 'XML' },
        csv: { icon: '📈', color: '#3498db', name: 'CSV' },
        zip: { icon: '📦', color: '#7f8c8d', name: 'ZIP' },
        rar: { icon: '📦', color: '#7f8c8d', name: 'RAR' },
        png: { icon: '🖼️', color: '#e91e63', name: 'Imagen' },
        jpg: { icon: '🖼️', color: '#e91e63', name: 'Imagen' },
        jpeg: { icon: '🖼️', color: '#e91e63', name: 'Imagen' },
        gif: { icon: '🎞️', color: '#9c27b0', name: 'GIF' },
        svg: { icon: '🎨', color: '#ff5722', name: 'SVG' },
        mp3: { icon: '🎵', color: '#00bcd4', name: 'Audio' },
        mp4: { icon: '🎬', color: '#673ab7', name: 'Video' },
        py: { icon: '🐍', color: '#3776ab', name: 'Python' },
        js: { icon: '⚡', color: '#f7df1e', name: 'JavaScript' },
        ts: { icon: '💠', color: '#3178c6', name: 'TypeScript' },
        html: { icon: '🌐', color: '#e34f26', name: 'HTML' },
        css: { icon: '🎨', color: '#1572b6', name: 'CSS' },
        java: { icon: '☕', color: '#007396', name: 'Java' },
        cpp: { icon: '⚙️', color: '#00599c', name: 'C++' },
        c: { icon: '⚙️', color: '#a8b9cc', name: 'C' },
        go: { icon: '🐹', color: '#00add8', name: 'Go' },
        rs: { icon: '🦀', color: '#dea584', name: 'Rust' },
        rb: { icon: '💎', color: '#cc342d', name: 'Ruby' },
        php: { icon: '🐘', color: '#777bb4', name: 'PHP' },
        sql: { icon: '🗃️', color: '#336791', name: 'SQL' },
        sh: { icon: '💻', color: '#4eaa25', name: 'Shell' },
        default: { icon: '📎', color: '#95a5a6', name: 'Archivo' }
    };
    
    // Estado
    const state = {
        attachments: [],
        previewOpen: false
    };
    
    // Inyectar estilos
    function injectStyles() {
        if (document.getElementById('attachments-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'attachments-styles';
        styles.textContent = `
            /* ===== CONTENEDOR DE ADJUNTOS ===== */
            .attachments-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 12px 0;
                padding: 12px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                border: 1px dashed #444;
            }
            
            .attachments-header {
                width: 100%;
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                font-size: 12px;
                color: #888;
                text-transform: uppercase;
            }
            
            /* ===== TARJETA DE ARCHIVO ===== */
            .attachment-card {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 14px;
                background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%);
                border: 1px solid #333;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s ease;
                min-width: 180px;
                max-width: 250px;
            }
            
            .attachment-card:hover {
                border-color: #58a6ff;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
            }
            
            .attachment-icon {
                font-size: 28px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
            
            .attachment-info {
                flex: 1;
                min-width: 0;
            }
            
            .attachment-name {
                font-weight: 500;
                color: #e6edf3;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-size: 13px;
            }
            
            .attachment-meta {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 11px;
                color: #8b949e;
                margin-top: 2px;
            }
            
            .attachment-type {
                padding: 2px 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                font-size: 10px;
                text-transform: uppercase;
            }
            
            .attachment-actions {
                display: flex;
                gap: 4px;
                opacity: 0;
                transition: opacity 0.2s;
            }
            
            .attachment-card:hover .attachment-actions {
                opacity: 1;
            }
            
            .attachment-btn {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ddd;
                cursor: pointer;
                font-size: 12px;
                transition: background 0.2s;
            }
            
            .attachment-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* ===== PREVIEW MODAL ===== */
            .attachment-preview-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.2s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .attachment-preview-container {
                background: #1e1e2e;
                border-radius: 16px;
                max-width: 90vw;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
            }
            
            .attachment-preview-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                border-bottom: 1px solid #333;
            }
            
            .attachment-preview-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                color: #e6edf3;
            }
            
            .attachment-preview-close {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                color: white;
                font-size: 20px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .attachment-preview-close:hover {
                background: rgba(248, 81, 73, 0.5);
            }
            
            .attachment-preview-content {
                padding: 20px;
                overflow: auto;
                max-height: 70vh;
            }
            
            .attachment-preview-content pre {
                background: #0d1117;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 0;
            }
            
            .attachment-preview-content code {
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 13px;
                line-height: 1.6;
            }
            
            .attachment-preview-content img {
                max-width: 100%;
                border-radius: 8px;
            }
            
            .attachment-preview-content iframe {
                width: 100%;
                height: 60vh;
                border: none;
                border-radius: 8px;
            }
            
            .attachment-preview-actions {
                display: flex;
                gap: 10px;
                padding: 16px 20px;
                background: #161b22;
                border-top: 1px solid #333;
            }
            
            .preview-action-btn {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .preview-action-btn.primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .preview-action-btn.primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            
            .preview-action-btn.secondary {
                background: rgba(255, 255, 255, 0.1);
                color: #ddd;
            }
            
            .preview-action-btn.secondary:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            
            /* ===== ZONA DE DROP ===== */
            .drop-zone {
                border: 2px dashed #444;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                transition: all 0.2s;
                margin: 10px 0;
            }
            
            .drop-zone.dragover {
                border-color: #58a6ff;
                background: rgba(88, 166, 255, 0.1);
            }
            
            .drop-zone-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            .drop-zone-text {
                color: #888;
                font-size: 14px;
            }
            
            .drop-zone-text strong {
                color: #58a6ff;
                cursor: pointer;
            }
            
            /* ===== BADGE DE ARCHIVO EN MENSAJES ===== */
            .file-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                background: rgba(88, 166, 255, 0.15);
                border: 1px solid rgba(88, 166, 255, 0.3);
                border-radius: 6px;
                font-size: 12px;
                color: #58a6ff;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .file-badge:hover {
                background: rgba(88, 166, 255, 0.25);
                transform: scale(1.02);
            }
            
            /* ===== LISTA DE ADJUNTOS INLINE ===== */
            .inline-attachments {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid #333;
            }
            
            /* ===== INDICADOR DE CARGA ===== */
            .attachment-loading {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                background: rgba(88, 166, 255, 0.1);
                border-radius: 8px;
                color: #58a6ff;
            }
            
            .attachment-loading-spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #333;
                border-top-color: #58a6ff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Obtener info del tipo de archivo
    function getFileTypeInfo(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        return FILE_TYPES[ext] || FILE_TYPES.default;
    }
    
    // Formatear tamaño de archivo
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    // Crear tarjeta de archivo
    function createAttachmentCard(file) {
        const typeInfo = getFileTypeInfo(file.name);
        
        const card = document.createElement('div');
        card.className = 'attachment-card';
        card.innerHTML = `
            <div class="attachment-icon" style="color: ${typeInfo.color}">${typeInfo.icon}</div>
            <div class="attachment-info">
                <div class="attachment-name" title="${file.name}">${file.name}</div>
                <div class="attachment-meta">
                    <span class="attachment-type" style="color: ${typeInfo.color}">${typeInfo.name}</span>
                    <span>${formatFileSize(file.size || 0)}</span>
                </div>
            </div>
            <div class="attachment-actions">
                <button class="attachment-btn" title="Vista previa">👁️</button>
                <button class="attachment-btn" title="Descargar">⬇️</button>
            </div>
        `;
        
        // Event listeners
        const previewBtn = card.querySelector('.attachment-btn:first-child');
        const downloadBtn = card.querySelector('.attachment-btn:last-child');
        
        previewBtn.onclick = (e) => {
            e.stopPropagation();
            showPreview(file);
        };
        
        downloadBtn.onclick = (e) => {
            e.stopPropagation();
            downloadFile(file);
        };
        
        card.onclick = () => showPreview(file);
        
        return card;
    }
    
    // Crear contenedor de adjuntos
    function createAttachmentsContainer(files) {
        const container = document.createElement('div');
        container.className = 'attachments-container';
        
        container.innerHTML = `
            <div class="attachments-header">
                <span>📎</span>
                <span>Archivos adjuntos (${files.length})</span>
            </div>
        `;
        
        files.forEach(file => {
            container.appendChild(createAttachmentCard(file));
        });
        
        return container;
    }
    
    // Mostrar preview
    function showPreview(file) {
        const typeInfo = getFileTypeInfo(file.name);
        
        const overlay = document.createElement('div');
        overlay.className = 'attachment-preview-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) closePreview(overlay);
        };
        
        let contentHTML = '';
        const ext = file.name.split('.').pop().toLowerCase();
        
        // Determinar cómo mostrar el contenido
        if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext)) {
            contentHTML = `<img src="${file.url || file.dataUrl}" alt="${file.name}">`;
        } else if (ext === 'pdf') {
            contentHTML = `<iframe src="${file.url || file.dataUrl}"></iframe>`;
        } else if (['txt', 'md', 'json', 'xml', 'csv', 'py', 'js', 'ts', 'html', 'css', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php', 'sql', 'sh'].includes(ext)) {
            const content = file.content || 'Contenido no disponible';
            contentHTML = `<pre><code class="language-${ext}">${escapeHtml(content)}</code></pre>`;
        } else {
            contentHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 64px; margin-bottom: 20px;">${typeInfo.icon}</div>
                    <div style="color: #888;">Vista previa no disponible para este tipo de archivo</div>
                    <div style="margin-top: 10px; color: #58a6ff;">${file.name}</div>
                </div>
            `;
        }
        
        overlay.innerHTML = `
            <div class="attachment-preview-container" style="min-width: 500px;">
                <div class="attachment-preview-header">
                    <div class="attachment-preview-title">
                        <span style="font-size: 24px;">${typeInfo.icon}</span>
                        <span>${file.name}</span>
                    </div>
                    <button class="attachment-preview-close" onclick="window.Attachments.closePreview(this.closest('.attachment-preview-overlay'))">×</button>
                </div>
                <div class="attachment-preview-content">
                    ${contentHTML}
                </div>
                <div class="attachment-preview-actions">
                    <button class="preview-action-btn primary" onclick="window.Attachments.downloadFile(${JSON.stringify(file).replace(/"/g, '&quot;')})">
                        ⬇️ Descargar
                    </button>
                    <button class="preview-action-btn secondary" onclick="window.Attachments.copyContent('${file.name}')">
                        📋 Copiar contenido
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        state.previewOpen = true;
        
        // Highlight code si está disponible
        if (window.hljs) {
            overlay.querySelectorAll('pre code').forEach(block => {
                window.hljs.highlightElement(block);
            });
        }
        
        // Cerrar con Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closePreview(overlay);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }
    
    // Cerrar preview
    function closePreview(overlay) {
        if (overlay) {
            overlay.remove();
            state.previewOpen = false;
        }
    }
    
    // Descargar archivo
    function downloadFile(file) {
        const link = document.createElement('a');
        link.href = file.url || file.dataUrl || '#';
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        if (window.showToast) {
            window.showToast(`Descargando ${file.name}`, 'success');
        }
    }
    
    // Copiar contenido
    async function copyContent(filename) {
        try {
            // Buscar el contenido en el preview actual
            const preCode = document.querySelector('.attachment-preview-content pre code');
            if (preCode) {
                await navigator.clipboard.writeText(preCode.textContent);
                if (window.showToast) {
                    window.showToast('Contenido copiado al portapapeles', 'success');
                }
            }
        } catch (e) {
            console.error('Error copiando:', e);
        }
    }
    
    // Escapar HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Crear badge de archivo inline
    function createFileBadge(file) {
        const typeInfo = getFileTypeInfo(file.name);
        
        const badge = document.createElement('span');
        badge.className = 'file-badge';
        badge.innerHTML = `${typeInfo.icon} ${file.name}`;
        badge.onclick = () => showPreview(file);
        
        return badge;
    }
    
    // Detectar menciones de archivos en respuestas
    function detectFileReferences(element) {
        if (!element) return;
        
        const text = element.textContent || '';
        
        // Patrones para detectar archivos mencionados
        const filePatterns = [
            /\b(\w+\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|md|json|xml|csv|zip|py|js|ts|html|css|java|cpp|c|go|rs|rb|php|sql|sh))\b/gi
        ];
        
        let foundFiles = [];
        filePatterns.forEach(pattern => {
            const matches = text.match(pattern);
            if (matches) {
                foundFiles = foundFiles.concat(matches);
            }
        });
        
        // Si encontramos archivos, mostrar indicador
        if (foundFiles.length > 0 && !element.querySelector('.inline-attachments')) {
            const uniqueFiles = [...new Set(foundFiles)];
            
            const container = document.createElement('div');
            container.className = 'inline-attachments';
            
            uniqueFiles.slice(0, 5).forEach(filename => {
                const badge = createFileBadge({ name: filename, size: 0 });
                container.appendChild(badge);
            });
            
            if (uniqueFiles.length > 5) {
                const more = document.createElement('span');
                more.className = 'file-badge';
                more.textContent = `+${uniqueFiles.length - 5} más`;
                container.appendChild(more);
            }
            
            element.appendChild(container);
        }
    }
    
    // Renderizar adjuntos en mensaje
    function renderAttachments(element, files) {
        if (!element || !files || files.length === 0) return;
        
        const container = createAttachmentsContainer(files);
        element.appendChild(container);
    }
    
    // Inicializar
    function init() {
        injectStyles();
        console.log('[Attachments] Módulo de adjuntos inicializado');
        
        // Observer para detectar referencias a archivos
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1 && node.classList && node.classList.contains('message')) {
                            setTimeout(() => detectFileReferences(node), 300);
                        }
                    });
                });
            });
            
            observer.observe(chatMessages, { childList: true, subtree: true });
        }
    }
    
    // Inicializar cuando DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 1000);
    }
    
    // Exponer API global
    window.Attachments = {
        init: init,
        createCard: createAttachmentCard,
        createContainer: createAttachmentsContainer,
        showPreview: showPreview,
        closePreview: closePreview,
        downloadFile: downloadFile,
        copyContent: copyContent,
        createBadge: createFileBadge,
        detectReferences: detectFileReferences,
        render: renderAttachments,
        getFileTypeInfo: getFileTypeInfo,
        formatFileSize: formatFileSize
    };
    
})();
