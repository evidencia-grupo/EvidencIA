---
title: "[FEAT]: Segmentação Robusta de Legendas ASR e Preservação de Frases da Transcrição Completa"
labels: ["enhancement", "nlp", "frontend", "backend"]
assignees: ""
---

### Problema ou Oportunidade
Legendas automáticas geradas pelo YouTube (ASR - Automatic Speech Recognition) não possuem pontuação formal (`.`, `!`, `?`). Quando o sistema junta os eventos da legenda e aplica `re.split` por pontuação, a transcrição de um vídeo inteiro de 10 a 20 minutos é interpretada como uma única string corrida de milhares de palavras. Como consequência, o modelo e o frontend renderizam blocos gigantescos de texto não pontuado dentro de um único card de alegação, tornando a leitura inviável para o usuário final.

### Solução Proposta
1. **Algoritmo de Segmentação Semântica para Fala sem Pontuação (`_segment_unpunctuated_stream`)**:
   - Detectar streams contínuos de palavras sem pontuação e dividi-los em orações gramaticais legíveis de 8 a 25 palavras.
   - Utilizar conectivos e marcadores discursivos em português (`então`, `portanto`, `segundo`, `estudos`, `existem`, `porque`, `mas`, `além`) como pontos de quebra natural de oração.
   - Capitalizar a primeira letra de cada frase e garantir a pontuação final com ponto (`.`).
2. **Preservação dos Segmentos com Timestamps (`caption-parser.ts`)**:
   - Manter a integridade da lista de `segments` temporizados extraídos do YouTube (`start`, `duration`, `text`) sem descarte por divergência de sanitização de espaços.
   - Garantir que a navegação temporal ("Ir para MM:SS") aponte para o segundo exato onde a frase foi proferida no vídeo.

### Critérios de Aceitação
- [x] Nenhuma alegação extraída ou exibida no painel lateral excede 35 palavras ou forma blocos contínuos de texto.
- [x] Transcrições ASR sem pontuação são divididas obrigatoriamente em frases curtas, claras e coesas.
- [x] A sincronização entre `segments` e a transcrição sanitizada é 100% válida perante o validador Pydantic do backend.

### Rastreabilidade
- **Épico Relacionado:** [Épico 2 — Extração de Transcrição](documentation/docs/requisitos/backlog-e-historias.md#epico-2-extracao-de-transcricao), [Épico 7 — Investigação Orientada por Alegações e Evidências](documentation/docs/requisitos/backlog-e-historias.md#epico-7-investigacao-orientada-por-alegacoes-e-evidencias)
- **Requisitos Vinculados:** RF-01, RF-02, RF-10, RNF-02
