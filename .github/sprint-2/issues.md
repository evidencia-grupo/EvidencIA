# Sprint 2 — Checklist de Issues & Execução Operacional

> **Milestone:** Sprint 2  
> **Período de Execução:** 05/10/2026 a 09/10/2026 (5 dias úteis)  
> **Data de Fechamento (Code Freeze Sprint 2):** 09 de Outubro de 2026  
> **Objetivo da Sprint 2:** Converter os resultados da investigação da Sprint 1 em um pipeline de evidências e uma UX que preserve o pensamento crítico (Evidence-First), eliminando a dependência estrutural do Ollama local e removendo em definitivo o score global e velocímetros da extensão.  
> **Total de Story Points:** 29 SP (7 issues oficiais)  
> **Referência Arquitetural:** [ADR-006 (Evidence-First Architecture)](../../documentation/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md) · [KANBAN.md](../../KANBAN.md)

---

## 1. Quadro de Responsabilidades e Prazos da Equipe (Sprint 2: 05/10 a 09/10)

| Issue | HU / ID | Título da História / Atividade | Épico | Responsável Principal | Co-responsável | Prazo de Entrega | Prioridade MoSCoW | SP |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|
| [#10](https://github.com/evidencia-grupo/EvidencIA/issues/10) | **HU10** | Notificação Rápida de Ausência de Transcrição | `epic:e2-transcricao` | @luizoryone | — | **06/10/2026** | `must-have` / `mvp:onda-1` | 3 |
| [#32](https://github.com/evidencia-grupo/EvidencIA/issues/32) | **HU16** | Provider Abstraction: Migração de OllamaProvider e RemoteLLMProvider | `epic:e3-ia-checagem` | @pedrohpsantos | — | **06/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#33](https://github.com/evidencia-grupo/EvidencIA/issues/33) | **HU13** | Evidence-First Schema: Migração de Contratos e Eliminação do Score Global | `epic:e3-ia-checagem` | @pedrohpsantos | @mahiaara | **07/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#34](https://github.com/evidencia-grupo/EvidencIA/issues/34) | **HU02** | Descongelamento Formal e Remoção do Score Global da UI | `epic:e3-ia-checagem` | @MylenaTrindade | — | **07/10/2026** | `must-have` / `mvp:onda-1` | 3 |
| [#35](https://github.com/evidencia-grupo/EvidencIA/issues/35) | **HU14** | Evidence Cards no Painel da Extensão | `epic:e4-confianca-fontes` | @MylenaTrindade | @luizoryone | **08/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#36](https://github.com/evidencia-grupo/EvidencIA/issues/36) | **HU15** | Reflection Questions no Painel da Extensão | `epic:e6-engajamento` | @mahiaara | @MylenaTrindade | **08/10/2026** | `must-have` / `mvp:onda-1` | 5 |
| [#37](https://github.com/evidencia-grupo/EvidencIA/issues/37) | **HU16** | Failure/Timeout Handling: Modo Evidence-Only e Eliminação de Mocks | `epic:e3-ia-checagem` | @pedrohpsantos | @lipestile | **09/10/2026** | `must-have` / `mvp:onda-1` | 3 |
| **Total** | | | | | | | | **29 SP** |

---

## 2. Detalhamento das Issues da Sprint 2

### [#10] [HU10] Notificação Rápida de Ausência de Transcrição · 3 SP
- **Labels:** `epic:e2-transcricao`, `must-have`, `mvp:onda-1`
- **Responsável:** @luizoryone
- **Prazo de Entrega:** 06/10/2026

#### Declaração de Valor
> **Como** Mariana (Consumidora de vídeos no YouTube)  
> **Pretendo** ser notificada imediatamente caso o vídeo assistido não possua legendas  
> **Para que** eu não perca tempo aguardando um resultado que não pode ser gerado.

#### Rastreabilidade
- **Épico:** `E2 — Extração de Transcrição`
- **Feature:** `F1.1 — Extração e Higienização de Transcrições`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `06/10/2026`
- **Requisitos Vinculados:** RF-08, RNF-01, RNF-06, RNF-07

#### Critérios de Aceitação (Gherkin)
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

### [#32] [HU16] Provider Abstraction: Migração de OllamaProvider e RemoteLLMProvider · 5 SP
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsável:** @pedrohpsantos
- **Prazo de Entrega:** 06/10/2026

#### Declaração de Valor
> **Como** Equipe de Engenharia / Sistema  
> **Pretendo** utilizar diferentes provedores de LLM por meio de uma interface comum  
> **Para que** não dependa estruturalmente do Ollama local e possamos alternar entre inferência local e remota sem alterar código de negócio.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `06/10/2026`
- **Requisitos Vinculados:** RF-14, RF-15, RNF-06, ADR-006 (Decisão 6)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Provedor de IA independente

  Cenário: Troca de provedor por configuração
    Dado que a variável de ambiente LLM_PROVIDER é alterada de "ollama" para "remote"
    Quando o serviço de backend intermediário é iniciado
    Então as inferências de extração e reflexão devem ser direcionadas ao provedor remoto sem qualquer alteração no código de negócio

  Cenário: Uso de Ollama local com Qwen 2.5-3B
    Dado que LLM_PROVIDER está configurado como "ollama"
    Quando o backend processa uma requisição de extração de alegações
    Então a inferência deve ser executada localmente via OllamaProvider consumindo o modelo configurado

  Cenário: Bloqueio estrito de mock em produção
    Dado que o sistema está em execução com ENV=production
    Quando há qualquer tentativa de configurar LLM_PROVIDER=mock
    Então o sistema deve abortar a inicialização imediatamente com código de erro e registrar evento no log de auditoria
```

#### Checklist de Implementação
- [ ] Conectar `FactCheckerService` ao `get_provider()` de `backend/app/services/providers/factory.py`
- [ ] Implementar `OllamaProvider.extract_claims` e `OllamaProvider.generate_reflection` em `backend/app/services/providers/ollama.py`
- [ ] Implementar `RemoteLLMProvider` em `backend/app/services/providers/remote.py` compatível com endpoints OpenAI/vLLM
- [ ] Desacoplar `fact_checker.py` da importação direta de `ollama_service`
- [ ] Validar que `test_provider_contract.py` passa 100% offline sem falhas

---

### [#33] [HU13] Evidence-First Schema: Migração de Contratos e Eliminação do Score Global · 5 SP
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @pedrohpsantos, @mahiaara
- **Prazo de Entrega:** 07/10/2026

#### Declaração de Valor
> **Como** Amanda (Consumidora Crítica de Conteúdo)  
> **Pretendo** visualizar as principais alegações verificáveis do vídeo separadamente com suas respectivas evidências  
> **Para que** eu investigue cada uma delas sem ser influenciada por uma classificação global ou porcentagem artificial de veracidade.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `07/10/2026`
- **Requisitos Vinculados:** RF-06, RF-07, RNF-07, ADR-006 (Decisões 1 e 2)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Investigação orientada por alegações e contratos evidence-first

  Cenário: Resposta do backend sem score global
    Dado que uma requisição POST para /analyze é enviada com a transcrição do vídeo
    Quando o backend processa a checagem com sucesso
    Então a resposta AnalyzeResponse deve conter a lista claims[] e o objeto reflection_questions
    E os campos score e FactCheckingSource.reliabilityScore não devem ser emitidos

  Cenário: Relação explícita em cada evidência associada à alegação
    Dado que uma alegação verificável foi identificada
    Quando suas evidências são retornadas pelo backend
    Então cada evidência deve possuir a relação explícita ("supports", "contradicts" ou "contextualizes")
    E conter title, url, publisher e published_date válidos

  Cenário: Desserialização compatível no cliente TypeScript
    Dado que a extensão recebe a resposta AnalyzeResponse atualizada
    Quando os tipos em shared/types.ts são consumidos
    Então nenhuma incompatibilidade de tipo deve ocorrer durante a compilação ou execução
```

#### Checklist de Implementação
- [ ] Atualizar schema `backend/app/schemas/` para remover `score` e `reliabilityScore`
- [ ] Estruturar `claims[]` com modelo `Claim` contendo `id`, `text`, `evidence[]`, e `category`
- [ ] Atualizar `shared/types.ts` e `extension/` para os contratos estritos de `Evidence` e `Claim`
- [ ] Atualizar testes em `backend/tests/` para refletir o schema evidence-first

---

### [#34] [HU02] Descongelamento Formal e Remoção do Score Global da UI · 3 SP
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsável:** @MylenaTrindade
- **Prazo de Entrega:** 07/10/2026

#### Declaração de Valor
> **Como** Dona Lurdes (Consumidora de receitas e dicas caseiras de saúde)  
> **Pretendo** visualizar uma síntese objetiva e clara sem indicadores confusos de porcentagem ou velocímetros  
> **Para que** eu compreenda o que tem evidências e o que não tem sem risco de interpretar mal um número simplista.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F2.3 — Síntese Visual e Acessibilidade WCAG`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `07/10/2026`
- **Requisitos Vinculados:** RF-03, RF-06, RNF-07, ADR-006 (Decisão 1)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Remoção de scores globais e velocímetros da interface

  Cenário: Renderização do painel lateral sem score gráfico
    Dado que o usuário aciona a verificação de um vídeo no YouTube
    Quando o painel lateral é renderizado com os resultados
    Então nenhum velocímetro gráfico (gauge), medidor numérico ou porcentagem global deve aparecer na tela
    E a lista atômica de alegações deve ocupar o destaque principal

  Cenário: Remoção segura dos arquivos de score congelados
    Dado que a Sprint 2 formalizou a eliminação do score global
    Quando os componentes legados são removidos
    Então o build de produção da extensão deve compilar com zero erros de TypeScript e zero avisos de dependência órfã
```

#### Checklist de Implementação
- [ ] Descongelar e remover componentes de score/gauge em `extension/src/components/`
- [ ] Atualizar `extension/src/components/Panel.tsx` para renderizar direto a lista de alegações
- [ ] Validar conformidade de contraste e acessibilidade WCAG 2.1 AA
- [ ] Executar build da extensão sem warnings ou erros de linting

---

### [#35] [HU14] Evidence Cards no Painel da Extensão · 5 SP
- **Labels:** `epic:e4-confianca-fontes`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @MylenaTrindade, @luizoryone
- **Prazo de Entrega:** 08/10/2026

#### Declaração de Valor
> **Como** Mayara (Jornalista investigativa e checadora de fatos)  
> **Pretendo** ver quais fontes sustentam, contradizem ou contextualizam cada alegação em cartões dedicados  
> **Para que** eu e qualquer espectador possamos auditar a origem das informações de forma autônoma e imediata.

#### Rastreabilidade
- **Épico:** `E4 — Confiança e Fontes`
- **Feature:** `F2.2 — Auditoria de Fontes e Transparência Editorial`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `08/10/2026`
- **Requisitos Vinculados:** RF-04, RF-13, RNF-05, ADR-006 (Decisões 2 e 5)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Evidence cards no painel da extensão

  Cenário: Exibição completa de atributos de evidência
    Dado que uma alegação possui evidências recuperadas de corpora verificados
    Quando o usuário visualiza o cartão de evidência
    Então título, URL, data de publicação, publisher e a relação factual devem estar explicitamente visíveis

  Cenário: Destaque visual por tipo de relação
    Dado que uma fonte contradiz a afirmação realizada no vídeo
    Quando o cartão dessa evidência é apresentado
    Então o indicador de relação "Contradiz" deve ser exibido com destaque e acompanhado do trecho factual correspondente

  Cenário: Consulta à fonte externa em nova aba
    Dado que o usuário clica no link da fonte jornalística
    Quando a navegação é disparada
    Então a página da fonte deve abrir em uma nova aba com rel="noopener noreferrer"
    E a reprodução do vídeo do YouTube não deve ser interrompida
```

#### Checklist de Implementação
- [ ] Criar componente `EvidenceCard` em `extension/src/components/EvidenceCard.tsx`
- [ ] Exibir título, publisher, data de publicação, relação (`supports`, `contradicts`, `contextualizes`) e trecho
- [ ] Garantir abertura segura com `target="_blank"` e `rel="noopener noreferrer"`
- [ ] Adicionar suporte a estados expansíveis/colapsáveis por alegação com suporte a leitor de tela

---

### [#36] [HU15] Reflection Questions no Painel da Extensão · 5 SP
- **Labels:** `epic:e6-engajamento`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @mahiaara, @MylenaTrindade
- **Prazo de Entrega:** 08/10/2026

#### Declaração de Valor
> **Como** Helena (Professora do ensino médio)  
> **Pretendo** receber perguntas que me ajudem a avaliar a alegação por conta própria antes de formar uma conclusão  
> **Para que** eu estimule o pensamento crítico e a autonomia investigativa sem aceitar vereditos dogmáticos da IA.

#### Rastreabilidade
- **Épico:** `E6 — Engajamento Reflexivo (Promovido para MVP)`
- **Feature:** `F3.1 — Estímulo ao Pensamento Crítico`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `08/10/2026`
- **Requisitos Vinculados:** RF-05, RNF-07, ADR-006 (Decisão 7)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Reflection questions no painel da extensão

  Cenário: Formulação de no mínimo 3 perguntas reflexivas
    Dado que a investigação de um vídeo foi concluída
    Quando o componente de perguntas reflexivas é exibido
    Então pelo menos 3 perguntas neutras orientadas à investigação pessoal devem ser apresentadas

  Cenário: Garantia de neutralidade nas perguntas geradas
    Dado que o assistente de IA formula as perguntas de reflexão
    Quando o texto é gerado
    Então nenhuma pergunta deve declarar se o vídeo está "certo" ou "errado", mantendo postura investigativa aberta

  Cenário: Fechamento ou omissão do bloco sem bloqueio
    Dado que o usuário não deseja interagir com as perguntas reflexivas
    Quando ele recolhe ou ignora a seção
    Então a navegação e a leitura das demais evidências devem seguir normalmente, sem bloqueios
```

#### Checklist de Implementação
- [ ] Integrar geração de perguntas reflexivas no pipeline da LLM (`generate_reflection`)
- [ ] Criar componente `ReflectionQuestions` no painel da extensão
- [ ] Garantir neutralidade e ausência de viés ideológico nos prompts
- [ ] Assegurar foco e navegabilidade por teclado (WCAG 2.1 AA)

---

### [#37] [HU16] Failure/Timeout Handling: Modo Evidence-Only e Eliminação de Mocks · 3 SP
- **Labels:** `epic:e3-ia-checagem`, `must-have`, `mvp:onda-1`
- **Responsáveis:** @pedrohpsantos, @lipestile
- **Prazo de Entrega:** 09/10/2026

#### Declaração de Valor
> **Como** Dona Lurdes (Consumidora de Notícias) e Equipe de Engenharia  
> **Pretendo** receber as evidências factuais recuperadas mesmo se o modelo de linguagem falhar ou demorar  
> **Para que** eu nunca fique sem informação útil e o sistema nunca exiba dados simulados (mocks) em produção.

#### Rastreabilidade
- **Épico:** `E3 — Análise e Checagem via IA`
- **Feature:** `F1.2 — Motor de Checagem Factual e IA`
- **Prioridade MoSCoW:** `Must Have` (Onda 1 - MVP)
- **Sprint:** `Sprint 2 (05/10/2026 a 09/10/2026)`
- **Prazo de Entrega:** `09/10/2026`
- **Requisitos Vinculados:** RF-14, RNF-06, ADR-006 (Decisão 6)

#### Critérios de Aceitação (Gherkin)
```gherkin
Funcionalidade: Degradação graciosa para modo Evidence-Only e eliminação de mocks

  Cenário: Provedor de LLM com timeout ou indisponível
    Dado que o provedor de LLM falha ou excede o timeout de 15 segundos
    Quando a requisição /analyze é processada
    Então o sistema deve retornar as evidências jornalísticas recuperadas no modo "evidence_only"
    E a flag evidence_only=true deve ser enviada para a extensão

  Cenário: Feedback visual claro no painel da extensão
    Dado que a extensão recebe resposta com evidence_only=true
    Quando o painel lateral é renderizado
    Então um aviso amigável deve informar que a síntese de linguagem está temporariamente indisponível
    E os cartões de evidências recuperados devem ser exibidos normalmente

  Cenário: Tentativa de uso de mock em produção
    Dado que o ambiente de execução é ENV=production
    Quando há qualquer tentativa de carregar o MockLLMProvider ou dados simulados
    Então a aplicação deve abortar imediatamente com erro e impedir a resposta com dados fictícios
```

#### Checklist de Implementação
- [ ] Implementar timeout de 15s com fallback para `evidence_only=True` em `FactCheckerService`
- [ ] Validar guard rail de bloqueio de mock em `backend/app/services/providers/factory.py` para `ENV=production`
- [ ] Adicionar banner de aviso no painel Preact quando `evidence_only: true`
- [ ] Testes unitários cobrindo timeout de LLM e retorno exclusivo de evidências
