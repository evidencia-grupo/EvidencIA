FROM python:3.12-slim

WORKDIR /app

# Instala dependências mínimas do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências e instala sem cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código do backend e módulos de ML/datasets
COPY app ./app
COPY ml ./ml

# Configuração padrão de produção na nuvem
ENV PORT=8000
ENV ENVIRONMENT=production
ENV ENV=production

EXPOSE 8000

# Inicia Uvicorn escutando na porta injetada pelo provedor de nuvem ($PORT)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
