# ¤¤backend-developer
# Dockerfile de producción para el Backend de Evydentia (Cloud Run / Container Runtime)
FROM python:3.12-slim

# Invariantes de runtime en contenedor
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Dependencias mínimas de sistema para compilación de extensiones y cliente PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias exactas desde requirements.txt (cache de capas de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# Exponer el puerto por defecto de Cloud Run (8080)
EXPOSE 8080

# Iniciar servidor Uvicorn respetando el puerto dinámico de Cloud Run ($PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
