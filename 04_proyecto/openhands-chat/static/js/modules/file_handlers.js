/**
 * File Handlers Module - File and image handling
 * Extracted from index.js for better maintainability
 */
(function() {
    'use strict';
    
    let attachedFiles = [];
    
    function attachFile() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.click();
    }
    
    function handleFileSelect(e) {
        const files = Array.from(e.target.files || []);
        processFiles(files);
        e.target.value = '';
    }
    
    function handlePaste(e) {
        const items = e.clipboardData?.items;
        if (!items) return;
        
        const files = [];
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                const file = item.getAsFile();
                if (file) files.push(file);
            }
        }
        
        if (files.length > 0) {
            e.preventDefault();
            processFiles(files);
        }
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer?.files || []);
        processFiles(files);
    }
    
    function processFiles(files) {
        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const dataUrl = event.target.result;
                const isImage = file.type.startsWith('image/');
                
                attachedFiles.push({
                    file: file,
                    dataUrl: dataUrl,
                    type: isImage ? 'image' : 'text',
                    name: file.name
                });
                
                updateAttachedFilesUI();
            };
            
            if (file.type.startsWith('image/')) {
                reader.readAsDataURL(file);
            } else {
                reader.readAsText(file);
            }
        });
    }
    
    function updateAttachedFilesUI() {
        const container = document.getElementById('attachedImages');
        if (!container) return;
        
        container.innerHTML = '';
        
        attachedFiles.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'attached-image-item';
            
            if (item.type === 'image') {
                div.innerHTML = `
                    <img src="${item.dataUrl}" alt="${item.name}">
                    <button class="remove-image" onclick="removeAttachedFile(${index})">×</button>
                `;
            } else {
                div.innerHTML = `
                    <div style="padding: 8px; background: #21262d; font-size: 12px; color: #8b949e;">
                        📎 ${item.name}
                    </div>
                    <button class="remove-image" onclick="removeAttachedFile(${index})">×</button>
                `;
            }
            
            container.appendChild(div);
        });
    }
    
    function removeAttachedFile(index) {
        attachedFiles.splice(index, 1);
        updateAttachedFilesUI();
    }
    
    function clearAttachedFiles() {
        attachedFiles = [];
        updateAttachedFilesUI();
    }
    
    function getAttachedFiles() {
        return [...attachedFiles];
    }
    
    function getMessageInputValue() {
        const el = document.getElementById('messageInput');
        return el ? el.textContent.trim() : '';
    }
    
    function setMessageInputValue(value) {
        const el = document.getElementById('messageInput');
        if (el) el.textContent = value;
    }
    
    // Setup event listeners when DOM is ready
    function setupFileHandlers() {
        const fileInput = document.getElementById('fileInput');
        const messageInputEl = document.getElementById('messageInput');
        const chatInputContainer = document.querySelector('.chat-input-container');
        
        if (fileInput) {
            fileInput.addEventListener('change', handleFileSelect);
        }
        
        if (messageInputEl) {
            messageInputEl.addEventListener('paste', handlePaste);
            
            messageInputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const form = document.getElementById('chatForm');
                    if (form) form.dispatchEvent(new Event('submit'));
                }
            });
        }
        
        if (chatInputContainer) {
            chatInputContainer.addEventListener('dragover', handleDragOver);
            chatInputContainer.addEventListener('dragleave', handleDragLeave);
            chatInputContainer.addEventListener('drop', handleDrop);
        }
    }
    
    // Auto-setup on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupFileHandlers);
    } else {
        setupFileHandlers();
    }
    
    // Exponer globalmente
    window.FileHandlersModule = {
        attach: attachFile,
        process: processFiles,
        updateUI: updateAttachedFilesUI,
        remove: removeAttachedFile,
        clear: clearAttachedFiles,
        getFiles: getAttachedFiles,
        getInputValue: getMessageInputValue,
        setInputValue: setMessageInputValue,
        setup: setupFileHandlers
    };
    
    window.attachFile = attachFile;
    window.handleFileSelect = handleFileSelect;
    window.handlePaste = handlePaste;
    window.handleDragOver = handleDragOver;
    window.handleDragLeave = handleDragLeave;
    window.handleDrop = handleDrop;
    window.processFiles = processFiles;
    window.updateAttachedFilesUI = updateAttachedFilesUI;
    window.removeAttachedFile = removeAttachedFile;
    window.clearAttachedFiles = clearAttachedFiles;
    window.getMessageInputValue = getMessageInputValue;
    window.setMessageInputValue = setMessageInputValue;
    window.attachedFiles = attachedFiles;
    
})();
