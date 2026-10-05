// @vitest-environment jsdom
import { describe, it, expect } from "vitest";
import { render } from "preact";
import { act } from "preact/test-utils";
import axe from "axe-core";
import { ClaimCard } from "./components/ClaimCard";
import { EvidenceCard } from "./components/EvidenceCard";
import { ReflectionQuestions } from "./components/ReflectionQuestions";
import { UncertaintyAlert } from "./components/UncertaintyAlert";
import { FeedbackSection } from "./components/FeedbackSection";
import type { Claim, Evidence, UncertaintyState, EvidenceRelation, FeedbackRequest } from "../../../shared/types/api";

describe("ReflectionQuestions Component", () => {
  it("exibe três perguntas neutras de fallback quando questions está ausente ou vazio", () => {
    for (const questions of [undefined, []]) {
      const container = document.createElement("div");
      render(<ReflectionQuestions questions={questions} />, container);
      expect(container.querySelectorAll(".reflection-item")).toHaveLength(3);
      expect(container.textContent).not.toMatch(/certo|errado|verdadeiro|falso/i);
    }
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

describe("EvidenceCard Component (HU14)", () => {
  const baseEvidence: Evidence = {
    sourceId: "src-10",
    relation: "supports",
    title: "Checagem Oficial",
    url: "https://www.fatooufake.com/artigo",
    publishedAt: "2023-08-10T12:00:00Z",
    publisher: "Agência Fato",
    snippet: "O dado apresentado é verdadeiro conforme dados do ministério.",
    provenance: {
      dataset: "factchecksbr",
      indexedAt: "2026-01-01T00:00:00Z",
    },
  };

  function renderCard(ev: Evidence) {
    const container = document.createElement("div");
    render(<EvidenceCard evidence={ev} />, container);
    return container;
  }

  it("exibe título, endereço, data, publisher e relação de forma explícita", () => {
    const container = renderCard(baseEvidence);

    expect(container.querySelector(".relation-supports")?.textContent).toContain("Apoia a alegação");
    expect(container.querySelector(".evidence-title")?.textContent).toContain("Checagem Oficial");
    expect(container.querySelector(".evidence-publisher")?.textContent).toBe("Agência Fato");
    expect(container.querySelector(".evidence-date time")?.getAttribute("dateTime")).toBe("2023-08-10T12:00:00Z");
    expect(container.querySelector(".evidence-date")?.textContent).toMatch(/10 de ago\.? de 2023/);
    expect(container.querySelector(".evidence-url")?.textContent).toBe("fatooufake.com/artigo");
    expect(container.querySelector(".evidence-provenance")?.textContent).toBe("FactChecks.br");
    expect(container.querySelector(".evidence-snippet")?.textContent).toContain("O dado apresentado é verdadeiro");

    const labels = Array.from(container.querySelectorAll(".evidence-meta dt")).map((dt) => dt.textContent);
    expect(labels).toEqual(["Publicado por", "Publicado em", "Endereço", "Base de checagens"]);
  });

  it("abre a fonte em nova aba de forma segura", () => {
    const link = renderCard(baseEvidence).querySelector(".evidence-title a");

    expect(link?.getAttribute("href")).toBe("https://www.fatooufake.com/artigo");
    expect(link?.getAttribute("target")).toBe("_blank");
    expect(link?.getAttribute("rel")).toBe("noopener noreferrer");
    expect(link?.textContent).toContain("(abre em nova aba)");
  });

  it("destaca a relação 'Contradiz' junto do trecho factual", () => {
    const container = renderCard({ ...baseEvidence, relation: "contradicts" });

    expect(container.querySelector(".evidence-card--contradicts")).not.toBeNull();
    expect(container.querySelector(".relation-contradicts")?.textContent).toContain("Contradiz a alegação");
    expect(container.querySelector(".evidence-snippet-label")?.textContent).toBe("O que a fonte diz:");
    expect(container.querySelector(".evidence-snippet")?.textContent).toContain("O dado apresentado");
  });

  it("exibe a relação 'Contextualiza' com os metadados completos", () => {
    const container = renderCard({ ...baseEvidence, relation: "contextualizes" });

    expect(container.querySelector(".evidence-card--contextualizes")).not.toBeNull();
    expect(container.querySelector(".relation-contextualizes")?.textContent).toContain("Contextualiza a alegação");
    expect(container.querySelectorAll(".evidence-meta-row").length).toBe(4);
  });

  it("avisa quando a fonte não trouxe trecho", () => {
    const container = renderCard({ ...baseEvidence, snippet: undefined });

    expect(container.querySelector(".evidence-snippet")).toBeNull();
    expect(container.querySelector(".evidence-snippet-missing")?.textContent).toContain("Abra o link");
  });

  it("não inventa data quando ela está ausente ou inválida", () => {
    expect(renderCard({ ...baseEvidence, publishedAt: "" }).querySelector(".evidence-date")?.textContent).toBe(
      "Data não informada"
    );
    expect(
      renderCard({ ...baseEvidence, publishedAt: "data-invalida" }).querySelector(".evidence-date")?.textContent
    ).toBe("Data não informada");
  });

  it("mostra a data do dia certo mesmo para datas sem horário", () => {
    const container = renderCard({ ...baseEvidence, publishedAt: "2024-01-01" });
    expect(container.querySelector(".evidence-date")?.textContent).toMatch(/1 de jan\.? de 2024/);
  });

  it("não cria link para endereços que não sejam http/https", () => {
    const container = renderCard({ ...baseEvidence, url: "javascript:alert(1)" });

    expect(container.querySelector("a")).toBeNull();
    expect(container.querySelector(".evidence-title")?.textContent).toBe("Checagem Oficial");
    expect(container.querySelector(".evidence-url")?.textContent).toBe("Endereço não disponível");
  });

  it("lida graciosamente com relação desconhecida e sem proveniência", () => {
    const ev = {
      ...baseEvidence,
      relation: "outra" as unknown as EvidenceRelation,
      provenance: undefined as unknown as Evidence["provenance"],
    };
    const container = renderCard(ev);

    expect(container.querySelector(".relation-contextualizes")?.textContent).toContain("Contextualiza a alegação");
    expect(container.querySelector(".evidence-provenance")).toBeNull();
  });

  it("não apresenta violações de acessibilidade (axe-core, WCAG 2.1 AA)", async () => {
    const relations: EvidenceRelation[] = ["supports", "contradicts", "contextualizes"];
    const host = document.createElement("main");
    host.setAttribute("lang", "pt-BR");
    document.body.appendChild(host);
    render(
      <section aria-label="Evidências">
        {relations.map((relation) => (
          <EvidenceCard key={relation} evidence={{ ...baseEvidence, sourceId: relation, relation }} />
        ))}
        <EvidenceCard evidence={{ ...baseEvidence, sourceId: "sem-dados", snippet: undefined, publishedAt: "" }} />
      </section>,
      host
    );

    // Contraste de cor depende de layout real e não é calculável no jsdom; os demais critérios são auditados aqui.
    const results = await axe.run(host, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);

    render(null, host);
    host.remove();
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

describe("FeedbackSection Component (HU12)", () => {
  it("renderiza opções discretas de feedback (positivo/negativo)", () => {
    const container = document.createElement("div");
    render(<FeedbackSection videoId="test-vid" />, container);

    expect(container.querySelector(".feedback-title")?.textContent).toContain("Esta análise foi útil para você?");
    expect(container.querySelector('button[aria-label="Avaliar análise como útil"]')).not.toBeNull();
    expect(container.querySelector('button[aria-label="Avaliar análise como não útil"]')).not.toBeNull();
  });

  it("submete feedback positivo de forma anônima e exibe mensagem de confirmação", async () => {
    const container = document.createElement("div");
    const submitted: FeedbackRequest[] = [];
    act(() => {
      render(
        <FeedbackSection
          videoId="test-vid"
          onSubmitFeedback={(p) => {
            submitted.push(p);
          }}
        />,
        container
      );
    });

    const usefulBtn = container.querySelector('button[aria-label="Avaliar análise como útil"]') as HTMLButtonElement;
    await act(async () => {
      usefulBtn.click();
    });

    expect(submitted).toHaveLength(1);
    expect(submitted[0]).toEqual({ videoId: "test-vid", rating: "positive" });
    expect(container.querySelector(".feedback-success-msg")?.textContent).toContain("Obrigado pelo seu feedback anônimo!");
  });

  it("permite selecionar motivo para feedback negativo antes de submeter", async () => {
    const container = document.createElement("div");
    const submitted: FeedbackRequest[] = [];
    act(() => {
      render(
        <FeedbackSection
          videoId="test-vid"
          onSubmitFeedback={(p) => {
            submitted.push(p);
          }}
        />,
        container
      );
    });

    const notUsefulBtn = container.querySelector('button[aria-label="Avaliar análise como não útil"]') as HTMLButtonElement;
    await act(async () => {
      notUsefulBtn.click();
    });

    const outdatedChip = Array.from(container.querySelectorAll(".feedback-chip")).find(
      (chip) => chip.textContent?.includes("Fontes desatualizadas")
    ) as HTMLButtonElement;
    expect(outdatedChip).not.toBeNull();
    await act(async () => {
      outdatedChip.click();
    });

    const submitBtn = container.querySelector(".feedback-submit-btn") as HTMLButtonElement;
    await act(async () => {
      submitBtn.click();
    });

    expect(submitted).toHaveLength(1);
    expect(submitted[0]).toEqual({
      videoId: "test-vid",
      rating: "negative",
      reason: "outdated_sources",
    });
    expect(container.querySelector(".feedback-success-msg")?.textContent).toContain("Obrigado pelo seu feedback anônimo!");
  });

  it("trata falha de rede silenciosamente sem interromper navegação", async () => {
    const container = document.createElement("div");
    const failingSubmit = () => {
      throw new Error("Network failure");
    };

    act(() => {
      render(<FeedbackSection videoId="test-vid" onSubmitFeedback={failingSubmit} />, container);
    });

    const usefulBtn = container.querySelector('button[aria-label="Avaliar análise como útil"]') as HTMLButtonElement;
    await act(async () => {
      expect(() => usefulBtn.click()).not.toThrow();
    });

    expect(container.querySelector(".feedback-success-msg")?.textContent).toContain("Obrigado pelo seu feedback anônimo!");
  });

  it("não apresenta violações de acessibilidade (axe-core, WCAG 2.1 AA)", async () => {
    const host = document.createElement("div");
    document.body.appendChild(host);
    render(<FeedbackSection videoId="test-vid" />, host);

    const results = await axe.run(host, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);

    render(null, host);
    host.remove();
  });
});

