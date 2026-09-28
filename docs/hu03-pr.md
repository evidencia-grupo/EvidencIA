## Identificação da mudança

- **Issue relacionada:** Refs #3 (não fechar até homologação com IA/busca real).
- **História:** HU03 — Checagem Rápida e Factual no Player.
- **Tipo:** Feature, Bugfix e Docs.

## Descrição técnica

Ao acionar a checagem, o botão confirma imediatamente, consulta primeiro o cache de 24h e sincroniza o painel mesmo quando o iframe ainda está carregando. Sem cache, lê as faixas do vídeo atual no contexto MAIN do Chrome, extrai a transcrição e solicita análise ao proxy com o orçamento restante do prazo total. Erros, ausência de legendas e timeout encerram o carregamento com possibilidade de nova tentativa; navegação invalida respostas antigas.

Inclui teclado/foco, contraste, validação das respostas, testes de regressão, cobertura por arquivo e testes Chromium/axe na CI. Resultados simulados ficam explicitamente identificados no contrato e na interface; provedores não integrados retornam erro, e o health identifica a integração pendente. Requer atualização conjunta de backend e extensão, pois `analysisMode` passou a ser obrigatório. A permissão `scripting` lê somente dados do player no host YouTube já autorizado.

## Rastreabilidade e conformidade

- **Épico / Feature:** E1 — Gatilho e Ativação / F2.1 — Disparo e Exibição Acessível WCAG.
- **Requisitos:** RF-01, RF-09, RNF-01; RNF-02 e RNF-07 para desempenho e acessibilidade.
- **ADRs:** ADR-001, ADR-002 e ADR-003.
- **Evidência:** [HU03](../HU03.md) e [relatório de validação](hu03-evidencias.md).

## Checklist de qualidade

- [x] Código compilado e tipado sem erros; Ruff aprovado.
- [x] Testes unitários implementados e passando: 63 da extensão e 10 do backend.
- [x] Cobertura acima de 80% nos módulos alterados: extensão 99,74% de linhas; backend 97,62% com ramificações.
- [x] Nenhum segredo ou credencial privada incluído no commit.
- [x] Navegabilidade por teclado validada em Chromium: Tab, Shift+Tab, Enter, Espaço e Escape.
- [ ] WCAG 2.1 AA integral: auditoria automática sem violações e contraste dos estados testados; revisão humana com leitor de tela ainda pendente.
- [ ] SLA e TBT homologados em produção: testes locais passam, mas IA/busca real ainda será implementada pela equipe.
- [x] Mensagens de commit no padrão Conventional Commits.

## Validação e limites

7 testes Playwright completos passaram. Em 10 execuções adicionais com FastAPI real e provedor mock: feedback máximo 23,3ms; síntese simulada máxima 437,6ms; cache máximo 31,8ms; excedente de tarefas longas 0ms na página controlada. P90 da síntese: 435,8ms. Estes resultados não medem qualidade factual ou latência de provedor externo.

Faltam a integração real de IA/busca, homologação com rede/vídeos reais e atualização do catálogo/matriz no portal externo. A CI foi configurada para reproduzir os checks; a execução remota ainda depende do envio da branch e abertura do PR.
