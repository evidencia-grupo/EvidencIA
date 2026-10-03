# EvidencIA — Extensão de Fact-Checking para YouTube

> Solução de navegador (Manifest V3) para checagem factual em tempo real de vídeos do YouTube através de transcrições, inteligência artificial e painel lateral com paradigma **Evidence-First** (ADR-006).

---

## 1. Visão Geral

O **EvidencIA** é um ecossistema projetado para capacitar usuários que consomem notícias e conteúdos informativos no YouTube a validar de forma autônoma e crítica as afirmações apresentadas diretamente na página de reprodução (`/watch`).

- **Arquitetura Evidence-First (ADR-006):** O resultado da análise não emite vereditos algorítmicos autoritários nem scores numéricos globais de "veracidade" (0–100%). Em vez disso, o sistema extrai alegações atômicas e exibe diretamente as **evidências documentadas**, fontes jornalísticas auditáveis e o grau de incerteza analítica associado.
- **Interface Integrada e Acessível (HU11 / WCAG 2.1 AA):** Botão "Checar Alegações" inserido via Shadow DOM sem conflito de estilos; painel lateral sandboxed com suporte completo a navegação por teclado e contraste de alta visibilidade.
- **Zero Segredos no Cliente (RNF-01 / ADR-002):** Todo o processamento de inteligência artificial e busca externa passa por um **Backend Proxy Seguro**, garantindo que nenhuma chave de API ou credencial sensível resida na extensão.
- **Privacidade por Padrão (RNF-05 / LGPD):** Sem rastreamento de histórico de navegação; permissões de manifesto estritamente delimitadas ao domínio do YouTube (`https://www.youtube.com/*`).
- **Cache Local Proativo (RNF-04 / ADR-003):** Latência $< 100\text{ ms}$ na reabertura de vídeos recentemente checados via `chrome.storage.local` com TTL de 24 horas.
- **Resiliência e Degradação Graciosa (RF-14 / Issue #37):** Em caso de falha ou tempo limite do provedor de IA, o sistema ativa automaticamente o modo *Evidence-Only*, garantindo que as evidências já recuperadas das bases de checagem continuem acessíveis ao usuário.

---

## 2. Estrutura do Repositório

O projeto segue estritamente a arquitetura de monorepo canônica:

```text
evidencia/
├── extension/             # Extensao de navegador (Manifest V3)
│   ├── manifest.json      # Declaracao de permissoes minimas (activeTab, storage)
│   ├── package.json       # Dependencias Preact, TypeScript e Vite
│   ├── vite.config.ts     # Build multi-entry (service-worker, content-script, panel)
│   └── src/
│       ├── background/    # Service Worker e gerenciador de cache
│       ├── content/       # Content Script e injetor Shadow DOM
│       └── panel/         # UI em Preact (ClaimCard, EvidenceCard, ReflectionQuestions)
├── backend/               # Backend Proxy de seguranca e orquestracao
│   ├── pyproject.toml     # Dependencias e configuracao de testes
│   ├── requirements.txt   # FastAPI, Pydantic v2, Uvicorn, SlowAPI
│   ├── .python-version    # Declaracao de versao Python para uv
│   ├── app/
│   │   ├── main.py        # Ponto de entrada FastAPI, CORS e Rate Limiting
│   │   ├── config.py      # Gestao segura de variaveis de ambiente
│   │   ├── schemas.py     # Modelos Pydantic v2 alinhados ao contrato
│   │   ├── api/v1/        # Endpoints /analyze e /health
│   │   ├── providers/     # LLMProvider (base.py, ollama.py, remote.py, mock.py)
│   │   └── services/      # Orquestrador assincrono e Brazilian Fact Matcher
│   ├── ml/                # Inteligência Artificial e Datasets
│   │   └── datasets/      # Script de download e sample_facts.json (FactChecks.br)
│   └── tests/             # Testes automatizados com Pytest
├── shared/                # Fonte unica da verdade para integracao
│   ├── schemas/           # api-schema.json validavel
│   └── types/             # api.ts (interfaces TypeScript para a extensao)
└── .github/
    └── workflows/ci.yml   # Esteira de CI unificada com 4 estagios para front e back
```

---

## 3. Como Executar Localmente

### 3.1 Pré-requisitos
- **Node.js** >= 20 LTS e **npm** >= 10
- **Python** >= 3.12 (ou ferramenta `uv`)
- Navegador Chromium (Google Chrome, Microsoft Edge ou Brave)
- *(Opcional)* **Ollama** com o modelo `qwen2.5:3b` instalado para inferência local de IA

---

### 3.2 Backend Proxy (Python FastAPI)

1. **Acessar o diretório do backend:**
   ```bash
   cd backend
   ```

2. **Criar e ativar o ambiente virtual (ou usar `uv`):**
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
   # Copie o arquivo de exemplo
   cp ../.env.example .env
   ```
   *Nota: Por padrão, o backend roda com `ENVIRONMENT=development` e `LLM_PROVIDER=mock` ou `ollama`.*

4. **Iniciar o servidor de desenvolvimento:**
   ```bash
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   O backend estará disponível em `http://127.0.0.1:8000` (documentação OpenAPI em `/docs`).

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
   # Para compilação de produção (gera a pasta dist/)
   npm run build

   # Ou modo desenvolvimento com hot reload
   npm run dev
   ```

4. **Carregar no Navegador (Google Chrome / Brave / Edge):**
   1. Abra `chrome://extensions/` no seu navegador.
   2. Ative a opção **Modo do desenvolvedor** (canto superior direito).
   3. Clique em **Carregar sem compactação** (*Load unpacked*).
   4. Selecione a pasta `extension/dist` gerada no build.
   5. Navegue até qualquer vídeo no YouTube (`https://www.youtube.com/watch?v=...`) e localize o botão **Checar Alegações** abaixo do player.

---

## 4. Como Executar os Testes

O projeto conta com baterias automatizadas de testes unitários, contratuais e de integração em ambas as camadas:

### 4.1 Testes do Backend (Pytest)
```bash
cd backend
uv run pytest -v
```
*Cobertura: contratos de schemas Pydantic, guarda anti-mock em produção (`test_no_mock_in_production.py`), modo Evidence-Only sob falha (`test_provider_failure.py`), orquestrador de checagem e integração com datasets.*

### 4.2 Testes da Extensão (Vitest + TypeScript)
```bash
cd extension

# Checagem estática de tipos e linter
npm run lint

# Suíte de testes unitários e de componentes
npm test
```
*Cobertura: parsers de legendas do YouTube, gerenciamento e TTL do cache local, validação de contrato e renderização dos componentes Preact (`ClaimCard`, `EvidenceCard`, `ReflectionQuestions`, `UncertaintyAlert`).*

---

## 5. Fonte de Verdade e Documentação

Conforme a governança do projeto, **o repositório de desenvolvimento não contém arquivos de documentação**. Toda a documentação oficial (requisitos RF/RNF, casos de uso UC, histórias HU, decisões de arquitetura ADRs, modelo de ameaças e matriz de rastreabilidade) reside exclusivamente no repositório dedicado:

- **Repositório Oficial de Documentação:** [github.com/evidencia-grupo/documentation](https://github.com/evidencia-grupo/documentation)
