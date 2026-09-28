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

### 2. 🎯 Ready for Sprint (Planejamento em 2 Semanas: 28/09 a 09/10)

> **Prazo Fatal do Projeto:** 09 de Outubro de 2026 (Sexta-feira).  
> **Cadência Operacional:** 2 Sprints semanais intensivas com 5 desenvolvedores.

#### 🚀 Sprint 1 (Semana 1: 28/09 a 02/10) — MVP Core Funcional (Happy Path Ponta a Ponta)
*Objetivo: Fechar a cadeia completa de valor: clique no YouTube -> extração -> backend proxy -> IA -> painel Preact.*

| Issue | Descrição da História | Responsável | Prazo | Status |
|:---|:---|:---:|:---:|:---:|
| [#1](https://github.com/evidencia-grupo/EvidencIA/issues/1) | **HU01:** Botão em Shadow DOM com feedback $\le 1\text{s}$ | @MylenaTrindade | 02/10 | Ready |
| [#3](https://github.com/evidencia-grupo/EvidencIA/issues/3) | **HU03:** UI de carregamento e mensageria MV3 | @lipestile | 02/10 | Ready |
| [#5](https://github.com/evidencia-grupo/EvidencIA/issues/5) | **HU05:** Interceptador e higienizador de legendas do player | @luizoryone | 02/10 | Ready |
| [#2](https://github.com/evidencia-grupo/EvidencIA/issues/2) | **HU02:** Orquestrador LLM para síntese sem jargões | @pedrohpsantos | 02/10 | Ready |
| [#4](https://github.com/evidencia-grupo/EvidencIA/issues/4) | **HU04:** Extrator de alegações estruturadas (apoiada/contradita) | @pedrohpsantos | 02/10 | Ready |
| [#7](https://github.com/evidencia-grupo/EvidencIA/issues/7) | **HU07:** Lista de fontes auditadas com `target="_blank"` | @mahiaara | 02/10 | Ready |

*Marco de Sexta (02/10): Demonstração interna do Happy Path executando em vídeo real do YouTube.*

---

#### 🛡️ Sprint 2 (Semana 2: 05/10 a 09/10) — Hardening, Acessibilidade, SLAs & Release 1.0 (Entrega Final)
*Objetivo: Blindagem de segurança, cache local instantâneo, acessibilidade WCAG 2.1 AA e testes E2E.*

| Issue | Descrição da História / Tarefa | Responsável | Prazo | Status |
|:---|:---|:---:|:---:|:---:|
| [#10](https://github.com/evidencia-grupo/EvidencIA/issues/10) | **HU10:** Alerta rápido $< 1\text{s}$ para vídeos sem legendas | @luizoryone | 06/10 | Backlog |
| [#9](https://github.com/evidencia-grupo/EvidencIA/issues/9) | **HU09:** Badge de incerteza analítica no topo do painel | @MylenaTrindade | 07/10 | Backlog |
| [#6](https://github.com/evidencia-grupo/EvidencIA/issues/6) | **HU06:** Cache local `chrome.storage.local` (TTL 24h, lazy eviction) | @lipestile | 07/10 | Backlog |
| [#8](https://github.com/evidencia-grupo/EvidencIA/issues/8) | **HU08:** Metadados temporais e canal no cabeçalho | @mahiaara | 08/10 | Backlog |
| `QA-E2E` | Testes Playwright em Chromium e validação TBT $\le 50\text{ ms}$ | @luizoryone, @lipestile | 08/10 | Backlog |
| `A11Y` | Auditoria de acessibilidade WCAG 2.1 AA via `axe-core` | @MylenaTrindade | 08/10 | Backlog |
| `REL-01` | Congelamento de código, Tag `v1.0.0-mvp`, artefatos e entrega | Toda a equipe | 09/10 | Backlog |

---

### 3. ⚙️ In Progress (Desenvolvimento Ativo)
*Histórias ou tarefas sendo executadas no ciclo atual:*

| ID / Tarefa | Descrição da Atividade | Responsável | Branch de Trabalho | Status |
|:---|:---|:---:|:---:|:---:|
| `SETUP-01` | Scaffolding do Monorepo (`extension/`, `backend/`, `shared/`) | Equipe Dev | `main` | **Concluído** |
| `SETUP-02` | Definição de Schemas e Contratos Tipados (`contrato-api.md`) | Arquiteto | `main` | **Concluído** |

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
- [x] **`SETUP-01` — Setup Inicial do Monorepo:** Extensão Preact MV3, Backend FastAPI, Schemas e CI.
- [x] **`GH-ISSUES` — Cadastro e Distribuição no GitHub:** 18 Issues cadastradas com datas (28/09 a 09/10) e assignees.

---

## 🗓️ Cronograma Regressivo de 2 Semanas (28/09 a 09/10)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SEMANA 1 (28/09 a 02/10): SPRINT 1 — "CORE MVP FUNCIONAL"                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Seg 28/09: Setup do monorepo, contratos e alinhamento de issues (FEITO)  │
│ • Ter 29/09: Injeção do botão Shadow DOM (Mylena) + Endpoints FastAPI (Pedro)│
│ • Qua 30/09: Parser de legendas (Luiz) + Agregador de fontes (Mayara)       │
│ • Qui 01/10: Roteamento Service Worker (Felipe) + Painel Preact Gauge (Mylena)│
│ • Sex 02/10: Integração do Happy Path completo (Demonstração E2E interna)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SEMANA 2 (05/10 a 09/10): SPRINT 2 — "HARDENING, SLAS & ENTREGA FINAL"      │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Seg 05/10: Cache local chrome.storage.local (Felipe) + Erros legendas (Luiz)│
│ • Ter 06/10: Badge de incerteza analítica (Mylena) + Rate limiter (Pedro)   │
│ • Qua 07/10: Auditoria WCAG 2.1 AA (Mylena) + Metadados temporais (Mayara)  │
│ • Qui 08/10: Medição de TBT <= 50ms (Luiz) + Testes Playwright (Felipe)     │
│ • Sex 09/10 (ENTREGA FINAL): Tag v1.0.0-mvp, build de produção e docs       │
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
