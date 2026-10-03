# EvidencIA — Backend Proxy & Orquestrador de IA

> Backend Proxy seguro, orquestrador assíncrono de inteligência artificial e motor de casamento com datasets brasileiros para o projeto EvidencIA.

---

## 1. Visão Geral e Papel na Arquitetura

O **Backend Proxy** é o componente responsável por isolar todo o acesso a modelos de inteligência artificial e serviços externos de busca de checagens de fatos. A extensão cliente interage unicamente com este serviço via HTTPS/JSON, implementando o princípio fundamental de **Zero Segredos no Cliente**.

### Princípios Arquiteturais e Decisões Formais (ADRs)
- **Isolamento de Credenciais ([ADR-002](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)):** Nenhuma chave de API (OpenAI, Gemini, Serper, etc.) reside no código da extensão. O backend centraliza a gestão segura de credenciais via variáveis de ambiente.
- **Modelo Local e Soberania em PT-BR ([ADR-005](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-005-modelo-local-e-datasets-brasileiros.md)):** Suporte nativo à inferência local soberana via Ollama utilizando o modelo `qwen2.5:3b-instruct` e priorização de checagens de agências brasileiras (FactChecks.br, Lupa, Aos Fatos).
- **Paradigma Evidence-First ([ADR-006](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)):** A API entrega coleções estruturadas de alegações, evidências rastreáveis e estados de incerteza analítica. Não são geradas notas numéricas unilaterais ou scores de veracidade.
- **Degradação Graciosa Evidence-Only ([RF-14](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-14)):** Em caso de indisponibilidade ou timeout do provedor de IA, o orquestrador sintetiza os dados das bases de checagem nacionais no modo `evidence_only`, mantendo o serviço operacional para o usuário.
- **Defesa em Profundidade contra Provedores Falsos ([RF-15](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-15)):** Travas em nível de configuração impedem estritamente a execução de `MockLLMProvider` em ambiente de produção (`ENVIRONMENT=production`).

---

## 2. Estrutura do Módulo

```text
backend/
├── pyproject.toml         # Configuração de empacotamento, dependências e pytest
├── requirements.txt       # Dependências para instalação via pip padrão
├── .python-version        # Declaração de runtime Python (3.12)
├── app/
│   ├── main.py            # Ponto de entrada FastAPI, CORS e Rate Limiting (SlowAPI)
│   ├── config.py          # Gestão tipada de variáveis de ambiente via Pydantic Settings
│   ├── schemas.py         # Schemas Pydantic v2 sincronizados com shared/schemas/api-schema.json
│   ├── api/v1/
│   │   └── endpoints.py   # Handlers para POST /api/v1/analyze e GET /api/v1/health
│   ├── providers/         # Camada agnóstica de provedores de IA (Factory Pattern)
│   │   ├── base.py        # Protocolo abstrato LLMProvider
│   │   ├── factory.py     # Resolução de provedor com guardas de segurança
│   │   ├── ollama.py      # Integração local via Ollama HTTP API (Qwen 2.5)
│   │   ├── remote.py      # Integração com APIs externas (OpenAI / Gemini)
│   │   ├── mock.py        # Provedor determinístico para testes e CI
│   │   └── types.py       # Dataclasses de extração e classificação
│   └── services/          # Serviços de negócio e orquestração assíncrona
│       ├── fact_checker.py            # Orquestrador assíncrono principal
│       ├── brazilian_fact_matcher.py  # Casamento semântico/léxico com bases nacionais
│       ├── fact_check_client.py       # Cliente para consumo de APIs de checagem
│       ├── ollama_service.py          # Utilitários de comunicação com Ollama
│       └── synthesis.py               # Síntese e formatação de respostas Evidence-First
├── ml/                    # Módulo de Aprendizado de Máquina e Datasets
│   ├── datasets/          # Catálogo, scripts de download e adapters de bases
│   │   ├── sample_facts.json          # Amostra curada de checagens nacionais
│   │   ├── ingest.py / normalize.py   # Pipeliners de dados e manifestos
│   │   └── adapters/                  # Adapters para FactChecks.br e Fake.br
│   ├── embeddings/        # Gerador de representações vetoriais
│   ├── retrieval/         # Mecanismos de busca e indexação local
│   └── schemas/           # Modelos de evidência de ML
└── tests/                 # Suíte automatizada de testes (Pytest)
```

---

## 3. Endpoints da API

Para a especificação completa de contratos e tipos de payload, consulte o [Contrato Canônico de API](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/contrato-api.md).

| Método | Rota | Descrição | Requisitos Relacionados |
|:---|:---|:---|:---|
| `POST` | `/api/v1/analyze` | Recebe metadados e transcrição do vídeo, orquestra extração, busca de evidências e retorna o payload Evidence-First | [RF-06](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-06), [RF-12](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-12), [RF-13](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-13), [RF-14](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rf-14) |
| `GET` | `/api/v1/health` | Verifica a disponibilidade do backend, do provedor de IA e a conectividade com os datasets | [RNF-06](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/requisitos/catalogo-requisitos.md#rnf-06) |

---

## 4. Como Executar Localmente

### 4.1 Pré-requisitos
- **Python >= 3.12** (recomendado o uso de [`uv`](https://github.com/astral-sh/uv))
- *(Opcional)* **Ollama** com o modelo `qwen2.5:3b` instalado para inferência local:
  ```bash
  ollama pull qwen2.5:3b
  ```

### 4.2 Instalação e Execução com `uv`
```bash
# 1. Instalar dependências e preparar ambiente virtual
uv sync

# 2. Configurar variáveis de ambiente
cp ../.env.example .env

# 3. Iniciar o servidor com reload automático
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4.3 Instalação e Execução com venv padrão
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 5. Como Executar a Suíte de Testes

Os testes automatizados validam contratos de schemas, proteção contra vazamento de mocks e resiliência:

```bash
# Executar todos os testes com Pytest
uv run pytest -v

# Executar com relatório de cobertura de código
uv run pytest --cov=app --cov-report=term-missing
```

---

## 6. Rastreabilidade com a Documentação Oficial

Toda a documentação conceitual e técnica deste serviço é mantida no repositório oficial [evidencia-grupo/documentation](https://github.com/evidencia-grupo/documentation) (branch `docs/reorganizacao`):

- **Arquitetura Geral:** [Documento de Arquitetura de Software](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/arquitetura.md)
- **Contrato de API:** [Especificação do Contrato de API](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/contrato-api.md)
- **Pipeline de IA e Datasets:** [IA e Datasets Brasileiros](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/ia-e-datasets.md)
- **Decisões Arquiteturais:**
  - [ADR-002: Backend Proxy Seguro](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-002-backend-proxy.md)
  - [ADR-005: Modelo Local e Datasets Brasileiros](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-005-modelo-local-e-datasets-brasileiros.md)
  - [ADR-006: Arquitetura Evidence-First](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/decisoes/ADR-006-evidence-first-architecture.md)
- **Segurança:** [Modelo de Ameaças (Threat Model)](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/threat-model.md)
- **Validação e Testes:** [Estratégia Global de Testes](https://github.com/evidencia-grupo/documentation/blob/docs/reorganizacao/docs/arquitetura/estrategia-testes.md)
