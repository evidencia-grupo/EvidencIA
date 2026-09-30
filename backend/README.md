# EvidencIA — Backend Proxy & ML Pipeline

Backend seguro em **FastAPI (Python 3.12+)** para o projeto **EvidencIA**, responsável por orquestrar a checagem factual de vídeos do YouTube, isolando credenciais sensíveis e operando com modelos de linguagem locais e bases de dados abertas brasileiras.

---

## 1. Arquitetura do Pipeline de Verificação

O backend adota um fluxo de verificação em camadas com degradação suave (*graceful degradation*):

```mermaid
flowchart TD
    Req[POST /api/v1/analyze] --> OllamaCheck{Ollama Local Ativo?\nqwen2.5:3b}
    OllamaCheck -- Sim --> OllamaExt[Extração Estruturada de Alegações\nJSON Schema]
    OllamaCheck -- Não / Falha --> HeuristicExt[Extração Heurística de Fallback]

    OllamaExt --> Matcher[Brazilian Fact Matcher\nFactChecks.br / sample_facts.json]
    HeuristicExt --> Matcher

    Matcher --> Found{Encontrou Checagem\nBrasileira (Jaccard >= 0.25)?}
    Found -- Sim --> LocalResp[Retorna Veredito & Fonte Oficial\nLupa, Aos Fatos, Boatos.org]
    Found -- Não --> GoogleCheck{Google Fact Check\nAPI Key configurada?}

    GoogleCheck -- Sim --> GoogleAPI[Google Fact Check Tools API]
    GoogleCheck -- Não / Miss --> Synth[Síntese sem Jargões via Ollama\nou Heurística]

    GoogleAPI --> Synth
    LocalResp --> Resp[AnalyzeResponse HTTP 200]
    Synth --> Resp
```

---

## 2. Configuração do Ambiente

### 2.1 Pré-requisitos
- Python >= 3.12 (recomendado 3.12 ou 3.14 via `uv`)
- [Ollama](https://ollama.ai) instalado localmente

### 2.2 Instalação com uv (Recomendado)
```bash
# Sincronizar ambiente e dependências
uv sync

# Configurar variáveis de ambiente
cp .env.example .env
```

### 2.3 Instalação com venv + pip
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 3. Modelo Local: Ollama com Qwen 2.5-3B

O EvidencIA utiliza o **Qwen 2.5-3B-Instruct** para processar transcrições em português brasileiro e gerar saídas JSON estruturadas com consumo de apenas ~2.2 GB de memória RAM.

```bash
# 1. Iniciar o daemon do Ollama e baixar o modelo
ollama run qwen2.5:3b

# 2. Testar conectividade (opcional)
curl http://localhost:11434/api/tags
```

### Variáveis de Ambiente (`.env`):
```ini
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=8.0
```

Se o Ollama não estiver rodando no momento da requisição, o backend automaticamente utiliza o fallback heurístico + base brasileira local, garantindo zero interrupção de serviço.

---

## 4. Datasets Brasileiros & MLOps

O repositório prioriza checagens factuais brasileiras sob licença aberta:

- **`FactChecks.br`**: Base consolidada com checagens da Agência Lupa, Aos Fatos e Boatos.org.
- **`Fake.br Corpus` (USP)**: Notícias balanceadas em PT-BR para benchmarking.
- **`sample_facts.json`**: Base embutida no repositório (`backend/ml/datasets/sample_facts.json`) com checagens brasileiras curadas (< 40 KB) para testes offline e CI/CD.

### Inspecionar ou Baixar Dados Completos:
```bash
# Exibe metadados e estatísticas do FactChecks.br
python ml/datasets/dataset_downloader.py --dataset factchecks

# Baixar para diretório local (ignorado pelo Git via .gitignore)
python ml/datasets/dataset_downloader.py --dataset factchecks --output-dir ml/datasets/data
```

> [!NOTE]
> Arquivos binários pesados de modelos (`.gguf`, `.safetensors`, `.bin`) e diretórios de dados brutos (`ml/datasets/data/`) são bloqueados no `.gitignore` para proteger a governança do repositório.

---

## 5. Execução do Servidor

```bash
# Modo desenvolvimento com hot-reload
uv run uvicorn app.main:app --reload --port 8000
```
Swagger UI disponível em: `http://localhost:8000/docs`

---

## 6. Testes Automatizados e Qualidade

```bash
# Executar todos os testes com cobertura
uv run pytest -v

# Linter de código
uv run ruff check .
```
