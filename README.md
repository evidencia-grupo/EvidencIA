# EvidencIA — Extensão de investigação de alegações para YouTube

[![CI/CD Pipeline](https://github.com/evidencia-grupo/EvidencIA/actions/workflows/ci.yml/badge.svg)](https://github.com/evidencia-grupo/EvidencIA/actions/workflows/ci.yml)
[![Manifest V3](https://img.shields.io/badge/Manifest-V3-success?logo=googlechrome&logoColor=white)](https://developer.chrome.com/docs/extensions/develop/migrate/what-is-mv3)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

- **Repositório:** https://github.com/evidencia-grupo/EvidencIA
- **Documentação:** https://evidencia-grupo.github.io/documentation/ ([código-fonte](https://github.com/evidencia-grupo/documentation))

## O que é

A EvidencIA é uma extensão para Google Chrome que ajuda a examinar o que é dito em vídeos do YouTube. Ao clicar em **Checar Alegações**, ela lê a legenda do vídeo, separa as afirmações verificáveis e mostra, para cada uma, as evidências encontradas em checagens publicadas, com link para a fonte original e perguntas para reflexão.

Princípios do produto:

- **Evidence-First:** sem nota ou veredito automático para o vídeo. Cada alegação recebe um estado (`supported`, `contradicted`, `contextualized`, `conflicting`, `insufficient_evidence`) sustentado por fontes rastreáveis. Ausência de evidência nunca vira "falso".
- **Zero segredos no cliente:** a extensão não contém chaves; todas as chamadas passam pelo backend, que exige autenticação em produção.
- **Privacidade:** só age em páginas de vídeo do YouTube e só quando a pessoa clica. Veja a [política de privacidade](https://evidencia-grupo.github.io/documentation/legal/politica-de-privacidade/).

## Estado atual

| Componente | Situação |
|:---|:---|
| Extensão (Manifest V3, Preact) | Completa; pacote para a Chrome Web Store gerado e verificado (`npm run package`). Publicação depende do backend em produção. |
| Backend (FastAPI) | Completo; Blueprint do Render em `render.yaml`. Ainda não publicado. |
| Evidências em produção | Google Fact Check Tools API (ClaimReview). O corpus de demonstração local é bloqueado fora do desenvolvimento. |
| Modelo de IA (Fake.br) | Experimento acadêmico reproduzível em `experiments/fakebr`; não é usado como veredito no produto. |

## Estrutura

```text
EvidencIA/
├── backend/        # API FastAPI: orquestração, provedores de LLM, recuperação de evidências, autenticação
│   ├── app/        # Endpoints /api/v1, serviços, schemas Pydantic e provedores (Ollama, remoto, mock)
│   ├── ml/         # Classificador linguístico de contingência e dados locais de desenvolvimento
│   └── tests/      # Pytest (cobertura mínima de 80%)
├── extension/      # Extensão Chrome (Manifest V3) em Preact + TypeScript
│   ├── src/        # Service worker, content script e painel lateral acessível
│   ├── e2e/        # Testes Playwright de aceitação, teclado e acessibilidade
│   └── store/      # Imagens da listagem da Chrome Web Store
├── experiments/    # Experimento Fake.br: EDA, treino, calibração e avaliação reproduzíveis
├── shared/         # Contratos gerados (JSON Schema e tipos TypeScript)
├── evaluation/     # Gold set piloto e guia de anotação
├── scripts/        # Geração de contratos, drift check e diagnóstico de prontidão
└── render.yaml     # Blueprint de produção (Render)
```

## Executar localmente

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 24.

```bash
# Backend (modo de demonstração, sem chaves)
cd backend
cp ../.env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Extensão
cd extension
npm ci
npm run build
```

No Chrome, abra `chrome://extensions`, ative o **Modo do desenvolvedor**, clique em **Carregar sem compactação** e selecione `extension/dist/`. Abra um vídeo do YouTube com legendas e clique em **Checar Alegações**.

O modo padrão (`LLM_PROVIDER=mock`) é só demonstração local. Para um modelo real, configure Ollama ou um provedor remoto no `.env` e rode `uv run python ../scripts/check_readiness.py --check-services`.

## Testes

```bash
cd backend && uv run pytest --cov=app && uv run ruff check . ../scripts
cd extension && npm run lint && npm test && npx playwright test
uv run --directory backend python ../scripts/generate_contracts.py --check
uv run --directory backend python ../scripts/check_drift.py
```

## Experimento de IA (Fake.br)

```bash
cd experiments/fakebr
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-lock.txt
python -m unittest source.test_experiment -v    # verifica artefatos e métricas
python -m source.eda                            # EDA (baixa o snapshot oficial do corpus)
```

Detalhes em [experiments/fakebr/README.md](experiments/fakebr/README.md) e no [relatório técnico](experiments/fakebr/relatorio_tecnico.md).

## Publicação

O roteiro de deploy do backend e de publicação na Chrome Web Store está em [Publicação na Chrome Web Store](https://evidencia-grupo.github.io/documentation/operacao/publicacao-chrome-web-store/).

## Equipe

[@pedrohpsantos](https://github.com/pedrohpsantos), [@MylenaTrindade](https://github.com/MylenaTrindade), [@luizoryone](https://github.com/luizoryone), [@lipestile](https://github.com/lipestile) e [@mahiaara](https://github.com/mahiaara).

## Governança e licença

[Guia de contribuição](CONTRIBUTING.md) · [Política de segurança](SECURITY.md) · [Código de conduta](CODE_OF_CONDUCT.md) · Licença [MIT](LICENSE).
