# Extensão EvidencIA

Chrome Manifest V3 / Preact / TypeScript. Node 24.

```bash
npm ci --ignore-scripts
npm run typecheck
npm run test:coverage
npm run build
npx playwright install chromium
E2E_PYTHON=../backend/.venv/bin/python npm run test:e2e
```

Carregue `dist` como extensão descompactada. Build local usa backend `http://127.0.0.1:8000`.

Produção: configure `VITE_API_BASE_URL` HTTPS e execute `npm run build:prod`. O manifesto gerado usa somente a origem configurada e YouTube; não libera hosts cloud por wildcard.

Legendas com tempo preservam segmentos reais. O cache por vídeo tem TTL de 24h e tolera falha de cota. Mensagens exigem `sender.id` próprio e origem YouTube; `postMessage` valida origem e janela. Token é emitido/renovado após 401/403, com no máximo uma nova tentativa.

Os E2E usam páginas e legendas interceptadas, com backend local em mock. Testes locais não certificam comportamento em todos os vídeos reais.

[Requisitos e decisões](https://github.com/evidencia-grupo/documentation).
