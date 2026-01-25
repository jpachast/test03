/**
 * diff_preview Tool Module
 */
(function() {
    'use strict';
    
    function opendiff_preview() {
        var html = '<div style="padding: 20px;"><p style="color: #9ca3af;">Cargando diff_preview...</p><div id="diff_preview-output" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px;"></div></div>';
        if (window.showModal) window.showModal('diff_preview', html);
    }
    
    window.opendiff_preview = opendiff_preview;
})();
