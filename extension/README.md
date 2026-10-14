# EvidencIA — Extensão de Navegador (Manifest V3)

> Extensão Chromium (Chrome, Edge, Brave) com interface em Preact, isolamento via Shadow DOM, conformidade com **WCAG 2.1 AA** e cache local de 24h em `chrome.storage.local`.

---

## 1. Estrutura do Módulo

```text
extension/
├── manifest.json              # Manifesto V3 com permissões mínimas (storage, scripting)
├── vite.config.ts             # Build multi-entry (service-worker, content-script, panel)
└── src/
    ├── background/            # Service worker, cache manager (TTL 24h) e autenticação
    ├── content/               # Content script in-page, injeção Shadow DOM e caption parser
    └── panel/                 # Interface do painel lateral em Preact (Cards e A11y)
```

---

## 2. Instalação e Compilação

```bash
# 1. Instalar dependências
npm install

# 2. Compilar bundles de produção (gera artefatos em dist/)
npm run build

# 3. Modo desenvolvimento contínuo (Watch)
npm run dev
```

---

## 3. Como Carregar no Navegador

1. Acesse `chrome://extensions/` no Chrome ou `edge://extensions/` no Edge.
2. Ative a chave **Modo do desenvolvedor** (*Developer mode*).
3. Clique em **Carregar sem compactação** (*Load unpacked*).
4. Selecione o diretório compilado `extension/dist/`.
5. Abra qualquer vídeo do YouTube (`youtube.com/watch?v=...`) e acione **Checar Alegações**.

### Pacote para a Chrome Web Store

```bash
# Build de produção + verificação (ícones, permissões, hosts HTTPS, sem código remoto) + zip
VITE_API_BASE_URL=https://<backend-de-producao> npm run package

# Regerar ícones (de assets/logo-icon.svg) e imagens da listagem (pasta store/)
npm run icons
npm run store:screenshots
```

Roteiro completo, textos da listagem e respostas da aba de privacidade: [Publicação na Chrome Web Store](https://evidencia-grupo.github.io/documentation/operacao/publicacao-chrome-web-store/).

---

## 4. Testes Automatizados e Linters

```bash
# Execução da suíte completa de testes (Vitest + axe-core WCAG 2.1 AA)
npm test

# Verificação estrita de tipagem TypeScript
npm run lint

# Testes com relatório de cobertura (mínimo: 81%)
npm run test:coverage
```

Documentação de interface e Design System: [docs/requisitos/design-system.md](https://github.com/evidencia-grupo/documentation/blob/main/docs/requisitos/design-system.md).
