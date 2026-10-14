# Guia de Contribuicao — EvidencIA

Agradecemos o interesse em contribuir com o **EvidencIA**! Este guia define os padroes de desenvolvimento, fluxo de trabalho e criterios de aceitacao necessarios para manter a qualidade, seguranca e acessibilidade do projeto.

---

## 1. Codigo de Conduta

Ao participar deste projeto, voce concorda em seguir os padroes de respeito e integridade descritos no [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 2. Como Contribuir

1. **Abra ou Escolha uma Issue:** Antes de iniciar uma mudanca substantiva, verifique as issues abertas ou crie uma proposta detalhando a motivacao e escopo.
2. **Crie um Branch Dedicado:**
   - Para correcoes: `fix/descricao-do-problema`
   - Para novas funcionalidades: `feat/nome-da-funcionalidade`
   - Para testes e documentacao: `test/nome-do-teste` ou `docs/ajuste-documental`
3. **Mantenha os Commits Atomicos:** Siga o padrao **Conventional Commits** (ex.: `feat: ...`, `fix: ...`, `test: ...`, `chore: ...`).
   - **Regra Importante:** Nao utilize emojis em mensagens de commit, codigo-fonte ou documentacao.

---

## 3. Ambiente de Desenvolvimento Local

O projeto e composto por dois componentes principais:

### 3.1 Backend Proxy (Python 3.12)

```bash
cd backend

# Instalacao de dependencias via uv (recomendado)
uv sync --frozen --extra dev

# Execucao do servidor local
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3.2 Extensao do Navegador (Node.js 24 LTS)

```bash
cd extension

# Instalacao limpa de dependencias
npm ci --ignore-scripts

# Build de desenvolvimento
npm run build

# Typecheck e Linter
npm run lint
```

---

## 4. Testes Automatizados e Portao de Qualidade

Antes de abrir um Pull Request, certifique-se de que todas as suites de testes executam com 100% de sucesso localmente:

### Testes do Backend

```bash
cd backend
uv run pytest -v --cov=app --cov-report=term-missing
```

### Testes da Extensao (Unitarios, Componentes e A11y)

```bash
cd extension
npm test
npm run test:coverage
```

### Verificacao de Integridade de Contratos e Drift

Os contratos entre backend e frontend residem em `shared/`. Nao edite os arquivos gerados manualmente; altere os modelos em `backend/app/schemas.py` e execute:

```bash
# Na raiz de EvidencIA
python scripts/generate_contracts.py --check
python scripts/check_drift.py --docs ../documentation
```

O script `check_drift.py` e fail-closed: nao sao permitidos apontamentos de severidade CRITICAL ou HIGH.

---

## 5. Diretrizes Arquiteturais e Invariantes

- **Evidence-First Architecture (ADR-006):** O sistema nunca emite pontuacoes numericas de verdade ("score de confiabilidade") ou rotulos binarios simplistas. As respostas devem sempre apresentar evidencias auditaveis e perguntas de reflexao critica.
- **Acessibilidade WCAG 2.1 AA:** Todos os elementos de interface devem garantir razao de contraste minima de 4.5:1 para texto normal, suporte integral a navegacao por teclado (`Tab`, `Shift+Tab`, `Escape`) e compatibilidade com leitores de tela.
- **Zero Segredos no Cliente:** Nenhuma credencial privada, token de terceiros ou dado sensivel pode ser persistido ou exposto no cliente Chromium.

---

## 6. Submissao de Pull Requests

1. Preencha integralmente o modelo em `.github/PULL_REQUEST_TEMPLATE.md`.
2. Garanta que a esteira de CI (`.github/workflows/ci.yml`) passe com sucesso em todos os jobs.
3. Solicite revisao dos mantenedores indicados no arquivo `.github/CODEOWNERS`.
