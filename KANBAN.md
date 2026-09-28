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

## 👥 Distribuição de Responsabilidades da Equipe (5 Membros)

A distribuição de trabalho foi balanceada de forma a atribuir domínios arquiteturais claros e ~8 pontos de história de MVP por integrante:

| Membro | Domínio Arquitetural | Features & Épicos | Histórias Atribuídas no GitHub | Story Points (MVP) |
|:---|:---|:---|:---|:---:|
| **@MylenaTrindade** | **UI/UX & Acessibilidade WCAG 2.1 AA** | E1 (F2.1), E3 (F2.3), E6 (F3.1) | [#1 (HU01)](https://github.com/evidencia-grupo/EvidencIA/issues/1), [#9 (HU09)](https://github.com/evidencia-grupo/EvidencIA/issues/9), [#13 (Épico 1)](https://github.com/evidencia-grupo/EvidencIA/issues/13) | **8 pts** |
| **@pedrohpsantos** | **Backend Proxy, IA & Segurança** | E3 (F1.2), Threat Model, E6 (F3.2) | [#2 (HU02)](https://github.com/evidencia-grupo/EvidencIA/issues/2), [#4 (HU04)](https://github.com/evidencia-grupo/EvidencIA/issues/4), [#15 (Épico 3)](https://github.com/evidencia-grupo/EvidencIA/issues/15) | **10 pts** |
| **@luizoryone** | **Content Script, Ingestão & Legendas** | E2 (F1.1), Player YouTube, Shadow DOM | [#5 (HU05)](https://github.com/evidencia-grupo/EvidencIA/issues/5), [#10 (HU10)](https://github.com/evidencia-grupo/EvidencIA/issues/10), [#14 (Épico 2)](https://github.com/evidencia-grupo/EvidencIA/issues/14) | **8 pts** |
| **@lipestile** | **Service Worker, Cache Local & SLAs** | E1 (F2.1), E5 (F1.3), Mensageria MV3 | [#3 (HU03)](https://github.com/evidencia-grupo/EvidencIA/issues/3), [#6 (HU06)](https://github.com/evidencia-grupo/EvidencIA/issues/6), [#17 (Épico 5)](https://github.com/evidencia-grupo/EvidencIA/issues/17) | **8 pts** |
| **@mahiaara** | **Auditoria de Fontes & Contexto Temporal** | E4 (F2.2), Confiabilidade Editorial | [#7 (HU07)](https://github.com/evidencia-grupo/EvidencIA/issues/7), [#8 (HU08)](https://github.com/evidencia-grupo/EvidencIA/issues/8), [#16 (Épico 4)](https://github.com/evidencia-grupo/EvidencIA/issues/16) | **6 pts (+ Onda 2)** |

---

## 📊 Status das Histórias e Features por Coluna

### 1. 📋 Product Backlog (Refinado)
Itens especificados, priorizados via MoSCoW e mapeados nas Issues do GitHub:

| ID | Épico / Feature | Título da História / Item | Responsável | Prioridade | Onda Lean | Story Points |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| **#8** | **E4** / F2.2 | [HU08 — Contextualização Temporal e Autoria](https://github.com/evidencia-grupo/EvidencIA/issues/8) | @mahiaara | Should Have | Onda 2 | 3 |
| **#11** | **E6** / F3.1 | [HU11 — Perguntas para Reflexão Crítica](https://github.com/evidencia-grupo/EvidencIA/issues/11) | @mahiaara, @MylenaTrindade | Could Have | Onda 3 (Out) | 5 |
| **#12** | **E6** / F3.2 | [HU12 — Avaliação e Feedback da Análise](https://github.com/evidencia-grupo/EvidencIA/issues/12) | @lipestile, @pedrohpsantos | Could Have | Onda 3 (Out) | 3 |
| `F3.3` | **E6** / F3.3 | Text-to-Speech e Recursos de Áudio Acessíveis | Equipe | Could Have | Onda 3 (Out) | 8 |

---

### 2. 🎯 Ready for Sprint (Sprints Imediatas)

#### 🚀 Sprint 1: Ingestão de Legendas & Gatilho na UI (E1 + E2)
- [ ] **[#1 — HU01](https://github.com/evidencia-grupo/EvidencIA/issues/1) (Verificação Simplificada):** Botão de acionamento em Shadow DOM com feedback imediato $\le 1\text{s}$ (@MylenaTrindade | 5 pts)
- [ ] **[#3 — HU03](https://github.com/evidencia-grupo/EvidencIA/issues/3) (Checagem Rápida no Player):** UI de carregamento e esqueleto de comunicação MV3 (@lipestile | 3 pts)
- [ ] **[#5 — HU05](https://github.com/evidencia-grupo/EvidencIA/issues/5) (Ingestão de Transcrição):** Interceptador de faixas do player do YouTube (@luizoryone | 5 pts)
- [ ] **[#10 — HU10](https://github.com/evidencia-grupo/EvidencIA/issues/10) (Ausência de Legendas):** Validação $< 1\text{s}$ com alerta informativo amigável (@luizoryone | 3 pts)

#### ⚡ Sprint 2: Backend Proxy & Pipeline de IA (E3)
- [ ] **[#2 — HU02](https://github.com/evidencia-grupo/EvidencIA/issues/2) (Síntese Estruturada):** Processador LLM para resumo analítico sem jargões (@pedrohpsantos | 5 pts)
- [ ] **[#4 — HU04](https://github.com/evidencia-grupo/EvidencIA/issues/4) (Categorização de Alegações):** Extrator de alegações (apoiada / contradita / inconclusiva) (@pedrohpsantos | 5 pts)
- [ ] **[#9 — HU09](https://github.com/evidencia-grupo/EvidencIA/issues/9) (Incerteza Analítica):** Detecção de conflito de fontes e badge no topo (@MylenaTrindade | 3 pts)

#### 🎨 Sprint 3: Painel Lateral, Velocímetro e Fontes (E4 + E1/E3 UI)
- [ ] **[#7 — HU07](https://github.com/evidencia-grupo/EvidencIA/issues/7) (Auditoria Direta de Fontes):** Hiperligações externas com `target="_blank"` e `noopener` (@mahiaara | 3 pts)
- [ ] **[#8 — HU08](https://github.com/evidencia-grupo/EvidencIA/issues/8) (Contextualização Temporal):** Metadados de publicação e canal no cabeçalho (@mahiaara | 3 pts)
- [ ] **Painel Lateral Preact:** Integração de UI com Gauge e componentes acessíveis (@MylenaTrindade | 5 pts)

#### 🛡️ Sprint 4: Performance, Cache Local e Homologação MVP (E5)
- [ ] **[#6 — HU06](https://github.com/evidencia-grupo/EvidencIA/issues/6) (Cache Local com TTL 24h):** Persistência em `chrome.storage.local` com lazy eviction (@lipestile | 5 pts)
- [ ] **SLA de Latência:** Validação de SLA $\le 10\text{ s}$ P90 e TBT $\le 50\text{ ms}$ (@lipestile, @pedrohpsantos | 5 pts)
- [ ] **Homologação WCAG 2.1 AA:** Auditoria com `axe-core` e testes E2E Playwright (@MylenaTrindade, @luizoryone | 3 pts)

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
