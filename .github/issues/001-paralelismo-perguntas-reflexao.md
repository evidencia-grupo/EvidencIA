---
title: "[PERF]: Pipeline de Paralelismo Assíncrono e Otimização de Latência das Perguntas de Reflexão"
labels: ["performance", "backend", "llm", "enhancement"]
assignees: ""
---

### Problema ou Oportunidade
Atualmente, as perguntas de reflexão orientadas por evidências são geradas iterando em sequência sobre cada alegação extraída (`for p_claim in provider_claims`). Em vídeos com 3 a 5 alegações e utilizando modelos de linguagem gratuitos ou locais (OpenRouter, Groq, Ollama), a latência acumulada ($N \times T$) ultrapassa facilmente o limite estrito de 15 segundos (`LLM_TIMEOUT_SECONDS=15.0`). Isso aciona o timeout da requisição ou degrada desnecessariamente a resposta inteira para o modo `evidence_only`.

### Solução Proposta
1. **Execução Concorrente via `asyncio.gather`**:
   - Paralelizar as requisições de geração de perguntas de reflexão de todas as alegações, reduzindo o tempo total para aproximadamente $\max(T_i)$ (~2 a 4 segundos).
2. **Fallback Atômico por Alegação**:
   - Se a reflexão falhar ou sofrer timeout para uma alegação individual, apenas ela assume o catálogo padronizado de fallback (`REFLECTION_QUESTIONS`), sem comprometer as demais alegações nem descartar evidências factuais já recuperadas.
3. **Controle de Concorrência**:
   - Utilizar semáforo assíncrono (`asyncio.Semaphore(3)`) para respeitar limites de taxa (rate limits) de provedores de IA gratuitos.

### Critérios de Aceitação
- [x] O tempo total da etapa de reflexão para 4 alegações não ultrapassa 4 segundos em ambiente local/mock e permanece inferior a 8 segundos em provedor remoto.
- [x] Falhas de timeout em alegações isoladas não cancelam as evidências recuperadas de outras alegações.
- [x] 100% dos testes unitários e de integração de timeout e orçamento compartilhado passam sem regressão.

### Rastreabilidade
- **Épico Relacionado:** [Épico 3 — Análise e Checagem via IA](documentation/docs/requisitos/backlog-e-historias.md#epico-3-analise-e-checagem-via-ia), [Épico 5 — Performance e Cache](documentation/docs/requisitos/backlog-e-historias.md#epico-5-performance-e-cache)
- **Requisitos Vinculados:** RF-02, RF-14, RNF-01, RNF-06
- **ADR de Referência:** ADR-001, ADR-006
