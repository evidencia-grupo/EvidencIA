## Identificação da Mudança

- **Issue Relacionada:** Refs #6 (manter aberta até homologação em produção com IA própria).
- **História de Usuário / Tarefa:** HU06 — Consulta Imediata via Cache Local.
- **Tipo de Alteração:**
  - [x] Nova Funcionalidade (Feature)
  - [ ] Correção de Falha (Bugfix)
  - [x] Refatoração de Código (Refactor)
  - [x] Otimização de Performance (Perf)
  - [x] Ajuste de Documentação ou Governança (Docs)

---

## Descrição Técnica

Implementa a arquitetura de persistência e recuperação instantânea de checagens factuais via `chrome.storage.local` conforme estipulado na **ADR-003** e nos requisitos de desempenho **RNF-01** e **RNF-05**:

1. **Módulo Especializado (`cache-manager.ts`):** Centraliza a validação rigorosa (`isValidCacheEntry`), consulta resiliente (`getCachedResult`) e persistência segura (`saveCachedResult`).
2. **Validação de Integridade e Contrato:** Verifica correspondência exata de `videoId`, presença de timestamp numérico positivo e não futuro, TTL de 24 horas (`86.400.000 ms`), idade estritamente inferior ao TTL e validação estrutural do contrato `AnalyzeResponse` (`isAnalysis`).
3. **Lazy Eviction Determinística:** Registros com idade $\ge 24\text{h}$, corrompidos ou com identificador divergente são descartados e removidos do storage sob demanda, disparando automaticamente uma nova análise completa sem intervenção manual.
4. **Otimização de Tráfego e Processamento:** Em caso de cache válido, o resultado é renderizado no iframe do painel sem nenhuma chamada ao backend proxy nem reextração de legendas do player, alcançando latência de **~18ms a 42ms** no Chromium (abaixo da meta estrita de $100\text{ms}$ da ADR-003 e do critério obrigatório de $< 1\text{s}$).
5. **Resiliência a Falhas de I/O:** Falhas na leitura do storage degradam graciosamente para a análise externa; falhas na gravação ou cota de storage não impedem a entrega do resultado ao usuário. Falhas na extração de legendas ou requisições HTTP com erro nunca são salvas como sucesso.
6. **Governança e Privacidade:** O armazenamento restringe-se exclusivamente aos dados da análise factual. Não há persistência de histórico geral de navegação, cookies, credenciais ou logs com transcrições.
7. **Identificação de Demonstração Mantida:** Preserva integralmente o campo `analysisMode` e os avisos visuais de que os dados atuais provêm de mock e simulação, enquanto a IA própria da equipe está em preparação.

---

## Rastreabilidade e Conformidade

- **Épico / Feature:** Épico E5 — Performance e Cache / Feature F1.3 — Cache Local e Otimização de Rede.
- **Requisitos Vinculados:** RF-09 (Exibição de síntese e classificação), RNF-01 (Latência $< 1\text{s}$ no cache), RNF-05 (Eficiência e retenção restrita).
- **Decisão Arquitetural Relacionada:** ADR-003 (Cache local de 24 horas via `chrome.storage.local`), alinhada com ADR-001 (Isolamento MV3) e ADR-002 (Backend Proxy).
- **Dependência de Branch:** Esta branch (`feat/hu06-cache-local`) foi baseada na branch `feat/hu03-checagem-rapida` (HU03), que introduziu o pipeline básico de UI e mensageria MV3. A HU03 já foi integrada à main pelo PR #19.

---

## Checklist de Qualidade (Definition of Done)

- [x] Código compilado e tipado sem erros (`npm run typecheck` estrito e Ruff aprovado).
- [x] Testes unitários implementados e executando com 100% de sucesso (97 testes na extensão, 10 testes no backend).
- [x] Cobertura de testes unitários superior a 80% nos módulos modificados (`cache-manager.ts` com 100%; extensão total com 99,76% de linhas; backend com 97,62% de branches).
- [x] Nenhum segredo, chave de API ou credencial privada incluída no commit.
- [x] Navegabilidade por teclado e acessibilidade mantidas sem regressão.
- [x] Validação E2E com 12 cenários Playwright em Chromium real aprovados.
- [x] Latência de cache validada em menos de 100ms (RNF-01 e ADR-003) e sem sobrecarga de Long Tasks (TBT = 0ms).
- [x] Mensagens de commit seguem a convenção Conventional Commits (`feat(hu06): ...`).
- [ ] Homologação factual em produção com IA própria (dependência externa anotada).

---

## Validação e Limites

- **Testes Unitários:** 97 testes Vitest na extensão e 10 testes Pytest no backend.
- **Testes E2E (Playwright no Chromium):** 12 cenários cobrindo cache hit instantâneo, persistência pós-reload (`page.reload()`), lazy eviction de registro com 24h exatas, descarte de timestamp futuro / payload divergente, proteção contra gravação de erros e resiliência a falhas de I/O.
- **Métricas:** Latência de renderização no cache hit medida entre 18ms e 42ms. Zero requisições de rede ou extrações de legenda disparadas no cache hit.
- **Limitações:** A suíte utiliza dados mock/controlados e perfil Chromium descartável. A integração com IA própria e a validação em ambiente real de produção dependem de etapas subsequentes da equipe.
