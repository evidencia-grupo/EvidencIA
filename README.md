# EvidencIA — Extensão de Fact-Checking para YouTube

> Solução de navegador (Manifest V3) para checagem factual em tempo real de vídeos do YouTube através de transcrições, inteligência artificial e painel lateral com tema escuro.

---

## 1. Visão Geral

O **EvidencIA** é um ecossistema projetado para capacitar usuários que consomem notícias e conteúdos informativos no YouTube a validar de forma autônoma a veracidade das afirmações apresentadas diretamente na página de reprodução (`/watch`).

- **Interface no Player:** Botão de veracidade discreto injetado via Shadow DOM.
- **Painel Lateral Sandboxed:** Exibe velocímetro tricolor (0-100%), síntese factual sem jargões e fontes auditáveis em nova aba.
- **Zero Segredos no Cliente:** Intermediação integral via **Backend Proxy Seguro** ([ADR-002](../documentation/docs/tecnico/decisoes/ADR-002-backend-proxy.md)).
- **Privacidade por Padrão (LGPD):** Sem retenção de histórico geral de navegação; permissão restrita a `activeTab` ([RNF-05](../documentation/docs/requisitos/catalogo-requisitos.md#rnf-05)).
- **Cache Local Proativo:** Latência < 100ms em vídeos reincidentes via `chrome.storage.local` com TTL de 24h ([ADR-003](../documentation/docs/tecnico/decisoes/ADR-003-estrategia-cache-local.md)).

---

## 2. Arquitetura e Stack Tecnológica

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

## 3. Gestão do Projeto e Backlog

Consulte os artefatos de governança ágil diretamente no repositório:

- [Quadro Kanban do Projeto (Épicos e Sprints)](./KANBAN.md)
- [Backlog do Produto e Histórias de Usuário (Critérios Gherkin)](./BACKLOG.md)
- [Portal de Documentação Completo (MkDocs)](../documentation/docs/index.md)

---

## 4. Como Executar Localmente

### 4.1 Pré-requisitos
- **Node.js** >= 20 LTS e **npm** >= 10
- **Python** >= 3.12
- Navegador Chromium (Google Chrome, Microsoft Edge ou Brave)

---

### 4.2 Backend Proxy (Python FastAPI)

#### Opção A (Recomendada): Usando uv
```bash
cd backend

# Sincronizar ambiente virtual e dependências
uv sync

# Configurar variáveis de ambiente
cp .env.example .env

# Iniciar servidor local
uv run uvicorn app.main:app --reload --port 8000
```

#### Opção B: Usando pip tradicional
```bash
cd backend

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env

# Iniciar servidor local
uvicorn app.main:app --reload --port 8000
```
O backend estará disponível em `http://127.0.0.1:8000` (documentação interativa em `/docs`).

#### 4.2.1 Execução com Ollama Local (Qwen 2.5-3B) e Datasets Brasileiros

O EvidencIA prioriza inferência local sem custos de nuvem e alinhamento com dados de checagem do Brasil:

1. **Instalar e Iniciar o Ollama com o Qwen 2.5-3B:**
   ```bash
   # Baixar e executar o modelo localmente (requer apenas ~2.2 GB de RAM)
   ollama run qwen2.5:3b
   ```
2. **Datasets Brasileiros (FactChecks.br & Fake.br):**
   O backend já inclui uma base de checagens brasileiras curadas (`ml/datasets/sample_facts.json`) para testes offline rápidos e CI/CD. Para baixar ou inspecionar os datasets completos do Hugging Face:
   ```bash
   cd backend
   # Inspecionar / baixar FactChecks.br (~10k+ checagens da Lupa, Aos Fatos, Boatos.org)
   python ml/datasets/dataset_downloader.py --dataset factchecks --output-dir ml/datasets/data
   ```
3. **Degradação Graciosa:** Caso o daemon do Ollama não esteja ativo, o backend não falha nem trava: ele degrada suavemente para a base curada brasileira local (`sample_facts.json`) ou oráculo externo (Google Fact Check Tools API).

---

### 4.3 Extensão de Navegador (Manifest V3)

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

## 5. Estratégia de Testes e CI/CD

```bash
# Testes unitários da extensão
cd extension && npm run test

# Testes automatizados do backend proxy (via uv)
cd backend && uv run pytest

# Ou via pytest tradicional (com ambiente ativado)
cd backend && pytest
```

### 5.1 Pipeline de Integração e Entrega Contínua (CI/CD)

A esteira do GitHub Actions (`.github/workflows/ci.yml`) orquestra duas trilhas simultâneas com quatro estágios sequenciais rigorosos:

- **Trilha Frontend (Extensão MV3):**  
  `lint front` &rarr; `build front` &rarr; `test front` &rarr; `deploy front`
  - *Lint:* Verificação estática de tipos via TypeScript (`tsc --noEmit`).
  - *Build:* Compilação multi-entry via Vite e empacotamento em `dist/`.
  - *Test:* Suíte unitária em Vitest para os parsers de legenda e Shadow DOM.
  - *Deploy:* Geração e arquivamento do bundle zip para publicação na Chrome Web Store.

- **Trilha Backend (Proxy FastAPI):**  
  `lint back` &rarr; `build back` &rarr; `test back` &rarr; `deploy back`
  - *Lint:* Análise estática com Ruff e compilação de bytecode (`py_compile`).
  - *Build:* Resolução de dependências Pydantic v2 e validação de inicialização do app.
  - *Test:* Suíte assíncrona de integração via Pytest e TestClient.
  - *Deploy:* Homologação de artefatos pronta para contêiner e nuvem.

---

## 6. Segurança e Governança

- Nenhuma chave de API ou credencial sensível deve ser adicionada à pasta `extension/`.
- Todos os endpoints externos são protegidos por Rate Limiting e validação de origem.
- Em caso de dúvidas de conformidade, consulte o [Threat Model (STRIDE)](../documentation/docs/tecnico/threat-model.md).

## HU03 — Validação da checagem no player

O fluxo da HU03 inclui feedback imediato, leitura das legendas do player, painel sincronizado, cache de 24h, timeout e recuperação de falhas. A integração de IA/busca ainda será implementada: o backend atual identifica respostas como demonstração (`analysisMode: demo`) e o painel mostra esse aviso. Não use essas respostas como checagem factual.

Consulte [HU03.md](./HU03.md) para testes de aceitação, cobertura, acessibilidade, comandos de execução e dependências de homologação. Após alterar o código, execute `npm run build` em `extension/`, recarregue a extensão em `chrome://extensions` e atualize o vídeo no YouTube. Selecione a pasta `extension/dist` em **Carregar sem compactação**.

## HU06 — Consulta Imediata via Cache Local

A história HU06 (Persona: Carlos Augusto) assegura que vídeos já auditados nas últimas 24 horas sejam recuperados de forma instantânea via `chrome.storage.local` com latência inferior a 1 segundo (e meta $< 100\text{ms}$ em ambiente controlado pela ADR-003), sem nova extração de legendas nem consumo de rede externa. Registros expirados ou corrompidos passam por *lazy eviction* automática, disparando nova análise completa.

Consulte [HU06.md](./HU06.md) para a matriz de critérios de aceitação, rastreabilidade e [docs/hu06-evidencias.md](docs/hu06-evidencias.md) para os relatórios de execução.

