# Relatório de Prontidão da Avaliação — EvidencIA (Fase 3)

**Data:** 2026-10-07  
**Status dos Artefatos Técnicos:** 100% PRONTO  
**Status dos Rótulos Humanos:** `PENDING_HUMAN_ANNOTATION` (Bloqueio H3)  

---

## 1. Verificação dos Artefatos Técnicos

- [x] **`evaluation/claims.jsonl`:** Coleção estruturada de 8 alegações factuais atômicas cobrindo saúde, ciência, economia, eleições, clima e tecnologia.
- [x] **`evaluation/candidates.jsonl`:** Pares `(alegação, candidato)` recuperados com scores algorítmicos e campos reservados para anotação cega (`human_relevance: null`, `human_stance: null`).
- [x] **`evaluation/annotation-guide.md`:** Manual duplo-cego completo com critérios operacionais de relevância (0, 1, 2) e postura (`contradicts`, `supports`, `contextualizes`, `unrelated`).
- [x] **`evaluation/README.md`:** Documentação do framework de avaliação e fórmulas matemáticas de Recall@k, MRR e nDCG.
- [x] **`scripts/evaluate_retrieval.py`:** Script automatizado de cálculo de métricas de IR e Stance, com salvaguarda fail-safe contra relatórios forjados.
- [x] **`backend/ml/notebooks/eda_retrieval.ipynb`:** Notebook reproduzível de análise exploratória com seed fixa (`SEED = 42`).

---

## 2. Garantia Antifabricação e Integridade Científica

Em conformidade estrita com o Princípio 1.1 do Plano Mestre:
> "Nenhum sucesso sem evidência. Nunca escreva 'validado' quando a validação ainda depende de usuário humano."

Nenhuma métrica de acurácia, F1, MRR ou Recall foi simulada por agentes de IA ou dados forjados. O cálculo real de performance de IR será disparado assim que dois avaliadores humanos independentes concluírem o preenchimento de `candidates.jsonl` de acordo com o `annotation-guide.md`.
