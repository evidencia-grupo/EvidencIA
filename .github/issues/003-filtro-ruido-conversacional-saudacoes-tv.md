---
title: "[BUG]: Filtragem de Ruído Conversacional / Saudações de TV e Aumento da Precisão do Extrator"
labels: ["bug", "nlp", "accuracy", "ml"]
assignees: ""
---

### Descrição do Defeito
Em programas de televisão, entrevistas e podcasts de saúde (como programas da TV Novo Tempo e canais médicos), as primeiras frases da fala costumam ser saudações ou apresentações do estúdio (ex.: *"Tá começando o seu programa de saúde aqui na TV Novo Tempo..."*, *"Hoje é dia de explorar um tema muito legal e olha só quem vem aqui com a gente. Doutor, tudo bem?"*). 
Como o sistema anterior apenas capturava as primeiras frases e identificava a palavra genérica "saúde", essas saudações eram incorretamente selecionadas como alegações factuais centrais do vídeo, recebendo vereditos e buscas de evidências sem qualquer relação com a afirmação principal.

### Passos para Reproduzir
1. Acessar um vídeo de programa de TV ou entrevista no YouTube com introdução de estúdio.
2. Clicar em "Checar Alegações".
3. Observar que a alegação extraída era a saudação da apresentadora e não a tese científica ou médica do convidado.

### Solução Proposta
1. **Expansão de Padrões Conversacionais (`CONVERSATIONAL_PATTERNS` e `phatic`)**:
   - Adicionar expressões típicas de abertura de estúdio, TV aberta e podcasts:
     `r"ta comecando (o|seu|o seu)?\s*programa"`, `r"comecando o seu programa"`, `r"programa de saude aqui"`, `r"vem pra ca"`, `r"olha so quem vem aqui"`, `r"doutor[, ]+tudo bem"`, `r"tudo bem[, ]+doutor"`, `r"vamos chamar o"`, etc.
2. **Rastreamento de Saliência em Toda a Legenda (`score_claim_saliency`)**:
   - Varrer toda a extensão do vídeo e ranquear as frases por densidade de afirmações factuais (verbos de asserção científica, substâncias, órgãos reguladores e termos de impacto).
   - Atribuir score 0.0 a qualquer frase conversacional de abertura.

### Critérios de Aceitação
- [x] Nenhuma saudação de estúdio ou pedido de inscrição é extraída como alegação verificável.
- [x] O extrator prioriza proposições centrais do vídeo mesmo que estejam localizadas minutos após o início da gravação.
- [x] Testes unitários com transcrições reais de programas de TV aprovados.

### Rastreabilidade
- **Requisitos Afetados:** RF-02, RF-04, RNF-01
- **Módulo:** Backend (`ml.classifier.claim_extractor`, `app.providers.mock`, `app.providers.remote`)
