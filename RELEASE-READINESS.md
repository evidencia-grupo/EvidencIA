# Relatório Central de Prontidão de Release — EvidencIA

**Data de Avaliação:** 2026-10-07  
**Branch:** `codex/go-phase-01-hardening`  
**Estado Geral Atual:** `BLOCKED` (Pré-condição de Patches da Fase 1 pendente)  
**Meta Final:** `PRÉ-RELEASE CANDIDATA`

---

## 1. Status Consolidado

```text
ESTADO ATUAL: BLOCKED (Aguardando arquivos de patch da Fase 1)
GATES TÉCNICOS: EM PROGRESSO
GATES HUMANOS: PENDENTES (Registrados em HUMAN-DECISIONS.md)
```

---

## 2. Bloqueadores Imediatos (Blockers)

### 🔴 Bloqueador 1: Pré-condição da Fase 1 (Patches Ausentes)
Conforme especificado no Plano Mestre de Fechamento:
> *"Os seguintes artefatos são esperados: `evidencia-code.patch`, `documentation.patch`, `drift-baseline.json`. Se algum patch não existir: pare e informe exatamente qual arquivo está faltando. Não recrie silenciosamente o patch."*

**Arquivos Faltantes no Workspace:**
- `evidencia-code.patch` (ausente no repositório e no workspace)
- `documentation.patch` (ausente no repositório e no workspace)
- `drift-baseline.json` (ausente no repositório e no workspace)
- Script dependente: `scripts/check_drift.py` (ausente; referenciado no plano para medição de drift com a documentação)

---

## 3. Technical Gates (Portões Técnicos)

| Gate Técnico | Status | Evidência / Notas |
| :--- | :---: | :--- |
| **Build & Typecheck (Frontend)** | 🟢 PASS | Compilação TypeScript e Vite do service worker, content scripts e painel limpas. |
| **Testes Unitários Frontend** | 🟢 PASS | `vitest`: 169 testes aprovados em 10 arquivos (`npm test`). |
| **Testes Unitários Backend** | 🟢 PASS | `pytest`: 129 testes aprovados, 1 skipped em `backend/tests/`. |
| **Root vs Subdir Execution** | 🟡 PENDENTE | Pytest na raiz necessita de padronização de `PYTHONPATH` ou flag de config. |
| **Rate Limit Funcional (429)** | 🟡 PENDENTE | Limiter configurado com `slowapi`; requer teste específico comprovando HTTP 429 sob rajada. |
| **CORS Restrito em Produção** | 🟡 PENDENTE | Regras existentes em `main.py`; necessita teste de bloqueio estrito para origens não autorizadas. |
| **Health Check Real (Liveness/Readiness)** | 🟡 PENDENTE | Endpoint `/health` precisa eliminar respostas estáticas e desacoplar liveness/readiness. |
| **Mock Bloqueado em Produção** | 🟢 PASS | Testes em `test_no_mock_in_production.py` e `test_llm_acceptance.py` abortam startup se `ENV=production`. |
| **Auditoria de Dependências** | 🟢 PASS | Python 3.14 + `uv.lock` no backend; `package-lock.json` no frontend. |
| **Separação Claim do Vídeo vs Fact-Check** | 🟢 PASS | ADR-006 implementado em `Claim` e `Evidence`. |
| **Timestamps Clicáveis no Player** | 🟡 PENDENTE | Mapeado para a Fase 2. |
| **Corpus Real & Pipeline Reproduzível** | 🟡 PENDENTE | Adaptadores presentes; aguarda resolução de licenças e escala para milhares de amostras. |
| **MkDocs Strict** | 🟡 PENDENTE | Execução de `uv run mkdocs build --strict` no repositório `documentation`. |
| **Drift Check (Docs ↔ Código)** | 🔴 BLOQUEADO | Dependente da disponibilização do script `check_drift.py` e `drift-baseline.json`. |
| **CI Fail-Closed** | 🟡 PENDENTE | Remoção de `continue-on-error: true` em `.github/workflows/`. |

---

## 4. Human Gates (Portões de Decisão Humana)

*Detalhes completos, alternativas e recomendações registradas em [`HUMAN-DECISIONS.md`](file:///Users/aluno1/Documents/challenge%20fake%20news/evidencia/HUMAN-DECISIONS.md).*

- [ ] **H1 — Autenticação:** Definição da estratégia de autorização da extensão pública (Recomendação: Installation Token anônimo + JWT efêmero).
- [ ] **H2 — Dataset License:** Confirmação jurídica das licenças de `Fake.br` e `FactChecks.br`.
- [ ] **H3 — Evaluation Labels:** Homologação do Gold Set e designação de anotadores humanos para cálculo de métricas de IR sem circularidade.
- [ ] **H4 — Política de Privacidade (LGPD):** Aprovação das diretrizes de retenção e anonimização em Hosted Mode.
- [ ] **H5 — Infraestrutura & Produção:** Definição do provedor cloud, domínio HTTPS e injeção de secrets em produção.
- [ ] **H6 — Validação com Usuários:** Execução do experimento empírico com pessoas reais conforme `protocolo-participante.md`.

---

## 5. External Dependencies (Dependências Externas)

- **Chrome Web Store:** Aprovação de publicação do pacote Manifest V3 pelo Google.
- **Google Fact Check Tools API:** Chave de API de produção opcional para complementação global.
- **Hospedagem Cloud:** Provedor gerenciado para o backend proxy (Render, Cloud Run ou VPS).

---

## 6. Registro de Evidências (Evidence Log)

- `artifacts/go/phase-01/auth-options.md`: Estudo técnico comparativo das 4 opções de autenticação para a extensão.
- `backend/ml/classifier/EVALUATION_REPORT.md`: Avaliação empírica do classificador estatístico e curva de aceitação por limiar.
