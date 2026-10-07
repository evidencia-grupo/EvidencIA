import { test as base, expect, chromium, type BrowserContext, type Worker } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { resolve } from "node:path";

const test = base.extend<{ extension: { context: BrowserContext; worker: Worker } }>({
  extension: async ({}, use) => {
    const path = resolve("dist");
    const context = await chromium.launchPersistentContext("", {
      channel: "chromium",
      headless: true,
      args: [`--disable-extensions-except=${path}`, `--load-extension=${path}`],
    });
    let worker = context.serviceWorkers()[0];
    if (!worker) {
      let interval: NodeJS.Timeout | undefined;
      const pollPromise = new Promise<Worker>((res) => {
        interval = setInterval(() => {
          const sw = context.serviceWorkers()[0];
          if (sw) {
            clearInterval(interval);
            res(sw);
          }
        }, 50);
      });
      worker = await Promise.race([context.waitForEvent("serviceworker"), pollPromise]);
      if (interval) clearInterval(interval);
    }
    await use({ context, worker });
    await context.close();
  },
});

const transcript =
  "Um estudo apresenta dados sobre a relacao entre exercicio fisico e qualidade de vida, com resultados que precisam de evidencias e revisao documental.";

async function setup(context: BrowserContext, id = "video", captions = true) {
  let captionCalls = 0;
  await context.route("https://www.youtube.com/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/timedtext") {
      captionCalls++;
      await route.fulfill({ contentType: "text/xml", body: `<transcript><text>${transcript}</text></transcript>` });
    } else {
      await route.fulfill({
        contentType: "text/html",
        body: `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vídeo de teste - Checagem sob demanda</title></head><body>
        <main><h1 class="ytd-watch-metadata">Ciência</h1><div id="channel-name">Canal de testes</div><div id="above-the-fold"></div><div id="movie_player"></div><video></video><a href="#footer">Próximo</a></main>
        <script>window.ytInitialPlayerResponse = {videoDetails:{videoId:new URLSearchParams(location.search).get('v')},captions:{playerCaptionsTracklistRenderer:{captionTracks:${captions ? JSON.stringify([{ baseUrl: "https://www.youtube.com/api/timedtext?v=" + id, languageCode: "pt" }]) : "[]"}}}};
        window.__evidencia_perf__ = {click:0, feedback:null, blocking:0};
        new PerformanceObserver(list => { for (const entry of list.getEntries()) window.__evidencia_perf__.blocking += Math.max(0,entry.duration-50); }).observe({type:'longtask',buffered:true});
        document.addEventListener('click', () => {
          window.__evidencia_perf__.click=performance.timeOrigin+performance.now();
          const root=document.querySelector('#evidencia-badge-host')?.shadowRoot;
          if (!root) return;
          const observer=new MutationObserver(()=>{
            if(root.querySelector('button')?.textContent.includes('Analisando')) {
              observer.disconnect();
              requestAnimationFrame(()=>window.__evidencia_perf__.feedback=performance.timeOrigin+performance.now()-window.__evidencia_perf__.click);
            }
          });
          observer.observe(root,{subtree:true,childList:true,characterData:true});
        },true);
        </script></body></html>`,
      });
    }
  });
  const page = await context.newPage();
  await page.goto(`https://www.youtube.com/watch?v=${id}`);
  const button = page.getByRole("button", { name: "Checar Alegações" });
  await expect(button).toBeVisible();
  const panel = page.frameLocator("#evidencia-side-panel");
  await expect(panel.getByRole("button", { name: /Fechar painel/, includeHidden: true })).toBeAttached();
  return { page, button, panel, captionCalls: () => captionCalls };
}

async function measureRender(page: import("@playwright/test").Page) {
  const frame = page.frames().find((f) => f.url().startsWith("chrome-extension://"))!;
  await frame.evaluate(() => {
    new MutationObserver(() => {
      if (document.querySelector(".panel-container") || document.querySelector(".claim-card") || document.querySelector(".alert-box")) {
        requestAnimationFrame(() => {
          (window as any).renderedAt ??= performance.timeOrigin + performance.now();
        });
      }
    }).observe(document.body, { childList: true, subtree: true });
  });
  return frame;
}

test("Checagem sob demanda: feedback <= 1s, síntese <= 10s, cache < 100ms sem nova extração/rede", async ({ extension }, info) => {
  const { page, button, panel, captionCalls } = await setup(extension.context);
  const frame = await measureRender(page);
  await button.click();
  await expect(panel.getByText("Checagem Factual")).toBeVisible();
  await expect(panel.getByText(/Alegações Analisadas/)).toBeVisible();
  const first = await page.evaluate(() => (window as any).__evidencia_perf__);
  const firstRender = await frame.evaluate(() => (window as any).renderedAt);
  expect(first.feedback).not.toBeNull();
  expect(first.feedback).toBeGreaterThanOrEqual(0);
  expect(first.feedback).toBeLessThanOrEqual(1000);
  expect(firstRender - first.click).toBeLessThanOrEqual(10000);
  expect(first.blocking).toBeLessThanOrEqual(50);
  expect(captionCalls()).toBe(1);

  await expect.poll(() => extension.worker.evaluate(async () => Boolean((await chrome.storage.local.get("video")).video))).toBe(true);
  await panel.getByRole("button", { name: /Fechar painel/ }).click();
  await frame.evaluate(() => {
    (window as any).renderedAt = undefined;
  });

  // Falha em qualquer tentativa de análise externa: cache deve continuar funcionando.
  await extension.worker.evaluate(() => {
    globalThis.fetch = async () => {
      throw new Error("Rede não deveria ser usada no cache hit");
    };
  });
  await page.getByRole("button", { name: /Checagem concluída|Checar Alegações/ }).click();
  await expect(panel.getByText("Checagem Factual")).toBeVisible();
  await expect.poll(() => frame.evaluate(() => (window as any).renderedAt)).toBeTruthy();
  const second = await page.evaluate(() => (window as any).__evidencia_perf__);
  const cacheMs = (await frame.evaluate(() => (window as any).renderedAt)) - second.click;
  expect(cacheMs).toBeLessThan(process.env.CI ? 250 : 100);
  expect(captionCalls()).toBe(1);

  // Reabrir o vídeo deve recuperar o armazenamento local, sem estado do painel anterior.
  await page.reload();
  await expect(page.getByRole("button", { name: "Checar Alegações" })).toBeVisible();
  await expect(panel.getByRole("button", { name: /Fechar painel/, includeHidden: true })).toBeAttached();
  const reopenedFrame = await measureRender(page);
  await page.getByRole("button", { name: "Checar Alegações" }).click();
  await expect(panel.getByText("Checagem Factual")).toBeVisible();
  await expect.poll(() => reopenedFrame.evaluate(() => (window as any).renderedAt)).toBeTruthy();
  const reopened = await page.evaluate(() => (window as any).__evidencia_perf__);
  const reopenedCacheMs = (await reopenedFrame.evaluate(() => (window as any).renderedAt)) - reopened.click;
  expect(reopenedCacheMs).toBeLessThan(process.env.CI ? 250 : 100);
  expect(captionCalls()).toBe(1);
  await info.attach("tempos.json", {
    body: JSON.stringify({
      feedbackMs: first.feedback,
      summaryMs: firstRender - first.click,
      cacheMs,
      reopenedCacheMs,
      blockingMs: first.blocking,
      provider: "mock",
      network: "localhost/fixtures",
    }),
    contentType: "application/json",
  });
});

test("Checagem sob demanda: cache expirado é substituído e iframe frio recebe o resultado", async ({ extension }) => {
  await extension.worker.evaluate(async () =>
    chrome.storage.local.set({
      video: {
        analysisMode: "evidence_first",
        videoId: "video",
        videoTitle: "Vídeo Antigo",
        channelName: "Canal",
        publishedAt: "2026-01-01T00:00:00Z",
        claims: [
          {
            id: "claim-antigo",
            text: "Alegação Antiga Expirada",
            uncertainty: "supported",
            temporalContext: { videoPublishedAt: "2026-01-01T00:00:00Z" },
            evidence: [],
          },
        ],
        timestamp: Date.now() - 86400000,
        ttl: 86400000,
      },
    })
  );
  const { button, panel, captionCalls } = await setup(extension.context);
  await button.click();
  await expect(panel.getByText("Checagem Factual")).toBeVisible();
  expect(captionCalls()).toBe(1);
  await expect(panel.getByText("Alegação Antiga Expirada")).toHaveCount(0);
});

test("Checagem sob demanda: sem legendas encerra carregamento sem interromper player", async ({ extension }) => {
  const { page, button, panel } = await setup(extension.context, "empty", false);
  await page.evaluate(() => {
    (window as any).pauses = 0;
    document.querySelector("video")!.pause = () => {
      (window as any).pauses++;
    };
  });
  await button.click();
  await expect(panel.getByRole("alert")).toContainText("Este vídeo não tem legendas");
  expect(await page.evaluate(() => (window as any).pauses)).toBe(0);
  await expect(page.getByRole("button", { name: /Sem legendas/ })).toBeEnabled();
});

test("Checagem sob demanda: erro HTTP permite nova tentativa; timeout nunca mostra sucesso tardio", async ({ extension }) => {
  // O prazo da extensão é 30s para acomodar os 15s de IA e a busca de evidências.
  // A fixture, a tentativa HTTP inicial e as verificações também consomem o timeout do teste.
  test.setTimeout(45_000);
  await extension.worker.evaluate(() => {
    globalThis.fetch = async () => new Response("", { status: 503 });
  });
  const { page, button, panel } = await setup(extension.context);
  await button.click();
  await expect(panel.getByRole("alert")).toContainText("Não conseguimos checar este vídeo agora");
  await extension.worker.evaluate(() => {
    (globalThis as any).requestAborted = false;
    globalThis.fetch = async (_url, init) => new Promise<Response>((resolve, reject) => {
      (globalThis as any).releaseLateResponse = () => resolve(new Response(JSON.stringify({
        analysisMode: "evidence_first", videoId: "video", videoTitle: "Resposta tardia",
        channelName: "Canal", publishedAt: "2026-10-07T00:00:00Z",
        processingTimeMs: 31_000, claims: [], limitations: [],
      }), { headers: { "Content-Type": "application/json" } }));
      init?.signal?.addEventListener("abort", () => {
        (globalThis as any).requestAborted = true;
        reject(new DOMException("Aborted", "AbortError"));
      });
    });
  });
  await page.getByRole("button", { name: "Tentar novamente" }).click();
  await expect(panel.getByRole("alert")).toContainText(/demorou mais do que o esperado/, { timeout: 35_000 });
  await expect(page.getByRole("button", { name: "Tentar novamente" })).toBeEnabled();
  await expect.poll(() => extension.worker.evaluate(() => (globalThis as any).requestAborted)).toBe(true);

  // Uma resposta que chega depois do cancelamento não deve substituir o erro nem entrar no cache.
  await extension.worker.evaluate(() => (globalThis as any).releaseLateResponse());
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(panel.getByRole("alert")).toContainText(/demorou mais do que o esperado/);
  await expect(panel.getByText(/Alegações Analisadas/)).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Checagem concluída/ })).toHaveCount(0);
  expect(await extension.worker.evaluate(async () => (await chrome.storage.local.get("video")).video)).toBeUndefined();
});

test("Checagem sob demanda: teclado, foco e WCAG 2.1 AA no resultado", async ({ extension }, info) => {
  const { page, button, panel } = await setup(extension.context);
  await page.keyboard.press("Tab");
  await expect(button).toBeFocused();
  await expect(button).toHaveCSS("outline-style", "solid");
  await page.keyboard.press("Enter");
  const close = panel.getByRole("button", { name: /Fechar painel/ });
  await expect(close).toBeFocused();
  await expect(panel.getByText("Checagem Factual")).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  await info.attach("axe-wcag21aa.json", { body: JSON.stringify(results), contentType: "application/json" });
  expect(results.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(page.locator("#evidencia-side-panel")).toBeHidden();
  await expect(page.getByRole("button", { name: /Checagem concluída|Checar Alegações/ })).toBeFocused();
  await page.keyboard.press("Space");
  await expect(close).toBeFocused();
});

test("Checagem sob demanda: navegação SPA invalida resposta e funciona ao chegar da home", async ({ extension }) => {
  const { page, button, panel } = await setup(extension.context);
  await extension.worker.evaluate(() => {
    globalThis.fetch = async () => new Promise(() => {});
  });
  await button.click();
  await page.evaluate(() => {
    history.pushState({}, "", "/");
    window.dispatchEvent(new Event("yt-navigate-finish"));
  });
  await expect(page.locator("#evidencia-badge-host")).toHaveCount(0);
  await expect(page.locator("#evidencia-side-panel")).toBeHidden();
  await page.evaluate(() => {
    history.pushState({}, "", "/watch?v=next");
    (window as any).ytInitialPlayerResponse.videoDetails.videoId = "next";
    window.dispatchEvent(new Event("yt-navigate-finish"));
  });
  await expect(page.getByRole("button", { name: "Checar Alegações" })).toBeVisible();
  await expect(panel.getByText(/Alegações Analisadas/)).toHaveCount(0);
});

test("Checagem sob demanda: WCAG nos estados de carregamento, falha e classificações", async ({ extension }, info) => {
  const { page, button, panel } = await setup(extension.context);
  await extension.worker.evaluate(() => {
    globalThis.fetch = async () => new Promise(() => {});
  });
  await button.click();
  await expect(panel.getByRole("status")).toContainText("analisando as alegações");
  const states: Array<{ state: string; violations: unknown[]; incomplete: unknown[] }> = [];
  async function audit(state: string) {
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    states.push({ state, violations: result.violations, incomplete: result.incomplete });
    expect(result.violations).toEqual([]);
  }
  await audit("carregamento");
  await page.evaluate(() =>
    document
      .querySelector<HTMLIFrameElement>("iframe")!
      .contentWindow!.postMessage(
        { type: "ANALYSIS_ERROR", error: "Não foi possível consultar o servidor. Tente novamente." },
        document.querySelector<HTMLIFrameElement>("iframe")!.src.split("/").slice(0, 3).join("/")
      )
  );
  await expect(panel.getByRole("alert")).toBeVisible();
  await audit("falha");
  for (const uncertainty of ["supported", "contradicted", "conflicting", "insufficient_evidence", "contextualized"]) {
    await page.evaluate(
      (u) => {
        const frame = document.querySelector<HTMLIFrameElement>("iframe")!;
        frame.contentWindow!.postMessage(
          {
            type: "ANALYSIS_SUCCESS",
            data: {
              analysisMode: "evidence_first",
              videoId: "video",
              videoTitle: "Vídeo Demonstrativo de Acessibilidade",
              channelName: "Canal Acessível",
              publishedAt: new Date().toISOString(),
              processingTimeMs: 120,
              limitations: ["Análise preliminar de demonstração."],
              claims: [
                {
                  id: `claim-${u}`,
                  text: `Alegação com estado analítico ${u} para teste WCAG`,
                  uncertainty: u,
                  temporalContext: { videoPublishedAt: "2026-01-01T00:00:00Z" },
                  evidence: [
                    {
                      sourceId: `source-${u}`,
                      relation: u === "contradicted" ? "contradicts" : "supports",
                      title: "Fonte Oficial de Checagem",
                      url: "https://agencialupa.com.br/checagem-acessibilidade",
                      publisher: "Agência Lupa",
                      publishedAt: "2026-01-05",
                      snippet: "Evidência documental auditada para conformidade.",
                      provenance: { dataset: "factchecks_br", indexedAt: "2026-01-06T00:00:00Z" },
                    },
                  ],
                  reflectionQuestions: ["Quem se beneficia com essa declaração?"],
                },
              ],
            },
          },
          frame.src.split("/").slice(0, 3).join("/")
        );
      },
      uncertainty
    );
    await expect(panel.getByText("Checagem Factual")).toBeVisible();
    await audit(uncertainty);
  }
  await info.attach("axe-estados.json", { body: JSON.stringify(states), contentType: "application/json" });
});
