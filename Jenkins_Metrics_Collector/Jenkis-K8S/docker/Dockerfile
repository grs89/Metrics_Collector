FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY exporter.py .

# Usuario no root para seguridad
RUN useradd -m -u 1000 exporter
USER exporter

# Ejecutar el exportador
CMD ["python", "-u", "exporter.py"]

