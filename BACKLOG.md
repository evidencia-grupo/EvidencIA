# Catálogo Consolidado de Histórias de Usuário & Backlog — EvidencIA

> Especificação detalhada de cada Épico, Feature e História de Usuário (HU) do projeto **EvidencIA**, com critérios de aceitação executáveis em sintaxe Gherkin e vínculos de rastreabilidade com o catálogo de requisitos e decisões de arquitetura.

---

## Índice por Épico

- [Épico 1 — Gatilho e Ativação](#epico-1--gatilho-e-ativacao) (HU01, HU03)
- [Épico 2 — Extração de Transcrição](#epico-2--extracao-de-transcricao) (HU05, HU10)
- [Épico 3 — Análise e Checagem via IA / Evidence-First](#epico-3--analise-e-checagem-via-ia) (HU02, HU04, HU09, HU13, HU14, HU16)
- [Épico 4 — Confiança e Fontes](#epico-4--confianca-e-fontes) (HU07, HU08)
- [Épico 5 — Performance e Cache](#epico-5--performance-e-cache) (HU06)
- [Épico 6 — Engajamento Reflexivo (MVP)](#epico-6--engajamento-reflexivo-promovido-para-o-mvp-na-sprint-2) (HU15; HU12 cancelada)

---

## Épico 1 — Gatilho e Ativação

> **Objetivo:** Fornecer ao usuário um ponto de entrada intuitivo e não-intrusivo para acionar a verificação diretamente no player do YouTube.

### Feature F2.1: Disparo e Exibição Acessível WCAG

---

### HU01 — Verificação Simplificada de Conteúdo em Vídeo
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Dona Lurdes (Consumidora de receitas caseiras e dicas de saúde)
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 01, UC-01, RF-01, RF-03, RNF-01, RNF-07

**Declaração de Valor:**
> *Como Dona Lurdes, pretendo iniciar a checagem de um vídeo com apenas um clique para que eu saiba se as receitas e dicas caseiras de saúde são seguras antes de seguir ou repassar a familiares.*

**Critérios de Aceitação:**
1. A extensão deve disponibilizar um botão de acionamento destacado e visível na interface da página de reprodução (`/watch`).
2. O primeiro resultado útil deve ser renderizado no painel lateral em linguagem clara, sem termos técnicos ou jargões da web.
3. Caso o vídeo não possua transcrição ou a rede falhe, o sistema deve exibir aviso em linguagem simples e amigável sem travar o navegador.

```gherkin
Funcionalidade: Verificação simplificada de conteúdo em vídeo

  Cenário: Acionar a checagem com um clique
    Dado que Dona Lurdes está em uma página de vídeo ativa do YouTube (/watch)
    Quando ela clica no botão de acionamento da extensão
    Então o painel deve exibir confirmação visual de processamento em até 1 segundo
    E o primeiro resultado útil deve ser renderizado em linguagem clara, sem jargões técnicos

  Cenário: Falha de rede ou ausência de transcrição
    Dado que Dona Lurdes aciona a checagem de um vídeo
    Quando o vídeo não possui transcrição disponível ou a rede falhe
    Então o sistema deve exibir um aviso em linguagem simples e amigável
    E o navegador não deve travar
```

---

### HU03 — Checagem Rápida e Factual no Player
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Amanda (Estudante universitária de ciências biológicas)
- **Pontos de História:** 3
- **Rastreabilidade:** Cenário 01, Cenário 03, UC-01, UC-03, RF-01, RF-09, RNF-01

**Declaração de Valor:**
> *Como Amanda, pretendo analisar afirmações de vídeos de divulgação científica em até 10 segundos para validar premissas sem interromper o fluxo dos meus estudos.*

**Critérios de Aceitação:**
1. O sistema deve fornecer confirmação visual imediata de processamento em até 1 segundo após o clique.
2. A síntese útil deve ser renderizada no painel lateral em no máximo 10 segundos em condições normais de rede.
3. Em vídeos já analisados recentemente, o sistema deve recuperar os dados instantaneamente a partir da memória local.

```gherkin
Funcionalidade: Checagem rápida e factual no player

  Cenário: Confirmação visual imediata
    Dado que Amanda aciona a checagem de um vídeo
    Quando o clique é processado
    Então uma confirmação visual de processamento deve aparecer em até 1 segundo

  Cenário: Entrega da síntese dentro do SLA
    Dado que a transcrição foi extraída com sucesso
    Quando o pipeline de IA e busca processa as alegações
    Então a síntese útil deve ser renderizada no painel em no máximo 10 segundos, em condições normais de rede

  Cenário: Recuperação instantânea de vídeo já analisado
    Dado que Amanda abre um vídeo checado recentemente
    Quando ela aciona a extensão
    Então o resultado deve ser recuperado da memória local instantaneamente, sem nova requisição
```

---

## Épico 2 — Extração de Transcrição

> **Objetivo:** Capturar e higienizar de forma autônoma as legendas expostas pelo player do YouTube, sem dependência de APIs externas de transcrição no MVP.

### Feature F1.1: Extração e Higienização de Transcrições

---

### HU05 — Ingestão e Processamento de Transcrição
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Carlos Augusto (Analista sênior de TI e entusiasta de segurança)
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 02, UC-02, RF-02, RF-08, RNF-03, RNF-06

**Declaração de Valor:**
> *Como Carlos Augusto, pretendo que o sistema obtenha e processe automaticamente a transcrição do vídeo para que a verificação de factualidade ocorra a partir do áudio exato do conteúdo.*

**Critérios de Aceitação:**
1. O sistema deve interceptar as faixas de legenda (nativas ou geradas automaticamente) diretamente do player do YouTube.
2. O texto extraído deve ser estruturado e higienizado antes do envio seguro ao backend intermediário.
3. Caso o criador tenha desativado as legendas e não haja transcrição disponível, o sistema deve exibir alerta informativo claro e liberar a tela.

```gherkin
Funcionalidade: Ingestão e processamento de transcrição

  Cenário: Extração de legendas nativas ou automáticas
    Dado que Carlos Augusto está em uma página de vídeo ativa
    Quando o sistema intercepta o identificador do vídeo
    Então as faixas de legenda (nativas ou automáticas) devem ser requisitadas ao player
    E o texto deve ser higienizado e estruturado antes do envio ao backend

  Cenário: Vídeo sem legendas disponíveis
    Dado que o criador do vídeo desativou as legendas
    Quando o sistema tenta obter a transcrição
    Então um alerta informativo claro deve ser exibido
    E o fluxo de checagem deve ser encerrado com segurança
```

---

### HU10 — Notificação Rápida de Ausência de Transcrição
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Mariana (Profissional conectada e usuária intensa de redes sociais)
- **Pontos de História:** 3
- **Rastreabilidade:** Cenário 08, UC-02, RF-08, RNF-01, RNF-06, RNF-07

**Declaração de Valor:**
> *Como Mariana, pretendo ser notificada imediatamente caso o vídeo assistido não possua legendas para não perder tempo aguardando um resultado que não pode ser gerado.*

**Critérios de Aceitação:**
1. O sistema deve validar a disponibilidade da transcrição em até 1 segundo após o acionamento da extensão.
2. Exibição de um alerta orientador informando a impossibilidade técnica de processar o vídeo sem legendas.
3. Interrupção segura do carregamento sem retenção de estado de espera ou bloqueio da aba.

```gherkin
Funcionalidade: Notificação rápida de ausência de transcrição

  Cenário: Vídeo sem legendas
    Dado que Mariana aciona a checagem de um vídeo sem transcrição disponível
    Quando o sistema valida a disponibilidade da transcrição
    Então um alerta orientador deve ser exibido em até 1 segundo
    E o carregamento deve ser interrompido com segurança, sem bloquear a aba

  Cenário: Falha temporária da API do YouTube
    Dado que ocorre um erro temporário ao consultar as legendas
    Quando o sistema detecta a falha
    Então um botão de nova tentativa deve ser disponibilizado no painel
```

---

## Épico 3 — Análise e Checagem via IA

> **Objetivo:** Processar o texto da transcrição através de inteligência artificial, isolando afirmações verificáveis e sintetizando o nível de comprovação factual.

### Feature F1.2: Motor de Checagem Factual e IA & Feature F2.3: Sinalização Visual de Incerteza

---

### HU02 — Síntese Estruturada sem Jargões Técnicos
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Dona Lurdes
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 10, UC-01, UC-03, RF-03, RF-06, RNF-07

**Declaração de Valor:**
> *Como Dona Lurdes, pretendo visualizar uma síntese objetiva com destaques visuais acessíveis para entender facilmente o que é verdade, mentira ou sem comprovação sem sobrecarga de leitura.*

**Critérios de Aceitação:**
1. As alegações devem ser agrupadas com separação nítida entre o que possui respaldo científico e o que é contradito pelas evidências.
2. O painel deve seguir normas WCAG de legibilidade, tipografia ampla e contraste cromático adequado.
3. A consulta não deve exigir configurações complexas, preenchimento de cadastros ou autenticação externa.

```gherkin
Funcionalidade: Síntese estruturada sem jargões técnicos

  Cenário: Separação visual entre alegações apoiadas e contraditas
    Dado que a checagem de um vídeo foi concluída
    Quando o painel lateral é renderizado
    Então as alegações com respaldo científico devem estar visualmente separadas das contraditas pelas evidências
    E o painel deve seguir contraste e tipografia compatíveis com WCAG AA

  Cenário: Consulta sem cadastro
    Dado que Dona Lurdes deseja visualizar a síntese
    Quando ela usa a extensão
    Então nenhuma configuração, cadastro ou autenticação externa deve ser exigida
```

---

### HU04 — Categorização Estruturada de Alegações
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Amanda
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 03, UC-03, RF-03, RF-06, RNF-02

**Declaração de Valor:**
> *Como Amanda, pretendo visualizar as principais alegações do vídeo categorizadas entre evidências que apoiam, contradizem ou contextualizam a fala para facilitar os meus fichamentos acadêmicos.*

**Critérios de Aceitação:**
1. As alegações extraídas pela IA devem ser listadas isoladamente, indicando claramente a sua relação com as evidências encontradas.
2. A injeção dos componentes na aba do YouTube não deve elevar o Tempo Total de Bloqueio (TBT) em mais de 50 ms.
3. O sistema não deve impor vereditos dogmáticos, mantendo foco na apresentação factual e analítica.

```gherkin
Funcionalidade: Categorização estruturada de alegações

  Cenário: Listagem isolada de alegações com relação às evidências
    Dado que a análise de um vídeo foi concluída
    Quando o painel exibe o resultado
    Então cada alegação extraída pela IA deve ser listada isoladamente
    E sua relação com as evidências (apoia, contradiz, contextualiza) deve estar explícita

  Cenário: Limite de sobrecarga de renderização
    Dado que os componentes da extensão são injetados na aba ativa do YouTube
    Quando a página é carregada
    Então o Tempo Total de Bloqueio (TBT) não deve aumentar mais de 50 ms
```

---

### HU09 — Alerta Visual Imediato de Incerteza Analítica
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Mariana
- **Pontos de História:** 3
- **Rastreabilidade:** Cenário 06, UC-06, RF-07, RNF-06, RNF-07

**Declaração de Valor:**
> *Como Mariana, pretendo receber um alerta visual destacado quando houver incerteza ou conflito de fontes sobre o vídeo para conter impulsos de repasse em mensagens no WhatsApp.*

**Critérios de Aceitação:**
1. Exibição de indicador visual de advertência (badge de incerteza) quando as evidências forem insuficientes ou divergentes.
2. Apresentação de um texto curto e direto explicando que a afirmação não possui confirmação factual consolidada.
3. O alerta deve estar visível no topo do painel lateral antes de qualquer detalhamento técnico.

```gherkin
Funcionalidade: Alerta visual imediato de incerteza analítica

  Cenário: Fontes conflitantes ou dados insuficientes
    Dado que o backend identifica ausência de evidências conclusivas ou divergência factual
    Quando o resultado é classificado como inconclusivo
    Então um badge visual de alerta deve ser exibido no topo do painel, antes de qualquer detalhamento técnico
    E um texto curto deve explicar que a afirmação não possui confirmação factual consolidada

  Cenário: Controvérsia legítima entre fontes
    Dado que existem referências legítimas com conclusões opostas
    Quando o sistema apresenta o resultado
    Então ambos os lados da controvérsia devem ser expostos, sem arbitrar um vencedor absoluto
```

---

## Épico 4 — Confiança e Fontes

> **Objetivo:** Assegurar a transparência editorial através do fornecimento de referências auditáveis e contexto de publicação.

### Feature F2.2: Auditoria de Fontes e Metadados

---

### HU07 — Auditoria Direta de Fontes e Referências
- **Prioridade:** Must Have | IN (Onda 1)
- **Persona:** Mayara (Jornalista investigativa e pesquisadora independente)
- **Pontos de História:** 3
- **Rastreabilidade:** Cenário 04, UC-04, RF-04, RNF-05, RNF-07

**Declaração de Valor:**
> *Como Mayara, pretendo acessar as fontes utilizadas na checagem por meio de hiperligações e metadados diretos para auditar a origem primária das evidências de forma autônoma.*

**Critérios de Aceitação:**
1. Cada cartão de alegação checada deve listar explicitamente as referências com título da fonte e hiperligação de acesso direto.
2. Ao clicar na fonte, a página externa deve ser aberta em uma nova aba do navegador sem fechar o painel lateral da extensão nem recarregar o vídeo.
3. Caso o endereço de destino esteja inacessível (erro HTTP), o navegador gerencia o erro sem travar a extensão.

```gherkin
Funcionalidade: Auditoria direta de fontes e referências

  Cenário: Abertura de fonte em nova aba
    Dado que Mayara visualiza um cartão de alegação checada com referências
    Quando ela clica na hiperligação da fonte
    Então a página original deve abrir em uma nova aba
    E o painel lateral e o player do vídeo devem permanecer intactos

  Cenário: Link inacessível
    Dado que a fonte referenciada retorna erro HTTP (ex.: 404)
    Quando Mayara tenta acessá-la
    Então o navegador deve tratar o erro na nova aba, sem travar a extensão
```

---

### HU08 — Contextualização Temporal e Autoria do Vídeo
- **Prioridade:** Should Have | IN (Onda 2)
- **Persona:** Mayara
- **Pontos de História:** 3
- **Rastreabilidade:** Cenário 09, UC-01, UC-03, RF-11, RNF-07

**Declaração de Valor:**
> *Como Mayara, pretendo visualizar a data original de publicação do vídeo e as informações do canal para avaliar se as afirmações analisadas estão anacrônicas ou fora de época.*

**Critérios de Aceitação:**
1. O painel de checagem deve exibir a data de upload original e o nome do canal responsável pelo vídeo no YouTube.
2. O cruzamento de dados deve considerar o marco temporal de publicação para evitar falsas contradições em conteúdos antigos.
3. Os metadados de contexto devem ser exibidos de forma compacta no cabeçalho do painel de análise.

```gherkin
Funcionalidade: Contextualização temporal e autoria do vídeo

  Cenário: Exibição de metadados de publicação
    Dado que a checagem de um vídeo foi concluída
    Quando o painel é renderizado
    Então a data de upload original e o nome do canal devem ser exibidos no cabeçalho

  Cenário: Cruzamento temporal das afirmações
    Dado que um vídeo antigo volta a circular como se fosse atual
    Quando a IA analisa as afirmações
    Então o cruzamento deve considerar o ano de produção do material
    E não deve classificar como falsa uma afirmação que era verídica à época
```

---

## Épico 5 — Performance e Cache

> **Objetivo:** Otimizar tempo de resposta e consumo de recursos através de persistência local determinística.

### Feature F1.3: Cache Local e Otimização de Rede

---

### HU06 — Consulta Imediata via Cache Local
- **Prioridade:** Should Have | IN (Onda 2 / MVP Hardening)
- **Persona:** Carlos Augusto
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 07, UC-01, RF-09, RNF-01, RNF-05, ADR-003

**Declaração de Valor:**
> *Como Carlos Augusto, pretendo recuperar checagens recentes salvas no cache local para não desperdiçar tráfego de rede nem consumir processamento em vídeos já auditados.*

**Critérios de Aceitação:**
1. A extensão deve verificar o armazenamento local pelo identificador do vídeo antes de efetuar chamadas externas de inferência.
2. Resultados em cache válido devem ser exibidos de forma instantânea (latência inferior a 1 segundo).
3. O armazenamento em cache local deve ser restrito ao escopo da extensão, sem reter histórico geral de navegação do usuário.

```gherkin
Funcionalidade: Consulta imediata via cache local

  Cenário: Cache válido disponível
    Dado que um vídeo já foi analisado recentemente
    Quando Carlos Augusto aciona a extensão nesse vídeo
    Então o sistema deve localizar o registro em cache pelo identificador do vídeo
    E exibir o resultado em menos de 1 segundo, sem nova chamada externa

  Cenário: Cache expirado ou corrompido
    Dado que o registro local de um vídeo está expirado ou corrompido
    Quando a extensão tenta recuperá-lo
    Então o sistema deve descartar o registro
    E disparar uma nova análise completa
```

---

## Épico 6 — Engajamento Reflexivo (Promovido para o MVP na Sprint 2)

> **Objetivo:** Estimular o pensamento crítico do usuário através de perguntas epistemológicas não-intrusivas, sem juízos dogmáticos.

### Feature F3.1: Estímulo ao Pensamento Crítico (Evidence-First)

---

### HU15 (Antiga HU11 Promovida) — Perguntas Orientadoras para Reflexão Crítica
- **Prioridade:** Must Have | IN (Onda 1 / Sprint 2)
- **Persona:** Helena (Professora do ensino médio)
- **Pontos de História:** 5
- **Rastreabilidade:** Cenário 05, UC-05, RF-05 (passivo), HU15 (ADR-006)
- **Componente:** `ReflectionQuestions.tsx`

**Declaração de Valor:**
> *Como Helena, pretendo receber perguntas reflexivas sobre os pontos controversos do vídeo para orientar a minha própria checagem sem que a IA imponha conclusões fechadas.*

```gherkin
Funcionalidade: Perguntas orientadoras para reflexão crítica

  Cenário: Exibição de pergunta reflexiva neutra
    Dado que as evidências de um vídeo com temática controversa foram apresentadas
    Quando o painel exibe o bloco de reflexão em cada card de alegação
    Então a pergunta não deve emitir juízo ideológico nem impor conclusão
    E a interface não deve exigir formulário ou coleta de dados do usuário

  Cenário: Ignorar a interação
    Dado que Helena não deseja interagir com a seção reflexiva
    Quando ela navega pelo painel
    Então a leitura deve seguir normalmente, sem bloqueios de interface
```

---

### HU12 — Avaliação de Relevância e Precisão da Análise (CANCELADA / FORA DO MVP)
- **Prioridade:** Could Have | OUT (Cancelada / DIV-01)
- **Persona:** Helena
- **Pontos de História:** 3
- **Rastreabilidade:** RF-10 (Fora do MVP), DIVERGENCIAS.md (DIV-01)
- **Status:** Cancelada por decisão de produto (atrito zero e conformidade LGPD sem retenção de feedback).

---

## Épico 3 (Extensão) — Histórias da Arquitetura Evidence-First (Sprint 2)

### HU13 — Evidence-First Schema e Eliminação de Veredito Global
- **Prioridade:** Must Have | IN (Sprint 2)
- **Persona:** Amanda (Estudante universitária)
- **Pontos de História:** 5
- **Rastreabilidade:** RF-06, RF-12, ADR-006, Issue #33
- **Status:** Concluído

```gherkin
Funcionalidade: Contrato Evidence-First sem nota numérica

  Cenário: Resposta da API sem campos de score
    Dado que o backend processa uma checagem factual
    Quando o payload de resposta é emitido
    Então nenhum campo de score numérico (0-100) deve estar presente
    E o payload deve conter uma lista estruturada de alegações, evidências e incertezas
```

---

### HU14 — Evidence Cards no Painel da Extensão
- **Prioridade:** Must Have | IN (Sprint 2)
- **Persona:** Carlos Augusto (Estudante)
- **Pontos de História:** 5
- **Rastreabilidade:** RF-06, ADR-006, Issue #35
- **Componente:** `EvidenceCard.tsx`
- **Status:** Concluído

```gherkin
Funcionalidade: Cards de evidência auditável

  Cenário: Exibição de evidência documental
    Dado que uma alegação possui correspondência em base jornalística
    Quando o usuário expande a alegação no painel
    Então cada evidência deve exibir o veículo checador, data, citação direta e link externo
    E a relação lógica deve ser classificada como apoia, contradiz ou contextualiza
```

---

### HU16 — Degradação Graciosa para Modo Evidence-Only
- **Prioridade:** Must Have | IN (Sprint 2)
- **Persona:** Amanda (Estudante com rede oscilante)
- **Pontos de História:** 3
- **Rastreabilidade:** RF-14, RNF-06, ADR-006, Issue #37
- **Status:** Concluído

```gherkin
Funcionalidade: Degradação graciosa em timeout ou falha de IA

  Cenário: Falha do motor de síntese por IA
    Dado que a requisição atinge o timeout de 8 segundos no LLM
    Quando o backend captura a falha de provedor
    Então a resposta deve chavear para o modo evidence_only
    E o painel da extensão deve exibir um banner de alerta informando a indisponibilidade da síntese
    E todas as evidências documentais já recuperadas devem ser apresentadas normalmente
```
