# EvidencIA — Módulos Compartilhados (Shared Contracts)

> Fonte única da verdade (Single Source of Truth) para os contratos de comunicação entre a Extensão de Navegador e o Backend Proxy do projeto EvidencIA.

---

## 1. Estrutura do Módulo

```text
shared/
├── schemas/
│   └── api-schema.json    # JSON Schema (Draft-07) canônico para requisições e respostas
└── types/
    └── api.ts             # Interfaces TypeScript e uniões discriminadas para o frontend
```

---

## 2. Entidades Fundamentais (Evidence-First)

Conforme a decisão [ADR-006](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md), o sistema não produz notas globais ou vereditos algorítmicos. A comunicação é estruturada em torno de:

- **`Claim` (Alegação Atômica):** Proposição fática independente do vídeo com contexto temporal, trecho de transcrição, evidências associadas e 3 perguntas reflexivas.
- **`Evidence` (Evidência Rastreável):** Fato documentado de agência checadora (Lupa, Aos Fatos) com relação (`supports`, `contradicts`, `contextualizes`), URL auditável e proveniência.
- **`UncertaintyState` (Estado de Incerteza):** Categorias analíticas transparentes (`supported`, `contradicted`, `contextualized`, `conflicting`, `insufficient_evidence`).

---

## 3. Governança de Contratos

Qualquer modificação nas interfaces de dados deve seguir a ordem estrita:
1. Atualizar o JSON Schema canônico em [`schemas/api-schema.json`](schemas/api-schema.json).
2. Sincronizar as tipagens do frontend em [`types/api.ts`](types/api.ts).
3. Sincronizar os modelos Pydantic v2 do backend em [`backend/app/schemas.py`](../backend/app/schemas.py).
4. Executar os testes de contrato: `pytest tests/test_provider_contract.py` e `npm test`.

Especificação detalhada: [docs/arquitetura/contrato-api.md](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/contrato-api.md).
