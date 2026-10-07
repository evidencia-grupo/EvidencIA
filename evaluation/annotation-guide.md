# Guia de Anotação Manual — Avaliação de Evidências e Relação Semântica (Gold Set)

**Versão:** 1.0.0  
**Data:** 2026-10-07  
**Público-alvo:** Anotadores humanos independentes (protocolo duplo-cego)  
**Projeto:** EvidencIA — Extensão para Avaliação Crítica de Notícias em Vídeo  

---

## 1. Objetivo da Anotação

Este guia instrui os avaliadores humanos na rotulação manual de pares compostos por:
1. **Alegação Extraída (`claim`):** Uma declaração factual identificada em um vídeo do YouTube.
2. **Documento Candidato (`candidate_evidence`):** Uma matéria de fact-checking ou documento oficial recuperado pelo sistema de busca semântica.

O objetivo do gold set é servir de padrão-ouro imparcial para medir:
- **Recuperação de Informação (IR):** O sistema recuperou as matérias de fato relevantes para a alegação?
- **Classificação de Relação Semântica (Stance):** O sistema classificou adequadamente a relação entre a fonte e a alegação?

> **ATENÇÃO:** O anotador não deve consultar o veredito prévio do sistema nem buscar induzir a resposta. A anotação deve ser baseada exclusivamente no texto da alegação e no texto do documento de evidência apresentado.

---

## 2. Protocolo de Avaliação (Duplo-Cego)

1. Cada par `(alegação, candidato)` deve ser avaliado por pelo menos **dois anotadores independentes**.
2. Os anotadores não compartilham suas anotações até a consolidação final.
3. Divergências entre anotadores serão mediadas por um terceiro revisor ou descartadas conforme o índice de concordância inter-anotador ($\kappa$ de Cohen / Fleiss).
4. O índice de concordância mínimo aceitável para validação do gold set é $\kappa \ge 0.70$.

---

## 3. Tarefa 1 — Relevância Tópica (Critério de IR)

Para cada par, atribua um valor de relevância:

| Grau | Rótulo | Descrição |
| :---: | :--- | :--- |
| **2** | **Altamente Relevante** | O documento trata exatamente do mesmo fato, evento, estatística ou declaração citada na alegação. |
| **1** | **Parcialmente Relevante** | O documento trata do mesmo tema ou figura pública, mas foca em aspecto ligeiramente diferente ou período distinto. |
| **0** | **Não Relevante** | O documento trata de outro assunto, usa termos coincidentes por acaso ou é completamente desconexo. |

---

## 4. Tarefa 2 — Relação Semântica / Postura (Stance)

Caso a relevância seja 1 ou 2, classifique a relação semântica do documento em relação à alegação em uma das 4 categorias:

### 4.1 `contradicts` (Contradiz / Refuta)
- **Definição:** O documento de evidência comprova formalmente que a alegação é incorreta, falsa, manipulada ou baseada em dados forjados.
- **Exemplo:**
  - *Alegação:* "Chá de casca de banana cura diabetes e zera a glicose em 3 dias."
  - *Evidência:* "Sociedade Brasileira de Diabetes afirma que infusão de casca de banana não cura diabetes e não substitui medicação."
  - *Classificação:* `contradicts`.

### 4.2 `supports` (Apoia / Confirma)
- **Definição:** O documento de evidência confirma a veracidade factual da afirmação com base em registros oficiais, estudos revisados por pares ou dados consolidados.
- **Exemplo:**
  - *Alegação:* "Vacinas passam por três fases de ensaios clínicos antes de aprovação pela Anvisa."
  - *Evidência:* "Resoluções da Anvisa detalham as fases I, II e III obrigatórias para registro de imunizantes."
  - *Classificação:* `supports`.

### 4.3 `contextualizes` (Contextualiza / Esclarece)
- **Definição:** A alegação contém elemento factual verdadeiro, mas omite contexto temporal, distorce a interpretação estatística, ou a matéria esclarece circunstâncias que mudam o sentido sem que seja puramente verdadeira ou falsa. Também aplicável quando a evidência aponta falta de consenso ou dados inconclusivos.
- **Exemplo:**
  - *Alegação:* "Uso de vitamina D reduz mortalidade em pacientes hospitalizados."
  - *Evidência:* "Estudos clínicos mostram resultados mistos e metanálise recente concluiu que não há benefício clínico comprovado estatisticamente."
  - *Classificação:* `contextualizes`.

### 4.4 `unrelated` (Não Relacionado)
- **Definição:** O documento de evidência não toma postura em relação à alegação porque não versa sobre o núcleo factual alegado.

---

## 5. Armadilhas Frequentes

1. **Confundir quem alega:** Lembre-se de que a *alegação* é o que o vídeo diz. A *evidência* é a checagem da agência. Não atribua a alegação ao checador nem o texto do checador como se fosse a fala do vídeo.
2. **Discordância pessoal vs evidência:** Avalie se o documento traz evidência factual, e não se você concorda pessoalmente com a afirmação.
3. **Hiper-sensibilidade de palavras-chave:** Duas frases podem conter a palavra "economia" e falar de tópicos totalmente desconexos. Classifique como `unrelated` se o núcleo da alegação não for abordado.

---

## 6. Formato de Saída das Anotações

Os anotadores preenchem a coluna `human_relevance` (0, 1, 2) e `human_stance` (`supports`, `contradicts`, `contextualizes`, `unrelated`) no arquivo de consolidação `evaluation/candidates.jsonl`.
