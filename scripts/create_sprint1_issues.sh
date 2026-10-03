#!/usr/bin/env bash
# =============================================================================
# scripts/create_sprint1_issues.sh — EvidencIA Sprint 1 Issue Package
#
# Uso:
#   DRY_RUN=1 ./scripts/create_sprint1_issues.sh          # validação (imprime, não executa)
#   ./scripts/create_sprint1_issues.sh                     # cria labels, milestone e issues
#   INCLUDE_SPRINT2=1 ./scripts/create_sprint1_issues.sh  # inclui issues planejadas da Sprint 2
#
# Variáveis de ambiente opcionais para responsáveis:
#   ASSIGN_DOCS, ASSIGN_DATA, ASSIGN_ML, ASSIGN_BACKEND, ASSIGN_FRONTEND
#   (se vazias, --assignee é omitido)
#
# Variáveis de configuração:
#   REPO       — padrão: evidencia-grupo/EvidencIA
#   MILESTONE  — padrão: Sprint 1
#   DRY_RUN    — se "1", imprime comandos sem executar
# =============================================================================
set -euo pipefail

REPO="${REPO:-evidencia-grupo/EvidencIA}"
MILESTONE="${MILESTONE:-Sprint 1}"
DRY_RUN="${DRY_RUN:-0}"
INCLUDE_SPRINT2="${INCLUDE_SPRINT2:-0}"

# --- Helpers ------------------------------------------------------------------

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[DRY_RUN] $*"
  else
    "$@"
  fi
}

assignee_flag() {
  local var_value="${1:-}"
  if [[ -n "$var_value" ]]; then
    echo "--assignee $var_value"
  else
    echo ""
  fi
}

# --- Labels (idempotente) ------------------------------------------------------

create_labels() {
  echo "==> Criando labels (idempotente)..."

  run gh label create "sprint-1"  --color "0075ca" --description "Sprint 1"             --repo "$REPO" --force || true
  run gh label create "sprint-2"  --color "1d76db" --description "Sprint 2 (planejado)" --repo "$REPO" --force || true
  run gh label create "data"      --color "e4e669" --description "Dados e datasets"      --repo "$REPO" --force || true
  run gh label create "ml"        --color "bfd4f2" --description "Machine Learning"      --repo "$REPO" --force || true
  run gh label create "backend"   --color "c5def5" --description "Backend Python"        --repo "$REPO" --force || true
  run gh label create "frontend"  --color "f9d0c4" --description "Extensão / UI"         --repo "$REPO" --force || true
  run gh label create "docs"      --color "0e8a16" --description "Documentação"          --repo "$REPO" --force || true
  run gh label create "freeze"    --color "b60205" --description "Caminho congelado"     --repo "$REPO" --force || true
  run gh label create "p0"        --color "d93f0b" --description "Prioridade 0 (crítico)" --repo "$REPO" --force || true
  run gh label create "p1"        --color "e99695" --description "Prioridade 1 (alta)"   --repo "$REPO" --force || true
  run gh label create "sp-2"      --color "fef2c0" --description "2 Story Points"        --repo "$REPO" --force || true
  run gh label create "sp-3"      --color "fef2c0" --description "3 Story Points"        --repo "$REPO" --force || true
  run gh label create "sp-5"      --color "fef2c0" --description "5 Story Points"        --repo "$REPO" --force || true
  run gh label create "sp-8"      --color "e4e669" --description "8 Story Points"        --repo "$REPO" --force || true
}

# --- Milestone ----------------------------------------------------------------

create_milestone() {
  echo "==> Criando milestone '$MILESTONE' (tolerante a falha)..."
  run gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    "/repos/${REPO}/milestones" \
    -f title="$MILESTONE" \
    -f state="open" \
    -f description="Sprint 1 — Foundation: issues, freeze, data pipeline scaffold, provider guard" \
    || echo "[WARN] Milestone pode já existir — ignorando erro."
}

# --- Sprint 1 Issues ----------------------------------------------------------

create_sprint1() {
  local DOCS_FLAG;   DOCS_FLAG="$(assignee_flag "${ASSIGN_DOCS:-}")"
  local DATA_FLAG;   DATA_FLAG="$(assignee_flag "${ASSIGN_DATA:-}")"
  local ML_FLAG;     ML_FLAG="$(assignee_flag "${ASSIGN_ML:-}")"
  local BE_FLAG;     BE_FLAG="$(assignee_flag "${ASSIGN_BACKEND:-}")"
  local FE_FLAG;     FE_FLAG="$(assignee_flag "${ASSIGN_FRONTEND:-}")"

  echo ""
  echo "==> Criando issues da Sprint 1..."

  # IS-01 — Guiding Questions
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-01] Guiding Questions publicadas e validadas pelo time" \
    --label "sprint-1,docs,p0,sp-3" \
    ${DOCS_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md).
A decisão de arquitetura *evidence-first* exige que as perguntas-guia (GQs) estejam formalizadas e validadas antes de qualquer implementação de pipeline de dados.

## Descrição técnica
- Arquivo a criar: `docs/pesquisa/guiding-questions.md` no repositório `documentation`
- Conteúdo obrigatório: 12 GQs numeradas (GQ01–GQ12) cobrindo qualidade de dados, métricas de retrieval, comportamento da LLM e critérios de evidência
- Seção "Pendências": hipóteses não validadas marcadas explicitamente
- Link bidirecional com ADR-001 (seção "Motivação")

## Critérios de aceitação
- [ ] PR no repositório `documentation` aprovado por ≥ 1 revisor diferente do autor
- [ ] Arquivo `docs/pesquisa/guiding-questions.md` contém exatamente 12 GQs (GQ01–GQ12)
- [ ] Hipóteses não validadas listadas em seção "Pendências" (pode estar vazia se todas validadas)
- [ ] ADR-001 referenciado por hyperlink no documento
- [ ] `grep -c "^## GQ" docs/pesquisa/guiding-questions.md` retorna `12`

## Fora de escopo
- Implementação de qualquer componente de software
- Coleta de dados ou execução de experimentos

## Dependências
- ADR-001 aprovado (IS-02)

## Definition of Done
- [ ] Código/doc criado e revisado por outro integrante
- [ ] Testes/validação: comando de verificação acima passa
- [ ] Documentação atualizada (este arquivo IS próprio)
- [ ] Issue vinculada ao PR via "Closes #IS-01"

**Story Points:** 3
BODY
)"

  # IS-02 — Essential Question
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-02] Alinhamento da Essential Question (decisão de produto)" \
    --label "sprint-1,docs,p0,sp-2" \
    ${DOCS_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md).
A transição de *score global* para *evidence-first* precisa ser formalizada como decisão de produto com aprovação explícita do Tech Lead.

## Descrição técnica
- Arquivo a criar: `docs/visao/essential-question-alignment.md`
- Conteúdo obrigatório:
  - Essential Question do projeto (1 frase)
  - Tabela DE/PARA: abordagem anterior (score global) → nova abordagem (evidence-first)
  - Assinatura do Tech Lead (nome + data)
- ADR-001: atualizar campo `status` de `Proposto` → `Aceito`

## Critérios de aceitação
- [ ] `docs/visao/essential-question-alignment.md` existe e está aprovado pelo Tech Lead (comentário de aprovação no PR)
- [ ] Tabela DE/PARA presente: mínimo 3 linhas de contraste entre as abordagens
- [ ] ADR-001 com `status: Aceito` na seção de metadados
- [ ] Sem pendências de revisão abertas no PR

## Fora de escopo
- Implementação de qualquer componente de software
- Remoção do score da UI (Sprint 2)

## Dependências
- Nenhuma (pode ser feito em paralelo com IS-01)

## Definition of Done
- [ ] Documento criado e revisado pelo Tech Lead
- [ ] ADR-001 atualizado no mesmo PR
- [ ] Issue vinculada ao PR via "Closes #IS-02"

**Story Points:** 2
BODY
)"

  # IS-03 — Dataset registry
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-03] Dataset registry versionado (sources.yaml)" \
    --label "sprint-1,data,p0,sp-3" \
    ${DATA_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ03 ("Quais datasets compõem o corpus de evidências?").
O registry centraliza metadados de todos os datasets usados, garantindo rastreabilidade e papéis explícitos.

## Descrição técnica
- Arquivo a criar: `backend/ml/datasets/sources.yaml`
- Schema por entrada:
  ```yaml
  <nome>:
    role: linguistic_corpus | fact_check_evidence | external_complementary | methodological_auxiliary
    language: pt-BR | pt-PT | en
    url: <URL oficial>
    license: <SPDX ou "A verificar">
    expected_columns: [col1, col2, ...]
    notes: <texto livre>
  ```
- Entradas obrigatórias:
  - `fakebr`: role=`linguistic_corpus` (NÃO é verdade factual — apenas corpus linguístico)
  - `factchecksbr`: role=`fact_check_evidence`
  - `claimreview`: role=`external_complementary`
  - `claimpt`: role=`methodological_auxiliary`, notes inclui "Português Europeu, não PT-BR"
- Teste de validação de schema YAML: `pytest backend/tests/test_ingestion.py::test_sources_yaml_schema -q`
- Nenhuma chave de API no YAML

## Critérios de aceitação
- [ ] `backend/ml/datasets/sources.yaml` existe com as 4 entradas obrigatórias
- [ ] Todos os campos obrigatórios presentes em cada entrada (`role`, `language`, `url`, `license`, `expected_columns`, `notes`)
- [ ] `role` do Fake.br é `linguistic_corpus` (não `fact_check_evidence`)
- [ ] ClaimPT tem nota explícita sobre Português Europeu
- [ ] `pytest backend/tests/test_ingestion.py::test_sources_yaml_schema -q` → PASSED
- [ ] `grep -i "api_key\|token\|secret" backend/ml/datasets/sources.yaml` retorna vazio

## Fora de escopo
- Download real de datasets (IS-04)
- Implementação dos adapters (IS-04)

## Dependências
- IS-04 depende deste

## Definition of Done
- [ ] YAML criado, validado por teste automatizado e revisado
- [ ] Issue vinculada ao PR

**Story Points:** 3
BODY
)"

  # IS-04 — Pipeline de ingestão
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-04] Pipeline de ingestão por adapters (Fake.br + FactChecks.br)" \
    --label "sprint-1,data,backend,p0,sp-5" \
    ${DATA_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ04 ("Como garantir reprodutibilidade da ingestão?").
Substitui `dataset_downloader.py` como fonte primária — o downloader existente NÃO é removido (Sprint 2).

## Descrição técnica
Módulos a criar (scaffold já gerado neste PR):
- `backend/ml/datasets/adapters/base.py` — `DatasetAdapter` ABC
- `backend/ml/datasets/adapters/fakebr.py` — produz `NewsRecord`
- `backend/ml/datasets/adapters/factchecksbr.py` — produz `EvidenceRecord`, mapeia vereditos PT-BR
- `backend/ml/datasets/ingest.py` — CLI: `python -m ml.datasets.ingest --source <nome> [--input-dir <dir>] [--dry-run]`
- `backend/ml/datasets/manifest.py` — SHA-256, versão, data, contagem

Contrato do CLI:
```
python -m ml.datasets.ingest --source fakebr --input-dir ./data/raw/fakebr
python -m ml.datasets.ingest --source factchecksbr --input-dir ./data/raw/factchecksbr
```

Pipeline: `--input-dir` (bronze) → normalização → `backend/data/silver/<fonte>.parquet` + `manifest.json`
Datasets brutos: NUNCA commitados (`.gitignore` já configurado)

Formato esperado dos datasets (contratos em `sources.yaml`):
- Fake.br: colunas `text`, `label` (fake/true) — `# TODO(verify-format)` se divergir
- FactChecks.br: colunas `claim`, `label`, `explanation`, `source`, `url` — `# TODO(verify-format)` se divergir

## Critérios de aceitação
- [ ] `python -m ml.datasets.ingest --source fakebr --input-dir <dir> --dry-run` retorna exit 0 sem rede
- [ ] `python -m ml.datasets.ingest --source factchecksbr --input-dir <dir>` gera `backend/data/silver/factchecksbr.parquet`
- [ ] 2ª execução idempotente: SHA-256 dos arquivos silver idêntico (testado por `test_ingestion_idempotent`)
- [ ] `backend/data/manifest.json` atualizado com `sha256`, `version`, `ingested_at`, `source_url`, `record_count`
- [ ] `pytest backend/tests/test_ingestion.py -q` passa offline (fixture local em `tests/fixtures/`)
- [ ] `git status` não mostra `*.parquet`, `bronze/`, `silver/` (regras do `.gitignore`)

## Fora de escopo
- Download da internet (use `--input-dir` local)
- Indexação vetorial (IS-06)
- Remoção de `dataset_downloader.py`

## Dependências
- IS-03 (sources.yaml), IS-05 (schema de evidência)

## Definition of Done
- [ ] Código criado, tipado, com docstrings
- [ ] Testes passando offline
- [ ] `manifest.json` gerado e verificável
- [ ] Revisado por outro integrante

**Story Points:** 5
BODY
)"

  # IS-05 — Schema canônico
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-05] Schema canônico de evidência (EvidenceRecord, NewsRecord)" \
    --label "sprint-1,data,ml,p0,sp-3" \
    ${ML_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ05 ("Qual é a unidade mínima de evidência?").
Define o contrato canônico que todos os adapters devem respeitar.

## Descrição técnica
Arquivo: `backend/ml/schemas/evidence.py` (Pydantic v2)

Modelos obrigatórios:
- `Provenance`: `source_url`, `content_hash` (formato `sha256:<hex>`), `ingested_at` (timezone-aware)
- `EmbeddingMeta`: `model`, `dimension`
- `VerdictNormalized` (enum): `supported`, `contradicted`, `misleading`, `mixed`, `unverifiable`, `unknown`
  - **Docstring obrigatória**: "Ausência de evidência/veredito NUNCA mapeia para `contradicted`."
  - Default: `unknown`
- `EvidenceRecord`: todos os campos listados no scaffolding (ver PR)
- `NewsRecord`: `record_type="news"`, `label` (fake/true), campos de texto e metadados

Validadores:
- `published_at`: timezone-aware ou None
- URLs: formato válido (http/https)
- `claim_text`: não vazio (min_length=1)

Tabela de mapeamento de vereditos PT-BR → `VerdictNormalized`:
- "falso" → `contradicted`
- "verdadeiro" / "correto" → `supported`
- "enganoso" / "impreciso" → `misleading`
- "sem evidência" / "não verificado" → `unknown`
- (qualquer desconhecido) → `unknown`

## Critérios de aceitação
- [ ] `from ml.schemas.evidence import EvidenceRecord, NewsRecord, VerdictNormalized` funciona
- [ ] `EvidenceRecord(verdict_normalized=None)` resulta em `VerdictNormalized.unknown`, nunca `contradicted`
- [ ] `EvidenceRecord(claim_text="")` levanta `ValidationError`
- [ ] `EvidenceRecord(review_url="not-a-url")` levanta `ValidationError`
- [ ] Tabela de mapeamento cobre os 5 casos PT-BR acima (testado em `test_normalization.py`)
- [ ] `pytest backend/tests/test_normalization.py -q` passa offline

## Fora de escopo
- Integração com Chroma (IS-06)
- Dados reais (fixtures sintéticas ≤ 10 registros)

## Dependências
- IS-04 usa este schema

## Definition of Done
- [ ] Modelos Pydantic criados com type hints e docstrings
- [ ] Testes passando
- [ ] Revisado por outro integrante

**Story Points:** 3
BODY
)"

  # IS-06 — Índice Chroma
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-06] Índice Chroma e retrieval vetorial (MVP)" \
    --label "sprint-1,ml,backend,p0,sp-5" \
    ${ML_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ06 ("Qual é o Recall@5 mínimo aceitável para o pipeline de evidências?").
Substitui `BrazilianFactMatcher` (Jaccard) por busca vetorial — o matcher existente NÃO é removido (Sprint 2).

## Descrição técnica
Módulos a preencher (scaffold já criado):
- `backend/ml/retrieval/index.py`: `build_index(silver_dir, collection_name)` — carrega silver, gera embeddings, persiste no Chroma
- `backend/ml/retrieval/search.py`: `search(query, k, filters) -> list[SearchHit]`
  - `SearchHit`: `evidence_id`, `score` (float 0–1), `record` (`EvidenceRecord|NewsRecord`), `provenance`
  - Filtro temporal: `filters={"after": "YYYY-MM-DD"}` opcional
- `backend/ml/embeddings/encoder.py`: wrapper `sentence-transformers`, modelo configurável via env `EMBEDDING_MODEL`

Imports pesados (`chromadb`, `sentence_transformers`): **dentro das funções** (import tardio)

CLI de build:
```
python -m ml.retrieval.index --collection evidencia --silver-dir backend/data/silver
```

Comparação de modelos: ≥ 2 modelos avaliados no notebook (seção 13)

## Critérios de aceitação
- [ ] `python -m ml.retrieval.index --collection evidencia --silver-dir <dir>` executa sem erro
- [ ] `search("vacina causa autismo", k=5)` retorna lista de `SearchHit` não vazia
- [ ] `SearchHit` tem campos `evidence_id`, `score`, `record`, `provenance`
- [ ] Filtro temporal funciona: `search("...", k=5, filters={"after": "2023-01-01"})` não retorna itens anteriores
- [ ] `pytest backend/tests/test_retrieval.py -q` passa: usa BM25 ou `pytest.importorskip("chromadb")`
- [ ] Nenhum import de `chromadb` no nível de módulo (import tardio)

## Fora de escopo
- Fine-tuning de modelos
- Integração com `FactCheckerService` (Sprint 2)

## Dependências
- IS-05 (schema), IS-04 (silver data)

## Definition of Done
- [ ] Interfaces tipadas implementadas
- [ ] Testes passando offline
- [ ] ≥ 2 modelos comparados no EDA
- [ ] Revisado por outro integrante

**Story Points:** 5
BODY
)"

  # IS-07 — Notebook EDA
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-07] Notebook EDA reprodutível (notebooks/eda_datasets.ipynb)" \
    --label "sprint-1,data,ml,p0,sp-8" \
    ${DATA_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQs 03–08.
O notebook é o artefato de evidência que fundamenta as decisões de pipeline (retrieval, embeddings, balanceamento).

## Descrição técnica
Arquivo: `notebooks/eda_datasets.ipynb`
Skeleton já criado neste PR — preencher seções 0–16 com análise real:

| Seção | Título | Saída esperada |
|-------|--------|----------------|
| 0 | Reprodutibilidade | Versões do ambiente, seeds fixas, paths |
| 1 | Dataset Inventory | Contagens por dataset e split |
| 2 | Data Quality | % nulos, duplicatas, textos inválidos |
| 3 | Class Distribution | Gráfico de barras por `label`/`verdict` |
| 4 | Temporal Analysis | Distribuição por ano de publicação |
| 5 | Length Analysis | Histograma de comprimento em tokens |
| 6 | Lexical Diversity | TTR, MATTR, MTLD, hapax ratio |
| 7 | Morphosyntax (POS) | Distribuição de POS tags (spaCy/stanza) |
| 8 | Sensationalism | % CAPS, `!`, `?`, palavras emocionais |
| 9 | N-grams | Top-20 bi/trigramas por classe |
| 10 | Named Entities | Frequência de entidades por tipo |
| 11 | Similarity | Near-duplicates entre splits (MinHash/SimHash) |
| 12 | Leakage | Overlap temporal e léxico treino/teste |
| 13 | Retrieval Baseline | Recall@1/3/5, MRR, nDCG@5: BM25 vs embeddings |
| 14 | Error Analysis | 10–20 casos de erro categorizados |
| 15 | Findings → Requirements | Tabela: Achado\|Evidência\|Impacto técnico\|Decisão |
| 16 | Limitações | Viés temporal, de fonte, de classe |

Regras:
- Seed fixa: `random.seed(42)`, `np.random.seed(42)` na seção 0
- Nenhum dado bruto commitado; caminhos relativos ao `manifest.json`
- Sem gráficos ou resultados fictícios

## Critérios de aceitação
- [ ] `jupyter nbconvert --to notebook --execute notebooks/eda_datasets.ipynb --output /tmp/eda_executed.ipynb` completa sem erro
- [ ] 17 seções numeradas (0–16) presentes com células de código preenchidas (não apenas `pass`)
- [ ] Seção 15 tem tabela markdown com ≥ 3 linhas (Achado | Evidência | Impacto técnico | Decisão)
- [ ] Seção 16 menciona viés temporal, de fonte e de classe
- [ ] `python -c "import nbformat; nbformat.validate(nbformat.read('notebooks/eda_datasets.ipynb', as_version=4))"` retorna sem exceção
- [ ] `git ls-files notebooks/` não mostra `*.csv`, `*.parquet`, `*.json` de dados brutos

## Fora de escopo
- Fine-tuning ou treino de modelos
- Gráficos interativos / dashboards

## Dependências
- IS-03 (sources.yaml), IS-04 (ingestão), IS-05 (schema), IS-06 (retrieval)

## Definition of Done
- [ ] Notebook executável de ponta a ponta
- [ ] Resultados em `docs/investigate/eda-results.md`
- [ ] Revisado por Data + ML

**Story Points:** 8
BODY
)"

  # IS-08 — Baseline retrieval
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-08] Baseline de retrieval (BM25/TF-IDF vs embeddings)" \
    --label "sprint-1,ml,p0,sp-5" \
    ${ML_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ06 ("Qual é o Recall@5 mínimo aceitável?").
Establece o baseline quantitativo que define a meta de qualidade do pipeline.

## Descrição técnica
Implementado na seção 13 do notebook EDA e extraído para:
- `docs/investigate/eda-results.md` (gerado pelo notebook)

Métricas obrigatórias:
- **Recall@1**, **Recall@3**, **Recall@5**
- **MRR** (Mean Reciprocal Rank)
- **nDCG@5**

Comparação: BM25 (`rank-bm25`) vs ≥ 1 modelo de embedding (`sentence-transformers`)

Conjunto de avaliação:
- Subconjunto do silver com queries e relevâncias anotadas (pode ser criado sinteticamente a partir dos campos `claim_text` ↔ `evidence_summary`)
- Mesmo seed, mesma divisão documentada

Análise de erros (seção 14):
- 10–20 casos de falso positivo / falso negativo categorizados
- Hipóteses sobre causas (ambiguidade lexical, negação, jargão técnico)

## Critérios de aceitação
- [ ] `docs/investigate/eda-results.md` existe com tabela de métricas (BM25 vs embeddings)
- [ ] Métricas Recall@1/3/5, MRR, nDCG@5 reportadas para ambos os métodos
- [ ] Análise qualitativa de ≥ 10 casos de erro presente
- [ ] Metodologia documentada: seed, split, tamanho do conjunto de avaliação
- [ ] Resultados reproduzíveis com `jupyter nbconvert --execute notebooks/eda_datasets.ipynb`

## Fora de escopo
- Fine-tuning ou treino de modelos
- Integração com produção (Sprint 2)

## Dependências
- IS-06 (retrieval), IS-07 (notebook EDA)

## Definition of Done
- [ ] Métricas calculadas com evidência reproduzível
- [ ] `eda-results.md` publicado
- [ ] Revisado por ML

**Story Points:** 5
BODY
)"

  # IS-09 — Proveniência e manifest
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-09] Proveniência e manifest de dados" \
    --label "sprint-1,data,p0,sp-2" \
    ${DATA_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md) e GQ09 ("Como rastrear a origem de cada evidência?").
Garante reprodutibilidade e auditabilidade do pipeline de dados.

## Descrição técnica
- `backend/ml/datasets/manifest.py`: módulo que gera/lê `backend/data/manifest.json`
  - Funções: `update_manifest(dataset, file_path, source_url, version)` e `verify_manifest(manifest_path)`
  - `verify_manifest` retorna exit code 0 se OK, 1 se hash diverge
- `backend/data/manifest.json`: criado pelo pipeline de ingestão (IS-04)
  - Estrutura: `{"datasets": {"fakebr": {"sha256": "...", "version": "...", "ingested_at": "...", "source_url": "...", "record_count": 0}, ...}}`
  - Deterministicamente ordenado (chaves alfabéticas)
- `backend/data/README.md`: documenta como reproduzir do zero

CLI de verificação:
```
python -m ml.datasets.manifest verify  # exit 0 se OK, 1 se divergência
```

## Critérios de aceitação
- [ ] `backend/data/manifest.json` tem campos `sha256`, `version`, `ingested_at`, `source_url`, `record_count` por dataset
- [ ] `python -m ml.datasets.manifest verify` retorna exit 0 sem modificações e exit 1 após edição manual do arquivo
- [ ] `backend/data/README.md` tem seções: "Como baixar", "Como ingerir", "Como verificar hashes", "Aviso: nunca commitar datasets"
- [ ] `pytest backend/tests/test_ingestion.py::test_manifest_deterministic -q` passa: 2 execuções geram manifest idêntico
- [ ] `manifest.json` não contém caminhos absolutos da máquina do desenvolvedor

## Fora de escopo
- Download automático de datasets
- Integração com DVC ou MLflow

## Dependências
- IS-04 (ingestão gera o manifest)

## Definition of Done
- [ ] Módulo criado com testes passando
- [ ] README documentado
- [ ] Revisado por outro integrante

**Story Points:** 2
BODY
)"

  # IS-10 — Congelamento da UI (transversal, 0 SP)
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-10] Congelamento da UI do gauge até validação do pipeline" \
    --label "sprint-1,frontend,freeze,p0" \
    ${FE_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md).
Impede alterações acidentais nos componentes de UI do gauge/score enquanto a validação do pipeline de dados está em andamento.

## Descrição técnica
Arquivos congelados (não modificar até descongelamento):
- `extension/src/panel/components/Gauge.tsx`
- `extension/src/panel/index.tsx` (referências a `score` e `Gauge`)
- `extension/src/panel/components/SourceList.tsx` (referência a `reliabilityScore`)
- `shared/types/api.ts` (campo `score` e `reliabilityScore`)
- `shared/schemas/api-schema.json` (campos `score` e `reliabilityScore`)

Mecanismo de congelamento:
- `.github/frozen-paths.txt`: um glob por linha
- `.github/workflows/freeze-guard.yml`: falha em PRs que toquem caminhos congelados sem label `unfreeze-approved`
- `.github/FREEZE.md`: documenta o congelamento completo
- `.github/CODEOWNERS`: adiciona `@TECH_LEAD_HANDLE` (placeholder) nos caminhos congelados

Critério de descongelamento:
1. EDA executado de ponta a ponta (IS-07 concluído)
2. Fake.br + FactChecks.br ingeridos (IS-04 concluído)
3. Retrieval validado com métricas (IS-08 concluído)
4. `sample_facts.json` deixou de ser fonte primária
5. Label `unfreeze-approved` aplicado pelo Tech Lead

## Critérios de aceitação
- [ ] Workflow `.github/workflows/freeze-guard.yml` ativo: job `freeze-guard` aparece em PRs
- [ ] PR de teste tocando `extension/src/panel/components/Gauge.tsx` (sem label `unfreeze-approved`) → job FALHA
- [ ] PR de teste tocando `extension/src/panel/components/Gauge.tsx` (com label `unfreeze-approved`) → job PASSA
- [ ] `.github/FREEZE.md` documenta: o quê, por quê, critério de descongelamento, como solicitar exceção
- [ ] Pull Request Template tem checkbox: "Este PR toca caminhos congelados? (ver .github/FREEZE.md)"
- [ ] CODEOWNERS atualizado com `@TECH_LEAD_HANDLE` como placeholder (substituição manual)

## Fora de escopo
- Remoção ou alteração do código do gauge (Sprint 2)
- Branch protection via `gh api` (passo manual documentado em FREEZE.md)

## Dependências
- Nenhuma (pode ser feito imediatamente)

## Definition of Done
- [ ] Workflow criado e testado
- [ ] Documentação completa
- [ ] Placeholder `@TECH_LEAD_HANDLE` registrado para substituição manual

**Story Points:** 0 (transversal)
BODY
)"

  # IS-11 — Interface LLMProvider (transversal, 0 SP)
  run gh issue create \
    --repo "$REPO" \
    --title "[IS-11] Preparação: interface LLMProvider e guard anti-mock" \
    --label "sprint-1,backend,p0" \
    ${BE_FLAG} \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao [ADR-001](../docs/tecnico/decisoes/ADR-001-arquitetura-evidence-first.md).
Isola os providers de LLM em uma interface tipada e impede que o mock apareça silenciosamente em produção.
**NÃO conecta o factory aos serviços existentes** (migração é Sprint 2, S2-01).

## Descrição técnica
Módulos a criar em `backend/app/services/providers/`:
- `types.py`: `Claim`, `EvidenceRef`, `ProviderUnavailableError`, `MockInProductionError`
- `base.py`: `LLMProvider` (Protocol, `@runtime_checkable`)
  - `name: str`, `is_mock: bool`
  - `async extract_claims(transcript, video_title) -> list[Claim]`
  - `async generate_reflection(claims, evidence) -> list[str]`
- `mock.py`: `MockProvider` — determinístico, sem rede, `is_mock=True`, `ANALYSIS_MODE="mock"`
- `ollama.py`: esqueleto — `NotImplementedError("TODO: migrar de ollama_service.py — ver issue S2-01")`
- `remote.py`: esqueleto — lê `REMOTE_LLM_BASE_URL`, `REMOTE_LLM_API_KEY` de env (nunca hardcode)
- `factory.py`: `get_provider()` — lê `LLM_PROVIDER` e `APP_ENV`
  - `LLM_PROVIDER=mock` + `APP_ENV=production*` → `MockInProductionError` (fail-fast)
  - Valor desconhecido → `ValueError` com lista de válidos
  - Sem fallback automático para mock

## Critérios de aceitação
- [ ] `pytest backend/tests/test_provider_contract.py -q` → PASSED
  - `isinstance(MockProvider(), LLMProvider)` é `True`
  - Assinaturas de `extract_claims` e `generate_reflection` batem com o Protocol
  - `MockProvider().is_mock` é `True`
- [ ] `pytest backend/tests/test_no_mock_in_production.py -q` → PASSED
  - `APP_ENV=production` + `LLM_PROVIDER=mock` → levanta `MockInProductionError`
  - `APP_ENV=development` + `LLM_PROVIDER=mock` → não levanta
  - Valor inválido de `LLM_PROVIDER` → levanta `ValueError`
  - Varredura estática: nenhum módulo em `backend/app/` (exceto `providers/mock.py` e `factory.py`) importa `providers.mock`
- [ ] `pytest backend/tests/test_no_silent_mock_fallback.py -q` → mostra `1 xfailed` (dívida documentada)
- [ ] Nenhuma modificação em `fact_checker.py`, `ollama_service.py` ou qualquer serviço de produção existente

## Fora de escopo
- Conectar `factory.py` aos serviços existentes (Sprint 2, S2-01)
- Remover `_mock_analysis` de `FactCheckerService` (Sprint 2, S2-06)

## Dependências
- Pode ser desenvolvido em paralelo com IS-03 a IS-09

## Definition of Done
- [ ] Interface e factory criados com type hints e docstrings
- [ ] 3 suítes de teste passando (contract + no-mock-in-prod + xfail de silent-fallback)
- [ ] Dívidas técnicas da Sprint 2 documentadas nos xfails
- [ ] Revisado por outro integrante

**Story Points:** 0 (transversal)
BODY
)"

  echo ""
  echo "==> Sprint 1: 11 issues criadas (9 com SP + 2 transversais)."
}

# --- Sprint 2 Issues (apenas com INCLUDE_SPRINT2=1) ---------------------------

create_sprint2() {
  echo ""
  echo "==> Criando issues planejadas da Sprint 2..."

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-01] Provider abstraction migration" \
    --label "sprint-2,backend,p0,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao ADR-001. Migra `ollama_service.py` e `fact_checker.py` para usar `LLMProvider` (IS-11).

## Descrição técnica
- Implementar `OllamaProvider` em `providers/ollama.py` (remover `NotImplementedError`)
- Substituir import direto de `ollama_service` em `fact_checker.py` por `get_provider()`
- Remover fallback automático para mock em `_execute_analysis`

## Critérios de aceitação
- [ ] `fact_checker.py` não importa `ollama_service` diretamente
- [ ] `get_provider()` retorna `OllamaProvider` quando `LLM_PROVIDER=ollama`
- [ ] Todos os testes existentes passam sem modificação de fixtures
- [ ] `test_no_silent_mock_fallback.py::test_no_silent_fallback_in_fact_checker` muda de xfail para PASSED

## Fora de escopo
- Remoção do campo `score` da UI (S2-03)

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-02] Evidence-first schema (eliminar score do pipeline interno)" \
    --label "sprint-2,backend,ml,p0,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Vinculado ao ADR-001. Remove `score` do pipeline interno; `AnalyzeResponse` passa a ser derivado de evidências.

## Critérios de aceitação
- [ ] `AnalyzeResponse.score` mantido apenas para compatibilidade retroativa (marcado como `deprecated`)
- [ ] Pipeline interno não mais calcula `score` via heurísticas de `FactCheckerService`
- [ ] "resultado sem evidência nunca é convertido em `contradicted`/`falso`" validado por teste

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-03] Remoção do score global da UI" \
    --label "sprint-2,frontend,p0,sp-3" \
    --body "$(cat <<'BODY'
## Contexto
Remove o componente `Gauge` e o campo `score` da UI. Requer descongelamento (label `unfreeze-approved`).

## Critérios de aceitação
- [ ] `Gauge.tsx` removido ou desativado
- [ ] `index.tsx` não renderiza `<Gauge>`
- [ ] "nenhum score global na UI" validado em testes E2E
- [ ] Label `unfreeze-approved` presente no PR

**Story Points:** 3
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-04] Evidence Cards (substituir Gauge por cards de evidência)" \
    --label "sprint-2,frontend,p1,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Implementa componente `EvidenceCard` exibindo alegação + evidências + veredito em linguagem clara.

## Critérios de aceitação
- [ ] `EvidenceCard` renderiza `claim_text`, `verdict_normalized`, `evidence_summary`, `source_urls`
- [ ] Nenhum score numérico visível ao usuário
- [ ] Testes de acessibilidade WCAG 2.1 AA passam
- [ ] Navegação por teclado funcional

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-05] Reflection Questions (perguntas geradas pela LLM)" \
    --label "sprint-2,backend,frontend,p1,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Implementa geração de perguntas reflexivas baseadas nas evidências encontradas.

## Critérios de aceitação
- [ ] `generate_reflection(claims, evidence) -> list[str]` implementado no provider ativo
- [ ] 3–5 perguntas exibidas no painel após análise
- [ ] Perguntas derivadas das evidências, não do score
- [ ] P90 ≤ 10 s total (incluindo retrieval + geração)

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-06] Failure/timeout handling (remover fallback mock)" \
    --label "sprint-2,backend,p0,sp-3" \
    --body "$(cat <<'BODY'
## Contexto
Remove caminhos de fallback silencioso para mock em `FactCheckerService`. Vinculado a IS-11 (dívida xfail).

## Critérios de aceitação
- [ ] `_mock_analysis` removido de `FactCheckerService`
- [ ] Timeout retorna `503` com mensagem clara (sem fallback para mock)
- [ ] `test_no_silent_mock_fallback.py` xfail removido (testes agora passam como PASSED)
- [ ] "mock nunca pode aparecer silenciosamente em produção" validado

**Story Points:** 3
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-07] Latency tests (P90 ≤ 10 s validado em CI)" \
    --label "sprint-2,backend,p1,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Adiciona job `latency-gate` no CI que valida P90 ≤ 10 s end-to-end.

## Critérios de aceitação
- [ ] Job `latency-gate` no CI: 50 requisições paralelas, P90 ≤ 10 s
- [ ] Falha do job bloqueia merge em `main`
- [ ] Resultados publicados como artefato CI

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-08] E2E atualizado (fluxo sem score global)" \
    --label "sprint-2,frontend,p1,sp-5" \
    --body "$(cat <<'BODY'
## Contexto
Atualiza testes E2E para o novo fluxo evidence-first sem `Gauge` e sem score numérico.

## Critérios de aceitação
- [ ] `hu03.spec.ts` e `hu06.spec.ts` atualizados sem referência a `score` ou `Gauge`
- [ ] Novos E2E cobrem `EvidenceCard` e `ReflectionQuestions`
- [ ] "nenhum score global na UI" verificado nos E2E

**Story Points:** 5
BODY
)"

  run gh issue create \
    --repo "$REPO" \
    --title "[S2-09] Sprint Review evidence (artefatos publicados)" \
    --label "sprint-2,docs,p1,sp-2" \
    --body "$(cat <<'BODY'
## Contexto
Publica os artefatos de evidência do Sprint Review: EDA executado, métricas de retrieval, decisões tomadas.

## Critérios de aceitação
- [ ] `docs/investigate/eda-results.md` publicado com métricas finais
- [ ] `docs/decisions/sprint-2-review.md` com tabela de decisões e evidências
- [ ] ADR-001 atualizado com status `Implementado`

**Story Points:** 2
BODY
)"

  echo ""
  echo "==> Sprint 2: 9 issues planejadas criadas."
}

# --- Main ---------------------------------------------------------------------

main() {
  echo "================================================"
  echo " EvidencIA — Sprint 1 Issue Package"
  echo " Repo: $REPO | Milestone: $MILESTONE"
  echo " DRY_RUN: $DRY_RUN"
  echo "================================================"

  create_labels
  create_milestone
  create_sprint1

  if [[ "$INCLUDE_SPRINT2" == "1" ]]; then
    create_sprint2
  else
    echo ""
    echo "[INFO] Sprint 2 issues não criadas. Use INCLUDE_SPRINT2=1 para criar."
  fi

  echo ""
  echo "================================================"
  echo " Concluído!"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo " MODO DRY_RUN — nenhum comando foi executado."
    echo " Remova DRY_RUN=1 para criar as issues de verdade."
  fi
  echo "================================================"
}

main "$@"
