# Backend EvidencIA

Python 3.12 / FastAPI. Instalação e testes:

```bash
uv sync --frozen --extra dev
cp .env.example .env
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
uv run ruff check .
uv run pytest --cov=app --cov-report=term-missing
```

- `POST /api/v1/analyze`: texto e segmentos reais; `analysisMode=evidence_only` evita chamadas ao provedor.
- `POST /api/v1/auth/token`: token anônimo de instalação, sujeito a rate limit.
- `POST /api/v1/feedback`: avaliação voluntária.
- `POST /api/v1/classify`: padrão linguístico; não é evidência factual.
- `GET /api/v1/health`, `/health/live`, `/health/ready`: estado da aplicação; health não testa conexão remota.

Limite de corpo: 524288 bytes (configurável); transcrição: até 100000 caracteres. Data desconhecida é string vazia. Sem segmentos reais, timestamps são nulos. Perguntas do provedor só são exibidas se pertencem ao catálogo aprovado. Hits externos contextualizam; relação factual local exige a mesma proposição textual.

`requirements.txt` é exportado do uv.lock, com versões/hashes de runtime. Dev está no extra `dev`; não instalar ferramentas de teste em produção. Docker usa usuário sem privilégios.

Produção exige Redis compartilhado, segredo de assinatura próprio, autenticação e CORS exato; nenhum segredo está nos exemplos. Configure `RATE_LIMIT_STORAGE_URI=redis://...` e `CORS_ALLOWED_ORIGINS=https://www.youtube.com,chrome-extension://ID_REAL`.

Modelo local em `ml/classifier/model.json`; treinamento: `uv run python -m ml.classifier.train --output caminho.json --report relatorio.md`. O relatório gerado é artefato operacional de treinamento, não demonstração de qualidade factual.

[Documentação oficial](https://github.com/evidencia-grupo/documentation).
