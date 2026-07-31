# Usamos la versión de Python que estás utilizando localmente
FROM python:3.12-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Fuerza a que la salida estándar (logs) se muestre en consola sin demoras
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias del sistema operativo necesarias para PostgreSQL
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero el requirements.txt para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

EXPOSE 8000