# Sumário Técnico da Pré-Release Candidata — EvidencIA (Fase 4)

**Data de Emissão:** 2026-10-07  
**Estado Consolidado:** `PRÉ-RELEASE CANDIDATA`  
**Branch:** `codex/go-phase-01-hardening`  

---

## 1. Conquistas Técnicas Desta Execução

Nesta sessão de trabalho, foram reconstruídas diretamente e homologadas com evidências 100% reais todas as alterações necessárias para transformar o repositório de um estado de impasse para uma **PRÉ-RELEASE CANDIDATA** robusta:

### 1.1 Hardening & Segurança (Fase 1)
- **Rate Limit Real:** Implementado middleware centralizado com `slowapi`, decorando todos os endpoints com limites adequados e comprovando emissão de HTTP 429 Too Many Requests quando sob estresse.
- **CORS Estrito por Ambiente:** Removido o risco de wildcard `*` em ambientes públicos. O backend recusa inicializar caso `ENVIRONMENT=production` e `CORS_ORIGINS` contenha `*`.
- **Autenticação Desacoplada e Segura:** Implementado mecanismo de tokens efêmeros baseados em assinatura criptográfica HMAC/SHA256 para clientes anônimos da extensão, com renovação transparente pelo Service Worker e bloqueio 401/403 no backend sob `REQUIRE_AUTH=True`.
- **Health Probes Reais:** Endpoints desacoplados `/health/live` e `/health/ready` para monitoramento de liveness e readiness sem respostas estáticas artificiais.
- **Defesa Contra Mocks:** Verificação em tempo de startup bloqueando o uso acidental de `MockLLMProvider` em produção.

### 1.2 Contrato Semântico e Separação Epistemológica (Fase 2)
- **Separação Estrita de Claim vs Evidência:** A alegação do vídeo (`ClaimCard`) reflete unicamente o que o criador de conteúdo do vídeo afirmou, sem contaminação pelo texto da agência de fact-checking externa.
- **Relação Semântica e Stance:** `brazilian_fact_matcher.py` agora degrada correspondências moderadas (< 0.55) para `contextualizes` e só atribui `contradicts`/`supports` para alta similaridade ($\ge 0.55$), evitando falsos conflitos ou falsos consensos.
- **Navegação Temporal Clicável:** Cada alegação carrega `transcriptSnippet` e marcadores temporais (`timestampStart`, `timestampEnd`). O painel lateral renderiza botões que instruem o content script a alterar instantaneamente o `video.currentTime` no YouTube player.
- **Justificativa Transparente:** O card de evidência exibe o bloco explicativo *"Por que esta fonte apareceu"*, aumentando a transparência algorítmica para a pessoa usuária.

### 1.3 Corpus, Retrieval e Avaliação Sem Circularidade (Fase 3)
- **Auditoria Formal de Datasets:** Auditoria documentada em `artifacts/go/phase-03/dataset-audit.md` e `sources.yaml`, isolando o Fake.br para estilometria e reservando FactChecks.br e ClaimReview para evidências factuais.
- **Gold Set & Manual Cego:** Criada a estrutura oficial em `evaluation/` (`claims.jsonl`, `candidates.jsonl`, `annotation-guide.md`, `README.md`) e script automatizado `evaluate_retrieval.py`.
- **Integridade Científica:** Nenhuma métrica simulada ou circular foi fabricada; o estado de rotulação humana está formalmente registrado como `PENDING_HUMAN_ANNOTATION` (Portão H3).
- **Notebook de EDA Reproduzível:** `backend/ml/notebooks/eda_retrieval.ipynb` implementado com seed fixa (`SEED = 42`).

### 1.4 Governança, CI e Documentação (Fase 4)
- **CI Fail-Closed:** Workflow `.github/workflows/ci.yml` atualizado com o job `check-drift` sem permissão para falhas silenciosas (`continue-on-error: true`).
- **Eliminação de Drift:** `scripts/check_drift.py` reporta **0 CRITICAL e 0 HIGH**, validando endpoints reais contra o manifesto, contratos Pydantic e tipos TypeScript.
- **Isolamento de Decisões Humanas:** O arquivo `HUMAN-DECISIONS.md` isola com clareza cristalina os 6 portões que dependem da liderança (H1 a H6).
