# Quadro Kanban & Planejamento Operacional — EvidencIA

> Mapeamento visual contínuo do fluxo de valor do projeto **EvidencIA**, integrando os Épicos homologados na documentação, Features do Sequenciador Lean Inception e Histórias de Usuário Gherkin.

---

## 🧭 Visão Geral do Quadro Kanban

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Product Backlog │──>│ Ready for Sprint │──>│   In Progress    │──>│  Review & Test   │──>│ Done (DoD Valid) │
│ (Elicitado/Spec) │   │  (Priorizado)    │   │  (Desenvolvimento│   │  (CI, QA & SAST) │   │ (Onda Concluída) │
└──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 📊 Status das Histórias e Features por Coluna

### 1. 📋 Product Backlog (Refinado)
Itens especificados, priorizados via MoSCoW e prontos para entrar no ciclo de sprint conforme a capacidade da equipe:

| ID | Épico / Feature | Título da História / Item | Prioridade | Onda Lean | Story Points |
|:---|:---|:---|:---:|:---:|:---:|
| `HU08` | **E4** / F2.2 | Contextualização Temporal e Autoria do Vídeo | Should Have | Onda 2 | 3 |
| `HU11` | **E6** / F3.1 | Perguntas Orientadoras para Reflexão Crítica | Could Have | Onda 3 (Out) | 5 |
| `HU12` | **E6** / F3.2 | Avaliação de Relevância e Precisão da Análise | Could Have | Onda 3 (Out) | 3 |
| `F3.3` | **E6** / F3.3 | Text-to-Speech e Recursos de Áudio Acessíveis | Could Have | Onda 3 (Out) | 8 |

---

### 2. 🎯 Ready for Sprint (Sprints Imediatas)

#### 🚀 Sprint 1: Ingestão de Legendas & Gatilho na UI
- [ ] **`HU01` — Verificação Simplificada em Vídeo:** Botão de acionamento em Shadow DOM com feedback imediato $\le 1\text{s}$ (Must Have | 5 pts)
- [ ] **`HU03` — Checagem Rápida no Player:** UI de carregamento e esqueleto de comunicação de mensagens (Must Have | 3 pts)
- [ ] **`HU05` — Ingestão e Processamento de Legendas:** Interceptador de faixas do player do YouTube (Must Have | 5 pts)
- [ ] **`HU10` — Notificação Rápida de Ausência de Legendas:** Validação $< 1\text{s}$ com alerta informativo amigável (Must Have | 3 pts)

#### ⚡ Sprint 2: Backend Proxy & Pipeline de IA
- [ ] **`HU02` (Backend) — Síntese Estruturada:** Processador LLM para resumo analítico sem jargões (Must Have | 5 pts)
- [ ] **`HU04` (Backend) — Categorização de Alegações:** Extrator de alegações (apoiada / contradita / inconclusiva) (Must Have | 5 pts)
- [ ] **`HU09` (Backend) — Incerteza Analítica:** Detecção de conflito de fontes ou falta de evidências (Must Have | 3 pts)

#### 🎨 Sprint 3: Painel Lateral, Velocímetro e Fontes
- [ ] **`HU02` (UI) — Renderização Acessível:** Painel sandboxed com tipografia e contraste WCAG 2.1 AA (Must Have | 5 pts)
- [ ] **`HU04` (UI) — Cartões de Alegações:** Visualização destacada de alegações categorizadas (Must Have | 5 pts)
- [ ] **`HU07` — Auditoria Direta de Fontes:** Lista de hiperligações externas com `target="_blank"` e `noopener` (Must Have | 3 pts)
- [ ] **`HU09` (UI) — Badge de Incerteza:** Destaque visual no topo do painel quando o resultado for inconclusivo (Must Have | 2 pts)

#### 🛡️ Sprint 4: Performance, Cache Local e Homologação MVP
- [ ] **`HU06` — Cache Local com TTL 24h:** Persistência em `chrome.storage.local` com lazy eviction (Should Have | 5 pts)
- [ ] **`SLA-01` — Homologação de Latência:** Validação de SLA $\le 10\text{ s}$ P90 e TBT $\le 50\text{ ms}$ (Must Have | 5 pts)
- [ ] **`SEC-01` — Hardening & Threat Model:** Auditoria SAST e validação de isolamento Shadow DOM / Sandbox (Must Have | 3 pts)

---

### 3. ⚙️ In Progress (Desenvolvimento Ativo)
*Histórias ou tarefas sendo executadas no ciclo atual:*

| ID / Tarefa | Descrição da Atividade | Responsável | Branch de Trabalho | Status |
|:---|:---|:---:|:---:|:---:|
| `SETUP-01` | Scaffolding do Monorepo (`extension/`, `backend/`, `shared/`) | Equipe Dev | `main` | **Em Andamento** |
| `SETUP-02` | Definição de Schemas e Contratos Tipados (`contrato-api.md`) | Arquiteto | `main` | **Em Andamento** |

---

### 4. 🔍 Code Review & QA (Validação)
*Itens aguardando validação de critérios de aceitação e testes automatizados:*

*(Nenhum item pendente de revisão no momento)*

---

### 5. ✅ Done (Definition of Done Validada)
*Itens integrados, testados com $\ge 80\%$ de cobertura e com documentação atualizada:*

- [x] **`DOC-01` — Levantamento de Requisitos e Elicitação:** Catálogo com 11 RFs e 7 RNFs homologados.
- [x] **`DOC-02` — Decisões Arquiteturais Registradas:** ADR-001 (MV3), ADR-002 (Backend Proxy), ADR-003 (Cache Local).
- [x] **`DOC-03` — Threat Model & Acessibilidade:** STRIDE formal, mapeamento LGPD e design tokens WCAG AA.
- [x] **`DOC-04` — Especificação de Contrato:** Schemas TypeScript e JSON para os endpoints `/analyze` e `/health`.

---

## 🗓️ Detalhamento das Sprints e Alocação de Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 0 (Semana 1-2): Fundação, Monorepo, Schemas e CI/CD                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Estrutura de pastas da extensão e do backend proxy                        │
│ • Schemas TypeScript e JSON exportados na pasta /shared                     │
│ • Pipeline de CI (GitHub Actions) com linters e testes                      │
│ • Docker/Virtualenv e scripts de execução local padronizados                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 1 (Semana 3-4): Ingestão de Transcrição e Botão no Player (E1 + E2)  │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Content Script com injeção em Shadow DOM no player do YouTube             │
│ • Parser de legendas (TimedText / CaptionTracks)                            │
│ • Fallback para vídeos sem legendas com alerta < 1s                         │
│ • Entregáveis: HU01, HU03 (botão), HU05, HU10                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 2 (Semana 5-6): Backend Proxy Seguro e Orquestrador de IA (E3)       │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Endpoints FastAPI: POST /api/v1/analyze e GET /api/v1/health              │
│ • Rate Limiting e cabeçalhos de segurança (CORS, TLS 1.3)                   │
│ • Orquestração assíncrona de LLM com timeout de 8,0s                        │
│ • Entregáveis: HU02 (backend), HU04 (backend), HU09 (backend)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 3 (Semana 7-8): Painel Lateral, Velocímetro e Fontes (E4 + E1/E3 UI)│
├─────────────────────────────────────────────────────────────────────────────┤
│ • Painel lateral em Preact rodando em iframe sandbox                        │
│ • Componente Gauge (velocímetro de veracidade 0-100%)                       │
│ • Cartões de alegações e lista de fontes auditáveis com target="_blank"     │
│ • Entregáveis: HU02 (UI), HU04 (UI), HU07, HU09 (UI), HU08                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 4 (Semana 9-10): Cache Local, Auditoria de SLA e Homologação MVP     │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Cache de resultados em chrome.storage.local (TTL 24h e lazy eviction)     │
│ • Testes E2E com Playwright em navegadores Chromium reais                   │
│ • Auditoria Lighthouse: TBT <= 50ms; Auditoria axe-core: WCAG AA            │
│ • Entregáveis: HU06, Validação RNF-01/02/06/07, Tag v1.0.0-MVP              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 Regras de Movimentação do Quadro

1. **Entrada em `In Progress`:** Requer que o desenvolvedor crie uma branch com o padrão `feat/huXX-descricao` ou `fix/huXX-descricao`.
2. **Entrada em `Review & Test`:** Requer Pull Request aberto, cobertura de testes unitários $\ge 80\%$, e aprovação de linter/typecheck no CI.
3. **Movimentação para `Done`:** Requer cumprimento estrito do **Definition of Done (DoD)**:
   - Critérios Gherkin validados por testes.
   - Zero alertas em auditoria de segurança e acessibilidade.
   - Atualização do catálogo de requisitos e documentação.
