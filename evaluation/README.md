# Framework de Avaliação de Recuperação e Stance — EvidencIA

Este diretório contém a estrutura oficial e reproduzível para avaliação empírica do sistema de recuperação de evidências e classificação de relação semântica (stance).

---

## 1. Princípios Metodológicos

1. **Separação Epistemológica:** A alegação extraída do vídeo (`claim`) é mantida separada do texto do documento de evidência (`evidence`).
2. **Não-Circularidade:** Nenhum modelo de linguagem (LLM) ou classificador pode gerar rótulos para avaliar a si mesmo. Métricas de qualidade científica dependem de anotação humana independente.
3. **Protocolo Duplo-Cego:** As diretrizes completas de rotulação estão definidas em [`annotation-guide.md`](file:///Users/aluno1/Documents/challenge%20fake%20news/evidencia/evaluation/annotation-guide.md).

---

## 2. Estrutura de Arquivos

- `claims.jsonl`: Coleção de alegações factuais atômicas extraídas de transcrições reais de vídeos no YouTube, contendo `claim_id`, título do vídeo, trecho da transcrição, timestamps e categoria.
- `candidates.jsonl`: Pares `(alegação, candidato)` recuperados pelo pipeline de busca semântica, contendo os escores algorítmicos e campos reservados para anotação humana (`human_relevance` e `human_stance`).
- `annotation-guide.md`: Manual detalhado para os avaliadores humanos com definição de critérios de relevância (0, 1, 2) e postura (`supports`, `contradicts`, `contextualizes`, `unrelated`).
- `README.md`: Este guia metodológico e operacional.

---

## 3. Métricas Avaliadas

### 3.1 Recuperação de Informação (IR)
- **Recall@k:** Proporção de documentos relevantes identificados entre os $k$ primeiros resultados devolvidos pelo retrieval.
- **MRR (Mean Reciprocal Rank):**
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  onde $\text{rank}_i$ é a posição do primeiro documento relevante para a alegação $i$.
- **nDCG@k (Normalized Discounted Cumulative Gain):** Avalia a ordenação ponderada pelo ganho de relevância graduada (0, 1, 2).

### 3.2 Relação Semântica (Stance Classification)
- **Macro-F1, Precisão e Revocação** calculados sobre as classes `contradicts`, `supports` e `contextualizes` em comparação direta com o consenso humano consolidado.

---

## 4. Como Executar a Avaliação

Quando as anotações humanas forem concluídas no arquivo `candidates.jsonl`:

```bash
# Execução do script de avaliação contra as anotações consolidadas
backend/.venv/bin/python3 scripts/evaluate_retrieval.py \
  --claims evaluation/claims.jsonl \
  --candidates evaluation/candidates.jsonl
```

Enquanto os avaliadores humanos não homologarem o conjunto, o status operacional permanece formalmente registrado como:
```text
STATUS: PENDING_HUMAN_ANNOTATION (Bloqueio H3 isolado)
```
Nenhuma métrica simulada ou forjada é aceita como prova de performance.
