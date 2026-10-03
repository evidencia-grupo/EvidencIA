# Matriz de Rastreabilidade — EvidencIA

> Documento de rastreabilidade bidirecional entre Requisitos Funcionais (RF), Requisitos Não Funcionais (RNF), Casos de Uso (UC), Histórias de Usuário (HU) e os componentes de código do projeto.
> Fonte de verdade: `documentation/docs/` (branch `docs/reorganizacao`).
> Status: Atualizado para a arquitetura Evidence-First (ADR-006).

---

## Legenda de Status
- **Implementado:** Código funcional, coberto por testes automatizados e em conformidade estrita com a documentação.
- **Parcial:** Funcionalidade básica existente, com melhorias ou dependências de modelos/APIs externas planejadas.
- **Fora do MVP:** Deliberadamente excluído do escopo inicial por decisão de produto (registrado em `DIVERGENCIAS.md`).
- **Divergente:** Implementado com refinamento técnico documentado em `DIVERGENCIAS.md`.

---

## 1. Requisitos Funcionais (RF)

| ID | Descrição Sumária | Módulos / Arquivos Principais | Status | Observações / Testes |
|:---|:---|:---|:---:|:---|
| **RF-01** | Extração de transcrição e metadados de vídeos do YouTube | `extension/src/content/caption-parser.ts`<br>`extension/src/content/caption-extraction.ts`<br>`extension/src/background/player-captions.ts` | **Implementado** | Coberto por `caption-parser.test.ts`, `caption-extraction.test.ts` e `player-captions.test.ts`. Suporta legendas manuais e ASR. |
| **RF-02** | Botão de acionamento não-invasivo na página do vídeo | `extension/src/content/content-script.ts` | **Implementado** | Injetado via Shadow DOM em `#above-the-fold` com botão "Checar Alegações". Testado em `content-script.test.ts`. |
| **RF-03** | Extração de alegações factuais checáveis via IA | `backend/app/providers/base.py`<br>`backend/app/providers/ollama.py`<br>`backend/app/providers/remote.py`<br>`backend/app/services/fact_checker.py` | **Implementado** | Interface `LLMProvider.extract_claims()` com suporte a Qwen 2.5-3B e APIs remotas. Coberto por `test_provider_contract.py`. |
| **RF-04** | Busca e recuperação de evidências em fontes confiáveis | `backend/app/services/brazilian_fact_matcher.py`<br>`backend/app/services/fact_check_client.py` | **Implementado** | Consulta híbrida: `FactChecks.br` local + Google Fact Check Tools API (ClaimReview). Coberto por `test_fact_checker.py`. |
| **RF-05** | Retorno reflexivo com questionamentos epistemológicos | `extension/src/panel/components/ReflectionQuestions.tsx` | **Fora do MVP** | Perguntas são exibidas de forma informativa (HU15/UX-01), mas a interação/coleta ativa de respostas foi excluída do MVP (DIV-01). |
| **RF-06** | Exibição de evidências por alegação (Evidence-First) | `extension/src/panel/components/ClaimCard.tsx`<br>`extension/src/panel/components/EvidenceCard.tsx`<br>`extension/src/panel/index.tsx` | **Implementado** | Substitui velocímetro/score por cards de alegação com evidências e citações auditáveis. Coberto por `index.test.tsx`. |
| **RF-07** | Sinalização explícita de incerteza analítica | `extension/src/panel/components/UncertaintyAlert.tsx`<br>`backend/app/schemas.py` | **Implementado** | Estados canônicos: `supported`, `contradicted`, `contextualized`, `conflicting`, `insufficient_evidence`. |
| **RF-08** | Contextualização temporal de alegações e publicações | `backend/app/schemas.py`<br>`shared/types/api.ts`<br>`extension/src/panel/components/ClaimCard.tsx` | **Implementado** | Campos `temporalContext` (ano de publicação, defasagem temporal e notas explicativas). |
| **RF-09** | Painel lateral com tema escuro e abertura sob demanda | `extension/src/panel/index.tsx`<br>`extension/src/panel/styles/theme.css` | **Implementado** | Iframe sandboxed aberto ao clicar no botão ou via mensagens do content script. Suporta tecla Escape. |
| **RF-10** | Coleta de feedback do usuário sobre a checagem | N/A | **Fora do MVP** | Excluído formalmente do escopo do MVP por decisão de produto (DIV-01). |
| **RF-11** | Cache local de resultados de checagem | `extension/src/background/cache-manager.ts`<br>`extension/src/background/service-worker.ts` | **Implementado** | Persistência em `chrome.storage.local` com TTL de 24h (86400000 ms). Coberto por `cache-manager.test.ts`. |
| **RF-12** | Sinalização de evidência insuficiente (`insufficient_evidence`) | `backend/app/services/fact_checker.py`<br>`extension/src/panel/components/UncertaintyAlert.tsx` | **Implementado** | Quando não há correspondência documental confiável, o sistema explicita que não há evidências suficientes para checar. |
| **RF-13** | Rastreabilidade e proveniência de dados das evidências | `shared/types/api.ts`<br>`backend/app/schemas.py`<br>`backend/app/services/brazilian_fact_matcher.py` | **Implementado** | Objeto `provenance` com dataset de origem (`factchecks_br`), timestamp de indexação e hash do conteúdo. |
| **RF-14** | Degradação graciosa para modo exclusivo de evidências | `backend/app/services/fact_checker.py`<br>`extension/src/panel/index.tsx` | **Implementado** | Em caso de timeout/falha do LLM, chaveia para `analysisMode="evidence_only"`, exibindo banner e evidências recuperadas. |

---

## 2. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição | Arquivos Envolvidos | Status | Evidência de Validação |
|:---|:---|:---|:---|:---:|:---|
| **RNF-01** | Segurança | Backend Proxy sem chaves no cliente | `backend/app/config.py`<br>`backend/app/providers/factory.py`<br>`extension/manifest.json` | **Implementado** | `SEC-01` e `SEC-02` passam. Chaves de IA e busca vivem estritamente no backend. Guarda anti-mock `MockInProductionError` ativa. |
| **RNF-02** | Desempenho / TBT | Impacto no carregamento da página $\le 50\text{ ms}$ | `extension/src/content/content-script.ts` | **Implementado** | Injeção assíncrona, Shadow DOM isolado, sem bibliotecas pesadas no content script. |
| **RNF-03** | Compatibilidade | Navegadores baseados em Chromium (Chrome, Edge, Brave) | `extension/manifest.json` | **Implementado** | Manifest V3 padrão, sem APIs exclusivas do Chrome. |
| **RNF-04** | Desempenho | Tempo de resposta total $\le 10\text{ s}$ | `extension/src/background/service-worker.ts`<br>`backend/app/services/fact_checker.py` | **Implementado** | Orçamento estrito: deadline de 9.5s no cliente, timeout de 8.0s no backend. Testes de timeout passam. |
| **RNF-05** | Privacidade | Conformidade com LGPD, permissões mínimas, sem rastreamento | `extension/manifest.json`<br>`extension/src/telemetry/` | **Implementado** | Sem envio de histórico de navegação à rede. Telemetria local sanitizada (`sanitize.test.ts`, `no-network.test.ts`). |
| **RNF-06** | Usabilidade / Tolerância | Mensagens amigáveis em português e tratamento de falhas | `extension/src/content/friendly-messages.ts`<br>`extension/src/panel/index.tsx` | **Implementado** | Textos explicativos para vídeo sem legenda, timeout de servidor e indisponibilidade de rede (`friendly-messages.test.ts`). |
| **RNF-07** | Acessibilidade | Conformidade WCAG 2.1 nível AA | `extension/src/panel/`<br>`extension/src/content/content-script.ts` | **Implementado** | Navegação integral por teclado, contraste alto validado, suporte a leitor de tela (testado com `@axe-core/playwright`). |

---

## 3. Histórias de Usuário (HU)

| ID | Título da História | Componentes Relacionados | Status | Critério de Aceitação |
|:---|:---|:---|:---:|:---|
| **HU01** | Extração de transcrição do vídeo | `caption-parser.ts`, `player-captions.ts` | **Implementado** | Extração síncrona/assíncrona sem interromper reprodução do vídeo. |
| **HU02** | Botão discreto de acionamento | `content-script.ts` | **Implementado** | Botão inserido na barra de ações do YouTube, respeitando o tema escuro. |
| **HU03** | Execução e SLA da checagem (<10s) | `service-worker.ts`, `fact_checker.py` | **Implementado** | Feedback de início imediato (<1s) e conclusão ou erro dentro de 10s. |
| **HU04** | Extração e exibição de alegações | `base.py`, `ollama.py`, `ClaimCard.tsx` | **Implementado** | Alegações centrais identificadas e apresentadas de forma isolada. |
| **HU05** | Consulta a fontes e bases factuais | `brazilian_fact_matcher.py`, `EvidenceCard.tsx` | **Implementado** | Citações diretas com títulos de fontes auditáveis e links externos. |
| **HU06** | Recuperação instantânea por Cache (<100ms) | `cache-manager.ts`, `service-worker.ts` | **Implementado** | Vídeos checados nas últimas 24h carregam instantaneamente sem rede. |
| **HU07** | Fechamento e atalhos de teclado do painel | `index.tsx`, `content-script.ts` | **Implementado** | Fechamento por botão e tecla Escape com retorno do foco ao player. |
| **HU08** | Contextualização de conteúdo antigo | `schemas.py`, `ClaimCard.tsx` | **Implementado** | Alerta quando alegações antigas são reapresentadas fora de contexto temporal. |
| **HU09** | Alerta de incerteza analítica | `UncertaintyAlert.tsx` | **Implementado** | Sinalização visível de controvérsia ou ausência de dados empíricos. |
| **HU10** | Vídeo sem legendas disponíveis | `friendly-messages.ts`, `index.tsx` | **Implementado** | Notificação clara ao usuário sem erro genérico de sistema. |
| **HU11** | Acessibilidade completa WCAG 2.1 AA | `index.tsx`, `theme.css`, `ClaimCard.tsx` | **Implementado** | Navegação completa por teclado, atributos ARIA e contraste $\ge 4.5:1$. |
| **HU12** | Interrupção por navegação do YouTube (SPA) | `content-script.ts` | **Implementado** | Troca de vídeo via `yt-navigate-finish` aborta checagem em andamento. |
| **HU13** | Apresentação Evidence-First por alegação | `ClaimCard.tsx`, `EvidenceCard.tsx` | **Implementado** | Alegação acompanhada diretamente por suas fontes pró, contra ou de contexto. |
| **HU14** | Card de evidência auditável | `EvidenceCard.tsx` | **Implementado** | Exibe trecho citado, veículo jornalístico, data e link para checagem original. |
| **HU15** | Perguntas reflexivas não-intrusivas | `ReflectionQuestions.tsx` | **Implementado** | Perguntas que instigam pensamento crítico sem exigir resposta ou formulário. |
| **HU16** | Degradação de IA (Modo Evidence-Only) | `fact_checker.py`, `index.tsx` | **Implementado** | Exibição das evidências recuperadas mesmo se o motor de síntese por IA falhar. |

---

## 4. Casos de Uso (UC)

| ID | Nome do Caso de Uso | Fluxo de Implementação | Status |
|:---|:---|:---|:---:|
| **UC01** | Checar vídeo em reprodução no YouTube | Usuário clica em "Checar Alegações" → Content script obtém legendas → Background despacha requisição com deadline → Backend busca evidências e extrai alegações → Painel exibe os cards. | **Implementado** |
| **UC02** | Consultar checagem em cache local | Content script solicita cache ao Service Worker → Se válido (< 24h), entrega imediatamente em < 100ms sem tráfego de rede. | **Implementado** |
| **UC03** | Tratar vídeo sem legendas ou transcrição | Content script detecta ausência de faixa de legendas → Emite evento `NO_CAPTIONS_AVAILABLE` → Painel instrui usuário com mensagem amigável. | **Implementado** |
| **UC04** | Tratar indisponibilidade temporária de rede | Requisição falha por HTTP 5xx ou timeout de 9.5s → Sistema captura exceção e exibe mensagem amigável com botão "Tentar novamente". | **Implementado** |
| **UC05** | Operar painel exclusivamente via teclado | Usuário navega com Tab até o botão, aciona com Enter/Espaço, percorre os cards com Tab e fecha com Escape. | **Implementado** |
| **UC06** | Navegar entre vídeos no player (SPA) | Evento nativo `yt-navigate-finish` reseta instâncias, remove badge anterior e aborta controllers assíncronos. | **Implementado** |
