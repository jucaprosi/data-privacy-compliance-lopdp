FROM python:3.12-slim

# Evitar escritura de bytecode y buffer en stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas (por ej. asyncpg requiere gcc en algunos casos o build-essentials)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear y activar entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias base requeridas
# (Nota: Asumimos que el código se ejecuta con fastapi, uvicorn, sqlalchemy, asyncpg, alembic)
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy asyncpg alembic pytest pytest-asyncio pydantic pydantic-settings httpx anyio

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto
EXPOSE 5000

# El entrypoint ejecutará alembic upgrade head y luego uvicorn, esperando a la BD
# En docker-compose se manejará el wait-for-it o depends_on con condition: service_healthy
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 5000"]
