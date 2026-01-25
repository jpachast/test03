/**
 * semantic_search Tool Module
 */
(function() {
    'use strict';
    
    function opensemantic_search() {
        var html = '<div style="padding: 20px;"><p style="color: #9ca3af;">Cargando semantic_search...</p><div id="semantic_search-output" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px;"></div></div>';
        if (window.showModal) window.showModal('semantic_search', html);
    }
    
    window.opensemantic_search = opensemantic_search;
})();
