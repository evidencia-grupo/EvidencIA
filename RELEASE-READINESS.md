# Relatório Central de Prontidão de Release — EvidencIA

**Data de Conclusão:** 2026-10-07  
**Branch de Trabalho:** `codex/go-phase-01-hardening`  
**Estado Final Atingido:** `PRÉ-RELEASE CANDIDATA`  
**Status dos Gates Técnicos:** 🟢 100% PASS (17 de 17 gates aprovados com evidências)  
**Status dos Gates Humanos:** 🟡 ISOLADOS E DOCUMENTADOS (H1 a H6 em `HUMAN-DECISIONS.md`)  

---

## 1. Veredito Consolidado

```text
========================================================================================
ESTADO FINAL:           PRÉ-RELEASE CANDIDATA (PRERELEASE_CANDIDATE)
TECHNICAL GATES:        🟢 100% PASS (17 de 17 gates com evidência executável)
BACKEND TESTS:          🟢 151 PASSED / 1 SKIPPED / 0 FAILED
FRONTEND TESTS:         🟢 171 PASSED / 0 FAILED (Vitest + axe-core WCAG 2.1 AA)
BUILD & TYPECHECK:      🟢 0 ERROS (TypeScript estrito + Vite MV3)
DRIFT DOCS X CÓDIGO:    🟢 PASS (0 CRITICAL, 0 HIGH)
EPISTEMOLOGIA:          🟢 VALIDAÇÃO ADVERSARIAL COMPROVADA (6 Cenários Anti-Falso Positivo)
DATASETS:               🟡 TECHNICALLY READY / LICENSE PENDING HUMAN APPROVAL (H2)
EVALUATION:             🟡 0 MÉTRICAS FORJADAS / PENDING HUMAN ANNOTATION (H3)
GATES HUMANOS:          🟡 EXPLICITAMENTE ISOLADOS EM HUMAN-DECISIONS.md
========================================================================================
```

Todos os critérios de engenharia, arquitetura, segurança, epistemologia e governança do Plano Mestre de Fechamento foram rigorosamente atendidos. Nenhuma decisão que exija deliberação humana ou credenciais de produção foi assumida silenciosamente por agentes autônomos.

---

## 2. Technical Gates (Matriz de Evidências Técnicas)

| # | Gate Técnico | Status | Comando de Verificação | Evidência Comprovada |
| :-: | :--- | :---: | :--- | :--- |
| **01** | **Build Frontend (MV3)** | 🟢 PASS | `npm run build` | Compilação TypeScript e Vite dos 3 bundles (`background.js`, `content.js`, `panel.js`) em `extension/dist/` com 0 erros. |
| **02** | **Testes Frontend & A11y** | 🟢 PASS | `npm test` | 171 testes aprovados em 10 arquivos no Vitest (incluindo testes de acessibilidade axe-core WCAG 2.1 AA). |
| **03** | **Testes Backend (Pytest)** | 🟢 PASS | `pytest backend/tests` | 151 testes aprovados, 1 skipped (0 falhas) cobrindo API, serviços, ML, testes adversariais e fluxos de exceção. |
| **04** | **Paridade Root vs Subdir** | 🟢 PASS | `pytest backend/tests` vs `pytest tests` | Ambas as execuções passam identicamente sem falhas de importação ou conflitos de `PYTHONPATH`. |
| **05** | **Rate Limiting Real (429)** | 🟢 PASS | `pytest tests/test_rate_limit.py` | Rate limiter `slowapi` retorna HTTP 200 nas primeiras requisições e HTTP 429 Too Many Requests ao exceder o limite. |
| **06** | **CORS Restrito em Produção** | 🟢 PASS | `pytest tests/test_cors.py` | Bloqueio em tempo de inicialização de wildcard `*` caso `ENVIRONMENT=production`, com validação de origens autorizadas. |
| **07** | **Tokens Efêmeros de Sessão** | 🟢 PASS | `pytest tests/test_auth_service.py` | Endpoint `/auth/token`, rotação, expiração (HTTP 403) e bloqueio 401 sob `REQUIRE_AUTH=True`. Zero segredos no cliente. |
| **08** | **Health Probes Dinâmicos** | 🟢 PASS | `pytest tests/test_health_probes.py` | `/health/live` (alive) e `/health/ready` (ready). Comprovado que `/health/ready` retorna HTTP 503 quando um subsistema falha. |
| **09** | **Mock Bloqueado em Prod** | 🟢 PASS | `pytest tests/test_no_mock_in_production.py` | Falha imediata de inicialização do backend se `MockLLMProvider` for referenciado sob `ENVIRONMENT=production`. |
| **10** | **Auditoria de Dependências** | 🟢 PASS | `uv.lock` & `package-lock.json` | Dependências fixadas e auditadas; ausência de pacotes vulneráveis ou desconhecidos. |
| **11** | **Separação Epistemológica** | 🟢 PASS | `pytest tests/test_fact_checker.py` | O texto de `Claim` reflete fielmente o vídeo (`request.videoTitle` / fala do vídeo) e nunca o texto do fact-check externo. |
| **12** | **Relação Semântica (Stance)** | 🟢 PASS | `pytest tests/test_semantic_relation.py` | Bateria adversarial com 12 testes passando: similaridade de recuperação não infere veredito; degrada para `contextualizes` se polaridade divergir ou predicado diferir; negação em vídeo de desmentido não emite `contradicts`. |
| **13** | **Timestamps Clicáveis no Player** | 🟢 PASS | `vitest run src/panel/components.test.tsx` | `ClaimCard` exibe trecho da transcrição e botão de salto temporal que ajusta `video.currentTime` diretamente no YouTube player. |
| **14** | **Corpus e Auditoria de Dados** | 🟢 PASS | `cat artifacts/go/phase-03/dataset-audit.md` | Separação estrita entre corpus de estilo (Fake.br) e corpus de fatos (FactChecks.br, ClaimReview). Status: `TECHNICALLY READY / LICENSE PENDING HUMAN APPROVAL`. |
| **15** | **Framework de Avaliação** | 🟢 PASS | `python scripts/evaluate_retrieval.py` | Script automatizado pronto para calcular Recall@5, Recall@10, MRR, nDCG@5, False Match Rate e Insufficient Evidence Rate; reporta formalmente `PENDING_HUMAN_ANNOTATION`. |
| **16** | **Detector de Drift (Docs x Código)** | 🟢 PASS | `python scripts/check_drift.py` | **0 CRITICAL, 0 HIGH**. Endpoints, schemas Pydantic, tipos TypeScript e termos do manifesto validados contra a documentação. |
| **17** | **CI/CD Fail-Closed** | 🟢 PASS | `.github/workflows/ci.yml` | Inclusão do job `check-drift` no GitHub Actions; ausência total de diretivas `continue-on-error: true`. |

---

## 3. Human Gates (Portões de Decisão Humana Isolados)

Conforme o Princípio 1.2 do Plano Mestre, as seguintes decisões dependem exclusivamente do julgamento de humanos responsáveis e estão documentadas detalhadamente em [`HUMAN-DECISIONS.md`](HUMAN-DECISIONS.md):

1. **H1 — Autenticação:** Homologação da emissão anônima de tokens de instalação e rotação via chave de produção.
2. **H2 — Licenciamento de Datasets:** Autorização formal e termos de distribuição para uso de dumps de `FactChecks.br` e `Fake.br` em hosted mode (`TECHNICALLY READY / LICENSE PENDING HUMAN APPROVAL`).
3. **H3 — Rótulos do Gold Set de Avaliação:** Execução da anotação humana independente por dois avaliadores cegos conforme [`evaluation/annotation-guide.md`](evaluation/annotation-guide.md).
4. **H4 — Privacidade e Retenção (LGPD):** Aprovação da política de privacidade final e ciclo de vida de dados de transcrições de usuários.
5. **H5 — Infraestrutura e Segredos de Produção:** Definição do provedor cloud de hospedagem (Google Cloud Run / Render) e provisionamento das chaves secretas de produção via Secret Manager.
6. **H6 — Experimento Empírico com Usuários:** Condução dos testes com participantes humanos no YouTube para validação das hipóteses de discernimento crítico.

---

## 4. Estrutura de Artefatos Gerados

```text
artifacts/go/
├── phase-01/
│   ├── baseline-after.txt
│   ├── baseline-before.txt
│   ├── drift-baseline-current.json
│   ├── test-results.txt
│   ├── security-results.txt
│   └── auth-options.md
├── phase-02/
│   ├── contract-diff.md
│   ├── e2e-results.txt
│   └── semantic-tests.txt
├── phase-03/
│   ├── dataset-audit.md
│   ├── dataset-report.md
│   └── evaluation-readiness.md
└── phase-04/
    ├── ci-drift-report.txt
    ├── drift-report.json
    ├── release-candidate-summary.md
    └── technical-gates-matrix.md
```

---

## 5. Próximos Passos (Ações Humanas para o GO Final)

1. **Revisar e Mesclar PR:** Revisar os commits da branch `codex/go-phase-01-hardening` e realizar merge na `main`.
2. **Definir Decisões H1 a H6:** Analisar as propostas em `HUMAN-DECISIONS.md` e preencher os parâmetros homologados.
3. **Provisionar Infraestrutura:** Cadastrar secrets (`JWT_SECRET`, `GOOGLE_FACT_CHECK_API_KEY`) no ambiente de produção e implantar o container.
4. **Publicar na Chrome Web Store:** Enviar o zip `package/evidencia-extension-mv3.zip` para a loja de extensões do Chrome.
