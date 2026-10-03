// @vitest-environment jsdom
import { describe, it, expect } from "vitest";
import { render } from "preact";
import { ClaimCard } from "./components/ClaimCard";
import { EvidenceCard } from "./components/EvidenceCard";
import { ReflectionQuestions } from "./components/ReflectionQuestions";
import { UncertaintyAlert } from "./components/UncertaintyAlert";
import type { Claim, Evidence, UncertaintyState, EvidenceRelation } from "../../../shared/types/api";

describe("ReflectionQuestions Component", () => {
  it("não renderiza nada se questions for undefined ou vazio", () => {
    const container = document.createElement("div");
    render(<ReflectionQuestions />, container);
    expect(container.innerHTML).toBe("");

    render(<ReflectionQuestions questions={[]} />, container);
    expect(container.innerHTML).toBe("");
  });

  it("renderiza lista numerada de perguntas reflexivas para pensamentos críticos", () => {
    const container = document.createElement("div");
    const questions = [
      "Quais fontes comprovam essa afirmação?",
      "Existe algum conflito de interesse no conteúdo?",
      "Os dados apresentados são recentes?",
    ];
    render(<ReflectionQuestions questions={questions} />, container);

    expect(container.querySelector(".reflection-title")?.textContent).toContain("Perguntas para Reflexão Crítica");
    const items = container.querySelectorAll(".reflection-item");
    expect(items.length).toBe(3);
    expect(items[0].textContent).toContain("1.Quais fontes comprovam essa afirmação?");
    expect(items[1].textContent).toContain("2.Existe algum conflito de interesse no conteúdo?");
    expect(items[2].textContent).toContain("3.Os dados apresentados são recentes?");
  });
});

describe("EvidenceCard Component", () => {
  const baseEvidence: Evidence = {
    sourceId: "src-10",
    relation: "supports",
    title: "Checagem Oficial",
    url: "https://fatooufake.com/artigo",
    publishedAt: "2023-08-10T12:00:00Z",
    publisher: "Agência Fato",
    snippet: "O dado apresentado é verdadeiro conforme dados do ministério.",
    provenance: {
      dataset: "FactChecks.br",
      indexedAt: "2026-01-01T00:00:00Z",
    },
  };

  it("renderiza card com relação 'supports'", () => {
    const container = document.createElement("div");
    render(<EvidenceCard evidence={baseEvidence} />, container);

    expect(container.querySelector(".relation-supports")?.textContent).toContain("Apoia a alegação");
    expect(container.querySelector(".evidence-publisher")?.textContent).toBe("Agência Fato");
    expect(container.querySelector(".evidence-title a")?.getAttribute("href")).toBe("https://fatooufake.com/artigo");
    expect(container.querySelector(".evidence-snippet")?.textContent).toContain("O dado apresentado é verdadeiro");
    expect(container.querySelector(".evidence-provenance")?.textContent).toContain("FactChecks.br");
  });

  it("renderiza card com relação 'contradicts'", () => {
    const container = document.createElement("div");
    const ev: Evidence = { ...baseEvidence, relation: "contradicts" };
    render(<EvidenceCard evidence={ev} />, container);

    expect(container.querySelector(".relation-contradicts")?.textContent).toContain("Contradiz a alegação");
  });

  it("renderiza card com relação 'contextualizes'", () => {
    const container = document.createElement("div");
    const ev: Evidence = { ...baseEvidence, relation: "contextualizes" };
    render(<EvidenceCard evidence={ev} />, container);

    expect(container.querySelector(".relation-contextualizes")?.textContent).toContain("Contextualiza a alegação");
  });

  it("lida graciosamente com relação desconhecida e data inválida", () => {
    const container = document.createElement("div");
    const ev = {
      ...baseEvidence,
      relation: "outra" as unknown as EvidenceRelation,
      publishedAt: "data-invalida",
      snippet: undefined,
      provenance: undefined as unknown as Evidence["provenance"],
    };
    render(<EvidenceCard evidence={ev} />, container);

    expect(container.querySelector(".relation-contextualizes")?.textContent).toContain("Contextualiza a alegação");
    expect(container.querySelector(".evidence-date")?.textContent).toContain("data-invalida");
    expect(container.querySelector(".evidence-snippet")).toBeNull();
    expect(container.querySelector(".evidence-provenance")).toBeNull();
  });
});

describe("ClaimCard Component", () => {
  const baseClaim: Claim = {
    id: "clm-99",
    text: "O chá cura doenças graves.",
    uncertainty: "contradicted",
    temporalContext: {
      videoPublishedAt: "2022-05-10T00:00:00Z",
      note: "Publicado em 2022 durante surto viral.",
    },
    evidence: [
      {
        sourceId: "ev-1",
        relation: "contradicts",
        title: "Anvisa desmente cura por ervas",
        url: "https://anvisa.gov.br/nota",
        publishedAt: "2022-05-11T00:00:00Z",
        publisher: "Anvisa",
        provenance: { dataset: "anvisa", indexedAt: "2026-01-01T00:00:00Z" },
      },
    ],
    reflectionQuestions: ["Existe estudo científico com humanos para essa alegação?"],
  };

  it("renderiza todos os estados de incerteza", () => {
    const states: UncertaintyState[] = [
      "supported",
      "contradicted",
      "contextualized",
      "conflicting",
      "insufficient_evidence",
    ];

    for (const st of states) {
      const container = document.createElement("div");
      render(<ClaimCard claim={{ ...baseClaim, uncertainty: st }} />, container);
      expect(container.querySelector(".claim-badge")).not.toBeNull();
    }
  });

  it("lida com incerteza desconhecida e fallback", () => {
    const container = document.createElement("div");
    render(<ClaimCard claim={{ ...baseClaim, uncertainty: "desconhecido" as unknown as UncertaintyState }} />, container);
    expect(container.querySelector(".uncertainty-insufficient")?.textContent).toContain("Sem evidência suficiente");
  });

  it("renderiza aviso quando não há evidências documentadas (RF-12)", () => {
    const container = document.createElement("div");
    render(<ClaimCard claim={{ ...baseClaim, evidence: [] }} />, container);
    expect(container.querySelector(".no-evidence-notice")?.textContent).toContain("Nenhuma evidência documental");
  });

  it("não renderiza nota temporal quando note não estiver definida", () => {
    const container = document.createElement("div");
    render(
      <ClaimCard
        claim={{
          ...baseClaim,
          temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
          reflectionQuestions: undefined,
        }}
      />,
      container
    );
    expect(container.querySelector(".temporal-context-note")).toBeNull();
    expect(container.querySelector(".reflection-section")).toBeNull();
  });
});

describe("UncertaintyAlert Component", () => {
  it("renderiza mensagem explicativa com badges de resumo para divergências (singular e plural)", () => {
    const container = document.createElement("div");
    const testClaims: Claim[] = [
      {
        id: "c-1",
        text: "Alegação 1",
        uncertainty: "supported",
        temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
        evidence: [],
      },
      {
        id: "c-2",
        text: "Alegação 2",
        uncertainty: "supported",
        temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
        evidence: [],
      },
      {
        id: "c-3",
        text: "Alegação 3",
        uncertainty: "contradicted",
        temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
        evidence: [],
      },
      {
        id: "c-4",
        text: "Alegação 4",
        uncertainty: "contradicted",
        temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
        evidence: [],
      },
    ];

    render(<UncertaintyAlert claims={testClaims} />, container);

    expect(container.querySelector("#uncertainty-alert-title")?.textContent).toContain("Evidências com divergências apuradas");
    expect(container.textContent).toContain("Alegações apoiadas");
    expect(container.textContent).toContain("2 alegações possuem evidência favorável");
    expect(container.textContent).toContain("Alegações contraditas");
    expect(container.textContent).toContain("2 alegações foram contestadas por checagens");
  });

  it("renderiza aviso quando todas as alegações são insuficientes", () => {
    const container = document.createElement("div");
    const testClaims: Claim[] = [
      {
        id: "c-1",
        text: "Alegação 1",
        uncertainty: "insufficient_evidence",
        temporalContext: { videoPublishedAt: "2024-01-01T00:00:00Z" },
        evidence: [],
      },
    ];

    render(<UncertaintyAlert claims={testClaims} />, container);

    expect(container.querySelector("#uncertainty-alert-title")?.textContent).toContain("Evidências documentais insuficientes");
    expect(container.textContent).toContain("Recomendamos cautela antes de compartilhar");
  });

  it("não renderiza nada se não houver divergência nem insuficiência total", () => {
    const container = document.createElement("div");
    render(<UncertaintyAlert claims={[]} />, container);
    expect(container.innerHTML).toBe("");
  });
});
