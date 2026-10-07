# Matriz Consolidada de Technical Gates — EvidencIA (Fase 4)

**Data de Validação:** 2026-10-07  
**Estado Geral:** 🟢 100% PASS (17 de 17 Portões Aprovados)  
**Branch:** `codex/go-phase-01-hardening`  

---

| # | Technical Gate | Critério Objetivo de Sucesso | Comando / Evidência Executada | Resultado Real |
| :-: | :--- | :--- | :--- | :---: |
| **01** | **Build Frontend (MV3)** | Bundle de background, content e panel gerados sem erros de TypeScript e Vite | `npm run build` | 🟢 PASS |
| **02** | **Testes Frontend & A11y** | 100% dos testes Vitest passando, incluindo testes de acessibilidade axe-core (WCAG 2.1 AA) | `npm test` (171/171 testes aprovados) | 🟢 PASS |
| **03** | **Testes Backend (Pytest)** | Suíte completa de testes unitários e de integração aprovada sem falhas | `pytest backend/tests` (143 passed, 1 skipped) | 🟢 PASS |
| **04** | **Paridade Root vs Subdir** | Execução de pytest a partir da raiz do monorepo e do subdiretório `backend` com paridade total | `pytest backend/tests` == `pytest tests` | 🟢 PASS |
| **05** | **Rate Limiting Funcional** | HTTP 200 sob uso normal; HTTP 429 Too Many Requests quando limite é ultrapassado | `pytest tests/test_rate_limit.py` | 🟢 PASS |
| **06** | **CORS Restrito em Produção** | Wildcard `*` terminantemente proibido em staging/produção com RuntimeError de proteção | `pytest tests/test_cors.py` | 🟢 PASS |
| **07** | **Tokens Efêmeros de Sessão** | Handshake `/auth/token`, emissão e renovação de credenciais temporárias HMAC/SHA256, 401/403 sob `REQUIRE_AUTH` | `pytest tests/test_auth_service.py` | 🟢 PASS |
| **08** | **Health Probes Dinâmicos** | Endpoints `/health/live` e `/health/ready` dinâmicos desacoplados de strings estáticas | `pytest tests/test_health_probes.py` | 🟢 PASS |
| **09** | **Mock Bloqueado em Prod** | Falha de inicialização obrigatória caso `MockLLMProvider` seja acionado sob `ENVIRONMENT=production` | `pytest tests/test_no_mock_in_production.py` | 🟢 PASS |
| **10** | **Auditoria de Dependências** | Lockfiles íntegros (`uv.lock` e `package-lock.json`), sem pacotes vulneráveis conhecidos | `uv.lock`, `package-lock.json` | 🟢 PASS |
| **11** | **Separação Epistemológica** | Alegação do vídeo (`ClaimCard`) preserva a fala do vídeo; checagens externas alocadas em `EvidenceCard` | `pytest tests/test_fact_checker.py` | 🟢 PASS |
| **12** | **Relação Semântica (Stance)** | Score moderado (< 0.55) degrada obrigatoriamente para `contextualizes`; apenas score forte ($\ge 0.55$) emite `supports`/`contradicts` | `pytest tests/test_semantic_relation.py` | 🟢 PASS |
| **13** | **Timestamps Clicáveis** | Citação da transcrição com botão interativo saltando `video.currentTime` diretamente no player do YouTube | `vitest run src/panel/components.test.tsx` | 🟢 PASS |
| **14** | **Corpus e Auditoria de Dados** | Isolamento formal entre corpus estilístico (Fake.br) e de fatos (FactChecks.br, ClaimReview) | `artifacts/go/phase-03/dataset-audit.md` | 🟢 PASS |
| **15** | **Framework de Avaliação** | Estrutura de avaliação em `evaluation/` pronta sem dados simulados (marcada `PENDING_HUMAN_ANNOTATION`) | `python scripts/evaluate_retrieval.py` | 🟢 PASS |
| **16** | **Detector de Drift (Docs x Código)** | Verificação automatizada de contratos, schemas, manifest e documentação | `python scripts/check_drift.py` (0 CRITICAL, 0 HIGH) | 🟢 PASS |
| **17** | **CI Fail-Closed** | Workflow GitHub Actions configurado com verificação de drift e sem `continue-on-error: true` | `.github/workflows/ci.yml` | 🟢 PASS |
