import { test as base, expect, chromium, type BrowserContext, type Worker } from "@playwright/test";
import { resolve } from "node:path";
import type { LocalCacheEntry } from "../../shared/types/api";

const test = base.extend<{ extension: { context: BrowserContext; worker: Worker } }>({
  extension: async ({}, use) => {
    const path = resolve("dist");
    const context = await chromium.launchPersistentContext("", {
      channel: "chromium",
      headless: true,
      args: [`--disable-extensions-except=${path}`, `--load-extension=${path}`],
    });
    const worker = context.serviceWorkers()[0] ?? (await context.waitForEvent("serviceworker"));
    await use({ context, worker });
    await context.close();
  },
});

const transcript =
  "Transcrição controlada do vídeo para validação de factualidade e checagem de alegações.";

async function setupPage(context: BrowserContext, videoId = "video-carlos", captionsAvailable = true) {
  let captionCalls = 0;
  await context.route("https://www.youtube.com/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/timedtext") {
      captionCalls++;
      await route.fulfill({
        contentType: "text/xml",
        body: `<transcript><text>${transcript}</text></transcript>`,
      });
    } else {
      await route.fulfill({
        contentType: "text/html",
        body: `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vídeo de Teste HU06</title></head><body>
          <main>
            <h1 class="ytd-watch-metadata">Título de Carlos Augusto</h1>
            <div id="channel-name">Canal de Tecnologia</div>
            <div id="above-the-fold"></div>
            <div id="movie_player"></div>
            <video></video>
          </main>
          <script>
            window.ytInitialPlayerResponse = {
              videoDetails: { videoId: new URLSearchParams(location.search).get('v') },
              captions: {
                playerCaptionsTracklistRenderer: {
                  captionTracks: ${captionsAvailable ? JSON.stringify([{ baseUrl: "https://www.youtube.com/api/timedtext?v=" + videoId, languageCode: "pt" }]) : "[]"}
                }
              }
            };
            window.hu06 = { click: 0, feedback: null, blocking: 0 };
            new PerformanceObserver(list => {
              for (const entry of list.getEntries()) {
                window.hu06.blocking += Math.max(0, entry.duration - 50);
              }
            }).observe({ type: 'longtask', buffered: true });
            document.addEventListener('click', () => {
              window.hu06.click = performance.timeOrigin + performance.now();
              const root = document.querySelector('#evidencia-badge-host')?.shadowRoot;
              if (!root) return;
              const observer = new MutationObserver(() => {
                if (root.querySelector('button')?.textContent.includes('Analisando')) {
                  observer.disconnect();
                  requestAnimationFrame(() => {
                    window.hu06.feedback = performance.timeOrigin + performance.now() - window.hu06.click;
                  });
                }
              });
              observer.observe(root, { subtree: true, childList: true, characterData: true });
            }, true);
          </script>
        </body></html>`,
      });
    }
  });

  const page = await context.newPage();
  await page.goto(`https://www.youtube.com/watch?v=${videoId}`);
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
      if (document.querySelector(".card")) {
        requestAnimationFrame(() => {
          (window as any).renderedAt ??= performance.timeOrigin + performance.now();
        });
      }
    }).observe(document.body, { childList: true, subtree: true });
  });
  return frame;
}

const mockValidEntry: LocalCacheEntry = {
  analysisMode: "evidence_first",
  videoId: "video-carlos",
  videoTitle: "Vídeo de Teste Carlos Augusto",
  channelName: "Canal de Testes",
  publishedAt: "2026-01-15T00:00:00Z",
  processingTimeMs: 120,
  limitations: [],
  claims: [
    {
      id: "claim-carlos-1",
      text: "Alegação verificada em cache",
      uncertainty: "supported",
      temporalContext: {
        videoPublishedAt: "2026-01-15T00:00:00Z",
        note: "As alegações foram apresentadas em 2026.",
      },
      evidence: [
        {
          sourceId: "ev-carlos-1",
          relation: "supports",
          title: "Fonte de Auditoria",
          url: "https://auditoria.org/relatorio",
          publisher: "auditoria.org",
          publishedAt: "2026-01-20",
          snippet: "Evidência confirmada em base documental",
          provenance: {
            dataset: "factchecks_br",
            indexedAt: "2026-09-30T10:00:00Z",
          },
        },
      ],
      reflectionQuestions: ["A metodologia da auditoria é independente?"],
    },
  ],
  timestamp: Date.now() - 3600000, // 1 hora atrás (válido, < 24h)
  ttl: 86400000,
};

test("HU06: Cenário 1 — Cache válido disponível exibe resultado em <1s sem nova extração de legendas nem backend", async ({
  extension,
}) => {
  // Pré-popula chrome.storage.local com registro válido de Carlos Augusto
  await extension.worker.evaluate(async (entry) => {
    await chrome.storage.local.set({ [entry.videoId]: entry });
  }, mockValidEntry);

  // Garante que o fetch do Service Worker falharia se qualquer requisição de rede fosse tentada
  await extension.worker.evaluate(() => {
    (globalThis as any).cacheFetchCalls = 0;
    globalThis.fetch = async () => {
      (globalThis as any).cacheFetchCalls++;
      throw new Error("REDE_BLOQUEADA: nenhuma chamada externa de checagem deve ocorrer no cache hit.");
    };
  });

  const { page, button, panel, captionCalls } = await setupPage(extension.context, "video-carlos");
  const frame = await measureRender(page);

  await button.click();

  // Valida que o resultado renderiza imediatamente
  await expect(panel.getByText("Alegação verificada em cache")).toBeVisible();
  await expect(panel.getByText("Fonte de Auditoria")).toBeVisible();

  // Verifica ausência absoluta de chamadas externas de legendas e backend
  expect(captionCalls()).toBe(0);
  expect(await extension.worker.evaluate(() => (globalThis as any).cacheFetchCalls)).toBe(0);

  // Medição de latência estrita: < 1s (critério obrigatório) e < 100ms (meta controlada ADR-003)
  const clickTime = await page.evaluate(() => (window as any).hu06.click);
  await expect.poll(() => frame.evaluate(() => (window as any).renderedAt)).toBeTruthy();
  const renderTime = await frame.evaluate(() => (window as any).renderedAt);
  const latencyMs = renderTime - clickTime;
  expect(latencyMs).toBeGreaterThan(0);
  expect(latencyMs).toBeLessThan(1000); // Critério obrigatório: < 1s
  expect(latencyMs).toBeLessThan(100); // Meta de cache controlado ADR-003: < 100ms
});

test("HU06: Cenário 1b — Cache continua funcionando após recarregar a página do vídeo", async ({
  extension,
}) => {
  await extension.worker.evaluate(async (entry) => {
    await chrome.storage.local.set({ [entry.videoId]: entry });
  }, mockValidEntry);

  await extension.worker.evaluate(() => {
    (globalThis as any).cacheFetchCalls = 0;
    globalThis.fetch = async () => {
      (globalThis as any).cacheFetchCalls++;
      throw new Error("REDE_BLOQUEADA: não deve acessar backend.");
    };
  });

  const { page, button, panel, captionCalls } = await setupPage(extension.context, "video-carlos");

  // Recarrega a página simulando nova navegação/reabertura do mesmo vídeo
  await page.reload();
  await expect(page.getByRole("button", { name: "Checar Alegações" })).toBeVisible();
  await expect(panel.getByRole("button", { name: /Fechar painel/, includeHidden: true })).toBeAttached();
  const reopenedFrame = await measureRender(page);

  await button.click();

  await expect(panel.getByText("Alegação verificada em cache")).toBeVisible();
  expect(captionCalls()).toBe(0);
  expect(await extension.worker.evaluate(() => (globalThis as any).cacheFetchCalls)).toBe(0);

  const reopenedClick = await page.evaluate(() => (window as any).hu06.click);
  await expect.poll(() => reopenedFrame.evaluate(() => (window as any).renderedAt)).toBeTruthy();
  const reopenedRender = await reopenedFrame.evaluate(() => (window as any).renderedAt);
  const latency = reopenedRender - reopenedClick;
  expect(latency).toBeLessThan(1000);
  expect(latency).toBeLessThan(100);
});

test("HU06: Cenário 2 — Cache expirado é descartado e inicia nova análise completa substituindo o registro", async ({
  extension,
}) => {
  // Injeta cache expirado (exatamente 24h atrás: idade = 86400000 ms)
  const expiredEntry: LocalCacheEntry = {
    ...mockValidEntry,
    claims: [
      {
        ...mockValidEntry.claims[0],
        text: "Conteúdo antigo e obsoleto",
      },
    ],
    timestamp: Date.now() - 86400000, // Exatamente 24h
  };
  await extension.worker.evaluate(async (entry) => {
    await chrome.storage.local.set({ [entry.videoId]: entry });
  }, expiredEntry);

  const { button, panel, captionCalls } = await setupPage(extension.context, "video-carlos");

  await button.click();

  // Espera a nova análise (que usará extração e backend mock)
  await expect(panel.getByText("Alegações Analisadas")).toBeVisible();

  // Confirma que o conteúdo obsoleto foi descartado
  await expect(panel.getByText("Conteúdo antigo e obsoleto")).toHaveCount(0);

  // Confirma que realizou extração de legendas e nova chamada
  expect(captionCalls()).toBe(1);

  // Confirma que o registro expirado foi substituído no storage com novo timestamp
  await expect
    .poll(async () => {
      return extension.worker.evaluate(async () => {
        const stored = (await chrome.storage.local.get("video-carlos"))["video-carlos"] as LocalCacheEntry;
        return stored && stored.timestamp > Date.now() - 10000 && stored.claims?.[0]?.text !== "Conteúdo antigo e obsoleto";
      });
    })
    .toBe(true);
});

test("HU06: Cenário 2b — Cache corrompido, timestamp futuro ou videoId divergente dispara nova análise", async ({
  extension,
}) => {
  // Injeta registros inválidos: timestamp futuro, dado corrompido e identificador divergente
  await extension.worker.evaluate(async () => {
    await chrome.storage.local.set({
      "video-carlos": {
        videoId: "outro-video-divergente", // videoId divergente da chave
        timestamp: Date.now() + 60000, // Timestamp futuro
      },
    });
  });

  const { button, panel, captionCalls } = await setupPage(extension.context, "video-carlos");

  await button.click();

  // Inicia nova análise completa
  await expect(panel.getByText("Alegações Analisadas")).toBeVisible();
  expect(captionCalls()).toBe(1);

  // O registro divergente foi descartado e substituído pelo novo resultado do vídeo correto
  await expect
    .poll(async () => {
      return extension.worker.evaluate(async () => {
        const stored = (await chrome.storage.local.get("video-carlos"))["video-carlos"] as LocalCacheEntry;
        return stored && stored.videoId === "video-carlos" && Array.isArray(stored.claims);
      });
    })
    .toBe(true);
});

test("HU06: Análise com erro não é salva no cache e permite nova tentativa", async ({
  extension,
}) => {
  // Limpa cache
  await extension.worker.evaluate(async () => {
    await chrome.storage.local.clear();
  });

  // Configura página sem legendas
  const { button, panel } = await setupPage(extension.context, "video-sem-legenda", false);

  await button.click();

  await expect(panel.getByRole("alert")).toContainText("Este vídeo não tem legendas");

  // Confirma que nenhuma entrada de sucesso foi salva no storage para esse vídeo
  const stored = await extension.worker.evaluate(async () => {
    return (await chrome.storage.local.get("video-sem-legenda"))["video-sem-legenda"];
  });
  expect(stored).toBeUndefined();
});
