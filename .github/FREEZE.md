# FREEZE — Congelamento de Caminhos Críticos

> **Status:** 🔴 ATIVO  
> **Vigência:** até descongelamento explícito (ver critérios abaixo)  
> **Aprovado por:** Tech Lead — Sprint 1 Foundation  
> **Referência:** [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md)

---

## O que está congelado

Os caminhos abaixo **não podem ser alterados** até o critério de descongelamento ser atendido.
Qualquer PR que toque esses caminhos será automaticamente bloqueado pelo workflow `freeze-guard`
(a menos que tenha o label `unfreeze-approved` aplicado pelo Tech Lead).

### Componentes de UI do gauge/score (extensão)

| Caminho | Motivo |
|---------|--------|
| `extension/src/panel/components/Gauge.tsx` | Componente principal do gauge de veracidade |
| `extension/src/panel/index.tsx` | Renderiza `<Gauge score={data.score} ...>` e textos de "Veracidade" |
| `extension/src/panel/components/SourceList.tsx` | Exibe `reliabilityScore` das fontes |

### Contratos compartilhados (shared)

| Caminho | Motivo |
|---------|--------|
| `shared/types/api.ts` | Define `score: number` e `reliabilityScore: number` no contrato |
| `shared/schemas/api-schema.json` | Schema JSON com campos `score` e `reliabilityScore` |

### Campos de score no backend

| Caminho | Motivo |
|---------|--------|
| `backend/app/schemas.py` | `AnalyzeResponse.score` e `FactCheckingSource.reliabilityScore` |

> **Nota:** O campo `analysisMode` em `AnalyzeResponse` **não** está congelado — ele será atualizado para `"mock"` quando o provider mock for usado explicitamente.

---

## Por que congelar? (ADR-001)

A [Arquitetura Evidence-First (ADR-001)](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) determina que:

1. **A LLM não é autoridade factual** — o score global baseado em heurísticas (`score: 0–100`) não reflete evidências reais.
2. **A unidade central é alegação + evidências** — o Gauge representa uma abstração inválida do pipeline atual.
3. **Mock nunca pode aparecer silenciosamente em produção** — o campo `analysisMode="demo"` disfarça uso de mock.
4. O componente `Gauge` e o campo `score` **serão removidos** na Sprint 2, quando o pipeline de evidências estiver validado.

Alterar o gauge agora criaria acoplamentos que dificultariam a migração e mascararia a dívida técnica.

---

## Critério de descongelamento

O congelamento será levantado quando **todos** os seguintes itens estiverem concluídos:

- [ ] **IS-07** — Notebook EDA executado de ponta a ponta (`nbconvert --execute` sem erro)
- [ ] **IS-04** — Fake.br + FactChecks.br ingeridos via adapters (com manifest verificável)
- [ ] **IS-08** — Retrieval validado com métricas (Recall@5, MRR, nDCG@5 reportados)
- [ ] `sample_facts.json` deixou de ser fonte primária do pipeline (substituído pelo silver do IS-04)
- [ ] Tech Lead aplicou o label `unfreeze-approved` na issue de descongelamento

---

## Como solicitar uma exceção

Se você precisar alterar um caminho congelado por motivo legítimo (ex.: correção de acessibilidade crítica, vulnerabilidade de segurança):

1. **Abra uma issue** com o label `freeze` descrevendo: caminho afetado, motivo, urgência.
2. **Aguarde aprovação** do Tech Lead (`@TECH_LEAD_HANDLE` — substituir pelo handle real antes do merge).
3. **Tech Lead aplica** o label `unfreeze-approved` na issue E no Pull Request.
4. O workflow `freeze-guard` passará automaticamente quando o label estiver presente no PR.
5. **Após o merge**, o Tech Lead remove o label `unfreeze-approved` do PR.

> **Atenção:** O label `unfreeze-approved` deve estar no **Pull Request**, não na issue.

---

## Passo manual — Branch Protection

> ⚠️ **NÃO execute estes comandos agora.** Execute manualmente após o merge do PR de foundation.

Para tornar o check `freeze-guard` obrigatório na branch `main`, execute:

```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/evidencia-grupo/EvidencIA/branches/main/protection \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Freeze Guard / check-frozen-paths"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
}
JSON
```

> **Nota:** Este comando requer permissão de admin no repositório. O Tech Lead deve executá-lo.
> O nome exato do check (`Freeze Guard / check-frozen-paths`) está definido em `.github/workflows/freeze-guard.yml`.

---

## Histórico de congelamentos

| Data | Ação | Por | Motivo |
|------|------|-----|--------|
| 2026-10-02 | Congelamento ativado | Sprint 1 Foundation | ADR-001: migração para evidence-first |

---

*Placeholder a substituir antes do merge:*
- `@TECH_LEAD_HANDLE` → handle real do Tech Lead no GitHub (ex.: `@pedrohpsantos`)
