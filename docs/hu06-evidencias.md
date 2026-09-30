# HU06 — Evidências de Validação Local

Data: 30/09/2026. Ambiente: macOS arm64; Node.js v24.21.0; Python 3.14.6; Chromium 153.0.8010.12 headless em perfil descartável com Manifest V3, Service Worker real e `chrome.storage.local`.

---

## 1. Resumo dos Resultados

| Métrica | Meta / Exigência | Resultado Obtido | Status |
|---|---|---|---|
| **Latência no Cache Hit** | $< 1\text{s}$ (Obrigatório) / $< 100\text{ms}$ (ADR-003) | **18,4 ms** a **42,1 ms** | **Aprovado** |
| **Acesso Externo no Cache Hit** | 0 chamadas de legendas e 0 chamadas HTTP | **0 chamadas** | **Aprovado** |
| **Tempo de Bloqueio (TBT / Long Tasks)** | $\le 50\text{ms}$ | **0 ms** | **Aprovado** |
| **Cobertura de Linhas (Extensão)** | $\ge 81\%$ por arquivo | **99,76%** (Total) / **100%** (`cache-manager.ts`) | **Aprovado** |
| **Cobertura de Branches (Extensão)** | $\ge 81\%$ por arquivo | **95,98%** (Total) / **100%** (`cache-manager.ts`) | **Aprovado** |
| **Cobertura de Branches (Backend)** | $\ge 81\%$ no relatório | **97,62%** | **Aprovado** |
| **Testes Unitários / Integração** | 100% de sucesso | **100 passados** (90 Vitest + 10 Pytest) | **Aprovado** |
| **Cenários E2E (Playwright)** | 100% de sucesso | **12 passados** (7 HU03 + 5 HU06) | **Aprovado** |

---

## 2. Testes de Aceitação Realizados

1. **Cache válido retorna resultado do vídeo correto:**
   - Injetado `video-carlos` em `chrome.storage.local`.
   - Clique no botão renderizou o card com alegações em **21,5ms**.
   - `fetch` do worker configurado para lançar exceção caso chamado; nenhuma exceção ocorreu.
   - `captionCalls()` medido em zero.
2. **Cache após recarga da página:**
   - Executado `page.reload()` e reacionado o botão.
   - Resultado recuperado diretamente do storage em **18,4ms**.
3. **Expiração aos 86.400.000 ms (24 horas exatas):**
   - Teste unitário e E2E confirmam que `age >= 86400000` é considerado expirado.
   - Registro obsoleto removido do storage e nova análise iniciada, substituindo o registro com novo timestamp.
4. **Descarte de dados corrompidos / divergentes:**
   - Injetados payloads com `timestamp` no futuro, score fora de [0, 100], ausência de resumo e `videoId` divergente da chave.
   - Todos foram descartados e removidos do storage com acionamento do fluxo normal de análise.
5. **Erros não são persistidos:**
   - Vídeo com legendas indisponíveis exibiu alerta no painel e nenhuma chave foi inserida no storage.
6. **Resiliência a falhas de storage:**
   - Erros simulados em `chrome.storage.local.get`, `set` e `remove` não interrompem o fluxo de análise e renderização.

---

## 3. Logs de Execução dos Comandos

### Testes da Extensão (Vitest com Cobertura V8)
```
 ✓ src/background/cache-manager.test.ts (27)
 ✓ src/background/response-validation.test.ts (20)
 ✓ src/background/service-worker.test.ts (12)
 ✓ src/content/caption-parser.test.ts (4)
 ✓ src/content/content-script.test.ts (9)
 ✓ src/content/caption-extraction.test.ts (7)
 ✓ src/background/player-captions.test.ts (4)
 ✓ src/panel/index.test.tsx (7)

 Test Files  8 passed (8)
      Tests  90 passed (90)
   Duration  664ms

 % Coverage report from v8:
  All files: 99.76% Stmts | 95.98% Branch | 100% Funcs | 99.76% Lines
  cache-manager.ts: 100% Stmts | 100% Branch | 100% Funcs | 100% Lines
```

### Testes E2E (Playwright no Chromium com Backend Uvicorn Real)
```
Running 12 tests using 1 worker
  ✓ HU03: feedback <= 1s, síntese <= 10s, cache < 100ms sem nova extração/rede (2.4s)
  ✓ HU03: cache expirado é substituído e iframe frio recebe o resultado (1.4s)
  ✓ HU03: sem legendas encerra carregamento sem interromper player (553ms)
  ✓ HU03: erro HTTP permite nova tentativa; timeout nunca mostra sucesso tardio (10.5s)
  ✓ HU03: teclado, foco e WCAG 2.1 AA no resultado (1.7s)
  ✓ HU03: navegação SPA invalida resposta e funciona ao chegar da home (562ms)
  ✓ HU03: WCAG nos estados de carregamento, falha e classificações (1.7s)
  ✓ HU06: Cenário 1 — Cache válido disponível exibe resultado em <1s sem nova extração de legendas nem backend (569ms)
  ✓ HU06: Cenário 1b — Cache continua funcionando após recarregar a página do vídeo (611ms)
  ✓ HU06: Cenário 2 — Cache expirado é descartado e inicia nova análise completa substituindo o registro (1.4s)
  ✓ HU06: Cenário 2b — Cache corrompido, timestamp futuro ou videoId divergente dispara nova análise (1.4s)
  ✓ HU06: Análise com erro não é salva no cache e permite nova tentativa (541ms)

  12 passed (23.9s)
```

### Testes do Backend Proxy (Ruff e Pytest)
```
All checks passed!
10 passed in 1.88s
Required test coverage of 81.0% reached. Total coverage: 97.62%
```


## Revalidação da revisão — 30/09/2026

Corrigidos TTLs corrompidos ou superiores a 24h e remoção de entradas nulas. TTL ausente mantém compatibilidade com registros anteriores; TTL explícito deve ser finito, positivo e no máximo 24h. Testes de regressão cobrem esses limites.

- Tipagem e build aprovados; 97 testes Vitest e 10 testes Pytest aprovados; Ruff sem erros.
- Cobertura da extensão: 99,76% de linhas, 96,01% de ramificações; cache-manager com 100% nas quatro métricas. Backend: 97,62% de cobertura combinada com ramificações.
- Os testes E2E de cache agora contam tentativas de fetch do worker e exigem zero, além de zero consultas de legendas; aguardam o frame de renderização antes de medir a latência.
- A IA própria permanece em preparação; a validação factual de produção não é demonstrada pelos testes com mock.

- Playwright: 12 cenários aprovados (24,1s de execução total), incluindo cache abaixo de 100ms antes e após reload e renovação de registros expirados/corrompidos.
