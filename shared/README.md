# EvidencIA — Módulos Compartilhados (Shared Contracts & Types)

> Fonte única da verdade (Single Source of Truth) para os contratos de comunicação entre a Extensão de Navegador e o Backend Proxy do projeto EvidencIA.

---

## 1. Visão Geral e Princípio de Integração

O diretório `shared/` estabelece o desacoplamento formal e a garantia de consistência entre o cliente (*frontend* da extensão em TypeScript) e o servidor (*backend proxy* em Python/FastAPI/Pydantic).

Ao centralizar as definições de dados neste módulo, o projeto garante que:
1. **Quebras de Contrato Sejam Detectadas em Tempo de Compilação:** A extensão importa tipos estáticos diretamente de [`shared/types/api.ts`](types/api.ts).
2. **Respostas da API Sejam Auditáveis em Tempo de Execução:** O arquivo [`shared/schemas/api-schema.json`](schemas/api-schema.json) fornece a especificação canônica validável em JSON Schema (Draft-07).
3. **Evolução Segura do Paradigma Evidence-First ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md)):** Alterações na modelagem de alegações, evidências ou estados de incerteza são registradas primeiramente nesta fronteira antes de serem implementadas nos subsistemas.

---

## 2. Estrutura do Módulo

```text
shared/
├── schemas/
│   └── api-schema.json    # JSON Schema (Draft-07) canônico para requisições e respostas
└── types/
    └── api.ts             # Interfaces TypeScript e uniões discriminadas para a extensão
```

---

## 3. Entidades Fundamentais (Evidence-First)

Conforme estabelecido pela decisão de arquitetura [ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md), o sistema não produz notas globais ou vereditos de veracidade. A comunicação é estruturada em torno de quatro entidades:

### 3.1 `Claim` (Alegação Atômica)
Representa uma proposição fática independente extraída do conteúdo do vídeo:
- `id`: Identificador único da alegação (ex.: `claim-01`).
- `text`: Texto exato da alegação em linguagem natural.
- `temporalContext`: Metadados temporais contendo a data da alegação e a data de publicação do vídeo, prevenindo anacronismos.
- `evidence`: Lista de evidências documentadas associadas.
- `uncertainty`: Estado analítico de incerteza da alegação.
- `reflectionQuestions`: Perguntas socráticas orientadas ao desenvolvimento do pensamento crítico do usuário ([HU15](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/backlog-e-historias.md#hu15)).

### 3.2 `Evidence` (Evidência Rastreável)
Representa um fato documentado originado de bases jornalísticas ou científicas auditáveis:
- `sourceId`: Identificador da fonte checadora (ex.: `lupa-12345`).
- `relation`: Relação com a alegação (`supports` | `contradicts` | `contextualizes`).
- `title` e `url`: Título da matéria e hiperlink para verificação direta pelo usuário.
- `publisher`: Nome da agência ou instituição responsável (ex.: *Agência Lupa*, *Aos Fatos*).
- `provenance`: Origem do dado (ex.: dataset `FactChecks.br`), data de indexação e hash do conteúdo.

### 3.3 `UncertaintyState` (Estado de Incerteza Analítica)
Substitui rótulos dogmáticos por categorias de incerteza transparente:
- `supported`: Amparada por evidências sólidas.
- `contradicted`: Desmentida ou refutada por checagens factuais.
- `contextualized`: Afirmação verdadeira mas dependente de contexto omitido.
- `conflicting`: Evidências de fontes confiáveis apontam direções divergentes.
- `insufficient_evidence`: Nenhuma base factual verificada foi encontrada para sustentar ou refutar.

---

## 4. Governança e Regras de Modificação de Contratos

Para preservar a integridade do sistema, qualquer alteração nas interfaces de dados deve seguir o fluxo de governança:

1. **Atualizar a Documentação Formal:** Propor a alteração no documento [Contrato Canônico de API](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/contrato-api.md).
2. **Atualizar o JSON Schema:** Modificar [`shared/schemas/api-schema.json`](schemas/api-schema.json).
3. **Sincronizar as Tipagens:**
   - Atualizar [`shared/types/api.ts`](types/api.ts) para o frontend.
   - Atualizar [`backend/app/schemas.py`](../backend/app/schemas.py) para os modelos Pydantic v2 do backend.
4. **Executar a Validação de Testes:**
   - No backend: `uv run pytest -v` (testes em `tests/test_provider_contract.py` e `tests/test_api.py`).
   - Na extensão: `npm test` (testes em `src/background/response-validation.test.ts`).

---

## 5. Rastreabilidade com a Documentação Oficial

- **Contrato Canônico:** [Especificação do Contrato de API](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/contrato-api.md)
- **Decisão Arquitetural:** [ADR-006: Arquitetura Evidence-First](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md)
- **Requisitos Vinculados:**
  - [RF-06 — Extração de Alegações Checáveis](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-06)
  - [RF-12 — Exibição de Evidências por Alegação](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-12)
  - [RF-13 — Exibição de Incerteza e Conflito de Evidências](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-13)
  - [RF-14 — Degradação Graciosa Evidence-Only](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-14)
- **Matriz Global:** [Matriz de Rastreabilidade](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/matriz-rastreabilidade.md)
