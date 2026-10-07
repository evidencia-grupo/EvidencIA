# EvidencIA — Gates e Decisões Humanas Consolidadas

**Status Geral:** `HUMAN_DECISION_REQUIRED`  
**Última Atualização:** 2026-10-07  
**Regra Fundamental:** Nenhuma das decisões abaixo pode ser tomada ou assumida silenciosamente por agentes autônomos. Cada item exige deliberação e aprovação explícita do responsável pelo projeto.

---

## H1 — Autenticação
> **Pergunta:** Qual estratégia será adotada para autenticar a extensão pública do Chrome contra o backend proxy?

### Contexto & Desafio
A extensão do Chrome é distribuída como código cliente aberto (Manifest V3). Segredos estáticos (API keys embutidas) são trivialmente extraídos por engenharia reversa.

### Alternativas Analisadas
1. **Solução A — API Key Estática Embutida:** Fácil implementação, mas segurança nula (vaza no `.crx`). Se revogada, derruba todos os usuários simultaneamente.
2. **Solução B — Token de Instalação Efêmero (App Check / UUID anônimo):** A extensão gera um `installation_id` anônimo e obtém credencial assinada após validar a origem `chrome-extension://`.
3. **Solução C — Requisição Assinada Criptograficamente (Web Crypto API):** Assinatura ECDSA por par de chaves local. Alta segurança contra replay, maior overhead no service worker.
4. **Solução D — Sessão Efêmera JWT Anônima:** Handshake em `/api/v1/auth/token` com emissão de JWT temporário (24h) com renovação transparente.

### Recomendação Técnica
**Adoção combinada de Solução B + D:** Handshake anônimo com validação de cabeçalho `Origin: chrome-extension://<EXTENSION_ID>` gerando JWT de curta duração com rotação automática em background.

### Status
- [ ] **Pendente de Decisão Humana** (Aguardando definição da liderança)

---

## H2 — Dataset e Licenciamento
> **Pergunta:** Podemos utilizar oficialmente as fontes e datasets sob suas respectivas licenças e termos de uso?

### Contexto & Evidência
- **Fake.br-Corpus (NILC / USP São Carlos):** Monteiro et al. (2018). Usado como corpus estilístico/linguístico. Repositório no GitHub não possui arquivo `LICENSE` explícito (marcado como "A verificar" em `sources.yaml`).
- **FactChecks.br (UFG):** Base curada de fact-checks de agências brasileiras IFCN (Lupa, Aos Fatos, Boatos.org). Licença também precisa de confirmação jurídica formal para distribuição em modo hosted comercial/público.
- **Google Fact Check Tools API:** Termos de serviço do Google requerem chave de API e obediência às cotas e políticas da ferramenta.

### Riscos Jurídicos
Incorporar dados em artefatos de distribuição comercial sem licença permissiva comprovada expõe o projeto a violação de direitos autorais.

### Recomendação Técnica
Obter confirmação formal dos mantenedores do Fake.br e FactChecks.br para uso acadêmico/aberto e configurar a ingestão via pipeline reprodutível sem comitar dumps brutos não licenciados.

### Status
- [ ] **Pendente de Decisão Humana** (Aguardando validação jurídica/acadêmica)

---

## H3 — Evaluation Labels (Gold Set de Avaliação)
> **Pergunta:** Quem realizará a rotulação humana das alegações e qual conjunto de dados será homologado como gold set oficial?

### Contexto & Regra Antifabricação
Modelos de IA e classificadores não podem avaliar a si mesmos de forma circular. Para calcular métricas oficiais de IR (Recall@5, Recall@10, MRR, nDCG), os pares alegação-evidência precisam de anotação humana independente e cega.

### Proposta Técnica Preparada
- Preparação de 50 a 100 amostras candidatas de transcrições do YouTube.
- Elaboração do guia de anotação [`EVAL-ANNOTATION-GUIDE.md`](file:///Users/aluno1/Documents/challenge%20fake%20news/evidencia/EVAL-ANNOTATION-GUIDE.md) definindo critérios objetivos: *Totalmente Relevante*, *Parcialmente Contextualiza*, *Irrelevante/Desconexa*.
- Pelo menos 2 anotadores humanos independentes com cálculo de concordância Kappa de Fleiss/Cohen.

### Status
- [ ] **Pendente de Decisão Humana** (Aguardando designação de avaliadores humanos e homologação do gold set)

---

## H4 — Privacidade e Retenção em Hosted Mode (LGPD)
> **Pergunta:** Qual política de retenção, anonimização e processamento de transcrições será adotada para o backend em produção?

### Contexto & Risco
Ao processar vídeos do YouTube, a transcrição pode conter nomes de pessoas, menções sensíveis ou relatos pessoais.

### Proposta Técnica
- **Princípio da Minimização:** Não armazenar o texto completo das transcrições permanentemente; persistir apenas o hash do conteúdo (`sha256`) e as alegações extraídas atômicas.
- **Feedback 100% Anônimo:** A rota `/api/v1/feedback` descarta qualquer identificador de rede (IP, cookies, User-Agent) antes de registrar métricas de utilidade.
- **Retenção de Cache:** TTL fixo de 7 dias para o cache de análises, com expiração automática.

### Status
- [ ] **Pendente de Decisão Humana** (Aguardando aprovação da política de privacidade)

---

## H5 — Infraestrutura de Deployment e Gerenciamento de Segredos
> **Pergunta:** Qual ambiente, domínio e provedor de hospedagem serão adotados para a release do backend e onde as credenciais serão armazenadas?

### Contexto
Para submeter a extensão à Chrome Web Store, o endpoint do backend precisa ser público, sob HTTPS e com domínio próprio estável (ex.: `api.evidencia.org.br` ou serviço em Cloud Run / Render).

### Alternativas
- **Google Cloud Run:** Escalabilidade serverless a zero, baixa latência, integração com Google Cloud Secret Manager.
- **Render / Railway:** Configuração simples com `render.yaml` já presente no repositório.
- **VPS / Docker Swarm:** Custo fixo, mas maior esforço de manutenção.

### Requisito
Secrets de produção (`OLLAMA_API_KEY`, `FACT_CHECK_API_KEY`, `JWT_SECRET`) devem ser injetados via variáveis de ambiente seguras no provedor, nunca gravados em arquivos de repositório.

### Status
- [ ] **Pendente de Decisão Humana** (Aguardando seleção do provedor de infraestrutura e provisionamento de domínio)

---

## H6 — Validação com Usuários Finais
> **Pergunta:** Quem conduzirá o experimento de validação empírica com usuários e quando a coleta será iniciada?

### Contexto
O projeto possui um protocolo de participante estruturado em `documentation/docs/validacao/protocolo-participante.md` e `plano-experimento.md`. Nenhum agente de IA pode atestar "produto validado" sem a realização do experimento com voluntários humanos.

### Critério de Pronto
O gate de validação humana só poderá mudar para `VALIDADO` após a submissão dos relatórios de teste com os usuários reais.

### Status
- [ ] **Pendente de Validação Humana** (Aguardando execução do experimento com participantes)
