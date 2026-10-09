# Contratos compartilhados

`schemas/api-schema.json` e `types/api.ts` são gerados dos modelos Pydantic em `backend/app/schemas.py`.

```bash
backend/.venv/bin/python scripts/generate_contracts.py
backend/.venv/bin/python scripts/generate_contracts.py --check
```

O JSON Schema usa Draft 7 com definições nomeadas. Campos opcionais Python preservam `null` no TypeScript. Não editar os arquivos gerados manualmente.

[Contrato e arquitetura](https://github.com/evidencia-grupo/documentation).
