#!/bin/bash
# Script de instalación para OpenHands Chat
# Ejecutar: ./install.sh

echo "🚀 Instalando OpenHands Chat..."

# Instalar dependencias de Python
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt

# Instalar Playwright browsers (necesario para browser tools)
echo "🌐 Instalando navegadores Playwright..."
python -m playwright install chromium || echo "⚠️ No se pudo instalar chromium automáticamente"

# Instalar dependencias del sistema para Playwright (si es posible)
echo "📦 Instalando dependencias del sistema..."
python -m playwright install-deps chromium 2>/dev/null || echo "⚠️ Instala dependencias manualmente si el browser falla"

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para iniciar la aplicación:"
echo "  ./start.sh"
echo ""
echo "O manualmente:"
echo "  python app.py"
