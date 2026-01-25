/**
 * mcp_protocol Tool Module
 */
(function() {
    'use strict';
    
    function openmcp_protocol() {
        var html = '<div style="padding: 20px;"><p style="color: #9ca3af;">Cargando mcp_protocol...</p><div id="mcp_protocol-output" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px;"></div></div>';
        if (window.showModal) window.showModal('mcp_protocol', html);
    }
    
    window.openmcp_protocol = openmcp_protocol;
})();
