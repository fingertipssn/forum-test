FROM python:3.12-slim

# Copiar uv desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo los archivos de dependencias primero (mejor cache de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias de producción (sin grupo dev)
RUN uv sync --frozen --no-dev

# Copiar el resto del código
COPY . .

# Añadir el entorno virtual al PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
