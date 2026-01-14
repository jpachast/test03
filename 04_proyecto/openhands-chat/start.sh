#!/bin/bash
# ==============================================
# SCRIPT DE INICIO - OpenHands Chat
# Este script instala todas las dependencias
# y levanta la aplicación automáticamente
# ==============================================
# 
# USO:
#   chmod +x start.sh && ./start.sh
#
# REQUISITOS:
#   - Python 3.10+
#   - pip
#   - curl
#
# ==============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  🚀 INICIANDO OPENHANDS CHAT"
echo "=============================================="

# === 1. INSTALAR DEPENDENCIAS PIP ===
echo ""
echo "📦 [1/5] Instalando dependencias de Python..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# === 2. INSTALAR PLAYWRIGHT BROWSERS ===
echo ""
echo "🌐 [2/5] Instalando navegadores de Playwright..."
python -m playwright install chromium 2>/dev/null || playwright install chromium || true

# === 3. INSTALAR CODE-SERVER (VS Code en navegador) ===
if ! command -v code-server &> /dev/null; then
    echo ""
    echo "💻 [3/5] Instalando code-server (VS Code)..."
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --method=standalone --prefix=$HOME/.local 2>/dev/null || true
fi
export PATH="$HOME/.local/bin:$PATH"

# === 4. MATAR PROCESOS ANTERIORES ===
echo ""
echo "🧹 [4/5] Limpiando procesos anteriores..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -9 -f "code-server" 2>/dev/null || true
sleep 2

# === 5. INICIAR LA APLICACIÓN ===
echo ""
echo "🚀 [5/5] Iniciando servidor en puerto 12000..."
export PORT=12000
export PATH="$HOME/.local/bin:$PATH"

# Iniciar en background
python app.py > server.log 2>&1 &
APP_PID=$!

# Esperar a que inicie
echo "  Esperando que el servidor inicie..."
sleep 5

# Verificar que está corriendo
if curl -s http://localhost:12000/health > /dev/null 2>&1; then
    echo ""
    echo "=============================================="
    echo "  ✅ OPENHANDS CHAT INICIADO CORRECTAMENTE"
    echo "=============================================="
    echo ""
    echo "  🌐 URL Local: http://localhost:12000"
    echo "  📁 Logs: $SCRIPT_DIR/server.log"
    echo "  🔧 PID: $APP_PID"
    echo ""
    echo "  📝 NOTA: La primera vez que uses el chat,"
    echo "     debes configurar tu API Key en Settings."
    echo ""
else
    echo ""
    echo "❌ ERROR: El servidor no inició correctamente"
    echo "Revisa los logs:"
    echo "----------------------------------------"
    cat server.log | tail -30
    exit 1
fi
