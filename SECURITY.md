# Politica de Seguranca — EvidencIA

Este documento define as diretrizes de seguranca, protocolo de divulgacao responsavel e principios de protecao da informacao adotados no projeto EvidencIA.

---

## 1. Versoes Suportadas

Priorizamos a correcao ativa de falhas de seguranca na versao estavel mais recente.

| Versao | Status de Suporte |
| --- | --- |
| 1.0.x (Release GO) | Suportada ativamente com correcoes de seguranca |
| versoes pre-1.0 | Descontinuadas / Sem suporte |

---

## 2. Reporte Responsavel de Vulnerabilidades

Caso voce identifique uma vulnerabilidade de seguranca em qualquer componente do EvidencIA (Extensao Manifest V3, Backend Proxy ou schemas compartilhados), solicitamos que nao abra uma issue publica imediatamente.

### Procedimento de Notificacao

1. Envie um e-mail detalhado para a equipe de seguranca ou utilize a funcionalidade de **Security Advisories** do GitHub:
   - Contato: `seguranca@evidencia.org` ou abra um [GitHub Private Security Advisory](https://github.com/evidencia-grupo/EvidencIA/security/advisories/new).
2. Inclua as seguintes informacoes no relatorio:
   - Descricao detalhada da vulnerabilidade e vetor de ataque.
   - Prova de conceito (PoC) ou passos reprodutiveis minimos.
   - Componente e versoes afetadas.
   - Avaliacao de impacto potencial (confidencialidade, integridade, disponibilidade).
3. Aguarde o retorno antes de qualquer divulgacao publica.

### Nossos Compromissos e SLA

- **Confirmacao de Recebimento:** em ate 48 horas uteis.
- **Triagem e Avaliacao Inicial:** em ate 5 dias uteis.
- **Plano de Remediacao e Patch:** priorizado de acordo com a severidade (CVSS v3).
- **Divulgacao Coordenada:** os creditos serao atribuidos ao pesquisador no changelog e advisory de seguranca apos a publicacao do patch.

---

## 3. Principios de Seguranca e Invariantes Arquiteturais

O EvidencIA segue uma linha de base defensiva estrita:

1. **Zero Segredos no Cliente (ADR-002):** A extensao de navegador nao contem tokens de API de terceiros, chaves privadas ou credenciais persistentes. Todas as integracoes ocorrem exclusivamente via Backend Proxy.
2. **Privacidade e LGPD (ADR-004):** O sistema opera de forma anonima. Nao coletamos identificadores pessoais, cookies de sessao, credenciais do Google/YouTube ou historico de navegacao. Os identificadores de instalacao sao rotativos e efemeros.
3. **Isolamento de Dados Nao Confiaveis:** Transcricoes de videos do YouTube sao tratadas estritamente como texto nao confiavel. Elas nunca sao executadas em contexto de avaliacao dinamica (sem `eval`, sem deserializacao insegura).
4. **Resistencia a Injecao de Prompt:** As diretrizes do modelo de linguagem separam dados de instrucoes atraves de schemas Pydantic tipados com validacao estrita (`StrictModel`).
5. **Acessibilidade e Usabilidade:** Em conformidade com a WCAG 2.1 AA, componentes de interface garantem navegacao segura e inclusiva por teclado e leitores de tela.
