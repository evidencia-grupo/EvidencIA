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

O projeto é estruturado como um monorepo modular:

```text
EvidencIA/
├── backend/                  # Backend Proxy Seguro (FastAPI + Python 3.12+)
│   ├── app/                  # Núcleo da aplicação FastAPI
│   │   ├── api/v1/           # Rotas da API (/analyze, /health)
│   │   ├── providers/        # Abstração de LLMs (Ollama, Remote, Mock)
│   │   ├── services/         # Recuperação de fatos (FactChecks.br) e orquestração
│   │   └── schemas.py        # Modelos Pydantic v2 do contrato Evidence-First
│   ├── ml/                   # Datasets (FactChecks.br, Fake.br) e schemas de ML
│   └── tests/                # Suíte de testes unitários e de integração (Pytest)
├── extension/                # Extensão de navegador Chromium (Manifest V3 + Preact)
│   ├── src/
│   │   ├── background/       # Service Worker, gerenciamento de cache e validação
│   │   ├── content/          # Extração de legendas e injeção do botão no YouTube
│   │   ├── panel/            # Interface Preact (EvidenceCard, ReflectionQuestions, etc.)
│   │   └── telemetry/        # Telemetria local sanitizada (sem emissão de rede)
│   ├── e2e/                  # Testes ponta a ponta (Playwright)
│   └── manifest.json         # Manifesto da extensão Chromium MV3
├── shared/                   # Contratos canônicos compartilhados entre cliente e servidor
│   ├── schemas/              # JSON Schemas formais (api-schema.json)
│   └── types/                # Definições de tipos TypeScript (api.ts)
├── docs/                     # Documentação de engenharia e desenvolvimento
│   └── RASTREABILIDADE.md    # Matriz completa de rastreabilidade (RF, RNF, HU, UC)
├── scripts/                  # Scripts de automação e auditoria contínua de completude
├── DIVERGENCIAS.md           # Registro formal de divergências entre docs e código
├── .env.example              # Modelo documentado de variáveis de ambiente do backend
└── README.md                 # Este guia
```

---

## 3. Como Executar Localmente

### 3.1 Pré-requisitos
- **Node.js** >= 20 LTS e **npm** >= 10
- **Python** >= 3.12
- Navegador Chromium (Google Chrome, Microsoft Edge ou Brave)
- *(Opcional)* **Ollama** com o modelo `qwen2.5:3b` instalado para inferência local de IA

---

### 3.2 Backend Proxy (Python FastAPI)

1. **Acessar o diretório do backend:**
   ```bash
   cd backend
   ```

2. **Criar e ativar o ambiente virtual:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variáveis de ambiente:**
   ```bash
   # Copie o arquivo de exemplo
   cp ../.env.example .env
   ```
   *Nota: Por padrão, o backend roda com `ENVIRONMENT=development` e `LLM_PROVIDER=mock` ou `ollama`.*

5. **Iniciar o servidor de desenvolvimento:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   O backend estará disponível em `http://127.0.0.1:8000` (documentação Swagger interativa em `/docs`).

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
.\.venv\Scripts\pytest -v
```
*Cobertura: contratos de schemas Pydantic, guarda anti-mock em produção (`test_no_mock_in_production.py`), modo Evidence-Only sob falha (`test_provider_failure.py`), orquestrador de checagem e integração com datasets.*

### 4.2 Testes da Extensão (Vitest + TypeScript)
```bash
cd extension

# Checagem estática de tipos
npm run typecheck

# Suíte de testes unitários
npm test
```
*Cobertura: parsers de legendas do YouTube, gerenciamento e TTL do cache local, sanitização de telemetria sem rede, validação de contrato e renderização dos componentes Preact (`ClaimCard`, `EvidenceCard`, `ReflectionQuestions`, `UncertaintyAlert`).*

---

## 5. Rastreabilidade e Governança

Para manter transparência total sobre o estado do projeto e sua conformidade com a engenharia de requisitos:

- **[Matriz de Rastreabilidade (docs/RASTREABILIDADE.md)](./docs/RASTREABILIDADE.md):** Mapeia cada Requisito Funcional (RF-01 a RF-14), Requisito Não Funcional (RNF-01 a RNF-07), História de Usuário (HU01 a HU16) e Caso de Uso (UC01 a UC06) até seus módulos e arquivos de implementação correspondentes.
- **[Registro de Divergências (DIVERGENCIAS.md)](./DIVERGENCIAS.md):** Documenta formalmente todas as discrepâncias pontuais entre o repositório de documentação e o código (ex.: descarte do RF-05/RF-10 no MVP, permissão `scripting` justificada pelo player do YouTube, etc.).
- **[Repositório Oficial de Documentação](https://github.com/evidencia-grupo/documentation):** Fonte primária de verdade com arquitetura de referência, histórico de decisões arquiteturais (ADRs), guia do usuário e modelos de ameaça.
