# Sprint 2 — Checklist de Issues & Plano de Conclusão do Projeto

> **Milestone:** Sprint 2  
> **Objetivo:** Converter os resultados da investigação da Sprint 1 em um pipeline de evidências e uma UX que preserve o pensamento crítico, eliminando a dependência estrutural do Ollama local e o score global.  
> **Total de Story Points:** 38 SP (9 issues)  
> **Referências:** [ADR-006](../documentation/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md) · [Sprint Backlog](../documentation/docs/scrum/sprint-02/sprint-backlog.md)

---

## Panorama de Progresso (Transição Sprint 1 → Sprint 2)

### Sprint 1 (Concluída e Integrada via PR #31)
- [x] **IS-01:** Guiding Questions publicadas e validadas (`documentation/docs/visao/guiding-questions.md`)
- [x] **IS-02:** Alinhamento da Essential Question (`documentation/docs/visao/essential-question-alignment.md`)
- [x] **IS-03:** Dataset registry versionado (`backend/ml/datasets/sources.yaml`)
- [x] **IS-04:** Pipeline de ingestão por adapters (`backend/ml/datasets/adapters/`, `ingest.py`)
- [x] **IS-05:** Schema canônico de evidência (`backend/ml/schemas/evidence.py`)
- [x] **IS-06:** Índice Chroma e retrieval vetorial (`backend/ml/retrieval/index.py`, `search.py`)
- [x] **IS-07:** Notebook EDA reprodutível com 17 seções (`notebooks/eda_datasets.ipynb`)
- [x] **IS-08:** Baseline de retrieval (BM25/TF-IDF) validado
- [x] **IS-09:** Proveniência e manifest de dados (`backend/data/manifest.json`, `manifest.py`)
- [x] **IS-10:** Congelamento da UI do gauge ativo (`.github/FREEZE.md`, `.github/workflows/freeze-guard.yml`)
- [x] **IS-11:** Interface LLMProvider e guard anti-mock (`backend/app/services/providers/`)

---

## Issues da Sprint 2 (38 SP)

### #S2-01 — Provider Abstraction: Migração de OllamaProvider e RemoteLLMProvider
**Labels:** `sprint-2` `backend` `p0` `sp-5` · **Estimativa:** 5 SP · **HU Relacionada:** HU16

**Contexto:**
Vinculado ao ADR-006 e ao isolamento de provedores criado na Sprint 1. Conecta o `FactCheckerService` à interface `LLMProvider`, permitindo alternância transparente entre inferência local (Qwen 2.5-3B) e modelos remotos, eliminando o acoplamento com `ollama_service.py`.

**Descrição Técnica:**
- Conectar `FactCheckerService` ao `get_provider()` de `backend/app/services/providers/factory.py`.
- Implementar `OllamaProvider.extract_claims` e `OllamaProvider.generate_reflection` em `backend/app/services/providers/ollama.py`, migrando as regras de prompt e tratamento JSON de `ollama_service.py`.
- Implementar `RemoteLLMProvider` em `backend/app/services/providers/remote.py` com suporte a endpoints compatíveis com OpenAI/vLLM.
- Desacoplar `fact_checker.py` da importação direta de `ollama_service`.

**Critérios de Aceitação:**
- [ ] `FactCheckerService` obtém provedor exclusivamente via `get_provider()`
- [ ] `OllamaProvider` implementa `extract_claims` e `generate_reflection` sem levantar `NotImplementedError`
- [ ] `RemoteLLMProvider` funcional via `REMOTE_LLM_BASE_URL` e `REMOTE_LLM_API_KEY`
- [ ] Suíte de testes `test_provider_contract.py` executando com 100% de sucesso
- [ ] Testes de regressão `test_fact_checker.py` e `test_ollama_service.py` passam sem falhas

---

### #S2-02 — Evidence-First Schema: Migração de Contratos (`claims[]` + `evidence[]`)
**Labels:** `sprint-2` `backend` `frontend` `p0` `sp-5` · **Estimativa:** 5 SP · **HU Relacionadas:** HU13, HU14

**Contexto:**
Vinculado ao ADR-006 (Decisão 2). O contrato da API passa a refletir a unidade central "Alegação + Evidências", descontinuando o score global de veracidade de 0 a 100.

**Descrição Técnica:**
- Atualizar `backend/app/schemas.py`: `AnalyzeResponse` com `analysisMode: "evidence_first"`, `claims: List[VerificationClaim]`, `evidence: List[EvidenceItem]`, `uncertainty: UncertaintyAlertData`, `reflectionQuestions: List[str]`.
- Marcar `score` e `reliabilityScore` como deprecados / opcionais para transição segura.
- Atualizar `shared/types/api.ts` e `shared/schemas/api-schema.json`.
- Garantir a invariante central: ausência de evidência fática NUNCA é classificada como "falso" ou "contraditada" (retorna `unverifiable` / `insufficient_evidence`).

**Critérios de Aceitação:**
- [ ] Endpoint `/api/v1/analyze` retorna payload aderente ao schema evidence-first
- [ ] Invariante de veredito fático validada por teste automatizado
- [ ] Contratos TypeScript em `shared/types/api.ts` compilando sem erro no frontend
- [ ] Testes de API em `backend/tests/test_api.py` atualizados e passando

---

### #S2-03 — Descongelamento Formal e Remoção do Score Global da UI
**Labels:** `sprint-2` `frontend` `freeze` `p0` `sp-3` · **Estimativa:** 3 SP · **HU Relacionadas:** HU02, HU04

**Contexto:**
Vinculado ao critério de descongelamento formalizado em `.github/FREEZE.md`. Com o pipeline de dados validado, os componentes de UI legados do gauge/score devem ser removidos da interface para evitar que o usuário seja induzido a um julgamento algorítmico dogmático.

**Descrição Técnica:**
- Aplicar o label `unfreeze-approved` pelo Tech Lead no PR de alteração.
- Atualizar `.github/FREEZE.md` e `.github/frozen-paths.txt` registrando o descongelamento definitivo.
- Remover a importação e renderização de `<Gauge />` em `extension/src/panel/index.tsx`.
- Desativar `extension/src/panel/components/Gauge.tsx` (marcado como legado).
- Remover textos de "Veracidade", "Índice de Confiabilidade" e porcentagens globais da UI do painel.

**Critérios de Aceitação:**
- [ ] PR passa pelo workflow `freeze-guard.yml` com autorização explícita
- [ ] Painel da extensão não renderiza nenhum elemento de velocímetro ou nota de 0 a 100
- [ ] Testes unitários do painel (`extension/src/panel/index.test.tsx`) atualizados e passando
- [ ] Documentação de FREEZE atualizada com status `DESCONGELADO`

---

### #S2-04 — Evidence Cards no Painel da Extensão
**Labels:** `sprint-2` `frontend` `p0` `sp-5` · **Estimativa:** 5 SP · **HU Relacionada:** HU14

**Contexto:**
Vinculado ao Épico 4 e ADR-006. Apresenta ao usuário a relação direta entre cada afirmação feita no vídeo e as checagens jornalísticas brasileiras auditadas correspondentes.

**Descrição Técnica:**
- Criar o componente `extension/src/panel/components/EvidenceCard.tsx` integrado ao Design System do projeto.
- Cada card apresenta: texto da alegação extraída, relação fática (`apoiada`, `contraditada`, `sem evidência`), título da matéria, veículo jornalístico (Lupa, Aos Fatos, Boatos.org, etc.), data de publicação e hiperlink direto com protocolo HTTPS.
- Integração com `UncertaintyAlert.tsx` (HU09) para destacar alegações inconclusivas ou controversas.
- Acessibilidade WCAG 2.1 AA: navegação por teclado (`Tab`, `Shift+Tab`, `Enter`), contraste 4.5:1 e leitor de tela (ARIA roles).

**Critérios de Aceitação:**
- [ ] Componente `EvidenceCard` renderiza corretamente todos os estados de evidência
- [ ] Links externos abrem em nova aba com atributos `target="_blank"` e `rel="noopener noreferrer"`
- [ ] Navegabilidade por teclado testada e funcional
- [ ] Testes unitários em Vitest criados e passando com cobertura > 80%

---

### #S2-05 — Reflection Questions no Painel da Extensão (HU11, HU15)
**Labels:** `sprint-2` `frontend` `backend` `p1` `sp-5` · **Estimativa:** 5 SP · **HU Relacionadas:** HU11, HU15

**Contexto:**
Vinculado ao Épico 6 (Engajamento Reflexivo) e issue aberta #11. A LLM atua formulando perguntas reflexivas para estimular o pensamento crítico de quem assiste, sem ditar o que a pessoa deve pensar.

**Descrição Técnica:**
- No backend: garantir que `generate_reflection(claims, evidence)` gere entre 2 e 4 perguntas instigantes e neutras.
- No frontend: criar componente `ReflectionQuestions.tsx` no painel exibindo as perguntas geradas.
- Mensagem acolhedora persona "Dona Lurdes" (HU02) sem jargões computacionais ou estatísticos.

**Critérios de Aceitação:**
- [ ] Painel exibe seção "Perguntas para Reflexão" com ≥ 3 perguntas abertas e neutras
- [ ] Nenhuma pergunta afirma veredito dogmático
- [ ] Testes unitários do componente cobrem casos com lista vazia e lista completa
- [ ] Issue #11 vinculada e fechada pela entrega

---

### #S2-06 — Failure/Timeout Handling: Modo Evidence-Only e Eliminação de Mocks
**Labels:** `sprint-2` `backend` `frontend` `p0` `sp-3` · **Estimativa:** 3 SP · **HU Relacionada:** HU16

**Contexto:**
Vinculado ao ADR-001 e IS-11. Elimina os fallbacks silenciosos mapeados na Sprint 1 e assegura tratamento resiliente de lentidão ou indisponibilidade da IA.

**Descrição Técnica:**
- Implementar hard timeout de 15s no Service Worker e 8s no backend.
- Em caso de timeout ou indisponibilidade do provider LLM, ativar automaticamente o modo `analysisMode: "evidence_only"`, apresentando as evidências factuais recuperadas diretamente das bases curadas sem gerar alucinações.
- Remover definitivamente do `backend/app/services/fact_checker.py`:
  - Método `_mock_analysis`
  - Heurísticas analíticas regex embutidas (`_extract_check_worthy_claims`)
  - Injeção forçada de fontes estáticas ("src-01", "scielo.br")
- Atualizar o teste `backend/tests/test_no_silent_mock_fallback.py` para passar como `PASSED` (removendo `@pytest.mark.xfail`).

**Critérios de Aceitação:**
- [ ] `test_no_silent_mock_fallback.py` passa sem decorator xfail
- [ ] Falha ou timeout de LLM ativa modo "Evidence-Only" com indicador explícito ao usuário
- [ ] `MockProvider` nunca é acionado quando `LLM_PROVIDER != mock`
- [ ] Nenhum mock de dados é retornado silenciosamente em produção

---

### #S2-07 — Testes de Latência e Performance (P90 ≤ 10s)
**Labels:** `sprint-2` `backend` `p1` `sp-5` · **Estimativa:** 5 SP · **HU Relacionada:** HU03

**Contexto:**
Vinculado ao RNF-01 (Tempo de Resposta) e HU03. Validação contínua do SLA de performance do EvidencIA.

**Descrição Técnica:**
- Criar suíte de testes de latência automatizada (`backend/tests/test_latency.py`).
- Executar benchmark de 20+ requisições concorrentes medindo P50, P90 e P99.
- Critério de performance: P90 ≤ 5s para carregamento das primeiras evidências e P90 ≤ 10s para processamento completo com síntese reflexiva.
- Adicionar verificação de tempo no workflow de CI.

**Critérios de Aceitação:**
- [ ] Script / teste de benchmark executável localmente e em CI
- [ ] Métricas P50, P90 e P99 registradas em relatório de evidência
- [ ] Alerta de falha se P90 > 10s no servidor

---

### #S2-08 — Atualização dos Testes E2E com Playwright
**Labels:** `sprint-2` `frontend` `p1` `sp-5` · **Estimativa:** 5 SP · **HU Relacionadas:** HU01, HU03, HU06

**Contexto:**
Garantir que a suíte completa de testes ponta a ponta (E2E) valide a nova experiência de usuário evidence-first no navegador Chromium com a extensão carregada.

**Descrição Técnica:**
- Atualizar `extension/e2e/hu03.spec.ts` e `extension/e2e/hu06.spec.ts`.
- Validar asserção explícita de que nenhum elemento com classe ou id referente a `.gauge` ou `#score` existe na DOM renderizada.
- Validar renderização dos Evidence Cards, do Uncertainty Alert e das Reflection Questions.
- Validar fluxo de acionamento do botão no player do YouTube até o preenchimento do painel lateral.

**Critérios de Aceitação:**
- [ ] Todos os testes E2E executando com 100% de sucesso via `npm run test:e2e`
- [ ] Testes cobrem: listagem de alegações, cards de evidência, perguntas reflexivas e aviso de ausência de transcrição (HU10)
- [ ] Nenhum erro de renderização ou violação de acessibilidade detectado

---

### #S2-09 — Sprint Review Evidence & Documentação Final do Projeto
**Labels:** `sprint-2` `docs` `p1` `sp-2` · **Estimativa:** 2 SP · **Entrega:** Conclusão do Projeto

**Contexto:**
Consolidação dos artefatos finais de entrega do projeto para a Sprint Review e documentação oficial para a banca/avaliação.

**Descrição Técnica:**
- Preencher `documentation/docs/scrum/sprint-02/review.md` e `retrospective.md`.
- Incluir capturas de tela finais da extensão operando no YouTube com Evidence Cards e Reflection Questions.
- Atualizar o `README.md` principal do repositório com o status final, arquitetura e instruções de instalação da extensão MV3.
- Homologar o fechamento formal dos Épicos #13–#18 e histórias associadas.

**Critérios de Aceitação:**
- [ ] Relatório de Sprint Review publicado com links para todos os PRs entregues
- [ ] Métricas finais de testes e cobertura documentadas (> 80% frontend e backend)
- [ ] Instruções claras e testadas de execução local e empacotamento da extensão
- [ ] Definição de Pronto (DoD) cumprida para 100% das entregas
