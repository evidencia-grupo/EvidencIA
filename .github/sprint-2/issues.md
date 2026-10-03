# Sprint 2 — Checklist de Issues & Execução Operacional

> **Milestone:** Sprint 2  
> **Objetivo:** Converter os resultados da investigação da Sprint 1 em um pipeline de evidências e uma UX que preserve o pensamento crítico (Evidence-First), eliminando a dependência estrutural do Ollama local e removendo em definitivo o score global e velocímetros da extensão.  
> **Total de Story Points:** 39 SP (9 issues oficiais)  
> **Referência Arquitetural:** [ADR-006 (Evidence-First Architecture)](../../documentation/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md) · [KANBAN.md](../../KANBAN.md)

---

## 1. Panorama de Progresso (Transição Sprint 1 → Sprint 2)

### Sprint 1 — Concluída e Integrada via PR #31 (`27c53e8`)
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
- [x] **Clean-up:** Diretório `scripts/` removido com sucesso.

---

## 2. Matriz de Atribuição da Equipe na Sprint 2 (Alinhada ao Kanban)

| Issue | HU / ID | Título da História / Atividade | Épico | Responsável Principal | Co-responsável | Prioridade MoSCoW | SP |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|
| [#32](https://github.com/evidencia-grupo/EvidencIA/issues/32) | **HU16** | Provider Abstraction: Migração de OllamaProvider e RemoteLLMProvider | `epic:e3-ia-checagem` | @pedrohpsantos | — | `must-have` / `mvp:onda-1` | 5 |
| [#33](https://github.com/evidencia-grupo/EvidencIA/issues/33) | **HU13** | Evidence-First Schema: Migração de Contratos e Eliminação do Score Global | `epic:e3-ia-checagem` | @pedrohpsantos | @mahiaara | `must-have` / `mvp:onda-1` | 5 |
| [#34](https://github.com/evidencia-grupo/EvidencIA/issues/34) | **HU02** | Descongelamento Formal e Remoção do Score Global da UI | `epic:e3-ia-checagem` | @MylenaTrindade | — | `must-have` / `mvp:onda-1` | 3 |
| [#35](https://github.com/evidencia-grupo/EvidencIA/issues/35) | **HU14** | Evidence Cards no Painel da Extensão | `epic:e4-confianca-fontes` | @MylenaTrindade | @luizoryone | `must-have` / `mvp:onda-1` | 5 |
| [#36](https://github.com/evidencia-grupo/EvidencIA/issues/36) | **HU15** | Reflection Questions no Painel da Extensão | `epic:e6-engajamento` | @mahiaara | @MylenaTrindade | `must-have` / `mvp:onda-1` | 5 |
| [#37](https://github.com/evidencia-grupo/EvidencIA/issues/37) | **HU16** | Failure/Timeout Handling: Modo Evidence-Only e Eliminação de Mocks | `epic:e3-ia-checagem` | @pedrohpsantos | @lipestile | `must-have` / `mvp:onda-1` | 3 |
| [#38](https://github.com/evidencia-grupo/EvidencIA/issues/38) | **HU03** | Testes de Latência e Performance (P90 <= 10s) | `epic:e5-performance-cache` | @lipestile | — | `must-have` / `mvp:onda-1` | 5 |
| [#39](https://github.com/evidencia-grupo/EvidencIA/issues/39) | **QA-E2E** | Testes E2E com Playwright para o Fluxo Evidence-First | `epic:e5-performance-cache` | @luizoryone | @lipestile | `must-have` / `mvp:onda-1` | 5 |
| [#40](https://github.com/evidencia-grupo/EvidencIA/issues/40) | **REL-01** | Sprint Review Evidence & Documentação Final do Projeto | `epic:e6-engajamento` | @mahiaara | @pedrohpsantos | `must-have` / `mvp:onda-1` | 3 |
| **Total** | | | | | | | **39 SP** |

---

## 3. Especificação Completa das Issues (Gherkin & Rastreabilidade)

### [#32] [HU16] Provider Abstraction: Migração de OllamaProvider e RemoteLLMProvider
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsável:** @pedrohpsantos
- **Story Points:** 5

#### Declaração de Valor
> **Como** Equipe de Engenharia / Sistema  
> **Pretendo** utilizar diferentes provedores de LLM por meio de uma interface comum  
> **Para que** não dependa estruturalmente do Ollama local e possamos alternar entre inferência local e remota sem alterar código de negócio.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-14, RF-15, RNF-06, ADR-006 (Decisão 6)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Provedor de IA independente

  Cenário: Troca de provedor por configuração
    Dado que a variável de ambiente LLM_PROVIDER é alterada de "ollama" para "remote"
    Quando o serviço de backend intermediário é iniciado
    Então as inferências de extração e reflexão devem ser direcionadas ao provedor remoto sem qualquer alteração no código de negócio

  Cenário: Uso de Ollama local com Qwen 2.5-3B
    Dado que LLM_PROVIDER está configurado como "ollama"
    Quando o backend processa uma requisição de extração de alegações
    Então a inferência deve ser executada localmente via OllamaProvider consumindo o modelo configurado

  Cenário: Bloqueio estrito de mock em produção
    Dado que o sistema está em execução com ENV=production
    Quando há qualquer tentativa de configurar LLM_PROVIDER=mock
    Então o sistema deve abortar a inicialização imediatamente com código de erro e registrar evento no log de auditoria
```

#### Checklist de Implementação
- [ ] Conectar `FactCheckerService` ao `get_provider()` de `backend/app/services/providers/factory.py`
- [ ] Implementar `OllamaProvider.extract_claims` e `OllamaProvider.generate_reflection` em `backend/app/services/providers/ollama.py`
- [ ] Implementar `RemoteLLMProvider` em `backend/app/services/providers/remote.py` compatível com endpoints OpenAI/vLLM
- [ ] Desacoplar `fact_checker.py` da importação direta de `ollama_service`
- [ ] Validar que `test_provider_contract.py` passa 100% offline sem falhas

---

### [#33] [HU13] Evidence-First Schema: Migração de Contratos e Eliminação do Score Global
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @pedrohpsantos, @mahiaara
- **Story Points:** 5

#### Declaração de Valor
> **Como** Amanda (Consumidora Crítica de Conteúdo)  
> **Pretendo** visualizar as principais alegações verificáveis do vídeo separadamente com suas respectivas evidências  
> **Para que** eu investigue cada uma delas sem ser influenciada por uma classificação global ou porcentagem artificial de veracidade.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-06, RF-07, RNF-07, ADR-006 (Decisões 1 e 2)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Investigação orientada por alegações e contratos evidence-first

  Cenário: Resposta do backend sem score global
    Dado que uma requisição POST para /analyze é enviada com a transcrição do vídeo
    Quando o backend processa a checagem com sucesso
    Então a resposta AnalyzeResponse deve conter a lista claims[] e o objeto reflection_questions
    E os campos score e FactCheckingSource.reliabilityScore não devem ser emitidos

  Cenário: Relação explícita em cada evidência associada à alegação
    Dado que uma alegação verificável foi identificada
    Quando suas evidências são retornadas pelo backend
    Então cada evidência deve possuir a relação explícita ("supports", "contradicts" ou "contextualizes")
    E conter title, url, publisher e published_date válidos

  Cenário: Desserialização compatível no cliente TypeScript
    Dado que a extensão recebe a resposta AnalyzeResponse atualizada
    Quando os tipos em shared/types.ts são consumidos
    Então nenhuma incompatibilidade de tipo deve ocorrer durante a compilação ou execução
```

#### Checklist de Implementação
- [ ] Atualizar schema `backend/app/schemas/` para remover `score` e `reliabilityScore`
- [ ] Estruturar `claims[]` com modelo `Claim` contendo `id`, `text`, `evidence[]`, e `category`
- [ ] Atualizar `shared/types.ts` e `extension/` para os contratos estritos de `Evidence` e `Claim`
- [ ] Atualizar testes em `backend/tests/` para refletir o schema evidence-first

---

### [#34] [HU02] Descongelamento Formal e Remoção do Score Global da UI
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsável:** @MylenaTrindade
- **Story Points:** 3

#### Declaração de Valor
> **Como** Dona Lurdes (Consumidora de receitas e dicas caseiras de saúde)  
> **Pretendo** visualizar uma síntese objetiva e clara sem indicadores confusos de porcentagem ou velocímetros  
> **Para que** eu compreenda o que tem evidências e o que não tem sem risco de interpretar mal um número simplista.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F2.3 — Síntese Visual e Acessibilidade WCAG`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-03, RF-06, RNF-07, ADR-006 (Decisão 1)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Remoção de scores globais e velocímetros da interface

  Cenário: Renderização do painel lateral sem score gráfico
    Dado que o usuário aciona a verificação de um vídeo no YouTube
    Quando o painel lateral é renderizado com os resultados
    Então nenhum velocímetro gráfico (gauge), medidor numérico ou porcentagem global deve aparecer na tela
    E a lista atômica de alegações deve ocupar o destaque principal

  Cenário: Remoção segura dos arquivos de score congelados
    Dado que a Sprint 2 formalizou a eliminação do score global
    Quando os componentes legados são removidos
    Então o build de produção da extensão deve compilar com zero erros de TypeScript e zero avisos de dependência órfã
```

#### Checklist de Implementação
- [ ] Descongelar e remover componentes de score/gauge em `extension/src/components/`
- [ ] Atualizar `extension/src/components/Panel.tsx` para renderizar direto a lista de alegações
- [ ] Validar conformidade de contraste e acessibilidade WCAG 2.1 AA
- [ ] Executar build da extensão sem warnings ou erros de linting

---

### [#35] [HU14] Evidence Cards no Painel da Extensão
- **Labels:** `epic:e4-confianca-fontes`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @MylenaTrindade, @luizoryone
- **Story Points:** 5

#### Declaração de Valor
> **Como** Mayara (Jornalista investigativa e checadora de fatos)  
> **Pretendo** ver quais fontes sustentam, contradizem ou contextualizam cada alegação em cartões dedicados  
> **Para que** eu e qualquer espectador possamos auditar a origem das informações de forma autônoma e imediata.

#### Rastreabilidade
- **Épico:** `E4 — Confiança e Fontes`
- **Feature:** `F2.2 — Auditoria de Fontes e Transparência Editorial`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-04, RF-13, RNF-05, ADR-006 (Decisões 2 e 5)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Evidence cards no painel da extensão

  Cenário: Exibição completa de atributos de evidência
    Dado que uma alegação possui evidências recuperadas de corpora verificados
    Quando o usuário visualiza o cartão de evidência
    Então título, URL, data de publicação, publisher e a relação factual devem estar explicitamente visíveis

  Cenário: Destaque visual por tipo de relação
    Dado que uma fonte contradiz a afirmação realizada no vídeo
    Quando o cartão dessa evidência é apresentado
    Então o indicador de relação "Contradiz" deve ser exibido com destaque e acompanhado do trecho factual correspondente

  Cenário: Consulta à fonte externa em nova aba
    Dado que o usuário clica no link da fonte jornalística
    Quando a navegação é disparada
    Então a página da fonte deve abrir em uma nova aba com rel="noopener noreferrer"
    E a reprodução do vídeo do YouTube não deve ser interrompida
```

#### Checklist de Implementação
- [ ] Criar componente `EvidenceCard` em `extension/src/components/EvidenceCard.tsx`
- [ ] Exibir título, publisher, data de publicação, relação (`supports`, `contradicts`, `contextualizes`) e trecho
- [ ] Garantir abertura segura com `target="_blank"` e `rel="noopener noreferrer"`
- [ ] Adicionar suporte a estados expansíveis/colapsáveis por alegação com suporte a leitor de tela

---

### [#36] [HU15] Reflection Questions no Painel da Extensão
- **Labels:** `epic:e6-engajamento`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @mahiaara, @MylenaTrindade
- **Story Points:** 5

#### Declaração de Valor
> **Como** Helena (Professora do ensino médio)  
> **Pretendo** receber perguntas que me ajudem a avaliar a alegação por conta própria antes de formar uma conclusão  
> **Para que** eu estimule o pensamento crítico e a autonomia investigativa sem aceitar vereditos dogmáticos da IA.

#### Rastreabilidade
- **Épico:** `E6 — Engajamento Reflexivo (Promovido para MVP)`
- **Feature:** `F3.1 — Estímulo ao Pensamento Crítico`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-05, RNF-07, ADR-006 (Decisão 7)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Reflection questions no painel da extensão

  Cenário: Formulação de no mínimo 3 perguntas reflexivas
    Dado que a investigação de um vídeo foi concluída
    Quando o componente de perguntas reflexivas é exibido
    Então pelo menos 3 perguntas neutras orientadas à investigação pessoal devem ser apresentadas

  Cenário: Garantia de neutralidade nas perguntas geradas
    Dado que o assistente de IA formula as perguntas de reflexão
    Quando o texto é gerado
    Então nenhuma pergunta deve declarar se o vídeo está "certo" ou "errado", mantendo postura investigativa aberta

  Cenário: Fechamento ou omissão do bloco sem bloqueio
    Dado que o usuário não deseja interagir com as perguntas reflexivas
    Quando ele recolhe ou ignora a seção
    Então a navegação e a leitura das demais evidências devem seguir normalmente, sem bloqueios
```

#### Checklist de Implementação
- [ ] Integrar geração de perguntas reflexivas no pipeline da LLM (`generate_reflection`)
- [ ] Criar componente `ReflectionQuestions` no painel da extensão
- [ ] Garantir neutralidade e ausência de viés ideológico nos prompts
- [ ] Assegurar foco e navegabilidade por teclado (WCAG 2.1 AA)

---

### [#37] [HU16] Failure/Timeout Handling: Modo Evidence-Only e Eliminação de Mocks
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @pedrohpsantos, @lipestile
- **Story Points:** 3

#### Declaração de Valor
> **Como** Dona Lurdes (Consumidora de Notícias) e Equipe de Engenharia  
> **Pretendo** receber as evidências factuais recuperadas mesmo se o modelo de linguagem falhar ou demorar  
> **Para que** eu nunca fique sem informação útil e o sistema nunca exiba dados simulados (mocks) em produção.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RF-14, RNF-06, ADR-006 (Decisão 6)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Degradação graciosa para modo Evidence-Only e eliminação de mocks

  Cenário: Provedor de LLM com timeout ou indisponível
    Dado que o provedor de LLM falha ou excede o timeout de 15 segundos
    Quando a requisição /analyze é processada
    Então o sistema deve retornar as evidências jornalísticas recuperadas no modo "evidence_only"
    E a flag evidence_only=true deve ser enviada para a extensão

  Cenário: Feedback visual claro no painel da extensão
    Dado que a extensão recebe resposta com evidence_only=true
    Quando o painel lateral é renderizado
    Então um aviso amigável deve informar que a síntese de linguagem está temporariamente indisponível
    E os cartões de evidências recuperados devem ser exibidos normalmente

  Cenário: Tentativa de uso de mock em produção
    Dado que o ambiente de execução é ENV=production
    Quando há qualquer tentativa de carregar o MockLLMProvider ou dados simulados
    Então a aplicação deve abortar imediatamente com erro e impedir a resposta com dados fictícios
```

#### Checklist de Implementação
- [ ] Implementar timeout de 15s com fallback para `evidence_only=True` em `FactCheckerService`
- [ ] Validar guard rail de bloqueio de mock em `backend/app/services/providers/factory.py` para `ENV=production`
- [ ] Adicionar banner de aviso no painel Preact quando `evidence_only: true`
- [ ] Testes unitários cobrindo timeout de LLM e retorno exclusivo de evidências

---

### [#38] [HU03] Testes de Latência e Performance (P90 <= 10s)
- **Labels:** `epic:e5-performance-cache`, `must-have`, `mvp:onda-1`
- **Responsável:** @lipestile
- **Story Points:** 5

#### Declaração de Valor
> **Como** Carlos (Estudante universitário com conexão móvel)  
> **Pretendo** que a checagem completa do vídeo seja concluída em menos de 10 segundos no percentil 90  
> **Para que** eu não desista da checagem nem sofra com lentidão enquanto assisto a vídeos no YouTube.

#### Rastreabilidade
- **Épico:** `E5 — Performance e Cache`
- **Feature:** `F1.3 — Cache Local e Otimização de SLA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
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

#### Checklist de Implementação
- [ ] Criar benchmark automatizado em `backend/tests/test_performance_sla.py`
- [ ] Medir latência do embedding Qwen2.5 / Chroma local vs busca
- [ ] Validar comportamento do cache `chrome.storage.local` com TTL de 24h
- [ ] Documentar resultados de latência P50, P90 e P99 para a entrega final

---

### [#39] [QA-E2E] Testes E2E com Playwright para o Fluxo Evidence-First
- **Labels:** `epic:e5-performance-cache`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @luizoryone, @lipestile
- **Story Points:** 5

#### Declaração de Valor
> **Como** Equipe de Engenharia & Qualidade  
> **Pretendo** validar o fluxo completo da extensão em um navegador Chromium real via Playwright  
> **Para que** tenhamos garantia de que a injeção no player, captura de legendas, comunicação com backend e renderização do painel funcionam de ponta a ponta sem regressão.

#### Rastreabilidade
- **Épico:** `E5 — Performance e Cache`
- **Feature:** `F1.1 / F1.3 — Ingestão, Interceptação e Validação Ponta a Ponta`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
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

#### Checklist de Implementação
- [ ] Atualizar suíte Playwright em `extension/tests/e2e/` ou `tests/e2e/`
- [ ] Validar injeção do botão no DOM do YouTube sem interferir no player nativo
- [ ] Testar renderização dos `EvidenceCard` e `ReflectionQuestions`
- [ ] Integrar execução dos testes E2E no GitHub Actions CI

---

### [#40] [REL-01] Sprint Review Evidence & Documentação Final do Projeto
- **Labels:** `epic:e6-engajamento`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @mahiaara, @pedrohpsantos
- **Story Points:** 3

#### Declaração de Valor
> **Como** Toda a Equipe / Avaliadores e Stakeholders  
> **Pretendo** consolidar todas as evidências de teste, métricas de qualidade, benchmarks e documentação do projeto  
> **Para que** o projeto EvidencIA atinja o Definition of Done (DoD) completo e esteja pronto para release e apresentação final.

#### Rastreabilidade
- **Épico:** `E6 — Engajamento Reflexivo (Promovido para MVP)`
- **Feature:** `F3.2 — Fechamento do Projeto, Auditoria e Documentação Final`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Requisitos Vinculados:** RNF-05, RNF-07, DoD do Projeto

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Evidências da Sprint Review e consolidação da entrega final

  Cenário: Validação do Definition of Done (DoD) completo
    Dado que todas as histórias da Sprint 1 e Sprint 2 foram desenvolvidas
    Quando a esteira de validação final é executada
    Então 100% dos testes unitários e de integração devem passar sem erros
    E a cobertura de testes deve ser igual ou superior a 80%
    E zero vulnerabilidades críticas ou altas devem ser apontadas pelo SAST

  Cenário: Documentação e tag de release
    Dado que os critérios de qualidade foram homologados
    Quando a tag v1.0.0-mvp é gerada
    Então o changelog, manual de instalação e matriz de rastreabilidade devem estar perfeitamente sincronizados
```

#### Checklist de Implementação
- [ ] Atualizar catálogo de requisitos e matriz de rastreabilidade em `documentation/docs/`
- [ ] Consolidar relatórios de cobertura de testes (>= 80%) e SAST (pip-audit / npm audit)
- [ ] Documentar o fluxo de demonstração da Sprint Review e gravação do screencast
- [ ] Gerar tag `v1.0.0-mvp` e release notes no repositório

---

## 4. Critérios Transversais e Guard Rails da Sprint 2

1. **Evidence-First Estrito:**
   - Nenhum score global (0-100), medidor gráfico (gauge) ou porcentagem de veracidade deve existir na extensão após a conclusão de #34 (HU02).
   - Alegações sem evidências retornam neutras com a relação `contextualizes` ou `unverified`, nunca convertidas automaticamente em `falso` ou `contradicted`.

2. **Blindagem de Produção (Anti-Mock Guard):**
   - MockLLMProvider só é permitido em `ENV=development` ou `ENV=test`. Qualquer tentativa de execução com `ENV=production` deve abortar imediatamente.
   - Degradação de rede ou timeout de LLM (>= 15s) entra em modo `evidence_only: true`.

3. **Performance & SLAs:**
   - Latência no P90 <= 10s para checagens a frio.
   - Recuperação local via `chrome.storage.local` <= 500ms (TTL 24h).
   - Total Blocking Time (TBT) no player <= 50ms.

4. **Acessibilidade & Usabilidade:**
   - Contraste e tipografia aderentes a WCAG 2.1 AA.
   - Navegabilidade total por teclado e suporte a leitores de tela em todos os cartões de evidência e perguntas de reflexão.
