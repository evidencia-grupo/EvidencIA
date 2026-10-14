---
title: "[FEAT]: Calibração Semântica do Matcher e Contexto Anti-Alucinação para Modelos Gratuitos"
labels: ["enhancement", "search", "fact-checking", "rag"]
assignees: ""
---

### Problema ou Oportunidade
No `BrazilianFactMatcher`, termos isolados de alta frequência como "saúde" ou "vacina" adicionavam um bônus de pontuação que permitia que frases genéricas ou saudações atingissem o limiar mínimo de 0.30, resultando em falsos positivos (por exemplo, associar a saudação *"Tá começando o seu programa de saúde..."* a uma checagem factual não relacionada e classificá-la como *"Contextualizada (Com ressalvas)"*). Além disso, modelos remotos gratuitos necessitam de delimitação estrita de formato e contexto para evitar que alucinem fontes ou inventem vereditos arbitrários.

### Solução Proposta
1. **Calibração do Limiar de Correspondência Factual**:
   - Bloquear imediatamente correspondências em frases identificadas como ruído conversacional (`is_conversational_filler`).
   - Exigir sobreposição mínima de múltiplos termos substantivos conceituais (sujeito + verbo + predicado) antes de conceder bônus de domínio.
2. **Engenharia de Prompt com Delimitação Rígida**:
   - Orientar os provedores remotos (`RemoteLLMProvider` e `OllamaProvider`) a extrair exclusivamente frases atômicas curtas (máximo 25 palavras ou 180 caracteres) sobre o tema central.
   - Proibir explicitamente a cópia de parágrafos extensos de legendas ASR e a atribuição de vereditos dogmáticos ao vídeo.

### Critérios de Aceitação
- [x] Frases com termos genéricos isolados não geram casamento indevido contra a base FactChecks.br.
- [x] O prompt do provedor remoto instrui e restringe o LLM a frases curtas ancoradas na transcrição.
- [x] Zero regressões em testes de proveniência de dados e não-dogmatismo.

### Rastreabilidade
- **Épico Relacionado:** [Épico 4 — Confiança e Fontes](documentation/docs/requisitos/backlog-e-historias.md#epico-4-confianca-e-fontes), [Épico 7 — Investigação Orientada por Alegações e Evidências](documentation/docs/requisitos/backlog-e-historias.md#epico-7-investigacao-orientada-por-alegacoes-e-evidencias)
- **Requisitos Vinculados:** RF-06, RF-07, RF-12, RNF-04, RNF-06
- **ADR de Referência:** ADR-006 (Evidence-First Architecture)
