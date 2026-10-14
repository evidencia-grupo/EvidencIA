# EvidencIA — Backend Proxy & Orquestrador de IA

> Backend Proxy assíncrono em FastAPI, isolador de credenciais (**Zero Segredos no Cliente** - [ADR-002](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)), orquestrador de inferência e motor de casamento com datasets brasileiros (FactChecks.br).

---

## 1. Estrutura do Módulo

```text
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS restrito e Rate Limiting (SlowAPI)
│   ├── config.py        # Configurações tipadas via Pydantic Settings
│   ├── schemas.py       # Modelos Pydantic v2 sincronizados com shared/
│   ├── api/v1/          # Endpoints (/analyze, /auth/token, /health, /classify)
│   ├── providers/       # Camada agnóstica de LLM (Ollama, Remote, Mock)
│   └── services/        # Orquestrador fact_checker, brazilian_fact_matcher, auth
├── ml/                  # Datasets curados (sample_facts.json) e classificador Naive Bayes
└── tests/               # Suíte Pytest (cobertura mínima obrigatória: 80%)
```

### Artefatos do classificador

- `ml/classifier/model.json`: único formato carregado em runtime (`ClassifierService`), desserializado como JSON puro.
- `ml/classifier/model.plk`: exportação pickle do mesmo modelo, mantida porque a extensão `.plk` foi solicitada como entregável acadêmico. Não é lida pela API; `tests/test_no_pickle_in_runtime.py` impede que `app/` ou `ml/` importem desserializadores pickle ou referenciem `.plk`/`.pkl`. Carregue-a só em ambiente confiável, pois `pickle.load` executa código.

---

## 2. Endpoints Principais (API v1)

- `POST /api/v1/analyze`: Recebe transcrição do vídeo e retorna alegações atômicas e evidências.
- `POST /api/v1/auth/token`: Emite credencial de acesso efêmera assinada para a extensão.
- `GET /api/v1/health`: Retorna status dinâmico do serviço (`healthy`, `degraded`, `unhealthy`).
- `GET /api/v1/health/live` e `/health/ready`: Liveness e readiness probes para orquestração.
- `POST /api/v1/feedback`: Registro voluntário e anônimo de utilidade (LGPD/RNF-05).
- `POST /api/v1/classify`: Classificação supervisionada de proposições com abstenção.

---

## 3. Instalação e Execução

```bash
# 1. Instalar dependências (recomendado: uv)
uv sync
# Ou via pip: pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp ../.env.example .env

# 3. Executar o servidor
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger UI disponível em: `http://127.0.0.1:8000/docs`

### Dependências

`pyproject.toml` + `uv.lock` são a fonte canônica. `requirements.txt` (runtime, usado pelo Dockerfile e pelo Render) e `requirements-dev.txt` (usado pelo E2E e pelo drift check no CI) são exportações com hashes e não devem ser editados à mão; o job `lint-back` falha se divergirem. Para regenerar, na raiz do repositório:

```bash
uv export --frozen --no-dev --no-emit-project --project backend --format requirements-txt > backend/requirements.txt
uv export --frozen --extra dev --no-emit-project --project backend --format requirements-txt > backend/requirements-dev.txt
```

`requirements-ml.txt` (índice vetorial e embeddings opcionais) e `requirements-notebook.txt` (reprodução do notebook entregue) são ambientes opcionais e isolados: não entram no runtime, na imagem Docker nem no Render.

---

## 4. Testes Automatizados

```bash
# Execução da suíte completa
uv run pytest -v

# Cobertura de código (mínimo obrigatório: 80%)
uv run pytest -v --cov=app --cov-report=term-missing
```

Documentação arquitetural completa: [docs/arquitetura/arquitetura.md](https://github.com/evidencia-grupo/documentation/blob/main/docs/arquitetura/arquitetura.md).

## Filtragem de ruído e extração atômica

Rastreabilidade: Épicos 4 e 7; RF-06, RF-07, RF-12, RNF-04, RNF-06; ADR-006.

O `BrazilianFactMatcher` rejeita ruído identificado por `is_conversational_filler`, incluindo aberturas como “Tá começando o seu programa de saúde…”. Antes de calcular o score ou conceder bônus de domínio, exige pelo menos três termos distintos em comum, depois de remover palavras funcionais e termos genéricos de apresentação. Pelo menos um termo compartilhado deve estar fora do vocabulário de domínio: uma lista como “vacina dengue Anvisa SUS” não basta. O limiar padrão continua em 0,30; reduzi-lo não desativa essas condições. Essa regra é uma aproximação lexical conservadora, não uma análise gramatical de sujeito, verbo e predicado, e pode deixar de recuperar paráfrases curtas.

Correspondências lexicais continuam apenas contextuais. Apoio ou contradição exigem a mesma proposição textual, sem inversão de negação; URL, data, trecho e hash de proveniência vêm do registro recuperado. A base demonstrativa permanece bloqueada em produção.

Ollama e Remote compartilham o prompt de extração: de zero a quatro trechos contínuos da transcrição, cada um com no máximo **25 palavras e 180 caracteres**, preservando negações e qualificadores. O título é contexto, não fonte. O prompt proíbe parágrafos extensos de ASR, fontes inventadas e vereditos globais. O backend também valida os limites de tamanho e quantidade: respostas inválidas acionam Evidence-Only explicitamente, sem truncar a frase. Os limites se aplicam à saída do LLM, não à transcrição de entrada nem ao extrator determinístico de contingência. Antes de buscar evidências, o orquestrador descarta trechos ausentes da transcrição e ruído conversacional; o fallback não reutiliza uma saudação inteira como alegação.

Regressões específicas, executadas de `backend/`:

```bash
uv run pytest tests/test_conversational_matching.py tests/test_extraction_constraints.py tests/test_semantic_relation.py
uv run pytest --cov=app --cov-report=term-missing
```

Os testes cobrem falsos positivos, todas as correspondências exatas da amostra local com sua proveniência, negações, limites de extração, instruções recebidas pelos dois provedores e fallback. As respostas dos LLMs são simuladas nesses testes; isso não mede a qualidade de um modelo remoto ao vivo.
