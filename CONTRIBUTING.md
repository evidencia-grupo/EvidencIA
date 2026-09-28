# Guia de Contribuicao e Governanca de Engenharia — EvidencIA

> Padroes tecnicos, modelo de branches, convencoes de commit e checklist de homologacao para os desenvolvedores do projeto.

---

## 1. Fluxo de Trabalho e Modelo de Ramificacao (Branching Model)

O repositorio adota o modelo **Trunk-Based com Feature Branches curtas**, dimensionadas para integracao continua no prazo de 2 semanas:

1. A branch `main` e a base estavel do produto. Commits diretos em `main` devem ser evitados; toda mudanca deve ser submetida via **Pull Request (PR)**.
2. Nomenclatura padronizada de branches:
   - Novas funcionalidades: `feat/huXX-nome-curto` (ex.: `feat/hu01-botao-player`)
   - Correcoes de defeitos: `fix/huXX-nome-curto` ou `fix/nome-do-bug` (ex.: `fix/hu05-parser-encoding`)
   - Tarefas tecnicas e documentacao: `chore/descricao` ou `docs/descricao`

---

## 2. Padrao de Mensagens de Commit (Conventional Commits)

Todas as mensagens de commit devem seguir estritamente o padrao **Conventional Commits**:

```
<tipo>(<escopo>): <descricao no imperativo>

[corpo opcional explicando o motivo e impacto tecnico]

[rodape opcional: Closes #numero-da-issue]
```

### Tipos Permitidos
- `feat`: Nova funcionalidade para o usuario ou arquitetura.
- `fix`: Correcao de falha ou comportamento divergente.
- `docs`: Modificacoes exclusivas em arquivos de documentacao.
- `test`: Inclusao ou correcao de testes unitarios, de integracao ou E2E.
- `refactor`: Alteracao interna de codigo que nao altera comportamento observavel.
- `perf`: Otimizacao de tempo de resposta, latencia ou consumo de memoria.
- `ci`: Alteracoes nos fluxos e scripts de automacao (GitHub Actions).
- `chore`: Atualizacao de dependencias, configuracoes de build ou tarefas de rotina.

---

## 3. Checklist Obrigatorio de Pre-Commit / Pre-Push

Antes de abrir um Pull Request ou enviar alteracoes, o desenvolvedor deve executar localmente:

### Na Extensao (`extension/`)
```bash
cd extension
npm run typecheck    # Verificacao estrita de tipos TypeScript
npm test             # Execucao dos testes unitarios via Vitest
npm run build        # Compilacao dos bundles para /dist e copia de manifest.json
```

### No Backend Proxy (`backend/`)
```bash
cd backend
# Opcao A (Recomendada via uv):
uv run ruff check .
uv run pytest -v

# Opcao B (Tradicional via pip):
ruff check .
python -m pytest -v
```

---

## 4. Convencoes de Estilo e Escrita

1. **Ausencia de Emojis:** Todos os documentos tecnicos, codigos, comentarios, commits e mensagens de erro do sistema devem ser estritamente profissionais, **sem utilizacao de emojis**, mantendo alinhamento com as diretrizes do portal de documentacao.
2. **Tratamento Seguro de Segredos:** Jamais introduza chaves de API, credenciais ou tokens em arquivos rastreados pelo Git. Chaves upstream residem exclusivamente no arquivo `.env` do backend proxy ([ADR-002](../documentation/docs/tecnico/decisoes/ADR-002-backend-proxy.md)).
3. **Isolamento de Estilos:** Elementos injetados na pagina do YouTube devem residir em **Shadow DOM** aberto; o painel lateral deve executar em **iFrame Sandbox** com politica restritiva ([ADR-001](../documentation/docs/tecnico/decisoes/ADR-001-manifest-v3.md)).
