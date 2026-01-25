/**
 * Multi-Agent Tool Module
 */
(function() {
    'use strict';

    function runMultiAgent(mode) {
        var title = mode === 'quick' ? 'Multi-Agent Rapido' : 'Multi-Agent Completo';
        var html = '<div style="padding: 20px;">' +
            '<div style="margin-bottom: 15px;">' +
                '<label style="display: block; margin-bottom: 5px; color: #e5e7eb;">Codigo a analizar:</label>' +
                '<textarea id="multiagent-code" placeholder="def ejemplo():" style="width: 100%; height: 150px; padding: 10px; background: #1f2937; border: 1px solid #374151; border-radius: 6px; color: #e5e7eb; font-family: monospace;"></textarea>' +
            '</div>' +
            '<button onclick="executeMultiAgent(\x27' + mode + '\x27)" style="padding: 10px 20px; background: #8b5cf6; color: white; border: none; border-radius: 6px; cursor: pointer;">Ejecutar Agentes</button>' +
            '<div id="multiagent-result" style="margin-top: 15px; display: none;"><div id="multiagent-output"></div></div>' +
        '</div>';
        if (window.showModal) window.showModal(title, html);
    }

    async function executeMultiAgent(mode) {
        var code = document.getElementById('multiagent-code').value;
        if (!code.trim()) { if (window.showToast) window.showToast('Ingresa codigo', 'warning'); return; }
        var resultDiv = document.getElementById('multiagent-result');
        var outputDiv = document.getElementById('multiagent-output');
        resultDiv.style.display = 'block';
        outputDiv.innerHTML = '<p style="color: #9ca3af;">Ejecutando agentes...</p>';
        try {
            var endpoint = mode === 'quick' ? '/api/advanced/multi-agent' : '/api/advanced/multi-agent-full';
            var response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code, language: 'python' })
            });
            var data = await response.json();
            outputDiv.innerHTML = '<pre style="color: #e5e7eb;">' + JSON.stringify(data, null, 2) + '</pre>';
        } catch (e) { outputDiv.innerHTML = '<p style="color: red;">Error: ' + e.message + '</p>'; }
    }

    window.MultiAgentTool = { run: runMultiAgent, execute: executeMultiAgent };
    window.runMultiAgent = runMultiAgent;
    window.executeMultiAgent = executeMultiAgent;
})();
