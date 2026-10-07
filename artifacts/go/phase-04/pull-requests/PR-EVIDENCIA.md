# Pull Request: EvidencIA (codex/go-phase-01-hardening → main)

**Título:** `feat(release): Release Candidate 1.0.0 — Hardening, Evidence Contract, Epistemic Stance, and CI Gating`  
**Base:** `main`  
**Head:** `codex/go-phase-01-hardening`  
**Status:** `PRÉ-RELEASE CANDIDATA (PRERELEASE_CANDIDATE)`  

---

## 1. Resumo Executivo
Este PR consolida o ciclo completo de fechamento da versão 1.0.0 do EvidencIA, transformando a base de código em uma **Release Candidate real** com todos os 17 Technical Gates aprovados, sem dívida técnica de segurança, sem conflito de drift e com integridade epistêmica comprovada.

---

## 2. Principais Alterações por Área

### Segurança e Hardening
- Rate limiting centralizado com `slowapi`, comprovando emissão de HTTP 429 sob excesso de requisições.
- Bloqueio estrito de CORS wildcard `*` em ambientes de staging e produção com interrupção de startup (`RuntimeError`).
- Emissão e validação de tokens efêmeros HMAC/SHA256 rotacionáveis (`/api/v1/auth/token`) para clientes anônimos da extensão; proteção 401/403 sob `REQUIRE_AUTH=True`. Zero chaves embutidas no cliente.
- Health probes desacoplados (`/health/live` e `/health/ready`), com detecção ativa de falhas de componentes upstream (HTTP 503).
- Proteção anti-mock obrigatória em tempo de inicialização caso `ENVIRONMENT=production`.

### Semântica e Epistemologia Evidence-First
- Separação epistemológica estrita: o texto do `ClaimCard` preserva fielmente o discurso do criador do vídeo (`request.videoTitle` / transcrição), enquanto a checagem da agência jornalística reside em `EvidenceCard`.
- Refinamento do `BrazilianFactMatcher`: similaridade lexical/semântica é tratada como relevância de recuperação (candidato a fact-check) e não autoriza inferir `supports` ou `contradicts`.
- Relação semântica graduada: `supports`/`contradicts` exigem correspondência proposicional alta sem divergência de polaridade. Textos com negação explícita (vídeos desmentindo boatos) degradam para `contextualizes`, eliminando falsos positivos factuais.
- Citação de trecho da transcrição e botão de salto temporal interativo (`JUMP_TO_TIMESTAMP`) sincronizado diretamente com o player do YouTube (`video.currentTime`).

### Governança, CI e Datasets
- Script detector de drift fail-closed (`scripts/check_drift.py`) validando endpoints, schemas Pydantic e tipos TypeScript contra `product-manifest.yaml`.
- Job `check-drift` integrado em `.github/workflows/ci.yml` sem diretivas permissivas de falha (`continue-on-error: true`).
- Framework de avaliação de IR em `evaluation/` com separação explícita: status registrado como `PENDING_HUMAN_ANNOTATION` (zero métricas forjadas por IA).
- Script `scripts/evaluate_retrieval.py` pronto para calcular Recall@5, Recall@10, MRR, nDCG@5, FMR e IER.
- Datasets marcados formalmente como `TECHNICALLY READY / LICENSE PENDING HUMAN APPROVAL`.

---

## 3. Lista de Commits
- `42f4410`: `fix(tests): allow stable root and subdir pytest execution via stable cwd and pythonpath`
- `1ea0a73`: `feat(hardening): complete phase 1 baseline, auth, rate limiting, health probes, product-manifest, and check_drift`
- `0342f37`: `feat(semantics): complete phase 2 evidence contract, timestamps, matchReason, and UI states`
- `c08467d`: `feat(evaluation): complete phase 3 corpus audit, gold set structure, eda notebook, and evaluation script`
- `5795361`: `feat(release): complete phase 4 CI hardening, drift reporting, and release readiness matrix`
- `dd6f3b4`: `feat(release): epistemic stance refinement, adversarial test battery, and release candidate hardening`

---

## 4. Evidências de Teste e Validação
- **Backend Tests:** 153 passed / 1 skipped / 0 failed (`pytest backend/tests`).
- **Frontend Tests:** 171 passed / 0 failed (`npm test` no Vitest, cobrindo acessibilidade axe-core WCAG 2.1 AA).
- **Frontend Build & Typecheck:** Sucesso em 95ms (`npm run build` e `tsc --noEmit`).
- **Drift Check:** `0 CRITICAL, 0 HIGH` (`python scripts/check_drift.py --docs ../documentation`).

---

## 5. Riscos e Mitigações
- **Risco de Falsos Positivos em Fact-Checking:** Mitigado pela regra de postura conservadora: qualquer divergência de polaridade ou similaridade moderada degrada para `contextualizes`.
- **Risco de Exposição de Segredos:** Mitigado pelo isolamento no Backend Proxy (`ADR-002`) e tokens efêmeros assinados.

---

## 6. Decisões Humanas Pendentes (Registradas em `HUMAN-DECISIONS.md`)
- **H1:** Homologação do fluxo de autenticação da extensão pública.
- **H2:** Confirmação jurídica das licenças de `FactChecks.br` e `Fake.br`.
- **H3:** Execução da anotação humana independente de `candidates.jsonl`.
- **H4:** Aprovação formal da política de privacidade e retenção (LGPD).
- **H5:** Provisionamento do ambiente cloud HTTPS e cadastro de secrets.
- **H6:** Execução dos testes empíricos com usuários voluntários.
