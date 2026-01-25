/**
 * Web Scraper Tool Module
 * Extracted from tools_menu_pro.js
 */
(function() {
    'use strict';

    function openWebScraper() {
        var html = '<div style="padding: 20px;">' +
            '<p style="margin-bottom: 15px; color: #9ca3af;">Extrae datos de paginas web: titulo, texto, links, imagenes y tablas.</p>' +
            '<div style="margin-bottom: 15px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">URL a extraer:</label>' +
                '<input type="text" id="scraper-url" placeholder="https://ejemplo.com" style="width: 100%; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb;">' +
            '</div>' +
            '<div style="margin-bottom: 15px; display: flex; gap: 15px; flex-wrap: wrap;">' +
                '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-links" checked> Extraer links</label>' +
                '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-images"> Extraer imagenes</label>' +
                '<label style="color: #9ca3af;"><input type="checkbox" id="scraper-tables"> Extraer tablas</label>' +
            '</div>' +
            '<button onclick="executeScrape()" style="padding: 10px 20px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer;">Extraer Datos</button>' +
            '<div id="scraper-result" style="margin-top: 15px; background: #1f2937; padding: 15px; border-radius: 8px; max-height: 300px; overflow: auto; display: none;">' +
                '<pre id="scraper-output" style="color: #e5e7eb; white-space: pre-wrap; margin: 0;"></pre>' +
            '</div>' +
        '</div>';
        if (window.showModal) window.showModal('Web Scraper', html);
    }

    async function executeScrape() {
        var url = document.getElementById('scraper-url').value;
        if (!url) { 
            if (window.showToast) window.showToast('Ingresa una URL', 'warning'); 
            return; 
        }
        var resultDiv = document.getElementById('scraper-result');
        var outputPre = document.getElementById('scraper-output');
        resultDiv.style.display = 'block';
        outputPre.textContent = 'Extrayendo datos...';
        try {
            var response = await fetch('/api/scraper/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    extract_links: document.getElementById('scraper-links').checked,
                    extract_images: document.getElementById('scraper-images').checked,
                    extract_tables: document.getElementById('scraper-tables').checked
                })
            });
            var data = await response.json();
            if (data.success) {
                var content = (data.text_content || '').substring(0, 500);
                outputPre.textContent = 'Titulo: ' + (data.title || 'N/A') + '\n\nContenido (500 chars):\n' + content + '...\n\nLinks: ' + (data.links || []).length + '\nImagenes: ' + (data.images || []).length + '\nTablas: ' + (data.tables || []).length;
                if (window.showToast) window.showToast('Datos extraidos', 'success');
            } else {
                outputPre.textContent = 'Error: ' + (data.error || 'Error');
            }
        } catch (e) { 
            outputPre.textContent = 'Error: ' + e.message; 
        }
    }

    // Exponer globalmente
    window.WebScraperTool = { open: openWebScraper, execute: executeScrape };
    window.openWebScraper = openWebScraper;
    window.executeScrape = executeScrape;
})();
