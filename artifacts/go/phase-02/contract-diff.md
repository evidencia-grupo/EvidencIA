# Diff de Contrato & Evolução Semântica — Fase 2 (Evidence-First)

**Data:** 2026-10-07  
**Fase:** Fase 2 — Contrato, Semântica e Confiança da Evidência  
**Referência:** ADR-006, RF-06, RF-12, RF-17  

---

## 1. Isolamento Epistemológico Estrito (Regra Fundamental)

Fica terminantemente proibido que o texto da alegação checada (`record.claim_text`) substitua a fala ou título real do vídeo no `ClaimCard`.

- **Claim do Vídeo:** Representa estritamente o que foi dito ou intitulado no conteúdo analisado (`request.videoTitle` ou sentença da transcrição).
- **EvidenceCard:** Representa a checagem jornalística ou estudo científico auditado recuperado por agência de checagem.
- **Relação Factual:** A relação (`supports`, `contradicts`, `contextualizes`) só é atribuída após validação semântica com limiar estrito ($\ge 0.55$). Matchings lexicais moderados degradam obrigatoriamente para `contextualizes` com estado `insufficient_evidence` ou `contextualized`.

---

## 2. Alterações nos Contratos (Pydantic & TypeScript)

### Modelo `Claim`
```diff
 interface Claim {
   id: string;
   text: string;
+  transcriptSnippet?: string;  // Trecho textual da transcrição onde a alegação ocorre
+  timestampStart?: number;     // Segundo inicial para salto no player de vídeo (RF-17)
+  timestampEnd?: number;       // Segundo final do trecho
   temporalContext: TemporalContext;
   evidence: Evidence[];
   uncertainty: UncertaintyState;
   reflectionQuestions?: string[];
 }
```

### Modelo `Evidence`
```diff
 interface Evidence {
   sourceId: string;
   relation: EvidenceRelation;
   title: string;
   url: string;
   publishedAt: string;
   publisher: string;
   snippet?: string;
+  matchReason?: string;        // Explicação objetiva: "Por que esta fonte apareceu?"
   provenance: EvidenceProvenance;
 }
```

---

## 3. UI: Eliminação de Veredito Semafórico / Score Algorítmico

- **Remoção de Veredito Binário:** Nenhum componente gauge ou velocímetro numérico (0–100%) está presente no painel lateral.
- **Estados Explicativos Humanizados:**
  - `supported`: *"Apoiada por evidências (Fato verificado)"*
  - `contradicted`: *"Contraditada por fatos (Informação falsa)"*
  - `contextualized`: *"Contextualizada (Com ressalvas)"*
  - `conflicting`: *"Evidências conflitantes (Divergente)"*
  - `insufficient_evidence`: *"Sem evidência suficiente (Não checado)"*
