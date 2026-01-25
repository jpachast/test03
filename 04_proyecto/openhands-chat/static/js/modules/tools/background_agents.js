/**
 * background_agents Tool Module
 */
(function() {
    'use strict';
    
    function openbackground_agents() {
        var html = '<div style="padding: 20px;"><p style="color: #9ca3af;">Cargando background_agents...</p><div id="background_agents-output" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px;"></div></div>';
        if (window.showModal) window.showModal('background_agents', html);
    }
    
    window.openbackground_agents = openbackground_agents;
})();
