
/**
 * Auto-Fix Loop Profesional
 * Detecta errores -> Genera corrección con LLM -> Aplica -> Re-ejecuta -> Verifica
 */

class AutoFixLoop {
    constructor() {
        this.maxRetries = 3;
        this.fixHistory = [];
    }

    /**
     * Ejecuta código con auto-fix habilitado
     */
    async executeWithAutoFix(code, language = 'python') {
        let currentCode = code;
        let attempts = [];

        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            console.log(`🔄 Intento ${attempt}/${this.maxRetries}`);

            // Ejecutar código
            const result = await this.execute(currentCode, language);
            attempts.push({
                attempt,
                code: currentCode,
                result
            });

            // Si éxito, retornar
            if (result.success) {
                return {
                    success: true,
                    finalCode: currentCode,
                    attempts,
                    output: result.stdout
                };
            }

            // Si hay error, intentar corregir
            if (attempt < this.maxRetries) {
                const fix = await this.generateFix(currentCode, result.stderr, language);
                if (fix && fix.correctedCode) {
                    console.log('💡 Corrección generada, aplicando...');
                    currentCode = fix.correctedCode;
                } else {
                    // No se pudo generar fix, salir
                    break;
                }
            }
        }

        return {
            success: false,
            finalCode: currentCode,
            attempts,
            error: attempts[attempts.length - 1]?.result?.stderr
        };
    }

    /**
     * Ejecuta código usando la API del sandbox
     */
    async execute(code, language) {
        try {
            const response = await fetch('/api/sandbox-chat/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            const data = await response.json();
            return data.result || data;
        } catch (error) {
            return { success: false, stderr: error.message };
        }
    }

    /**
     * Genera una corrección usando el LLM
     */
    async generateFix(code, error, language) {
        // Primero intentar fix local (patrones conocidos)
        const localFix = this.tryLocalFix(code, error, language);
        if (localFix) return localFix;

        // Si no hay fix local, pedir al LLM
        try {
            const response = await fetch('/api/autofix/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code,
                    error,
                    language
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.error('Error generando fix:', e);
        }

        return null;
    }

    /**
     * Intenta fixes locales para errores comunes
     */
    tryLocalFix(code, error, language) {
        if (language !== 'python') return null;

        const fixes = [
            // NameError: variable no definida
            {
                pattern: /NameError: name '(\w+)' is not defined/,
                fix: (match, code) => {
                    const varName = match[1];
                    // Intentar importar si parece un módulo común
                    const commonModules = ['os', 'sys', 'json', 're', 'math', 'datetime', 'random', 'time'];
                    if (commonModules.includes(varName)) {
                        return {
                            correctedCode: `import ${varName}\n${code}`,
                            explanation: `Añadido: import ${varName}`
                        };
                    }
                    return null;
                }
            },
            // ImportError: No module named
            {
                pattern: /No module named '([\w.]+)'/,
                fix: (match, code) => {
                    const module = match[1];
                    return {
                        correctedCode: code,
                        explanation: `Módulo '${module}' no instalado. Ejecuta: pip install ${module}`,
                        needsInstall: module
                    };
                }
            },
            // IndentationError
            {
                pattern: /IndentationError/,
                fix: (match, code) => {
                    // Intentar normalizar indentación a 4 espacios
                    const lines = code.split('\n');
                    const fixed = lines.map(line => {
                        const stripped = line.trimStart();
                        const indent = line.length - stripped.length;
                        const spaces = Math.floor(indent / 4) * 4;
                        return ' '.repeat(spaces) + stripped;
                    }).join('\n');
                    return {
                        correctedCode: fixed,
                        explanation: 'Normalizada indentación a 4 espacios'
                    };
                }
            },
            // SyntaxError: missing colon
            {
                pattern: /SyntaxError.*expected ':'/,
                fix: (match, code) => {
                    // Añadir : al final de líneas con def, if, for, while, class, etc.
                    const fixed = code.replace(/((?:def|if|elif|else|for|while|class|try|except|finally|with)\s+[^:]+)(?<!:)$/gm, '$1:');
                    if (fixed !== code) {
                        return {
                            correctedCode: fixed,
                            explanation: 'Añadido : faltante'
                        };
                    }
                    return null;
                }
            }
        ];

        for (const { pattern, fix } of fixes) {
            const match = error.match(pattern);
            if (match) {
                const result = fix(match, code);
                if (result) return result;
            }
        }

        return null;
    }

    /**
     * UI para mostrar el proceso de auto-fix
     */
    showFixProgress(container, attempts) {
        let html = '<div class="autofix-progress" style="padding: 12px; background: #1e1e2e; border-radius: 8px; margin-top: 10px;">';
        html += '<div style="color: #cdd6f4; font-weight: bold; margin-bottom: 10px;">🔄 Auto-Fix Progress</div>';

        attempts.forEach((a, i) => {
            const icon = a.result.success ? '✅' : '❌';
            const color = a.result.success ? '#22c55e' : '#ef4444';
            html += `
                <div style="padding: 8px; background: #313244; border-radius: 6px; margin: 6px 0; border-left: 3px solid ${color};">
                    <div style="color: ${color}; font-size: 12px;">${icon} Intento ${a.attempt}</div>
                    ${!a.result.success ? `<div style="color: #f38ba8; font-size: 11px; margin-top: 4px;">${a.result.stderr?.substring(0, 100)}...</div>` : ''}
                </div>
            `;
        });

        html += '</div>';
        
        if (container) {
            container.innerHTML = html;
        }
        return html;
    }
}

// Instancia global
window.autoFixLoop = new AutoFixLoop();
console.log('✅ AutoFixLoop inicializado');
