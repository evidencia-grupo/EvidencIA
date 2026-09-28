# EvidencIA — Extensão de Fact-Checking para YouTube

> Solução de navegador (Manifest V3) para checagem factual em tempo real de vídeos do YouTube através de transcrições, inteligência artificial e painel lateral com tema escuro.

---

## 📌 Visão Geral

O **EvidencIA** é um ecossistema projetado para capacitar usuários que consomem notícias e conteúdos informativos no YouTube a validar de forma autônoma a veracidade das afirmações apresentadas diretamente na página de reprodução (`/watch`).

- **Interface no Player:** Botão de veracidade discreto injetado via Shadow DOM.
- **Painel Lateral Sandboxed:** Exibe velocímetro tricolor (0-100%), síntese factual sem jargões e fontes auditáveis em nova aba.
- **Zero Segredos no Cliente:** Intermediação integral via **Backend Proxy Seguro** ([ADR-002](../documentation/docs/tecnico/decisoes/ADR-002-backend-proxy.md)).
- **Privacidade por Padrão (LGPD):** Sem retenção de histórico geral de navegação; permissão restrita a `activeTab` ([RNF-05](../documentation/docs/requisitos/catalogo-requisitos.md#rnf-05)).
- **Cache Local Proativo:** Latência < 100ms em vídeos reincidentes via `chrome.storage.local` com TTL de 24h ([ADR-003](../documentation/docs/tecnico/decisoes/ADR-003-estrategia-cache-local.md)).

---

## 🏗️ Arquitetura e Stack Tecnológica

O repositório é organizado em formato **Monorepo**:

```
evidencia/
├── extension/          # Extensão de navegador Chromium (Manifest V3 + Preact + TypeScript)
├── backend/            # Backend Proxy Seguro (FastAPI + Pydantic v2 + Python 3.12+)
├── shared/             # Contratos de API, tipos TypeScript e Schemas JSON
├── KANBAN.md           # Painel de acompanhamento ágil (Épicos, Features e Sprints)
├── BACKLOG.md          # Backlog refinado com histórias em formato Gherkin
└── README.md           # Guia mestre do projeto
```

### Decisões Técnicas Homologadas

| Camada | Tecnologia | Motivação Técnica |
|:---|:---|:---|
| **Extensão** | **Preact + TypeScript + Vite** | Overhead mínimo: bundle ~3 KB, garantindo impacto de TBT $\le 50\text{ ms}$ (RNF-02). |
| **Isolamento de DOM** | **Shadow DOM + iFrame Sandbox** | Previne conflitos com o CSS/JS do YouTube e impede vazamento de dados. |
| **Backend Proxy** | **FastAPI (Python 3.12+)** | Validação estrita via Pydantic, processamento assíncrono para orquestrar LLMs em $\le 8\text{ s}$. |
| **Cache Local** | **`chrome.storage.local` (TTL 24h)** | Armazenamento local rápido e compatível com o ciclo de vida do Service Worker MV3. |
| **Testes** | **Vitest + Playwright + Pytest** | Testes unitários rápidos e testes E2E reais no Chromium em páginas do YouTube. |

---

## 📋 Gestão do Projeto e Backlog

Consulte os artefatos de governança ágil diretamente no repositório:

- [Quadro Kanban do Projeto (Épicos e Sprints)](./KANBAN.md)
- [Backlog do Produto e Histórias de Usuário (Critérios Gherkin)](./BACKLOG.md)
- [Portal de Documentação Completo (MkDocs)](../documentation/docs/index.md)

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos
- **Node.js** >= 20 LTS e **npm** >= 10
- **Python** >= 3.12
- Navegador Chromium (Google Chrome, Microsoft Edge ou Brave)

---

### 2. Backend Proxy (Python FastAPI)

```bash
cd backend

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
# Ou via pip em modo editável:
pip install -e .

# Configurar variáveis de ambiente
cp .env.example .env

# Iniciar servidor local
uvicorn app.main:app --reload --port 8000
```
O backend estará disponível em `http://127.0.0.1:8000` (documentação interativa em `/docs`).

---

### 3. Extensão de Navegador (Manifest V3)

```bash
cd extension

# Instalar dependências
npm install

# Compilar em modo desenvolvimento com observação de arquivos
npm run dev

# Ou compilar o bundle de produção para /dist
npm run build
```

#### Carregar no Google Chrome / Brave / Edge:
1. Abra `chrome://extensions/` no navegador.
2. Ative a chave **Modo do desenvolvedor** no canto superior direito.
3. Clique em **Carregar sem compactação** (*Load unpacked*).
4. Selecione a pasta `evidencia/extension/dist`.
5. Acesse qualquer vídeo em `https://www.youtube.com/watch?v=...` para testar.

---

## 🧪 Estratégia de Testes

```bash
# Testes unitários da extensão
cd extension && npm run test

# Testes automatizados do backend proxy
cd backend && pytest

# Testes de contrato de dados (JSON Schema)
npm run test:contract
```

---

## 🔒 Segurança e Governança

- Nenhuma chave de API ou credencial sensível deve ser adicionada à pasta `extension/`.
- Todos os endpoints externos são protegidos por Rate Limiting e validação de origem.
- Em caso de dúvidas de conformidade, consulte o [Threat Model (STRIDE)](../documentation/docs/tecnico/threat-model.md).