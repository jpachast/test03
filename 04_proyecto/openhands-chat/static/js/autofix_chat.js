// ============================================================
// AUTO-FIX INTEGRATION - Chat Responses
// ============================================================

// Estado global de auto-fix
window.chatAutoFix = {
    enabled: true,
    lastCode: null,
    lastError: null
};

// Patrones de error para detectar en respuestas
const ERROR_PATTERNS = [
    /SyntaxError:\s*(.+)/i,
    /NameError:\s*(.+)/i,
    /TypeError:\s*(.+)/i,
    /ZeroDivisionError:\s*(.+)/i,
    /IndexError:\s*(.+)/i,
    /KeyError:\s*(.+)/i,
    /ImportError:\s*(.+)/i,
    /ModuleNotFoundError:\s*(.+)/i,
    /ValueError:\s*(.+)/i,
    /AttributeError:\s*(.+)/i,
    /FileNotFoundError:\s*(.+)/i,
    /Traceback \(most recent call last\)/i
];

// Detectar si hay error en el texto
function detectErrorInText(text) {
    if (!text) return { hasError: false };
    
    for (const pattern of ERROR_PATTERNS) {
        const match = text.match(pattern);
        if (match) {
            return {
                hasError: true,
                errorMessage: match[0],
                errorType: match[1] || 'unknown'
            };
        }
    }
    return { hasError: false };
}

// Extraer código de un mensaje
function extractCodeFromMessage(message) {
    // Buscar bloques de código markdown
    const codeBlockMatch = message.match(/```(?:python|py)?\n([\s\S]*?)```/);
    if (codeBlockMatch) {
        return codeBlockMatch[1].trim();
    }
    return null;
}

// Llamar al endpoint de auto-fix
async function tryAutoFix(code, errorOutput) {
    if (!window.chatAutoFix.enabled || !code) return null;
    
    try {
        const formData = new FormData();
        formData.append('code', code);
        formData.append('error_output', errorOutput);
        formData.append('language', 'python');
        
        const response = await fetch('/api/chat/autofix/detect', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) return null;
        
        const result = await response.json();
        return result;
    } catch (e) {
        console.error('Auto-fix error:', e);
        return null;
    }
}

// Formatear resultado de auto-fix para mostrar en chat
function formatAutoFixResult(result) {
    if (!result || !result.auto_fixed) return '';
    
    let html = `
        <div class="autofix-result" style="
            margin-top: 15px;
            padding: 15px;
            background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
            border-radius: 10px;
            border-left: 4px solid #4caf50;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <span style="font-size: 24px;">🔧</span>
                <span style="color: #4caf50; font-weight: bold; font-size: 16px;">Auto-Fix Aplicado</span>
            </div>
            
            <div style="color: #a5d6a7; margin-bottom: 10px;">
                ✅ ${result.fixes_applied || 1} corrección(es) aplicada(s)
                ${result.verified ? '<br>✅ Código verificado - ejecuta correctamente' : ''}
            </div>
            
            <div style="margin-bottom: 10px;">
                <div style="color: #81c784; font-weight: bold; margin-bottom: 5px;">Código corregido:</div>
                <pre style="
                    background: #0d1117;
                    padding: 12px;
                    border-radius: 6px;
                    overflow-x: auto;
                    color: #c9d1d9;
                    font-family: 'Fira Code', monospace;
                    font-size: 13px;
                    border: 1px solid #30363d;
                "><code>${escapeHtml(result.fixed_code || '')}</code></pre>
            </div>
    `;
    
    if (result.final_output) {
        html += `
            <div>
                <div style="color: #81c784; font-weight: bold; margin-bottom: 5px;">Resultado:</div>
                <pre style="
                    background: #161b22;
                    padding: 10px;
                    border-radius: 6px;
                    color: #8b949e;
                    font-size: 12px;
                    max-height: 150px;
                    overflow-y: auto;
                ">${escapeHtml(result.final_output.substring(0, 500))}</pre>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Escape HTML para evitar XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Procesar respuesta del agente buscando errores
async function processAgentResponseForAutoFix(responseElement, responseText) {
    if (!window.chatAutoFix.enabled) return;
    
    // Detectar si hay error
    const errorCheck = detectErrorInText(responseText);
    if (!errorCheck.hasError) return;
    
    // Extraer código del mensaje o usar el último código conocido
    const code = extractCodeFromMessage(responseText) || window.chatAutoFix.lastCode;
    if (!code) return;
    
    // Guardar error
    window.chatAutoFix.lastError = errorCheck.errorMessage;
    
    // Intentar auto-fix
    const result = await tryAutoFix(code, responseText);
    
    if (result && result.auto_fixed) {
        // Agregar resultado de auto-fix a la respuesta
        const autoFixHtml = formatAutoFixResult(result);
        if (autoFixHtml && responseElement) {
            const autoFixDiv = document.createElement('div');
            autoFixDiv.innerHTML = autoFixHtml;
            responseElement.appendChild(autoFixDiv);
            
            // Scroll al resultado
            autoFixDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }
}

// Guardar código cuando el usuario lo envía
function saveCodeContext(message) {
    const code = extractCodeFromMessage(message);
    if (code) {
        window.chatAutoFix.lastCode = code;
    }
}

// Habilitar/deshabilitar auto-fix
function toggleAutoFix(enabled) {
    window.chatAutoFix.enabled = enabled;
    console.log('Auto-Fix:', enabled ? 'habilitado' : 'deshabilitado');
}

console.log('✅ Auto-Fix Integration para Chat cargado');
