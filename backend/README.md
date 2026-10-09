# EvidencIA — Backend Proxy & Orquestrador de IA

> Backend Proxy assíncrono em FastAPI, isolador de credenciais (**Zero Segredos no Cliente** - [ADR-002](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)), orquestrador de inferência e motor de casamento com datasets brasileiros (FactChecks.br).

---

## 1. Estrutura do Módulo

```text
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS restrito e Rate Limiting (SlowAPI)
│   ├── config.py        # Configurações tipadas via Pydantic Settings
│   ├── schemas.py       # Modelos Pydantic v2 sincronizados com shared/
│   ├── api/v1/          # Endpoints (/analyze, /auth/token, /health, /classify)
│   ├── providers/       # Camada agnóstica de LLM (Ollama, Remote, Mock)
│   └── services/        # Orquestrador fact_checker, brazilian_fact_matcher, auth
├── ml/                  # Datasets curados (sample_facts.json) e classificador Naive Bayes
└── tests/               # 151 testes automatizados (Pytest com cobertura > 90%)
```

---

## 2. Endpoints Principais (API v1)

- `POST /api/v1/analyze`: Recebe transcrição do vídeo e retorna alegações atômicas e evidências.
- `POST /api/v1/auth/token`: Emite credencial de acesso efêmera assinada para a extensão.
- `GET /api/v1/health`: Retorna status dinâmico do serviço (`healthy`, `degraded`, `unhealthy`).
- `GET /api/v1/health/live` e `/health/ready`: Liveness e readiness probes para orquestração.
- `POST /api/v1/feedback`: Registro voluntário e anônimo de utilidade (LGPD/RNF-05).
- `POST /api/v1/classify`: Classificação supervisionada de proposições com abstenção.

---

## 3. Instalação e Execução

```bash
# 1. Instalar dependências (recomendado: uv)
uv sync
# Ou via pip: pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp ../.env.example .env

# 3. Executar o servidor
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger UI disponível em: `http://127.0.0.1:8000/docs`

---

## 4. Testes Automatizados

```bash
# Execução da suíte completa de 151 testes
uv run pytest -v

# Cobertura de código (mínimo obrigatório: 80%)
uv run pytest -v --cov=app --cov-report=term-missing
```

Documentação arquitetural completa: [docs/arquitetura/arquitetura.md](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/arquitetura.md).
