# Auditoria Formal de Datasets — EvidencIA (Fase 3)

**Data da Auditoria:** 2026-10-07  
**Status de Conformidade:** `CONDITIONAL_PASS` (Bloqueio H2 Isolado)  
**Documento de Referência:** `backend/ml/datasets/sources.yaml`, ADR-001  

---

## 1. Resumo Executivo

O projeto EvidencIA utiliza conjuntos de dados para duas finalidades estritamente separadas e não intercambiáveis:
1. **Corpus Linguístico e Estilístico:** Análise textual e detecção de padrões de redação em desinformação.
2. **Corpus de Evidências Factuais (Fact-Checking):** Indexação e recuperação semântica de checagens produzidas por agências jornalísticas profissionais certificadas pela IFCN.

A presente auditoria avaliou a proveniência, licenciamento, limitações e riscos jurídicos/éticos de cada base de dados registrada no pipeline.

---

## 2. Inventário e Avaliação por Fonte

### 2.1 Fake.br-Corpus
- **Instituição / Autores:** NILC / USP São Carlos (Monteiro et al., 2018).
- **Repositório Oficial:** `https://github.com/roneysco/Fake.br-Corpus`
- **Papel no Sistema:** `linguistic_corpus` (corpus linguístico para análise de estilo).
- **Idioma:** pt-BR (7.200 notícias alinhadas e balanceadas, 3.600 verdadeiras e 3.600 falsas).
- **Licenciamento:** Ausência de arquivo `LICENSE` explícito no repositório de origem (status: *A verificar*).
- **Risco Epistemológico:** **CRÍTICO SE MAL UTILIZADO**. O Fake.br contém textos falsos inteiros rotulados como `fake`. Se esses textos forem injetados no índice de recuperação de evidências, o sistema poderia recuperar afirmações falsas como se fossem comprovações científicas.
- **Mitigação Técnica Implementada:** O Fake.br é expressamente excluído do pipeline de busca semântica (`backend/ml/retrieval/index.py`). Seu uso é restrito ao treinamento e benchmarking de modelos de estilometria e classificação sintática.
- **Veredito Jurídico:** Permitido para pesquisa e avaliação interna; distribuição de dump bruto em produção comercial requer contato com o NILC/USP (registrado no portão humano **H2**).

### 2.2 FactChecks.br
- **Instituição / Mantenedores:** Universidade Federal de Goiás (UFG) e colaboradores acadêmicos.
- **Repositório Oficial:** `https://github.com/fake-news-UFG/FactChecks.br`
- **Papel no Sistema:** `fact_check_evidence` (base primária de evidências factuais em língua portuguesa).
- **Idioma:** pt-BR.
- **Fontes Primárias Contidas:** Agência Lupa, Aos Fatos, Boatos.org, E-farsas, G1 Fato ou Fake (agências com signatários do código de princípios da IFCN).
- **Licenciamento:** Coletado para fins científicos e acadêmicos. O texto das matérias de checagem pertence aos respectivos veículos de imprensa.
- **Uso no Sistema:** Indexação vetorial e BM25 de alegações checadas e resumos de refutação com link para a matéria original.
- **Mitigação de Direitos Autorais:** O sistema não republica o artigo integral; atua como motor de busca apontando para a URL original da agência (citação e fair use jornalístico/científico com atribuição clara de publisher e data).
- **Veredito Jurídico:** Aprovado tecnicamente para o protótipo e pré-release. Homologação para operação em larga escala sob domínio público registrada no portão humano **H2**.

### 2.3 Google Fact Check Tools API / ClaimReview Markup
- **Provedor:** Google / Schema.org (`ClaimReview`).
- **Endpoint / Documentação:** `https://toolbox.google.com/factcheck/apis`
- **Papel no Sistema:** `external_complementary` (recuperação externa em tempo real para complementar o corpus local).
- **Idioma:** Multilíngue (filtrado dinamicamente para pt-BR e pt).
- **Licenciamento / Termos:** Sujeito aos Termos de Serviço da Google API. Requer autenticação por chave (`GOOGLE_FACT_CHECK_API_KEY`).
- **Proteção de Segredos:** Nenhuma chave embutida no repositório. O backend opera com mock seguro em desenvolvimento/teste e consome a chave via variável de ambiente segura em staging/produção.

### 2.4 ClaimPT
- **Instituição:** IST-EDIT (Portugal).
- **Repositório Oficial:** `https://github.com/IST-EDIT/ClaimPT`
- **Papel no Sistema:** `methodological_auxiliary`.
- **Idioma:** pt-PT (Português Europeu).
- **Restrição Estrita:** Não utilizado no pipeline de produção nem no cálculo de relevância semântica devido a divergências sintáticas, lexicais e de contexto sócio-político com pt-BR. Mantido exclusivamente como referência de taxonomia de check-worthiness.

---

## 3. Matriz de Separação Epistemológica

| Fonte | Tipo | Uso Autorizado | Uso Proibido |
| :--- | :--- | :--- | :--- |
| **Fake.br** | Notícias completas rotuladas | Modelos de estilo e vocabulário | Recuperação como fonte de evidência |
| **FactChecks.br** | Checagens jornalísticas IFCN | Índice de evidências, BM25, embeddings | Treino de geradores sem atribuição |
| **ClaimReview** | Metadados de checagens abertas | Consulta em tempo real com atribuição | Armazenamento de corpus bruto |
| **ClaimPT** | Sentenças PT-PT anotadas | Referência teórica de taxonomia | Indexação para usuários brasileiros |

---

## 4. Conclusão da Fase 3

A infraestrutura de dados cumpre todas as salvaguardas técnicas:
1. Nenhuma dependência de licença desconhecida foi embutida como código estático irreversível.
2. Não há contaminação entre corpus de estilo e corpus de fatos.
3. As decisões comerciais e institucionais pendentes estão claramente isoladas em `HUMAN-DECISIONS.md` (H2).
