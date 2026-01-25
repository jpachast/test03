/**
 * Tools Core Module - Shared utilities for tools
 */
(function() {
    'use strict';

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function showModal(title, content) {
        var existing = document.getElementById('tools-modal');
        if (existing) existing.remove();

        var modal = document.createElement('div');
        modal.id = 'tools-modal';
        modal.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 10000;';
        modal.innerHTML = '<div style="background: #1f2937; border-radius: 12px; max-width: 600px; width: 90%; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;">' +
            '<div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #374151;">' +
                '<h3 style="margin: 0; color: #e5e7eb;">' + title + '</h3>' +
                '<button onclick="closeToolsModal()" style="background: none; border: none; color: #9ca3af; font-size: 24px; cursor: pointer;">&times;</button>' +
            '</div>' +
            '<div style="padding: 0; overflow-y: auto; flex: 1;">' + content + '</div>' +
        '</div>';
        
        modal.onclick = function(e) { if (e.target === modal) closeToolsModal(); };
        document.body.appendChild(modal);
    }

    function closeToolsModal() {
        var modal = document.getElementById('tools-modal');
        if (modal) modal.remove();
    }

    function showToast(message, type) {
        var toast = document.createElement('div');
        var bg = type === 'success' ? '#22c55e' : (type === 'error' ? '#ef4444' : '#f59e0b');
        toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; padding: 12px 20px; background: ' + bg + '; color: white; border-radius: 8px; z-index: 10001; animation: fadeIn 0.3s;';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(function() { toast.remove(); }, 3000);
    }

    window.ToolsCore = { escapeHtml: escapeHtml, showModal: showModal, closeModal: closeToolsModal, showToast: showToast };
    window.escapeHtml = escapeHtml;
    window.showModal = showModal;
    window.closeToolsModal = closeToolsModal;
    window.showToast = showToast;
})();
