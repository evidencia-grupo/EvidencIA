# Backlog de Issues do Projeto EvidencIA

Este diretório consolida as issues técnicas priorizadas para a finalização do produto, cobrindo os gargalos de paralelismo, segmentação de legendas ASR e calibração de modelos. Todas foram auditadas contra o código e os testes em 14/10/2026:

| Issue | Título | Tipo | Módulos Impactados | Link GitHub | Status |
|:---|:---|:---:|:---|:---:|:---:|
| [#66](001-paralelismo-perguntas-reflexao.md) | Pipeline de Paralelismo Assíncrono e Otimização de Latência das Perguntas de Reflexão | Performance / LLM | Backend (`fact_checker.py`, `remote.py`) | [#66](https://github.com/evidencia-grupo/EvidencIA/issues/66) | Concluída e validada |
| [#67](002-segmentacao-semantica-legendas-asr.md) | Segmentação Robusta de Legendas ASR e Preservação de Frases da Transcrição Completa | Feature / NLP | Backend (`claim_extractor.py`), Extensão (`caption-parser.ts`) | [#67](https://github.com/evidencia-grupo/EvidencIA/issues/67) | Concluída e validada |
| [#68](003-filtro-ruido-conversacional-saudacoes-tv.md) | Filtragem de Ruído Conversacional / Saudações de TV e Aumento da Precisão do Extrator | Bug / Acurácia | Backend (`claim_extractor.py`, `mock.py`) | [#68](https://github.com/evidencia-grupo/EvidencIA/issues/68) | Concluída e validada |
| [#69](004-calibracao-relevancia-matcher-evidencias.md) | Calibração Semântica do Matcher e Contexto Anti-Alucinação para Modelos Gratuitos | Feature / RAG | Backend (`brazilian_fact_matcher.py`, `prompts.py`) | [#69](https://github.com/evidencia-grupo/EvidencIA/issues/69) | Concluída e validada |

---

### Entregas e evidências

| Issue | Pull requests | Testes que comprovam |
|:---|:---|:---|
| #66 | #73 e `fix/release-closure-audit` | `tests/test_issue_66_reflection_concurrency.py`: limite de 3 reflexões simultâneas, falha isolada por alegação, ordem preservada e latência de duas rodadas em vez de quatro |
| #67 | #72 e `fix/release-closure-audit` | `tests/test_asr_segmentation.py` (pausas da fala, conectivos, limite de 35 palavras e tempos exatos dos segmentos), `extension/src/content/timed-captions.test.ts` e `caption-parser.test.ts` |
| #68 | #70, #71 e `fix/release-closure-audit` | `tests/test_claim_extraction.py`: aberturas de telejornal e chamadas do canal com saliência zero, sem descartar alegação factual curta após saudação |
| #69 | #71 e `fix/release-closure-audit` | `tests/test_semantic_relation.py` e `tests/test_extraction_constraints.py`: tema genérico não casa, números divergentes só contextualizam, números por extenso equivalem aos algarismos, modelo não introduz fontes nem vereditos |

As issues já existem no GitHub; estes arquivos são a cópia versionada do escopo e dos critérios de aceitação.
