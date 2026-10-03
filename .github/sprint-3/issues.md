# Sprint 3 — Checklist de Issues, Hardening & Apresentação Final

> **Milestone:** Sprint 3  
> **Período de Execução:** 12/10/2026 a 16/10/2026 (5 dias úteis)  
> **Marco Decisivo do Projeto:** **16 de Outubro de 2026 (Sexta-feira) — Apresentação Final da Solução**  
> **Objetivo da Sprint 3:** Hardening de produção, garantia dos SLAs de latência (P90 $\le 10\text{s}$), persistência instantânea em cache local, suíte E2E automatizada com Playwright, auditoria de acessibilidade WCAG 2.1 AA (axe-core), geração da tag `v1.0.0-mvp` e preparação dos artefatos da banca avaliadora.  
> **Total de Story Points:** 21 SP (5 issues oficiais)  
> **Referência Arquitetural:** [ADR-003 (Cache Local)](../../documentation/docs/tecnico/decisoes/ADR-003-estrategia-cache-local.md) · [ADR-006 (Evidence-First)](../../documentation/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md) · [KANBAN.md](../../KANBAN.md)

---

## 1. Quadro de Responsabilidades e Prazos da Equipe (Sprint 3: 12/10 a 16/10)

| Issue | HU / ID | Título da História / Atividade | Épico | Responsável Principal | Co-responsável | Prazo de Entrega | Prioridade MoSCoW | SP |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|
| [#6](https://github.com/evidencia-grupo/EvidencIA/issues/6) | **HU06** | Consulta Imediata via Cache Local (`chrome.storage.local`) | `epic:e5-performance-cache` | @lipestile | — | **13/10/2026** | `should-have` / `mvp:onda-1` | 5 |
| [#38](https://github.com/evidencia-grupo/EvidencIA/issues/38) | **HU03** | Testes de Latência e Performance (SLA P90 $\le 10\text{s}$) | `epic:e5-performance-cache` | @lipestile | — | **13/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#39](https://github.com/evidencia-grupo/EvidencIA/issues/39) | **QA-E2E** | Testes E2E com Playwright para o Fluxo Evidence-First | `epic:e5-performance-cache` | @luizoryone | @lipestile | **14/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#42](https://github.com/evidencia-grupo/EvidencIA/issues/42) | **A11Y-01** | Auditoria Completa de Acessibilidade WCAG 2.1 AA via `axe-core` | `epic:e1-gatilho` | @MylenaTrindade | — | **15/10/2026** | `must-have` / `mvp:onda-1` | 3 |
| [#40](https://github.com/evidencia-grupo/EvidencIA/issues/40) | **REL-01** | Sprint Review Evidence, Release `v1.0.0-mvp` & **Apresentação Final** | `epic:e6-engajamento` | @mahiaara | @pedrohpsantos | **16/10/2026** *(Apresentação)* | `must-have` / `mvp:onda-1` | 3 |
| **Total** | | | | | | | | **21 SP** |

---

## 2. Detalhamento das Issues da Sprint 3

### [#6] [HU06] Consulta Imediata via Cache Local · 5 SP
- **Labels:** `epic:e5-performance-cache`, `should-have`, `mvp:onda-1`
- **Responsável:** @lipestile
- **Prazo de Entrega:** 13/10/2026

#### Declaração de Valor
> **Como** Carlos Augusto (Estudante conectado com navegação intensa)  
> **Pretendo** recuperar checagens recentes salvas no cache local  
> **Para que** não desperdice tráfego de rede nem consuma processamento em vídeos já auditados.

#### Rastreabilidade
- **Épico:** `E5 — Performance e Cache`
- **Feature:** `F1.3 — Cache Local e Otimização de Rede`
- **Prioridade MoSCoW:** `Should Have` (Onda 1 / Hardening MVP)
- **Sprint:** `Sprint 3 (12/10/2026 a 16/10/2026)`
- **Prazo de Entrega:** `13/10/2026`
- **Requisitos Vinculados:** RF-09, RNF-01, RNF-05, ADR-003

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Consulta imediata via cache local

  Cenário: Cache válido disponível
    Dado que um vídeo já foi analisado recentemente nas últimas 24 horas
    Quando Carlos Augusto aciona a extensão nesse vídeo
    Então o sistema deve localizar o registro em cache pelo identificador do vídeo
    E exibir o resultado em menos de 1 segundo, sem nova chamada externa

  Cenário: Cache expirado ou corrompido
    Dado que o registro local de um vídeo está expirado (> 24h) ou corrompido
    Quando a extensão tenta recuperá-lo
    Então o sistema deve descartar o registro
    E disparar uma nova análise completa
```

---

### [#38] [HU03] Testes de Latência e Performance (P90 <= 10s) · 5 SP
- **Labels:** `epic:e5-performance-cache`, `must-have`, `mvp:onda-1`
- **Responsável:** @lipestile
- **Prazo de Entrega:** 13/10/2026

#### Declaração de Valor
> **Como** Carlos (Estudante universitário com conexão móvel)  
> **Pretendo** que a checagem completa do vídeo seja concluída em menos de 10 segundos no percentil 90  
> **Para que** eu não desista da checagem nem sofra com lentidão enquanto assisto a vídeos no YouTube.

#### Rastreabilidade
- **Épico:** `E5 — Performance e Cache`
- **Feature:** `F1.3 — Cache Local e Otimização de SLA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 3 (12/10/2026 a 16/10/2026)`
- **Prazo de Entrega:** `13/10/2026`
- **Requisitos Vinculados:** RF-09, RNF-01, RNF-02, ADR-003

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Garantia de SLA de latência e performance da checagem

  Cenário: Checagem com recuperação via cache local
    Dado que um vídeo já foi analisado previamente nas últimas 24 horas
    Quando o usuário aciona a verificação
    Então o resultado deve ser recuperado do chrome.storage.local em menos de 500ms
    E nenhuma chamada de rede ao backend deve ser disparada

  Cenário: Checagem a frio dentro do SLA de 10 segundos
    Dado que o vídeo é analisado pela primeira vez
    Quando a extração e busca vetorial são executadas
    Então o tempo total de resposta no percentil 90 (P90) deve ser menor ou igual a 10 segundos
    E o Total Blocking Time (TBT) na página do YouTube deve permanecer <= 50ms
```

---

### [#39] [QA-E2E] Testes E2E com Playwright para o Fluxo Evidence-First · 5 SP
- **Labels:** `epic:e5-performance-cache`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @luizoryone, @lipestile
- **Prazo de Entrega:** 14/10/2026

#### Declaração de Valor
> **Como** Equipe de Engenharia & Qualidade  
> **Pretendo** validar o fluxo completo da extensão em um navegador Chromium real via Playwright  
> **Para que** tenhamos garantia de que a injeção no player, captura de legendas, comunicação com backend e renderização do painel funcionam de ponta a ponta sem regressão.

#### Rastreabilidade
- **Épico:** `E5 — Performance e Cache`
- **Feature:** `F1.1 / F1.3 — Ingestão, Interceptação e Validação Ponta a Ponta`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 3 (12/10/2026 a 16/10/2026)`
- **Prazo de Entrega:** `14/10/2026`
- **Requisitos Vinculados:** RF-01, RF-02, RF-03, RNF-01, RNF-05

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Teste E2E automatizado do fluxo Evidence-First

  Cenário: Fluxo completo de checagem no YouTube via extensão
    Dado que a extensão está carregada em uma instância headless do Chromium via Playwright
    E uma página de vídeo do YouTube está aberta
    Quando o script clica no botão de verificação injetado no player
    Então a transcrição deve ser extraída com sucesso
    E o painel lateral deve renderizar os cartões de alegações e evidências sem erros no console

  Cenário: Vídeo sem legendas disponíveis no player
    Dado que o vídeo carregado não possui faixa de legenda disponível
    Quando o usuário aciona a verificação
    Então o painel deve exibir em menos de 1s a mensagem informativa sobre ausência de transcrição
```

---

### [#42] [A11Y-01] Auditoria Completa de Acessibilidade WCAG 2.1 AA via axe-core · 3 SP
- **Labels:** `epic:e1-gatilho`, `must-have`, `mvp:onda-1`
- **Responsável:** @MylenaTrindade
- **Prazo de Entrega:** 15/10/2026

#### Declaração de Valor
> **Como** Dona Lurdes (Consumidora de receitas com dificuldades visuais ou motoras)  
> **Pretendo** navegar pela extensão exclusivamente via teclado e com leitores de tela em alto contraste  
> **Para que** eu consiga entender as evidências e checagens sem barreiras de acessibilidade digital.

#### Rastreabilidade
- **Épico:** `E1 — Gatilho e Ativação` (e UX Acessível)
- **Feature:** `F2.1 — Disparo e Exibição Acessível WCAG`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 3 (12/10/2026 a 16/10/2026)`
- **Prazo de Entrega:** `15/10/2026`
- **Requisitos Vinculados:** RF-01, RNF-07

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Auditoria de acessibilidade WCAG 2.1 AA

  Cenário: Navegação completa por teclado no painel lateral
    Dado que o usuário aciona a extensão sem utilizar o mouse
    Quando ele utiliza as teclas Tab, Shift+Tab, Enter e Espaço
    Então o foco visual deve ser evidente em todos os elementos interativos
    E nenhum foco deve ficar preso (keyboard trap)

  Cenário: Auditoria automatizada com axe-core
    Dado que a suíte de testes de acessibilidade é executada contra os componentes do painel
    Quando o axe-core analisa a árvore DOM
    Então zero violações de nível A e AA devem ser reportadas
    E o contraste de cores entre texto e fundo deve atender à razão mínima de 4.5:1
```

---

### [#40] [REL-01] Sprint Review Evidence, Release v1.0.0-mvp & Apresentação Final (16/10) · 3 SP
- **Labels:** `epic:e6-engajamento`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @mahiaara, @pedrohpsantos
- **Prazo de Entrega:** 16/10/2026
- **Data da Apresentação:** **16/10/2026 (Sexta-feira)**

#### Declaração de Valor
> **Como** Toda a Equipe / Avaliadores e Banca do Desafio  
> **Pretendo** consolidar todas as evidências de teste, métricas de qualidade, benchmarks, tag v1.0.0-mvp e apresentação final  
> **Para que** o projeto EvidencIA seja apresentado com sucesso no dia 16/10/2026 e cumpra 100% do Definition of Done (DoD).

#### Rastreabilidade
- **Épico:** `E6 — Engajamento Reflexivo / Entrega Final`
- **Feature:** `F3.2 — Fechamento do Projeto, Auditoria e Documentação Final`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 3 (12/10/2026 a 16/10/2026)`
- **Prazo de Entrega:** `16/10/2026`
- **Data da Apresentação:** `16/10/2026`
- **Requisitos Vinculados:** RNF-05, RNF-07, DoD do Projeto

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Evidências da Sprint Review, entrega final e apresentação

  Cenário: Validação do Definition of Done (DoD) completo
    Dado que todas as histórias das Sprints 1, 2 e 3 foram desenvolvidas
    Quando a esteira de validação final é executada
    Então 100% dos testes unitários e de integração devem passar sem erros
    E a cobertura de testes deve ser igual ou superior a 80%
    E zero vulnerabilidades críticas ou altas devem ser apontadas pelo SAST

  Cenário: Apresentação Final da Solução (16/10/2026)
    Dado que a entrega final do projeto está homologada
    Quando a banca examinadora avalia a solução no dia 16/10
    Então a extensão deve executar o fluxo ponta a ponta ao vivo no YouTube
    E o pacote de slides, documentação e vídeo de demonstração devem estar disponíveis
```

---

## 3. Checklist para o Dia da Apresentação Final (16/10/2026)

- [ ] Extensão empacotada pronta para carregamento descompactado no Google Chrome / Chromium.
- [ ] Backend Proxy ativo e operacional com resposta no modo Evidence-First.
- [ ] Demonstração prática gravada em vídeo de alta resolução (screencast de backup).
- [ ] Apresentação de slides estruturada com Contexto, Problema, Arquitetura Evidence-First, Demonstração e Resultados.
- [ ] Relatório de métricas comprovando:
  - Latência no percentil 90 (P90 $\le 10\text{s}$)
  - Cobertura de testes unitários e de integração ($\ge 80\%$)
  - Zero vulnerabilidades críticas no SAST
  - Acessibilidade validada WCAG 2.1 AA
