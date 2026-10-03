# Registro de Divergências — EvidencIA

> Documento de alinhamento entre a documentação oficial (`documentation`, branch `docs/reorganizacao`) e o código do repositório de desenvolvimento (`EvidencIA`).
> Data de emissão: Outubro de 2026.
> Regra de governança: A documentação é a fonte de verdade. Discrepâncias de escopo, permissões de plataforma ou refinamentos técnicos de engenharia são registradas neste artefato com contexto, impacto e recomendação.

---

## Sumário das Divergências Identificadas

| ID | Tema | Versão Documentação | Versão Código / Implementação | Impacto | Recomendação |
|:---|:---|:---|:---|:---|:---|
| **DIV-01** | Escopo MVP: Retorno Reflexivo (RF-05) e Feedback (RF-10) | Listados como requisitos funcionais do sistema | Excluídos explicitamente do MVP por decisão de produto. Componente de reflexão (`ReflectionQuestions.tsx`) opera de modo passivo/informativo sem coleta ou persistência. | Baixo | Atualizar o catálogo de requisitos em `documentation` marcando RF-05 e RF-10 como `Pós-MVP`. |
| **DIV-02** | Permissão `scripting` no Manifest V3 (RNF-05) | RNF-05 restringe permissões a `activeTab` e `storage` | `manifest.json` inclui `scripting` restrita a `https://www.youtube.com/*`. | Médio (Segurança/Privacidade) | Documentar no ADR de segurança e no manifesto que a permissão `scripting` é estritamente necessária para ler faixas de legendas do player do YouTube (`window.ytInitialPlayerResponse`) no contexto `MAIN`. |
| **DIV-03** | Autenticação no Backend Proxy (RNF-01) | Menciona backend proxy autenticado para proteger APIs | MVP implementa autenticação em nível de aplicação/cliente (CORS restrito a extensões, cabeçalho `X-Client-Version` e Rate Limiting por IP), sem exigir cadastro/login de usuário final. | Baixo | Clarificar na documentação que o MVP adota autenticação de aplicação cliente, postergando JWT/OAuth de usuário final para versão com contas pessoais. |
| **DIV-04** | Extinção de Score Global e Termos de "Veracidade" (ADR-006) | Sprint 1 previa score 0-100% e velocímetro; Sprint 2 adota arquitetura Evidence-First (ADR-006) | Código foi 100% alinhado: `Gauge.tsx`, `SourceList.tsx` e qualquer menção a score/veracidade foram eliminados. Todo resultado é orientado a alegações e evidências documentais. | Alto (Arquitetural) | Garantir que o repositório de documentação reflita a remoção definitiva do gauge e do score numérico em todos os diagramas e textos. |
| **DIV-05** | Degradação Graciosa: Modo Evidence-Only (RF-14 / Issue #37) | Documentação de Sprint 2 especifica degradação graciosa em timeout de LLM | Implementado em `fact_checker.py`: quando o motor LLM falha ou esgota o tempo limite, o sistema entrega as evidências recuperadas diretamente das bases (`FactChecks.br`), com `analysisMode: "evidence_only"`. | Positivo (Resiliência) | Consolidar a especificação do RF-14 e da HU16 na documentação técnica. |
| **DIV-06** | Papéis dos Datasets Brasileiros (DATA-01) | `sources.yaml` especifica papéis dos corpora locais | `Fake.br` é tratado como corpus linguístico (NLP); `FactChecks.br` é a base primária de evidências factuais para recuperação via `brazilian_fact_matcher.py`. | Baixo | Alinhar os cartões de dados (Dataset Cards) da documentação para deixar explícito que `Fake.br` não deve ser usado como base de checagem factual. |
| **DIV-07** | Orçamento de Tempo e SLA de 10s (RNF-04) | SLA global exige resposta em $\le 10\text{ s}$ | O content script aborta em 9.5s e o backend tem timeout interno de LLM de 8.0s, garantindo que o teto de 10s nunca seja violado por atrasos de rede. | Neutro | Documentar o particionamento do orçamento de tempo (8s backend + 1.5s margem de rede/renderização). |
| **DIV-08** | Inclusão da HU11 (Acessibilidade WCAG 2.1 AA) no MVP | Inicialmente planejada para refinamento | Implementada integralmente no MVP: navegação completa por teclado, contraste alto validado e atributos semânticos ARIA no painel Preact. | Positivo | Manter HU11 como parte integrante e obrigatória do MVP na documentação. |

---

## Detalhamento das Divergências

### DIV-01: RF-05 (Retorno Reflexivo) e RF-10 (Feedback do Usuário)
- **Documentação:** Especificava que a extensão deveria permitir que o usuário respondesse a perguntas reflexivas e avaliasse a utilidade da checagem.
- **Código:** Por orientação explícita do autor do projeto, qualquer interação com envio de feedback foi descartada do MVP para evitar complexidade desnecessária de banco de dados e coleta de dados pessoais (LGPD). O componente `ReflectionQuestions.tsx` exibe perguntas metodológicas apenas para reflexão individual do leitor.
- **Ação Recomendada:** Atualizar o catálogo de requisitos em `documentation/docs/requisitos/catalogo-requisitos.md` marcando RF-05 e RF-10 como fora do MVP.

### DIV-02: Permissão `scripting` no Manifest V3
- **Documentação:** Cita permissão restrita a `activeTab` e `storage` (RNF-05).
- **Código:** `extension/manifest.json` declara:
  ```json
  "permissions": ["activeTab", "storage", "scripting"]
  ```
- **Justificativa Técnica:** O YouTube renderiza legendas de modo dinâmico em componentes proprietários do player. Quando o endpoint `/api/timedtext` não é invocado diretamente, a única forma de obter as faixas de legendas sem violar a estabilidade é executar um script pontual no mundo da página para ler `window.ytInitialPlayerResponse.captions`. A extensão restringe isso unicamente a URLs `https://www.youtube.com/*`.
- **Ação Recomendada:** Adicionar justificativa no RNF-05 e na documentação de extensão para submissão à Chrome Web Store.

### DIV-03: Modelo de Autenticação no Backend Proxy
- **Documentação:** Menciona "backend proxy autenticado".
- **Código:** A autenticação no MVP protege contra uso abusivo de terceiros via:
  1. Restrição de CORS (`chrome-extension://*`);
  2. Validação de versão do cliente (`X-Client-Version`);
  3. Rate limiting no gateway (`RATE_LIMIT_MAX_PER_MINUTE`);
  4. Centralização de chaves de IA/Busca estritamente no servidor (RNF-01).
  Não há sistema de contas ou login por senha/OAuth para o usuário final.
- **Ação Recomendada:** Ajustar a redação para "Proxy com controle de acesso e chaves centralizadas", evitando a impressão de que o usuário precisa criar conta para usar a extensão.

### DIV-04: Transição Completa para Evidence-First (ADR-006)
- **Documentação:** Reorganizada para o paradigma Evidence-First, eliminando o conceito de veracidade numérica.
- **Código:** Todo o código legado do Sprint 1 (`Gauge.tsx`, `SourceList.tsx`, scores 0-100, status "verdadeiro/falso") foi completamente expurgado da base de código. A interface exibe:
  - Lista de alegações extraídas;
  - Relação de cada evidência documental (`supports`, `contradicts`, `contextualizes`);
  - Indicador de incerteza analítica (`supported`, `contradicted`, `contextualized`, `conflicting`, `insufficient_evidence`);
  - Perguntas reflexivas não-intrusivas.
- **Ação Recomendada:** Aprovar a remoção do código legado e certificar que todos os materiais da Sprint 2 na documentação referenciem `EvidenceCard.tsx` e `ReflectionQuestions.tsx`.
