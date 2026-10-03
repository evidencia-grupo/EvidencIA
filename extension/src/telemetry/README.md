# Modulo de Telemetria Comportamental — Fase CBL Act

## Visao Geral

Este modulo implementa a instrumentacao de telemetria estrita para a fase experimental **Act** do framework *Challenge-Based Learning* (CBL) no projeto **EvidencIA**.

Sua finalidade e registrar interacoes comportamentais objetivas do usuario para avaliar empiricamente se a arquitetura **Evidence-First** (Condicao B) estimula maior escrutinio critico do que a abordagem baseada em veredito e gauge (Condicao A).

---

## Politica Estrita de Privacidade e LGPD

O modulo foi desenhado sob principios de **privacidade por design** e **minimizacao de dados**:

- **Desligado por Padrao**: O modulo e totalmente inerte em compilacoes de producao.
- **Duplo Gate em Memoria**:
  1. A flag de compilacao `EXPERIMENT_MODE` deve ser explicitamente definida como `true`.
  2. O consentimento do participante (`grantConsent()`) deve ser acionado na sessao em curso.
- **Zero Persistencia de Rastreamento**: Nao armazena cookies, nao grava em `localStorage` e nao mantem consentimento entre reinicializacoes.
- **Zero Acesso a Rede Externa**: O modulo nao contem chamadas a `fetch`, `XMLHttpRequest`, `sendBeacon`, `WebSocket` ou endpoints remotos. Toda a coleta reside estritamente em memoria no buffer local (`MemorySink`).
- **Falha Fechada (Fail-Closed)**: Qualquer evento com campo desconhecido, fora de faixa ou contendo caracteres suspeitos (URLs, e-mails, CPFs) e sumariamente descartado e contabilizado em estatisticas de rejeicao (`getRejectionStats()`).

### Dados Expressamente Vetados (Nunca Coletados)
- Transcricoes completas ou trechos de fala de videos.
- Textos literais de alegacoes ou cards de evidencia.
- URLs de videos, paginas ou canais do YouTube.
- Identificadores de video (`video_id`).
- Textos livres digitados pelo participante (respostas discursivas).
- Dados de identificacao pessoal (nome, e-mail, CPF, telefone).
- Enderecos IP, User-Agents completos ou timestamps absolutos UTC.

---

## Estrutura do Modulo

```text
extension/src/telemetry/
├── events.ts                          # Definicao de tipos, enums e allowlist estrita
├── sanitize.ts                        # Sanitizador fail-closed com contadores de rejeicao
├── consent.ts                         # Gate duplo (EXPERIMENT_MODE + grantConsent em memoria)
├── session.ts                         # Gestor de sessao (UUID v4, seq e deltas t_ms)
├── sink.ts                            # Interfaces de sink, MemorySink e serializador JSONL
├── index.ts                           # Ponto unico de exportacao da API
├── schema/
│   └── telemetry-event.schema.json    # JSON Schema normativo (draft 2020-12)
└── __tests__/                         # Bateria de testes unitarios e de isolamento
```

---

## Como Utilizar em Ambiente Experimental

```typescript
import {
  setExperimentMode,
  grantConsent,
  createSession,
  MemorySink,
} from './telemetry';

// 1. Habilitar modo de experimento (em dev/testes controlados)
setExperimentMode(true);

// 2. Registrar o aceite formal do TCLE pelo participante
grantConsent();

// 3. Inicializar a sessao do participante
const session = createSession({
  pid: 'P-0001',
  cond: 'B',
  phase: 'assisted',
  item_id: 'IT-001',
});

// 4. Instanciar o sink em memoria
const sink = new MemorySink();

// 5. Emitir e registrar eventos validados
const startEvent = session.createRawEvent('session_started', {
  build: 'a1b2c3d',
});
sink.record(startEvent);

const expandEvent = session.createRawEvent('evidence_expanded', {
  claim_ordinal: 1,
  evidence_ordinal: 1,
  relation: 'supports',
});
sink.record(expandEvent);

// 6. Exportar payload serializado em JSONL ao final da sessao
const jsonlData = sink.exportJsonl();
// O pesquisador salva manualmente como act_P-0001_<sid8>.jsonl
```
