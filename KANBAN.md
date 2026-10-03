# Quadro Kanban & Planejamento Operacional — EvidencIA

> Mapeamento visual contínuo do fluxo de valor do projeto **EvidencIA**, integrando os Épicos homologados na documentação, Features do Sequenciador Lean Inception, Histórias de Usuário Gherkin e o status real de entrega.
> **Última atualização:** Outubro de 2026 — Sprints 1 e 2 **100% Concluídas**, entrando na Sprint 3 (Hardening & Release).

---

## 1. Visão Geral do Quadro Kanban

```text
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Product Backlog │──>│ Ready for Sprint │──>│   In Progress    │──>│  Review & Test   │──>│ Done (DoD Valid) │
│ (Elicitado/Spec) │   │  (Sprint 3 Ativa)│   │  (Sprint 3 QA)   │   │  (CI, QA & SAST) │   │ (S1 e S2 Feitas) │
└──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 2. Status Geral do Roadmap

| Fase / Sprint | Período | Objetivo Central | Status | Progresso |
|:---|:---:|:---|:---:|:---:|
| **Sprint 1: Core MVP** | 28/09 a 02/10 | Happy Path: Injeção no player, captura de legendas, proxy e painel | **CONCLUÍDA** | 100% (8/8 issues) |
| **Sprint 2: Evidence-First** | 05/10 a 09/10 | Descongelamento, fim do score/gauge, Evidence Cards, Providers e resiliência | **CONCLUÍDA** | 100% (7/7 issues) |
| **Sprint 3: Hardening & Release** | 12/10 a 16/10 | SLAs P90, E2E Playwright, auditoria WCAG AA axe-core e Release v1.0.0-mvp | **EM ANDAMENTO** | 4 tarefas restantes |

---

## 3. O Que Resta Para Concluir o Produto (Sprint 3 — 12/10 a 16/10)

Estas são as **únicas 4 tarefas restantes** para o encerramento do MVP e homologação perante a banca:

| Issue | ID / Código | Título da Atividade | Responsável | Prazo | Dependências / Critério de Aceitação |
|:---:|:---:|:---|:---:|:---:|:---|
| [#38](https://github.com/evidencia-grupo/EvidencIA/issues/38) | **HU03** | Testes de Latência e Performance (SLA P90 $\le 10\text{s}$) | @lipestile | 13/10 | Benchmark automatizado de P50, P90 e P99 com cache e busca vetorial. |
| [#39](https://github.com/evidencia-grupo/EvidencIA/issues/39) | **QA-E2E** | Testes E2E com Playwright para o Fluxo Evidence-First | @luizoryone, @lipestile | 14/10 | Execução da suíte E2E em Chromium real contra o YouTube watch page. |
| [#42](https://github.com/evidencia-grupo/EvidencIA/issues/42) | **A11Y-01** | Auditoria Completa de Acessibilidade WCAG 2.1 AA via `axe-core` | @MylenaTrindade | 15/10 | Scanner automatizado com axe-core comprovando zero violações de acessibilidade. |
| [#40](https://github.com/evidencia-grupo/EvidencIA/issues/40) | **REL-01** | Sprint Review Evidence, Tag `v1.0.0-mvp` & **Apresentação Final** | @mahiaara, @pedrohpsantos | **16/10** | Tag oficial gerada, relatório de DoD completo e demo gravada/ao vivo. |

---

## 4. Histórico de Entregas por Coluna

### 4.1 Product Backlog (Itens Fora do MVP / Futuros)
| ID | Descrição do Item | Decisão / Motivo | Status |
|:---:|:---|:---|:---:|
| [#12](https://github.com/evidencia-grupo/EvidencIA/issues/12) | **HU12 / RF-10:** Feedback e Avaliação do Usuário | Excluído do MVP (DIV-01) para manter atrito zero e privacidade LGPD | **Cancelado (Out)** |
| `F3.3` | Text-to-Speech e Recursos de Áudio Acessíveis | Onda 3 pós-MVP | **Backlog Futuro** |

---

### 4.2 In Progress & Review (Sprint 3 Ativa)
- [ ] **[#38] HU03:** Validação dos testes de latência e P90 $\le 10\text{s}$ no backend e na extensão.
- [ ] **[#39] QA-E2E:** Execução dos testes automatizados Playwright (`e2e/hu03.spec.ts` e `e2e/hu06.spec.ts`).
- [ ] **[#42] A11Y-01:** Relatório final axe-core de acessibilidade com zero violações.
- [ ] **[#40] REL-01:** Preparação da demonstração ao vivo e geração da tag `v1.0.0-mvp`.

---

### 4.3 Done (100% Concluído e Validado no Código na Branch `main`)

#### Sprint 1 — Happy Path & Core Funcional
- [x] **[#1] HU01:** Botão em Shadow DOM com feedback $\le 1\text{s}$ no YouTube.
- [x] **[#2] HU02:** Orquestrador LLM para síntese sem jargões para Dona Lurdes.
- [x] **[#3] HU03:** UI de carregamento e mensageria Manifest V3.
- [x] **[#4] HU04:** Extrator de alegações estruturadas.
- [x] **[#5] HU05:** Ingestão e higienização de transcrições do player.
- [x] **[#7] HU07:** Lista de fontes auditadas com links externos.
- [x] **[#8] HU08:** Contextualização temporal e autoria do vídeo.
- [x] **[#9] HU09:** Alerta visual imediato de incerteza analítica.
- [x] **[#6] HU06:** Cache local `chrome.storage.local` com TTL de 24h e recuperação em $< 100\text{ ms}$.

#### Sprint 2 — Evidence-First, Descongelamento & Resiliência
- [x] **[#10] HU10:** Alerta rápido $< 1\text{s}$ para vídeos sem legendas (`friendly-messages.ts`).
- [x] **[#32] HU16:** Abstração `LLMProvider` em `backend/app/providers/` (`OllamaProvider`, `RemoteLLMProvider`, `MockInProductionError`).
- [x] **[#33] HU13:** Contratos canônicos Evidence-First (`shared/schemas/api-schema.json`, `shared/types/api.ts`, `backend/app/schemas.py`).
- [x] **[#34] HU02:** Descongelamento formal e expurgo de `Gauge.tsx`, `SourceList.tsx` e menções a "veracidade".
- [x] **[#35] HU14:** `EvidenceCard.tsx` no painel da extensão, com citações e base `FactChecks.br`.
- [x] **[#36] HU15:** `ReflectionQuestions.tsx` (antiga HU11 promovida) integrada ao `ClaimCard.tsx`.
- [x] **[#37] HU16:** Modo gracioso `evidence_only` sob timeout/falha de IA em `fact_checker.py`.

#### Governança & Arquitetura
- [x] **`DOC-01` — Catálogo de Requisitos:** 14 RFs e 7 RNFs mapeados em `docs/RASTREABILIDADE.md`.
- [x] **`DOC-02` — Registro de Divergências:** `DIVERGENCIAS.md` documentando todas as decisões do produto.
- [x] **`DOC-03` — Decisões Arquiteturais:** ADR-001 (MV3), ADR-002 (Proxy), ADR-003 (Cache), ADR-006 (Evidence-First).
- [x] **`SETUP-01` — Monorepo & CI:** Suítes automatizadas passando (58 testes backend + 139 testes frontend).

---

## 5. Cronograma Regressivo até a Entrega Final (16/10)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 1 (28/09 a 02/10): CORE MVP FUNCIONAL               [100% CONCLUÍDA] │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Setup do monorepo, contratos de API e injeção no player                   │
│ • Captura de legendas, orquestrador de síntese e painel lateral             │
│ • Cache local chrome.storage.local (TTL 24h) e fontes auditáveis            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 2 (05/10 a 09/10): CORE EVIDENCE-FIRST              [100% CONCLUÍDA] │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Descongelamento formal e remoção definitiva de velocímetro/score          │
│ • Schemas Evidence-First, EvidenceCard e ReflectionQuestions                │
│ • Provedores Ollama e RemoteLLM com proteção MockInProductionError          │
│ • Degradação graciosa para modo Evidence-Only sob falha de IA               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPRINT 3 (12/10 a 16/10): HARDENING, SLAS & RELEASE FINAL    [EM ANDAMENTO] │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Issue #38: Benchmark automatizado de latência (P90 <= 10s)                │
│ • Issue #39: Execução da suíte E2E Playwright Evidence-First                │
│ • Issue #42: Auditoria final WCAG 2.1 AA via axe-core com zero violações    │
│ • Issue #40: Tag v1.0.0-mvp, release notes e Apresentação Final (16/10)     │
└─────────────────────────────────────────────────────────────────────────────┘
```
