# ¤demo
# Imagen del Cloud Run Job purga-demo. Construir desde la raíz del repositorio:
#   docker build -f jobs/purga_demo/Dockerfile -t purga-demo .
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app_core ./app_core
COPY features ./features
COPY jobs ./jobs
RUN useradd --system --no-create-home --uid 10001 purga
USER 10001
CMD ["python", "-m", "jobs.purga_demo"]
