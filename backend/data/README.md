# Backend Data — EvidencIA Pipeline

> **ATENÇÃO: NUNCA commitar datasets brutos, processados, embeddings ou índices neste diretório.**
> Consulte `.gitignore` para as regras de exclusão.

---

## Estrutura

```
backend/data/
├── manifest.json     — Registro de versão, SHA-256 e contagens por dataset
├── bronze/           — Dados brutos (download direto; nunca commitados)
│   └── .gitkeep
├── silver/           — Dados normalizados e validados (parquet/jsonl; nunca commitados)
│   └── .gitkeep
└── gold/             — Dados finais prontos para indexação (nunca commitados)
    └── .gitkeep
```

---

## Como reproduzir do zero

### 1. Baixar os datasets

```bash
# Fake.br Corpus (NILC / USP São Carlos)
# Site: https://github.com/roneysco/Fake.br-Corpus
# Baixe manualmente ou via git clone e coloque em:
mkdir -p backend/data/bronze/fakebr
# Copie os CSVs para backend/data/bronze/fakebr/

# FactChecks.br (fake-news-UFG)
# Site: https://github.com/fake-news-UFG/FactChecks.br
mkdir -p backend/data/bronze/factchecksbr
# Copie os JSON/CSVs para backend/data/bronze/factchecksbr/
```

### 2. Ingerir (bronze → silver)

```bash
# A partir do diretório backend/
python -m ml.datasets.ingest --source fakebr \
    --input-dir data/bronze/fakebr \
    --output-dir data/silver

python -m ml.datasets.ingest --source factchecksbr \
    --input-dir data/bronze/factchecksbr \
    --output-dir data/silver
```

Para validar sem gravar:
```bash
python -m ml.datasets.ingest --source fakebr \
    --input-dir data/bronze/fakebr \
    --dry-run
```

### 3. Verificar hashes

```bash
python -m ml.datasets.manifest verify
```

Saída esperada:
```
✅ Todos os hashes do manifest conferem.
```

### 4. Construir índice vetorial

```bash
python -m ml.retrieval.index \
    --collection evidencia \
    --silver-dir data/silver
```

---

## Arquivo manifest.json

O `manifest.json` é gerado automaticamente pela ingestão e contém:

```json
{
  "datasets": {
    "fakebr": {
      "ingested_at": "2026-10-02T00:00:00+00:00",
      "record_count": 7200,
      "sha256": "sha256:<hex64>",
      "source_url": "https://github.com/roneysco/Fake.br-Corpus",
      "version": "2024-01"
    },
    "factchecksbr": {
      ...
    }
  }
}
```

**O manifest é o único arquivo deste diretório que é commitado** (exceto `.gitkeep`).

---

## Regras de segurança

- ❌ NUNCA commitar: `*.csv`, `*.parquet`, `*.jsonl`, `*.json` (exceto `manifest.json`), `chroma/`, `*.sqlite3`, `*.npy`
- ✅ SEMPRE commitar: `manifest.json`, `README.md`, `.gitkeep`
- 🔑 Chaves de API: usar `.env` (nunca commitado); ver `.env.example`
