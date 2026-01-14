#!/bin/bash
# Script de instalación para OpenHands Chat
# Ejecutar: ./install.sh

set -e

echo "🚀 Instalando OpenHands Chat..."

# Instalar dependencias de Python
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt

# Instalar Playwright browsers (necesario para screenshots)
echo "🌐 Instalando navegadores Playwright..."
playwright install chromium

echo "✅ Instalación completada!"
echo ""
echo "Para iniciar la aplicación:"
echo "  ./start.sh"
echo ""
echo "O manualmente:"
echo "  python app.py"
