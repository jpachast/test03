/**
 * codemaps Tool Module
 */
(function() {
    'use strict';
    
    function opencodemaps() {
        var html = '<div style="padding: 20px;"><p style="color: #9ca3af;">Cargando codemaps...</p><div id="codemaps-output" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px;"></div></div>';
        if (window.showModal) window.showModal('codemaps', html);
    }
    
    window.opencodemaps = opencodemaps;
})();
