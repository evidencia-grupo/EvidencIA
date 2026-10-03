# EvidencIA — Extensão de Navegador (Manifest V3)

> Extensão para navegadores Chromium (Google Chrome, Microsoft Edge e Brave) para checagem factual em vídeos do YouTube com arquitetura Evidence-First e interface acessível em Preact.

---

## 1. Visão Geral e Princípios Técnicos

A extensão **EvidencIA** é executada diretamente nas páginas de reprodução do YouTube (`https://www.youtube.com/watch?v=...`) e atua como a interface do usuário com as ferramentas de checagem.

### Princípios Arquiteturais e Decisões Formais (ADRs)
- **Manifest V3 e Princípio do Menor Privilégio ([ADR-001](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-001-manifest-v3.md)):** Declaração mínima e estrita de permissões (`activeTab`, `storage`). O host permission é restrito unicamente a `*://*.youtube.com/*`. Não são executados scripts remotos, em estrita conformidade com a política de segurança da Chrome Web Store.
- **Cache Local com TTL de 24h ([ADR-003](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-003-estrategia-cache-local.md)):** Resultados de checagens anteriores são gravados em `chrome.storage.local`. Ao revisitar um vídeo já analisado, o painel é carregado instantaneamente em menos de 100 ms ([RNF-04](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-04)), poupando requisições ao backend proxy.
- **Preact, TypeScript e Shadow DOM ([ADR-004](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-004-stack-tecnologica.md)):** A interface do painel lateral utiliza Preact (~4 kB) e é injetada via **Shadow DOM fechado/isolado**, prevenindo colisões entre o CSS do YouTube e o design system do EvidencIA.
- **Paradigma Evidence-First ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md)):** A extensão exibe evidências rastreáveis e perguntas reflexivas ([HU15](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu15)) por alegação, abolindo vereditos simplistas e scores globais de veracidade.
- **Acessibilidade Universal ([HU11](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu11) / [RNF-07](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-07)):** Total conformidade com as diretrizes WCAG 2.1 nível AA: navegação completa via teclado, atributos ARIA adequados e contraste de cores superior a 4.5:1.

---

## 2. Estrutura do Módulo

```text
extension/
├── manifest.json              # Manifesto V3 com permissões mínimas
├── package.json               # Dependências de compilação (Preact, Vite, TypeScript, Vitest)
├── tsconfig.json              # Configuração estrita de TypeScript
├── vite.config.ts             # Build multi-entry para Service Worker, Content Script e Panel
└── src/
    ├── background/            # Service Worker e infraestrutura de segundo plano
    │   ├── service-worker.ts      # Roteador central de mensagens e ciclo de vida MV3
    │   ├── cache-manager.ts       # Gestor de armazenamento em chrome.storage.local (TTL 24h)
    │   ├── response-validation.ts # Validador em tempo de execução dos contratos de API
    │   └── player-captions.ts     # Fallback de extração de legendas via Player API
    ├── content/               # Content Script injetado nas páginas do YouTube
    │   ├── content-script.ts      # Observador de navegação SPA, injeção de botão e Shadow DOM
    │   ├── caption-parser.ts      # Parser robusto de legendas (Timed Text XML e JSON)
    │   └── friendly-messages.ts   # Mensagens amigáveis de status, erro e degradação
    └── panel/                 # Interface do Painel Lateral em Preact
        ├── index.tsx              # Componente raiz do painel lateral
        ├── index.html             # Shell HTML de desenvolvimento e montagem
        ├── components/            # Componentes visuais acessíveis (Design System)
        │   ├── ClaimCard.tsx          # Card de alegação com selo temporal e incerteza
        │   ├── EvidenceCard.tsx       # Card de evidência rastreável com link para agência
        │   ├── ReflectionQuestions.tsx# Perguntas orientadoras de pensamento crítico
        │   └── UncertaintyAlert.tsx   # Alerta de evidência conflitante ou insuficiente
        └── styles/
            └── theme.css          # Variáveis CSS (Design Tokens, Dark/Light Mode, WCAG AA)
```

---

## 3. Como Desenvolver e Compilar

### 3.1 Pré-requisitos
- **Node.js** >= 20 LTS
- **npm** >= 10

### 3.2 Instalação das Dependências
```bash
npm install
```

### 3.3 Compilação de Produção
```bash
npm run build
```
O build gera os artefatos empacotados no diretório `extension/dist/`, pronto para ser carregado no navegador.

### 3.4 Modo Desenvolvimento (Watch)
```bash
npm run dev
```

---

## 4. Como Carregar a Extensão no Navegador

1. Abra a página de extensões do seu navegador:
   - **Google Chrome:** `chrome://extensions/`
   - **Microsoft Edge:** `edge://extensions/`
   - **Brave Browser:** `brave://extensions/`
2. No canto superior direito, ative a chave **Modo do desenvolvedor** (*Developer mode*).
3. Clique no botão **Carregar sem compactação** (*Load unpacked*).
4. Selecione a pasta `extension/dist`.
5. Acesse um vídeo qualquer no YouTube (`https://www.youtube.com/watch?v=...`) e utilize o botão **Checar Alegações**.

---

## 5. Como Executar a Suíte de Testes

A suíte automatizada combina testes unitários rápidos e testes de componentes com JSDOM:

```bash
# Executar todos os testes com Vitest
npm test

# Executar verificação de tipagem estrita (TypeScript)
npm run lint

# Executar testes em modo observação (Watch)
npm run test:watch

# Executar cobertura de testes
npm run test:coverage
```

---

## 6. Rastreabilidade com a Documentação Oficial

Toda a especificação conceitual e técnica deste módulo reside no repositório oficial [evidencia-grupo/documentation](https://github.com/evidencia-grupo/documentation) (branch `docs/reorganizacao`):

- **Arquitetura Geral:** [Documento de Arquitetura de Software](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/arquitetura.md)
- **Design System:** [Design System e Componentes Preact](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/design/design-system.md)
- **Decisões Arquiteturais:**
  - [ADR-001: Manifest V3 e Permissões Mínimas](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-001-manifest-v3.md)
  - [ADR-003: Estratégia de Cache Local com TTL](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-003-estrategia-cache-local.md)
  - [ADR-004: Stack Tecnológica (Preact + TypeScript)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-004-stack-tecnologica.md)
  - [ADR-006: Arquitetura Evidence-First](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md)
- **Histórias de Usuário:**
  - [HU06 — Feedback de Progresso e Degradação Graciosa](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu06)
  - [HU08 — Botão Discreto na Interface do YouTube](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu08)
  - [HU09 — Painel Lateral com Alegações e Evidências](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu09)
  - [HU10 — Alertas Climatológicos, Saúde e Fraudes](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu10)
  - [HU11 — Acessibilidade WCAG 2.1 AA no Painel Lateral](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu11)
  - [HU15 — Perguntas Reflexivas para Pensamento Crítico](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu15)
- **Validação e Qualidade:** [Estratégia de Testes](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/estrategia-testes.md)
