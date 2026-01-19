FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema (incluyendo Chromium para browser tool)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl chromium nodejs npm ripgrep && \
    rm -rf /var/lib/apt/lists/*

# Instalar playwright y chromium
RUN pip install playwright && playwright install chromium --with-deps || true

# Copiar requirements y instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY . .

# Puerto
EXPOSE 12000

# Comando
CMD ["python", "app.py"]
