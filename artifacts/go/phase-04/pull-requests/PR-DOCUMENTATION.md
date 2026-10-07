# Pull Request: Documentation (codex/go-phase-01-hardening → main)

**Título:** `docs(release): Release Candidate Documentation — Maturity Status, Gated Governance, and Verification Parity`  
**Base:** `main`  
**Head:** `codex/go-phase-01-hardening`  
**Status:** `PRÉ-RELEASE CANDIDATA (PRERELEASE_CANDIDATE)`  

---

## 1. Resumo Executivo
Este PR sincroniza a documentação oficial com o estado da base de código do EvidencIA, garantindo rastreabilidade total, eliminação de menções desatualizadas a componentes legados, conformidade com as diretrizes de governança (zero emojis no corpo técnico e ausência de links quebrados) e registro transparente das decisões humanas isoladas.

---

## 2. Principais Alterações
- **Matriz de Prontidão Central (`RELEASE-READINESS.md`):** Documento detalhado atestando o estado de Release Candidate com 17 Technical Gates aprovados.
- **Registro de Decisões Humanas (`HUMAN-DECISIONS.md`):** Catalogação formal dos 6 portões exclusivos de julgamento humano (H1 a H6) com recomendações técnicas fundamentadas.
- **Guias de Anotação Manual:** Inclusão de `EVAL-ANNOTATION-GUIDE.md` e `evaluation/annotation-guide.md` para suportar o protocolo duplo-cego da validação de Information Retrieval.
- **README Atualizado:** Declaração explícita do que é Funcional, Parcial e Pendente.
- **Validação Estrita:** 100% dos links relativos validados e 0 emojis encontrados nos arquivos de documentação técnica.

---

## 3. Lista de Commits
- `8d517e7`: `docs(governance): add release readiness and human decisions register`
- `199f938`: `docs(readiness): synchronize release readiness, evaluation guides and human decisions matrix`
- `2e87a0c`: `docs(release): update maturity status and synchronized release readiness matrix`

---

## 4. Evidências de Validação
- **Validação de Links Relativos:** `0 links quebrados` (`docs-links.yml` script aprovado).
- **Conformidade Corporativa:** `0 emojis` encontrados na documentação técnica (`ci-docs.yml` script aprovado).
- **Drift Check com Código:** `0 CRITICAL, 0 HIGH` (`python scripts/check_drift.py --docs ../documentation`).

---

## 5. Decisões Humanas Pendentes
- Homologação dos 6 portões de decisão humana registrados em `HUMAN-DECISIONS.md`.
