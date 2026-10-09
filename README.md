# EvidencIA — Extensão de Fact-Checking para YouTube

> **Repositório de Desenvolvimento (Código-Fonte, Testes e Configurações)**  
> Sistema de verificação factual sob o paradigma **Evidence-First** ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)), com **Zero Segredos no Cliente** ([ADR-002](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)), isolamento via **Shadow DOM** e conformidade estrita com **WCAG 2.1 AA**.

[![CI/CD Pipeline](https://github.com/evidencia-grupo/EvidencIA/actions/workflows/ci.yml/badge.svg)](https://github.com/evidencia-grupo/EvidencIA/actions/workflows/ci.yml)
[![Status: GO (Release 1.0.0)](https://img.shields.io/badge/Status-GO%20(Release%201.0.0)-brightgreen)](https://github.com/evidencia-grupo/documentation/blob/main/docs/governanca/prontidao.md)
[![Manifest V3](https://img.shields.io/badge/Manifest-V3-success?logo=googlechrome&logoColor=white)](https://developer.chrome.com/docs/extensions/develop/migrate/what-is-mv3)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Preact](https://img.shields.io/badge/Preact-10.20+-673AB7?logo=preact&logoColor=white)](https://preactjs.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Visão Geral do Produto

O **EvidencIA** capacita cidadãos a exercerem pensamento crítico no YouTube (`youtube.com/watch?v=...`). Sem emitir scores algorítmicos autoritários de "verdadeiro ou falso", o sistema decompõe o discurso em proposições verificáveis e apresenta evidências rastreáveis de agências jornalísticas profissionais brasileiras (Agência Lupa, Aos Fatos, FactChecks.br) e perguntas socráticas reflexivas.

- **Status da Release:** **GO — Pronto para Produção (v1.0.0)**. Todos os 17 Technical Gates e 6 Human Gates (H1–H6) homologados.
- **Documentação Oficial:** Todo o detalhamento analítico, C4, ADRs e modelagem de ameaças reside no repositório [documentation](https://github.com/evidencia-grupo/documentation).

---

## 2. Estrutura do Repositório

```text
EvidencIA/
├── backend/               # Backend Proxy FastAPI, orquestrador de IA e matching
│   ├── app/               # Endpoints (/api/v1), serviços, schemas e provedores
│   ├── ml/                # Datasets curados (sample_facts.json) e classificador
│   └── tests/             # 151 testes automatizados (pytest, cobertura > 90%)
├── extension/             # Extensão Chromium (Manifest V3) em Preact + TypeScript
│   ├── src/background/    # Service worker, cache local 24h e autenticação
│   ├── src/content/       # Content script in-page e parsers de legenda
│   ├── src/panel/         # UI acessível em Preact (WCAG 2.1 AA) e Shadow DOM
│   └── vitest.config.ts   # 171 testes automatizados (vitest, cobertura > 99%)
├── shared/                # Fonte única da verdade para contratos
│   ├── schemas/           # api-schema.json (JSON Schema Draft-07 canônico)
│   └── types/             # api.ts (Interfaces TypeScript compartilhadas)
├── evaluation/            # Gold set piloto e guia de anotação humana
└── scripts/               # Scripts de validação de drift e avaliação
```

---

## 3. Como Executar Localmente

### 3.1 Backend Proxy (FastAPI)

```bash
cd backend
# Opção A: uv (Recomendado)
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Opção B: Virtualenv padrão
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell (ou source .venv/bin/activate no Linux/macOS)
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API e documentação OpenAPI ativa em: `http://127.0.0.1:8000/docs`

### 3.2 Extensão Chrome (Manifest V3)

```bash
cd extension
npm install
npm run build
```
1. No Chrome/Edge, acesse `chrome://extensions/` e ative o **Modo do desenvolvedor**.
2. Clique em **Carregar sem compactação** (*Load unpacked*) e selecione a pasta `extension/dist/`.
3. Abra qualquer vídeo no YouTube (`youtube.com/watch?v=...`) e clique em **Checar Alegações**.

---

## 4. Testes Automatizados e Portões de Qualidade

```bash
# Testes do Backend (Pytest) — 151 testes passando
cd backend
pytest -v --cov=app --cov-report=term-missing

# Testes da Extensão (Vitest & A11y axe-core) — 171 testes passando
cd extension
npm run lint
npm test
```

---

## 5. Rastreabilidade com a Documentação Oficial

Para arquitetura completa, atas de decisão e requisitos, consulte o repositório [evidencia-grupo/documentation](https://github.com/evidencia-grupo/documentation):
- [Documento de Arquitetura (DAS - C4)](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/arquitetura.md)
- [Contrato Canônico de API](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/contrato-api.md)
- [Catálogo de Decisões de Arquitetura (ADR-001 a ADR-006)](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/registro-decisoes.md)
- [Modelagem de Ameaças (STRIDE & LGPD)](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/modelagem-ameacas.md)
- [Relatório Central de Prontidão de Release (GO)](https://github.com/evidencia-grupo/documentation/blob/main/RELEASE-READINESS.md)

---

## 6. Governança e Contribuição

O projeto adota práticas formais de governança técnica e colaboração aberta:
- [Guia de Contribuição](CONTRIBUTING.md): padrões de branch, Conventional Commits e ambiente local.
- [Política de Segurança](SECURITY.md): relato responsável de vulnerabilidades e baseline defensivo.
- [Código de Conduta](CODE_OF_CONDUCT.md): compromissos de convivência e inclusão comunitária.

---

## 7. Licença

Distribuído sob os termos da licença **MIT**. Consulte [LICENSE](LICENSE) para mais informações.
