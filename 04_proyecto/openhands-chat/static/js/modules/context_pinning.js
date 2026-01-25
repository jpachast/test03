/**
 * Context Pinning Module - File pinning for context
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let pinnedFiles = [];
    
    async function loadPinnedFiles() {
        const currentProject = window.currentProject;
        if (!currentProject) return;
        
        try {
            const response = await fetch(`/api/chat/pins/${encodeURIComponent(currentProject)}`);
            const data = await response.json();
            pinnedFiles = data.pins || [];
            renderPinnedFiles();
        } catch (e) {
            console.error('Error loading pins:', e);
        }
    }
    
    async function pinFile(filePath, description = null) {
        const currentProject = window.currentProject;
        if (!currentProject) return;
        
        try {
            const formData = new FormData();
            formData.append('file_path', filePath);
            if (description) formData.append('description', description);
            
            const response = await fetch(`/api/chat/pins/${encodeURIComponent(currentProject)}`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (result.success) {
                await loadPinnedFiles();
                if (window.showNotification) {
                    window.showNotification('📌 Archivo fijado al contexto');
                }
            }
        } catch (e) {
            console.error('Error pinning file:', e);
        }
    }
    
    async function unpinFile(filePath) {
        const currentProject = window.currentProject;
        if (!currentProject) return;
        
        try {
            const response = await fetch(
                `/api/chat/pins/${encodeURIComponent(currentProject)}/${encodeURIComponent(filePath)}`,
                { method: 'DELETE' }
            );
            const result = await response.json();
            if (result.success) {
                await loadPinnedFiles();
                if (window.showNotification) {
                    window.showNotification('📌 Archivo quitado del contexto');
                }
            }
        } catch (e) {
            console.error('Error unpinning file:', e);
        }
    }
    
    function renderPinnedFiles() {
        const container = document.getElementById('pinnedFilesContainer');
        if (!container) return;
        
        if (pinnedFiles.length === 0) {
            container.innerHTML = '<div class="no-pins">No hay archivos fijados</div>';
            return;
        }
        
        container.innerHTML = pinnedFiles.map(pin => `
            <div class="pinned-file">
                <span class="pin-icon">📌</span>
                <span class="pin-name" title="${pin.path}">${pin.path.split('/').pop()}</span>
                <button class="unpin-btn" onclick="unpinFile('${pin.path}')" title="Quitar">×</button>
            </div>
        `).join('');
    }
    
    function getPinnedFiles() {
        return [...pinnedFiles];
    }
    
    // Cargar pins cuando se abre una conversación
    document.addEventListener('conversationOpened', loadPinnedFiles);
    
    // Exponer globalmente
    window.ContextPinningModule = {
        load: loadPinnedFiles,
        pin: pinFile,
        unpin: unpinFile,
        render: renderPinnedFiles,
        getFiles: getPinnedFiles
    };
    
    window.loadPinnedFiles = loadPinnedFiles;
    window.pinFile = pinFile;
    window.unpinFile = unpinFile;
    window.renderPinnedFiles = renderPinnedFiles;
    window.pinnedFiles = pinnedFiles;
    
})();
