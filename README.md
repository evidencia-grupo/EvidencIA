# EvidencIA — Extensão de Fact-Checking para YouTube

> Solução de navegador (Manifest V3) para checagem factual em tempo real de vídeos do YouTube através de transcrições, inteligência artificial e painel lateral com paradigma **Evidence-First** ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)).

---

## 1. Visão Geral

O **EvidencIA** é um ecossistema projetado para capacitar usuários que consomem notícias e conteúdos informativos no YouTube a validar de forma autônoma e crítica as afirmações apresentadas diretamente na página de reprodução (`/watch`).

- **Arquitetura Evidence-First ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)):** O resultado da análise não emite vereditos algorítmicos autoritários nem scores numéricos globais de "veracidade" (0–100%). Em vez disso, o sistema extrai alegações atômicas e exibe diretamente as **evidências documentadas**, fontes jornalísticas auditáveis e o grau de incerteza analítica associado.
- **Interface Integrada e Acessível ([HU11](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu11) / [WCAG 2.1 AA](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-07)):** Botão "Checar Alegações" inserido via Shadow DOM sem conflito de estilos; painel lateral sandboxed com suporte completo a navegação por teclado e contraste de alta visibilidade.
- **Zero Segredos no Cliente ([RNF-01](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-01) / [ADR-002](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)):** Todo o processamento de inteligência artificial e busca externa passa por um **Backend Proxy Seguro**, garantindo que nenhuma chave de API ou credencial sensível resida na extensão.
- **Privacidade por Padrão ([RNF-05](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-05) / LGPD):** Sem rastreamento de histórico de navegação; permissões de manifesto estritamente delimitadas ao domínio do YouTube (`https://www.youtube.com/*`).
- **Cache Local Proativo ([RNF-04](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-04) / [ADR-003](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-003-estrategia-cache-local.md)):** Latência $< 100\text{ ms}$ na reabertura de vídeos recentemente checados via `chrome.storage.local` com TTL de 24 horas.
- **Resiliência e Degradação Graciosa ([RF-14](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-14)):** Em caso de falha ou tempo limite do provedor de IA, o sistema ativa automaticamente o modo *Evidence-Only*, garantindo que as evidências já recuperadas das bases de checagem continuem acessíveis ao usuário.

---

## 2. Estrutura do Repositório

O projeto segue estritamente a arquitetura de monorepo canônica:

```text
evidencia/
├── extension/             # Extensão de navegador (Manifest V3) -> ver extension/README.md
│   ├── manifest.json      # Declaração de permissões mínimas (activeTab, storage)
│   ├── package.json       # Dependências Preact, TypeScript e Vite
│   ├── vite.config.ts     # Build multi-entry (service-worker, content-script, panel)
│   └── src/
│       ├── background/    # Service Worker e gerenciador de cache
│       ├── content/       # Content Script e injetor Shadow DOM
│       └── panel/         # UI em Preact (ClaimCard, EvidenceCard, ReflectionQuestions)
├── backend/               # Backend Proxy de segurança e orquestração -> ver backend/README.md
│   ├── pyproject.toml     # Dependências e configuração de testes
│   ├── requirements.txt   # FastAPI, Pydantic v2, Uvicorn, SlowAPI
│   ├── .python-version    # Declaração de versão Python para uv
│   ├── app/
│   │   ├── main.py        # Ponto de entrada FastAPI, CORS e Rate Limiting
│   │   ├── config.py      # Gestão segura de variáveis de ambiente
│   │   ├── schemas.py     # Modelos Pydantic v2 alinhados ao contrato
│   │   ├── api/v1/        # Endpoints /analyze e /health
│   │   ├── providers/     # LLMProvider (base.py, ollama.py, remote.py, mock.py)
│   │   └── services/      # Orquestrador assíncrono e Brazilian Fact Matcher
│   ├── ml/                # Inteligência Artificial e Datasets
│   │   └── datasets/      # Script de download e sample_facts.json (FactChecks.br)
│   └── tests/             # Testes automatizados com Pytest
├── shared/                # Fonte única da verdade para integração -> ver shared/README.md
│   ├── schemas/           # api-schema.json validável
│   └── types/             # api.ts (interfaces TypeScript para a extensão)
└── .github/
    └── workflows/ci.yml   # Esteira de CI unificada com 4 estágios para front e back
```

---

## 3. Como Executar Localmente

### 3.1 Pré-requisitos
- **Node.js** >= 20 LTS e **npm** >= 10
- **Python** >= 3.12 (ou ferramenta `uv`)
- Navegador Chromium (Google Chrome, Microsoft Edge ou Brave)
- *(Opcional)* **Ollama** com o modelo `qwen2.5:3b` instalado para inferência local de IA ([ADR-005](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-005-modelo-local-e-datasets-brasileiros.md))

---

### 3.2 Backend Proxy (Python FastAPI)

1. **Acessar o diretório do backend:**
   ```bash
   cd backend
   ```

2. **Instalar dependências e preparar ambiente:**
   ```bash
   # Com uv (recomendado):
   uv sync

   # Ou com venv padrão (Windows PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente:**
   ```bash
   cp ../.env.example .env
   ```
   *Nota: Por padrão, o backend opera com `ENVIRONMENT=development` e `LLM_PROVIDER=mock` ou `ollama`.*

4. **Iniciar o servidor:**
   ```bash
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   O backend estará disponível em `http://127.0.0.1:8000` (documentação OpenAPI em `/docs`).  
   Consulte os detalhes operacionais em [`backend/README.md`](backend/README.md).

---

### 3.3 Extensão de Navegador (Manifest V3)

1. **Acessar o diretório da extensão:**
   ```bash
   cd extension
   ```

2. **Instalar dependências:**
   ```bash
   npm install
   ```

3. **Compilar o projeto:**
   ```bash
   npm run build
   ```

4. **Carregar no Navegador (Chromium):**
   1. Abra `chrome://extensions/` no navegador.
   2. Ative o **Modo do desenvolvedor**.
   3. Clique em **Carregar sem compactação** (*Load unpacked*).
   4. Selecione a pasta `extension/dist`.
   5. Abra qualquer vídeo no YouTube (`https://www.youtube.com/watch?v=...`) e acione o botão **Checar Alegações**.  
   Consulte os detalhes operacionais em [`extension/README.md`](extension/README.md).

---

## 4. Como Executar os Testes

O projeto segue a [Estratégia de Testes](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/estrategia-testes.md) documentada oficialmente:

### 4.1 Testes do Backend (Pytest)
```bash
cd backend
uv run pytest -v
```
*Valida: contratos de schemas Pydantic, isolamento de segredos, guarda anti-mock em produção ([RF-15](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-15)), degradação Evidence-Only ([RF-14](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-14)) e matching com datasets locais.*

### 4.2 Testes da Extensão (Vitest + Playwright)
```bash
cd extension
npm run lint
npm test
```
*Valida: parser de legendas ([RF-02](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-02)), gerenciador de cache com TTL ([RF-09](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-09)), validação de contratos e componentes Preact acessíveis ([RNF-07](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-07)).*

---

## 5. Rastreabilidade com o Repositório de Documentação

Conforme a governança editorial do projeto, **o repositório de desenvolvimento não armazena arquivos de documentação**. Toda a especificação formal reside no repositório oficial [evidencia-grupo/documentation](https://github.com/evidencia-grupo/documentation) (branch `docs/reorganizacao`):

| Domínio de Conhecimento | Artefatos Oficiais de Documentação |
|:---|:---|
| **Visão & Estratégia** | • [Visão Geral do Projeto](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/visao/visao-geral-do-projeto.md)<br>• [Mapa do Projeto](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/visao/mapa-do-projeto.md)<br>• [Status Atual do Desenvolvimento](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/visao/status.md) |
| **Arquitetura & Design** | • [Documento de Arquitetura de Software](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/arquitetura.md)<br>• [Contrato Canônico de API](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/contrato-api.md)<br>• [Pipeline de IA e Datasets Brasileiros](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/ia-e-datasets.md)<br>• [Design System e Componentes Preact](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/design-system.md) |
| **Decisões Arquiteturais (ADRs)** | • [ADR-001: Manifest V3 e Permissões](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-001-manifest-v3.md)<br>• [ADR-002: Backend Proxy Seguro](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)<br>• [ADR-003: Estratégia de Cache Local com TTL](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-003-estrategia-cache-local.md)<br>• [ADR-004: Stack Tecnológica](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-004-stack-tecnologica.md)<br>• [ADR-005: Modelo Local e Datasets](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-005-modelo-local-e-datasets-brasileiros.md)<br>• [ADR-006: Arquitetura Evidence-First](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)<br>• [Decision Log](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/decision-log.md) |
| **Requisitos & Rastreabilidade** | • [Catálogo de Requisitos Funcionais e Não-Funcionais](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md)<br>• [Matriz de Rastreabilidade Bidirecional](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/matriz-rastreabilidade.md)<br>• [Casos de Uso Detalhados (UC01 a UC06)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/casos-de-uso.md)<br>• [Backlog e Histórias de Usuário (HU01 a HU16)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md)<br>• [Priorização MoSCoW e Ondas de MVP](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/priorizacao-e-mvp.md) |
| **Segurança, Qualidade & Testes** | • [Modelo de Ameaças (Threat Model)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/threat-model.md)<br>• [Estratégia Global de Testes](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/estrategia-testes.md)<br>• [Definition of Done (DoD)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/validacao/definition-of-done.md)<br>• [Guia de Contribuição de Engenharia](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/guia-contribuicao.md) |
