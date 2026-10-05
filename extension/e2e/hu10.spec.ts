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
    const worker = context.serviceWorkers()[0] ?? (await context.waitForEvent("serviceworker"));
    await use({ context, worker });
    await context.close();
  },
});

async function setup(context: BrowserContext, id = "video", captions = true) {
  let captionCalls = 0;
  await context.route("https://www.youtube.com/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/timedtext") {
      captionCalls++;
      await route.fulfill({
        contentType: "text/xml",
        body: `<transcript><text>Um estudo apresenta dados sobre a relacao entre exercicio fisico e qualidade de vida.</text></transcript>`,
      });
    } else {
      await route.fulfill({
        contentType: "text/html",
        body: `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vídeo de teste HU10</title></head><body>
        <main><h1 class="ytd-watch-metadata">Vídeo Teste</h1><div id="channel-name">Canal de testes</div><div id="above-the-fold"></div><div id="movie_player"></div><video></video><a href="#footer">Próximo</a></main>
        <script>
        window.ytInitialPlayerResponse = {
          videoDetails: { videoId: new URLSearchParams(location.search).get('v') },
          captions: {
            playerCaptionsTracklistRenderer: {
              captionTracks: ${captions ? JSON.stringify([{ baseUrl: "https://www.youtube.com/api/timedtext?v=" + id, languageCode: "pt" }]) : "[]"}
            }
          }
        };
        window.hu10 = { click: 0, alertTime: null, blocking: 0 };
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) window.hu10.blocking += Math.max(0, entry.duration - 50);
        }).observe({ type: 'longtask', buffered: true });
        document.addEventListener('click', () => {
          window.hu10.click = performance.timeOrigin + performance.now();
        }, true);
        </script></body></html>`,
      });
    }
  });

  const page = await context.newPage();
  await page.goto(`https://www.youtube.com/watch?v=${id}`);
  const button = page.getByRole("button", { name: "Verificar Veracidade" });
  await expect(button).toBeVisible();
  const panel = page.frameLocator("#evidencia-side-panel");
  await expect(panel.getByRole("button", { name: /Fechar painel/, includeHidden: true })).toBeAttached();
  return { page, button, panel, captionCalls: () => captionCalls };
}

test("HU10: Cenário 1 — Vídeo sem legendas notifica em até 1s e encerra com segurança sem bloquear a aba", async ({ extension }) => {
  const { page, button, panel, captionCalls } = await setup(extension.context, "no-captions-video", false);

  // Monitora reprodução do vídeo e tarefas longas
  await page.evaluate(() => {
    (window as any).pauses = 0;
    document.querySelector("video")!.pause = () => {
      (window as any).pauses++;
    };
  });

  const start = Date.now();
  await button.click();

  // Alerta deve ser exibido com role="alert" informando a impossibilidade técnica
  const alert = panel.getByRole("alert");
  await expect(alert).toContainText("Legendas Indisponíveis");
  await expect(alert).toContainText("não possui transcrição ou legendas ativadas");

  const elapsedMs = Date.now() - start;
  expect(elapsedMs).toBeLessThanOrEqual(1500); // 1.0s com tolerância de frame

  // Player não deve ter sido pausado nem a aba bloqueada
  expect(await page.evaluate(() => (window as any).pauses)).toBe(0);
  const blocking = await page.evaluate(() => (window as any).hu10.blocking);
  expect(blocking).toBeLessThanOrEqual(50);

  // Nenhuma chamada externa a timedtext
  expect(captionCalls()).toBe(0);

  // Botão no player informa o status e permite nova tentativa
  await expect(page.getByRole("button", { name: /Sem legendas/ })).toBeEnabled();

  // Botão de nova tentativa também acessível no painel
  await expect(panel.getByRole("button", { name: "Tentar novamente" })).toBeVisible();

  // Validação de acessibilidade WCAG no painel com o alerta ativo
  const frameElement = await page.$("#evidencia-side-panel");
  const panelFrame = await frameElement?.contentFrame();
  if (panelFrame) {
    const axeResults = await new AxeBuilder({ page: panelFrame as any }).analyze();
    expect(axeResults.violations).toEqual([]);
  }
});

test("HU10: Cenário 2 — Falha temporária da API do YouTube exibe botão de nova tentativa no painel", async ({ extension }) => {
  // Simula falha de rede/API na consulta de legendas
  await extension.worker.evaluate(() => {
    (globalThis as any).originalFetch = fetch;
    globalThis.fetch = async (url) => {
      if (String(url).includes("/api/timedtext")) {
        return new Response("", { status: 503, statusText: "Service Unavailable" });
      }
      return (globalThis as any).originalFetch(url);
    };
  });

  const { button, panel } = await setup(extension.context, "temp-fail-video", true);
  await button.click();

  // Painel deve exibir o alerta com o erro e o botão de nova tentativa
  const alert = panel.getByRole("alert");
  await expect(alert).toContainText("HTTP 503");
  const retryBtn = panel.getByRole("button", { name: "Tentar novamente" });
  await expect(retryBtn).toBeVisible();

  // Restaura a API para simular recuperação
  await extension.worker.evaluate(() => {
    globalThis.fetch = (globalThis as any).originalFetch;
  });

  // Aciona nova tentativa pelo botão dentro do painel
  await retryBtn.click();

  // Verifica que o painel volta ao estado de carregamento e processa com sucesso
  await expect(panel.getByText("Por que essa classificação?")).toBeVisible({ timeout: 10000 });
});
