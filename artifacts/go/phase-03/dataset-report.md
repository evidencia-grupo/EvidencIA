# Relatório de Datasets e Corpus — EvidencIA (Fase 3)

**Data:** 2026-10-07  
**Status:** CONCLUÍDO  
**Repositório:** `evidencia`  

---

## 1. Inventário de Recursos de Dados

| Recurso | Função | Localização / Fonte | Registros | Status de Uso |
| :--- | :--- | :--- | :--- | :--- |
| **sample_facts.json** | Base local de checagens curadas IFCN | `backend/ml/datasets/sample_facts.json` | 20 fatos atômicos curados | Ativo em dev/test/offline |
| **FactChecks.br** | Base primária de fact-checking em PT-BR | UFG / Agências IFCN brasileiras | ~10k alegações | Integrado conceitualmente via adapter |
| **Fake.br-Corpus** | Corpus linguístico (estilometria) | NILC / USP São Carlos | 7.200 notícias | Restrito a análise de estilo (NÃO evidência) |
| **ClaimReview API** | Complementação em tempo real | Google Fact Check Tools API | Dinâmico sob demanda | Provider implementado (`GOOGLE_FACT_CHECK_API_KEY`) |
| **ClaimPT** | Taxonomia de check-worthiness | IST-EDIT | Referência metodológica | Apenas referência conceitual (PT-PT) |

---

## 2. Separação Epistemológica Garantida

- **Isolamento de Fake News:** O Fake.br-Corpus **nunca** é consultado pelo motor de busca de evidências. Apenas matérias jornalísticas de fact-checking (`fact_check_evidence`) compõem os índices de recuperação.
- **Transparência de Proveniência:** Cada evidência recuperada carrega obrigatoriamente `publisher`, `reviewUrl` e `retrievedSummary`.

---

## 3. Bloqueios Humanos Relacionados (H2)

- O uso comercial amplo de dados raspados do FactChecks.br e a redistribuição direta de dumps do Fake.br exigem homologação formal descrita no portão **H2** em `HUMAN-DECISIONS.md`.
