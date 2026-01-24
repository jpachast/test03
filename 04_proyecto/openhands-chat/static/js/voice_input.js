// ============================================
// VOICE INPUT - MULTIPLE BACKENDS
// ============================================

// Estado global de voice input
let voiceInputState = {
    isRecording: false,
    recognition: null,
    mediaRecorder: null,
    audioChunks: [],
    backend: 'web_speech' // web_speech, openai_whisper, groq_whisper
};

// Inicializar Voice Input
function initVoiceInput() {
    // Verificar soporte de Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceInputState.recognition = new SpeechRecognition();
        voiceInputState.recognition.continuous = false;
        voiceInputState.recognition.interimResults = true;
        voiceInputState.recognition.lang = 'es-ES';
        
        voiceInputState.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            
            // Actualizar el campo de input
            const chatInput = document.querySelector('input[type="text"], textarea');
            if (chatInput) {
                chatInput.value = transcript;
            }
            
            // Si es resultado final
            if (event.results[0].isFinal) {
                showToast('✅ Transcripción completada', 'success');
            }
        };
        
        voiceInputState.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let errorMsg = 'Error de reconocimiento de voz';
            
            switch(event.error) {
                case 'not-allowed':
                    errorMsg = 'Permiso de micrófono denegado. Permite el acceso en tu navegador.';
                    break;
                case 'no-speech':
                    errorMsg = 'No se detectó voz. Intenta de nuevo.';
                    break;
                case 'network':
                    errorMsg = 'Error de red. Verifica tu conexión.';
                    break;
            }
            
            showToast(errorMsg, 'error');
            stopVoiceRecording();
        };
        
        voiceInputState.recognition.onend = () => {
            voiceInputState.isRecording = false;
            updateVoiceButton(false);
        };
        
        console.log('✅ Web Speech API inicializado');
        return true;
    } else {
        console.warn('⚠️ Web Speech API no soportado');
        return false;
    }
}

// Toggle grabación
function toggleVoiceInput() {
    if (voiceInputState.isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Iniciar grabación
async function startVoiceRecording() {
    const backend = voiceInputState.backend;
    
    if (backend === 'web_speech') {
        // Usar Web Speech API (gratis)
        if (!voiceInputState.recognition) {
            if (!initVoiceInput()) {
                showToast('Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge.', 'error');
                return;
            }
        }
        
        try {
            voiceInputState.recognition.start();
            voiceInputState.isRecording = true;
            updateVoiceButton(true);
            showToast('🎤 Escuchando... Habla ahora', 'info');
        } catch (e) {
            showToast('Error al iniciar grabación: ' + e.message, 'error');
        }
    } else {
        // Usar grabación de audio para API (OpenAI/Groq)
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            voiceInputState.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            voiceInputState.audioChunks = [];
            
            voiceInputState.mediaRecorder.ondataavailable = (event) => {
                voiceInputState.audioChunks.push(event.data);
            };
            
            voiceInputState.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(voiceInputState.audioChunks, { type: 'audio/webm' });
                stream.getTracks().forEach(track => track.stop());
                
                // Enviar a la API
                await transcribeWithAPI(audioBlob);
            };
            
            voiceInputState.mediaRecorder.start();
            voiceInputState.isRecording = true;
            updateVoiceButton(true);
            showToast('🎤 Grabando... Click para detener', 'info');
        } catch (e) {
            showToast('Error al acceder al micrófono: ' + e.message, 'error');
        }
    }
}

// Detener grabación
function stopVoiceRecording() {
    if (voiceInputState.backend === 'web_speech') {
        if (voiceInputState.recognition) {
            voiceInputState.recognition.stop();
        }
    } else {
        if (voiceInputState.mediaRecorder && voiceInputState.mediaRecorder.state === 'recording') {
            voiceInputState.mediaRecorder.stop();
        }
    }
    
    voiceInputState.isRecording = false;
    updateVoiceButton(false);
}

// Transcribir con API (OpenAI/Groq)
async function transcribeWithAPI(audioBlob) {
    showToast('⏳ Transcribiendo...', 'info');
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('backend', voiceInputState.backend);
    
    try {
        const response = await fetch('/api/features/voice/transcribe', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.text) {
            const chatInput = document.querySelector('input[type="text"], textarea');
            if (chatInput) {
                chatInput.value = data.text;
            }
            showToast('✅ Transcripción completada', 'success');
        } else {
            showToast('❌ ' + (data.error || 'Error de transcripción'), 'error');
            
            // Si hay sugerencia, mostrarla
            if (data.suggestion) {
                setTimeout(() => showToast('💡 ' + data.suggestion, 'info'), 2000);
            }
        }
    } catch (e) {
        showToast('Error de red: ' + e.message, 'error');
    }
}

// Actualizar estado visual del botón
function updateVoiceButton(isRecording) {
    const voiceBtn = document.querySelector('.voice-btn, #voiceBtn');
    if (voiceBtn) {
        if (isRecording) {
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '🔴';
            voiceBtn.title = 'Grabando... Click para detener';
        } else {
            voiceBtn.classList.remove('recording');
            voiceBtn.innerHTML = '🎤';
            voiceBtn.title = 'Activar entrada de voz';
        }
    }
}

// Mostrar panel de configuración de Voice
async function showVoiceSettings() {
    try {
        const response = await fetch('/api/features/voice/status');
        const status = await response.json();
        
        const backends = status.backends || {};
        
        let html = `
            <div class="voice-settings-panel">
                <h3>🎤 Configuración de Voz</h3>
                <p class="voice-description">Selecciona cómo quieres transcribir tu voz</p>
                
                <div class="voice-backends">
        `;
        
        // Web Speech (siempre primero, es gratis)
        html += `
            <div class="voice-backend-item ${voiceInputState.backend === 'web_speech' ? 'selected' : ''}" 
                 onclick="selectVoiceBackend('web_speech')">
                <div class="backend-header">
                    <span class="backend-name">🌐 Web Speech API</span>
                    <span class="backend-badge free">GRATIS</span>
                </div>
                <p class="backend-desc">Reconocimiento de voz del navegador (Chrome/Edge)</p>
                <p class="backend-note">✅ No requiere API key • Funciona offline</p>
            </div>
        `;
        
        // Groq Whisper (tier gratuito)
        const groq = backends.groq_whisper || {};
        html += `
            <div class="voice-backend-item ${voiceInputState.backend === 'groq_whisper' ? 'selected' : ''}"
                 onclick="selectVoiceBackend('groq_whisper')">
                <div class="backend-header">
                    <span class="backend-name">⚡ Groq Whisper</span>
                    <span class="backend-badge free">TIER GRATUITO</span>
                </div>
                <p class="backend-desc">Whisper ultra-rápido con tier gratuito</p>
                <p class="backend-note">${groq.key_configured ? '✅ API key configurada' : '⚠️ Requiere GROQ_API_KEY'}</p>
                ${!groq.key_configured ? '<a href="https://console.groq.com" target="_blank" class="get-key-link">Obtener API key gratis →</a>' : ''}
            </div>
        `;
        
        // OpenAI Whisper (de pago)
        const openai = backends.openai_whisper || {};
        html += `
            <div class="voice-backend-item ${voiceInputState.backend === 'openai_whisper' ? 'selected' : ''}"
                 onclick="selectVoiceBackend('openai_whisper')">
                <div class="backend-header">
                    <span class="backend-name">🤖 OpenAI Whisper</span>
                    <span class="backend-badge paid">DE PAGO</span>
                </div>
                <p class="backend-desc">Alta precisión con OpenAI</p>
                <p class="backend-note">${openai.key_configured ? '✅ API key configurada' : '⚠️ Requiere OPENAI_API_KEY'}</p>
                <p class="backend-price">💰 $0.006/minuto de audio</p>
            </div>
        `;
        
        html += `
                </div>
                
                <div class="voice-test">
                    <button class="voice-test-btn" onclick="testVoiceInput()">
                        🎤 Probar micrófono
                    </button>
                </div>
            </div>
        `;
        
        showModal('Entrada de Voz', html);
    } catch (e) {
        showToast('Error cargando configuración: ' + e.message, 'error');
    }
}

// Seleccionar backend de voz
function selectVoiceBackend(backend) {
    voiceInputState.backend = backend;
    
    // Actualizar UI
    document.querySelectorAll('.voice-backend-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
    
    // Guardar preferencia
    localStorage.setItem('voiceBackend', backend);
    
    showToast(`Backend de voz: ${backend}`, 'success');
}

// Probar micrófono
async function testVoiceInput() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        showToast('✅ Micrófono funcionando correctamente', 'success');
    } catch (e) {
        showToast('❌ No se puede acceder al micrófono: ' + e.message, 'error');
    }
}

// Cargar preferencia guardada
function loadVoicePreference() {
    const saved = localStorage.getItem('voiceBackend');
    if (saved) {
        voiceInputState.backend = saved;
    }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', () => {
    loadVoicePreference();
    initVoiceInput();
});
