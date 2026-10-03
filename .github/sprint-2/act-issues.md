# Rascunhos de Issues para a Sprint 2 — Instrumentacao e Prototipo CBL Act

Este documento reune os rascunhos das issues tecnicas necessarias para viabilizar a execucao experimental da fase CBL Act. Conforme as regras do projeto, estas propostas permanecem aqui documentadas e **nao sao criadas diretamente no GitHub** ate a aprovacao formal da lideranca tecnica.

---

## Issue 1 — Integracao da Telemetria aos Evidence Cards e Reflection Questions (Pos-Unfreeze)

- **Titulo**: `[S2-ACT-01] Integrar Modulo de Telemetria aos Componentes EvidenceCard e ReflectionQuestions`
- **Story Points**: 5 SP
- **Prioridade**: P0 (Bloqueador do Experimento)
- **Labels**: `sprint-2`, `frontend`, `telemetry`, `act`
- **Contexto**: O modulo de telemetria isolado foi entregue em `extension/src/telemetry/`. Para registrar o comportamento real dos participantes na Condicao B durante o experimento, os eventos precisam ser despachados no ciclo de vida e nas interacoes dos novos componentes de UI (`EvidenceCard.tsx` e `ReflectionQuestions.tsx`) apos o descongelamento formal da Sprint 2.
- **Descricao Tecnica**:
  1. No componente `EvidenceCard.tsx`: emitir evento `evidence_expanded` ao clicar para expandir o card de evidencia, informando `claim_ordinal`, `evidence_ordinal` e a relacao semantica (`supports`, `contradicts`, `contextualizes`).
  2. No componente `EvidenceCard.tsx`: emitir `source_opened` quando o link da fonte original for acionado.
  3. No componente `UncertaintyAlert.tsx`: emitir `uncertainty_viewed` ao renderizar sinalizadores de incerteza metodologica.
  4. No componente `ReflectionQuestions.tsx`: emitir `reflection_viewed` ao exibir pergunta e `reflection_interacted` nas acoes de resposta, expansao ou dispensa (`expanded`, `answered`, `dismissed`).
  5. Assegurar que toda emissao passe pelo gate `canEmitTelemetry()` e `validateEvent()`.
- **Criterios de Aceitacao (DoD)**:
  - [ ] Nenhuma chamada de telemetria dispara se `isExperimentMode()` for falso ou se consentimento nao tiver sido concedido.
  - [ ] Interacoes com `EvidenceCard` geram eventos estritamente compativeis com `telemetry-event.schema.json`.
  - [ ] Interacoes com `ReflectionQuestions` geram eventos estritamente compativeis com `telemetry-event.schema.json`.
  - [ ] Testes unitarios cobrindo os disparos de eventos com mocks de `MemorySink` com cobertura >= 85%.

---

## Issue 2 — Prototipo Experimental da Condicao A (Controle com Gauge)

- **Titulo**: `[S2-ACT-02] Prototipo Estatico da Condicao A em experiments/control-gauge-prototype com CI Guard`
- **Story Points**: 5 SP
- **Prioridade**: P0 (Bloqueador do Experimento)
- **Labels**: `sprint-2`, `frontend`, `experiment`, `ci-cd`
- **Contexto**: A Condicao A do experimento requer a apresentacao de gauge e score consolidado de veredito, conforme especificado no `experiment-plan.md` e autorizado como excecao controlada D-008 no `decision-log.md`. Este componente nao pode, sob hipotese alguma, poluir o bundle de producao da extensao.
- **Descricao Tecnica**:
  1. Criar aplicacao estatica isolada no diretorio `experiments/control-gauge-prototype/`.
  2. Renderizar componentes de gauge, score global (0 a 100), rotulo de veredito taxativo e botao "Ver fontes" (colapsado por padrao).
  3. Integrar com fixtures estaticas dos conjuntos S1, S2 e S3 (sem bater em nenhum backend).
  4. Emitir os mesmos eventos de telemetria com campo fixo `cond: "A"`.
  5. Adicionar passo de validacao no workflow de CI (`freeze-guard.yml` ou workflow especifico) que verifique e garanta que nenhum arquivo sob `experiments/` seja empacotado na pasta `dist/` da extensao.
- **Criterios de Aceitacao (DoD)**:
  - [ ] Prototipo funcional operando localmente via servidor estatico leve (ex.: Vite preview ou similar).
  - [ ] O bundle final da extensao (`npm run build`) nao contem nenhum arquivo de `experiments/`.
  - [ ] Teste automatizado de CI falha se qualquer arquivo de `experiments/` for detectado dentro de `dist/`.
  - [ ] Eventos emitidos pela Condicao A passam com 100% de sucesso na validacao de `validateEvent()`.

---

## Issue 3 — Interface Minima do Pesquisador para Exportacao JSONL

- **Titulo**: `[S2-ACT-03] Painel de Administracao Local do Pesquisador para Exportacao de Telemetria`
- **Story Points**: 3 SP
- **Prioridade**: P1
- **Labels**: `sprint-2`, `frontend`, `ux-research`, `telemetry`
- **Contexto**: Para respeitar a politica de zero transmissao por rede, a telemetria do participante e acumulada no `MemorySink`. Ao termino da sessao, o pesquisador precisa salvar o payload JSONL localmente de forma simples e auditavel.
- **Descricao Tecnica**:
  1. Criar componente de overlay ou tela reservada oculta para o facilitador (ex.: atalho de teclado restrito `Ctrl+Shift+E` ou rota `/export` no prototipo).
  2. Exibir resumo da sessao: `pid`, `sid`, quantidade de eventos registrados, quantidade de eventos rejeitados.
  3. Botao "Baixar Sessao (JSONL)": aciona download via Blob com nome padronizado `act_<pid>_<sid8>.jsonl`.
  4. Botao "Limpar Buffer da Sessao" para preparar o proximo participante.
- **Criterios de Aceitacao (DoD)**:
  - [ ] Download manual do arquivo JSONL opera sem conexao com a internet.
  - [ ] Nome do arquivo exportado segue rigorosamente o formato `act_<pid>_<sid8>.jsonl`.
  - [ ] Conteudo do arquivo e 100% compativel com a entrada esperada por `analysis/act/compute_metrics.py`.

---

## Issue 4 — Deliberacao e Politica da Permissao `storage`

- **Titulo**: `[S2-ACT-04] Auditoria e Formalizacao do Uso da Permissao storage no Manifest V3`
- **Story Points**: 2 SP
- **Prioridade**: P1
- **Labels**: `sprint-2`, `architecture`, `security`, `manifest`
- **Contexto**: A permissao `"storage"` ja se encontra declarada no arquivo `extension/manifest.json`. E necessario formalizar tecnicamente se ela sera usada pelo `ChromeStorageSink` como mecanismo de contingencia para sessoes longas ou se o experimento operara estritamente com `MemorySink`.
- **Descricao Tecnica**:
  1. Documentar analise de ameacas (Threat Model) sobre gravacao de telemetria em `chrome.storage.local`.
  2. Implementar politicas de expiracao e autodestruicao local dos dados caso `ChromeStorageSink` seja adotado como fallback.
  3. Obter ratificacao formal do Tech Lead e do Security Auditor sobre a retencao transiente.
- **Criterios de Aceitacao (DoD)**:
  - [ ] Documento de justificativa da permissao `storage` atualizado no `threat-model.md`.
  - [ ] Politica de delecao imediata de dados pos-exportacao implementada.
  - [ ] Decisao registrada no log de arquitetura.

---

## Issue 5 — Preparacao do Ambiente Experimental com Fixtures Congeladas e Mock Rotulado

- **Titulo**: `[S2-ACT-05] Setup de Fixtures de Evidencia Congeladas e Modo Mock Explosito para Testes`
- **Story Points**: 3 SP
- **Prioridade**: P1
- **Labels**: `sprint-2`, `backend`, `dev-environment`, `act`
- **Contexto**: Conforme o `experiment-plan.md`, a realizacao do experimento exige eliminar a variabilidade estocastica de chamadas a provedores de LLM e oscilacoes de latencia de rede, garantindo igualdade estrita de condicoes entre participantes.
- **Descricao Tecnica**:
  1. Montar fixtures de recuperacao factual pre-armazenadas para os itens do conjunto S2.
  2. Configurar o provider de IA para operar em modo `analysisMode="mock"` no ambiente do experimento.
  3. Garantir que a sinalizacao visual de modo de teste esteja visivel no console de desenvolvimento, mas sem poluir a UX do participante.
  4. Garantir que `analysisMode="mock"` seja estritamente bloqueado em builds de producao (`vite build --mode production`).
- **Criterios de Aceitacao (DoD)**:
  - [ ] Todas as chamadas para os itens S2 retornam respostas congeladas identicas em tempo <= 200 ms.
  - [ ] Nenhuma chamada externa a APIs pagas ou redes externas e disparada durante a sessao de teste.
  - [ ] O build de producao contem guard que impede a ativacao do modo mock.
