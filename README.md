# EvidencIA

Extensão Chrome MV3 e backend FastAPI para investigação de alegações em vídeos do YouTube. Evidências, datas conhecidas e incertezas aparecem por alegação. O classificador local descreve padrões linguísticos; não comprova a veracidade de uma fala.

## Desenvolvimento local

Requisitos: Node 24 e Python 3.12.

```bash
cd backend
uv sync --frozen --extra dev
cp .env.example .env
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```bash
cd extension
npm ci --ignore-scripts
npm run build
```

Carregue `extension/dist` como extensão descompactada em `chrome://extensions`. O exemplo usa mock explícito, sem chave paga. Nunca coloque credenciais no cliente ou no Git.

## Validação

```bash
cd backend
uv run ruff check .
uv run pytest --cov=app --cov-report=term-missing
cd ../extension
npm run typecheck
npm run test:coverage
npx playwright install chromium
E2E_PYTHON=../backend/.venv/bin/python npm run test:e2e
cd ..
backend/.venv/bin/python scripts/generate_contracts.py --check
backend/.venv/bin/python scripts/check_drift.py --docs ../documentation
```

Contratos JSON/TypeScript são gerados de `backend/app/schemas.py`. Alterações exigem executar `scripts/generate_contracts.py`.

## Build e hospedagem

Build de produção exige `VITE_API_BASE_URL` HTTPS explícita. O manifesto gerado concede acesso apenas ao YouTube e à origem desse backend.

```bash
cd extension
VITE_API_BASE_URL=https://seu-backend.example npm run build:prod
```

A URL acima é ilustrativa; substitua pela origem provisionada. No backend de produção configure provedor real, `REQUIRE_AUTH=true`, `AUTH_SECRET` próprio de pelo menos 32 caracteres, Redis em `RATE_LIMIT_STORAGE_URI` e origens CORS exatas, incluindo o ID real da extensão. Wildcards e configuração de desenvolvimento são recusados. A emissão de tokens de instalação é anônima e não comprova identidade.

## Organização

- `extension/`: cliente MV3 e testes.
- `backend/`: API, classificador, fixtures, dados locais e testes.
- `shared/`: contratos gerados.
- `evaluation/`: dados de avaliação aguardando anotação humana.
- `scripts/`: geração/checagem de contratos e avaliação.

[Arquitetura, requisitos e decisões](https://github.com/evidencia-grupo/documentation). [Narrativas históricas migradas](https://github.com/evidencia-grupo/documentation/tree/main/docs/auditorias/historico/0ffe395). Prontidão científica e de produção depende de dados/licenças, infraestrutura e validação humana; resultados locais não a substituem.


## Experimento de IA reproduzido

[Fake.br e regressão logística calibrada](experiments/fakebr/README.md): notebook executado, código de reprodução, modelo `.pkl` e `.plk`, manifesto e partições. No teste de 1.088 notícias: acurácia 93,47% e macro-F1 0,9347. Esses números avaliam notícias históricas; não demonstram veracidade de vídeos ou relação com uma evidência. O modelo da API permanece um diagnóstico linguístico, subordinado às fontes.

Para diagnosticar o ambiente sem mostrar credenciais:

```bash
backend/.venv/bin/python scripts/check_readiness.py
backend/.venv/bin/python scripts/check_readiness.py --check-services
```

A segunda opção consulta os modelos Ollama e, quando disponível, a coleção Chroma local. A existência de uma chave não comprova validade ou quota. O modo mock continua disponível para desenvolvimento.

A análise usa somente legendas. Descrição, tempos inventados e cache de versão anterior não entram na checagem. Sem legenda suficiente, a extensão permite tentar novamente e não envia uma análise.
