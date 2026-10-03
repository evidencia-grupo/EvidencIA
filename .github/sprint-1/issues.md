# Sprint 1 — Checklist de Issues

> Referência: [ADR-001](../docs/tecnico/decisoes/) · Milestone: **Sprint 1**
> Execute `DRY_RUN=1 ./scripts/create_sprint1_issues.sh` para validar antes de criar.

---

## Labels a criar (idempotente)

- [ ] `sprint-1` · `sprint-2` · `data` · `ml` · `backend` · `frontend` · `docs` · `freeze` · `p0` · `p1`
- [ ] Estimativas: `sp-2` · `sp-3` · `sp-5` · `sp-8`

---

## Issues da Sprint 1 (36 SP total)

### #IS-01 — Guiding Questions publicadas e validadas pelo time · 3 SP
**Labels:** `sprint-1` `docs` `p0` `sp-3` · **Resp:** ASSIGN_DOCS

**Critérios de aceitação:**
- [ ] PR no repositório `documentation` aprovado por ≥ 1 revisor
- [ ] Arquivo `docs/pesquisa/guiding-questions.md` contém exatamente 12 GQs numeradas (GQ01–GQ12)
- [ ] Hipóteses não validadas listadas em seção "Pendências"
- [ ] Vinculado ao ADR-001

---

### #IS-02 — Alinhamento da Essential Question (decisão de produto) · 2 SP
**Labels:** `sprint-1` `docs` `p0` `sp-2` · **Resp:** ASSIGN_DOCS

**Critérios de aceitação:**
- [ ] `docs/visao/essential-question-alignment.md` criado e aprovado pelo Tech Lead
- [ ] DE/PARA publicado: o que muda de abordagem (score global → evidence-first)
- [ ] ADR-001 marcado como `Aceito` (status atualizado)
- [ ] Nenhuma pendência de revisão aberta

---

### #IS-03 — Dataset registry versionado (`sources.yaml`) · 3 SP
**Labels:** `sprint-1` `data` `p0` `sp-3` · **Resp:** ASSIGN_DATA

**Critérios de aceitação:**
- [ ] `backend/ml/datasets/sources.yaml` contém entradas para: Fake.br (`linguistic_corpus`), FactChecks.br (`fact_check_evidence`), ClaimReview (`external_complementary`), ClaimPT (`methodological_auxiliary`)
- [ ] Cada entrada tem: `role`, `language`, `url`, `license`, `expected_columns`, `notes`
- [ ] ClaimPT tem nota: "Português Europeu, não PT-BR"
- [ ] Teste `pytest backend/tests/test_ingestion.py::test_sources_yaml_schema -q` passa
- [ ] Nenhuma chave de API no YAML

---

### #IS-04 — Pipeline de ingestão por adapters (Fake.br + FactChecks.br) · 5 SP
**Labels:** `sprint-1` `data` `backend` `p0` `sp-5` · **Resp:** ASSIGN_DATA

**Critérios de aceitação:**
- [ ] `python -m ml.datasets.ingest --source fakebr --input-dir <dir> --dry-run` executa sem erro
- [ ] `python -m ml.datasets.ingest --source factchecksbr --input-dir <dir>` gera silver com SHA-256 no manifest
- [ ] 2ª execução idempotente: `manifest.json` não altera hashes existentes
- [ ] Datasets brutos em `backend/data/bronze/` (fora do Git via `.gitignore`)
- [ ] `pytest backend/tests/test_ingestion.py -q` passa offline (fixture local)

---

### #IS-05 — Schema canônico de evidência · 3 SP
**Labels:** `sprint-1` `data` `ml` `p0` `sp-3` · **Resp:** ASSIGN_ML

**Critérios de aceitação:**
- [ ] `EvidenceRecord` e `NewsRecord` importáveis de `ml.schemas.evidence`
- [ ] `VerdictNormalized.unknown` é o valor default quando veredito ausente — NUNCA `contradicted`
- [ ] Validação Pydantic rejeita `claim_text` vazio e URLs mal-formadas
- [ ] `pytest backend/tests/test_normalization.py -q` passa com fixtures sintéticas (≤ 10 registros)
- [ ] `published_at` timezone-aware ou None; nunca naive datetime

---

### #IS-06 — Índice Chroma e retrieval vetorial (MVP) · 5 SP
**Labels:** `sprint-1` `ml` `backend` `p0` `sp-5` · **Resp:** ASSIGN_ML

**Critérios de aceitação:**
- [ ] `python -m ml.retrieval.index --collection evidencia --silver-dir <dir>` constrói coleção
- [ ] `search(query, k=5)` retorna lista de `SearchHit` com `evidence_id`, `score`, `record`, `provenance`
- [ ] Filtro temporal: `search(query, k=5, filters={"after": "2023-01-01"})` funciona
- [ ] ≥ 2 modelos de embedding comparados no notebook EDA (seção 13)
- [ ] `pytest backend/tests/test_retrieval.py -q` passa com fixture sintética (sem Chroma obrigatório: `pytest.importorskip("chromadb")`)

---

### #IS-07 — Notebook EDA reprodutível (`notebooks/eda_datasets.ipynb`) · 8 SP
**Labels:** `sprint-1` `data` `ml` `p0` `sp-8` · **Resp:** ASSIGN_DATA + ASSIGN_ML

**Critérios de aceitação:**
- [ ] `jupyter nbconvert --to notebook --execute notebooks/eda_datasets.ipynb` completa sem erro
- [ ] 17 seções (0–16) preenchidas com métricas reais (não `pass` ou `TODO` nos resultados)
- [ ] Seção 15 ("Findings → Requirements") tem tabela: Achado | Evidência | Impacto técnico | Decisão
- [ ] Seção 16 ("Limitações") cita viés temporal, de fonte e de classe
- [ ] `nbformat.validate(...)` retorna sem exceção
- [ ] Sem dados brutos commitados; notebook usa caminhos relativos ao `manifest.json`
- [ ] Seed fixa: `random.seed(42)`, `np.random.seed(42)` na célula 0

---

### #IS-08 — Baseline de retrieval (BM25/TF-IDF vs embeddings) · 5 SP
**Labels:** `sprint-1` `ml` `p0` `sp-5` · **Resp:** ASSIGN_ML

**Critérios de aceitação:**
- [ ] Métricas reportadas: Recall@1, Recall@3, Recall@5, MRR, nDCG@5 — para BM25 e ≥ 1 modelo de embedding
- [ ] Análise qualitativa de 10–20 casos de erro com categorização (falso positivo/negativo, ambiguidade)
- [ ] Resultados publicados em `docs/investigate/eda-results.md` (gerado pelo notebook, não editado à mão)
- [ ] Metodologia reproducível: mesmo seed, mesma divisão treino/teste descrita

---

### #IS-09 — Proveniência e manifest de dados · 2 SP
**Labels:** `sprint-1` `data` `p0` `sp-2` · **Resp:** ASSIGN_DATA

**Critérios de aceitação:**
- [ ] `backend/data/manifest.json` contém para cada dataset: `sha256`, `version`, `ingested_at`, `source_url`, `record_count`
- [ ] `backend/data/README.md` documenta como reproduzir do zero (download → ingestão → verificação de hash)
- [ ] `python -m ml.datasets.manifest verify` retorna exit code 0 se hashes OK, 1 se divergência
- [ ] `pytest backend/tests/test_ingestion.py::test_manifest_deterministic -q` passa

---

## Issues Transversais (0 SP)

### #IS-10 — Congelamento da UI do gauge até validação do pipeline
**Labels:** `sprint-1` `frontend` `freeze` `p0` · **Resp:** ASSIGN_FRONTEND

**Critérios de aceitação:**
- [ ] Workflow `.github/workflows/freeze-guard.yml` ativo na branch `main`
- [ ] PR de teste tocando `extension/src/panel/components/Gauge.tsx` é bloqueado automaticamente
- [ ] `.github/FREEZE.md` publicado com: o quê, por quê, critério de descongelamento, como solicitar exceção
- [ ] CODEOWNERS atualizado para caminhos congelados
- [ ] Pull Request Template atualizado com checkbox de caminhos congelados

---

### #IS-11 — Preparação: interface LLMProvider e guard anti-mock
**Labels:** `sprint-1` `backend` `p0` · **Resp:** ASSIGN_BACKEND

**Critérios de aceitação:**
- [ ] `pytest backend/tests/test_provider_contract.py -q` passa: MockProvider satisfaz `isinstance(x, LLMProvider)`
- [ ] `pytest backend/tests/test_no_mock_in_production.py -q` passa:
  - `APP_ENV=production` + `LLM_PROVIDER=mock` → `MockInProductionError`
  - `APP_ENV=development` + `LLM_PROVIDER=mock` → permitido
  - Valor inválido de `LLM_PROVIDER` → `ValueError`
- [ ] `pytest backend/tests/test_no_silent_mock_fallback.py -q` mostra xfail (dívida documentada da Sprint 2)
- [ ] Nenhuma modificação em serviços de produção existentes

---

## Issues da Sprint 2 (planejadas — `INCLUDE_SPRINT2=1`)

| # | Título | SP |
|---|---|---:|
| S2-01 | Provider abstraction migration (migrar `ollama_service.py` → `LLMProvider`) | 5 |
| S2-02 | Evidence-first schema (eliminar `score` do pipeline interno) | 5 |
| S2-03 | Remoção do score global da UI | 3 |
| S2-04 | Evidence Cards (substituir Gauge por cards de evidência) | 5 |
| S2-05 | Reflection Questions (perguntas geradas pela LLM) | 5 |
| S2-06 | Failure/timeout handling (remover fallback mock; tratar timeout) | 3 |
| S2-07 | Latency tests (P90 ≤ 10 s validado em CI) | 5 |
| S2-08 | E2E atualizado (fluxo sem score global) | 5 |
| S2-09 | Sprint Review evidence (artefatos de evidência publicados) | 2 |
| **Total** | | **38** |

**Critérios transversais Sprint 2:**
- "resultado sem evidência nunca é convertido em `contradicted`/`falso`"
- "nenhum `score` global na UI após S2-03"
- "P90 ≤ 10 s validado no job `latency-gate` em CI"
