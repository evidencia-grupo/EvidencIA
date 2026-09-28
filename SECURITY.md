# Politica de Seguranca da Informacao — EvidencIA

> Diretrizes de seguranca, isolamento de credenciais e procedimento formal para reporte de vulnerabilidades.

---

## 1. Escopo de Seguranca e Principios Arquiteturais

A arquitetura do EvidencIA adota o modelo de **Confianca Zero no Cliente (Zero Trust Client-Side)**:

1. **Isolamento Absoluto de Credenciais:** O codigo da extensao de navegador nao armazena chaves de API, tokens de acesso a modelos de linguagem ou credenciais upstream. Toda a comunicacao externa e intermediada pelo **Backend Proxy Seguro** ([ADR-002](../documentation/docs/tecnico/decisoes/ADR-002-backend-proxy.md)).
2. **Privacidade por Padrao (Conformidade LGPD):** A extensao opera exclusivamente sob a permissao restrita `activeTab` e escopo `https://www.youtube.com/*`. Nao ha coleta de historico geral de navegacao nem retencao de dados de navegacao em servidores ([RNF-05](../documentation/docs/requisitos/catalogo-requisitos.md#rnf-05)).
3. **Isolamento de DOM e Contexto de Execucao:**
   - Botao de veracidade injetado via **Shadow DOM** aberto para isolamento de estilos e eventos do YouTube.
   - Painel lateral executado em **iFrame Sandboxed** (`sandbox="allow-scripts"`), prevenindo cross-site scripting (XSS) e vazamento de informacoes entre origens.
4. **Protecao de Servico:** O backend proxy implementa limitadores de requisicao (*Rate Limiting*) por endereco IP e controle estrito de CORS para conter abusos e ataques de negacao de servico.

---

## 2. Versoes Suportadas

Apenas a versao corrente da branch principal e compativel com correcoes de seguranca ativas:

| Versao | Suporte de Seguranca |
|:---|:---:|
| 1.0.x (Release MVP) | Sim |
| Versoes de Desenvolvimento (`main`) | Sim |

---

## 3. Reporte de Vulnerabilidades

Caso identifique uma vulnerabilidade de seguranca, falha de isolamento de credenciais ou brecha de privacidade:

1. **Nao abra uma issue publica no GitHub.**
2. Envie um relatorio confidencial detalhado para a equipe de manutencao do repositorio ou contate diretamente os administradores do projeto.
3. Inclua no relatorio:
   - Descricao da vulnerabilidade identificada;
   - Passos detalhados para reproducao do cenario;
   - Impacto potencial conforme o modelo de ameacas STRIDE homologado na documentacao;
   - Proposta de mitigacao ou patch corretivo, caso disponivel.

A equipe realizara a triagem da ocorrencia em ate 48 horas uteis e aplicara a correcao prioritariamente no ciclo de sprint ativo.
